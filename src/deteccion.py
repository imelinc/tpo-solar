"""Residuo real − esperado, índice relativo a las plantas vecinas, alertas y semáforo.

Dos familias de detectores (se comparan en 04_deteccion):
- Contra el propio modelo: residuo relativo diario con umbral (z robusto) y CUSUM.
- Contra las vecinas (método del notebook de referencia): índice real/esperado dividido por
  la mediana de las plantas cercanas del mismo día y por el "normal" de cada planta, con
  alerta de falla grave (< 0,5), CUSUM e Isolation Forest.
Las funciones `serie_planta`, `diario_flota` y `semaforo_flota` son las que usa el dashboard:
leen solo data/processed y models/ (sin APIs).
"""
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from src.config import DATA_PROCESSED, MODELS
from src.modelos import energia_diaria, preparar
from src.negocio import PRECIO_USD_MWH

MIN_FRAC_ESPERADA = 0.25  # días con menos del 25% de la energía de un día claro típico: sin decisión
MIN_FRAC_SENSOR = 0.3     # sensor de planta < 30% de la irradiancia satelital del día: sensor caído
UMBRAL_GRAVE = 0.5        # índice relativo < 0,5: falla grave (la planta rinde menos de la mitad)
FEATS_ISO = ["indice", "indice_rel", "cambio"]


# ----------------------------------------------------------------------------- residuo propio
def residuo_diario(d: pd.DataFrame, yhat, ref: dict | None = None) -> pd.DataFrame:
    """Por planta y día: energía real y esperada (MWh/MW), residuo normalizado por capacidad
    (real − esperado, MWh/MW) y residuo relativo (residuo / esperado).

    Quedan sin decisión (residuo_rel NaN): los días muy nublados (esperado < 25% del p90 de la
    planta, donde el error relativo del modelo es grande) y los días con el sensor de planta
    caído (lee < 30% de lo que da el satélite; station09 desde el 4/6/2019). `ref` =
    {plant_id: p90 de e_esp} guardado al calibrar; si no se pasa, se calcula con los mismos datos.
    """
    e = energia_diaria(d, yhat)
    e["residuo"] = e["e_real"] - e["e_esp"]
    p90 = (e["plant_id"].map(ref) if ref is not None
           else e.groupby("plant_id")["e_esp"].transform(lambda s: s.quantile(0.9)))
    e["falla_sensor"] = False
    if {"poa", "om_poa"} <= set(d.columns):
        irr = d.groupby(["plant_id", "date_local"])[["poa", "om_poa"]].sum().reset_index()
        irr["falla_sensor"] = irr["poa"] < MIN_FRAC_SENSOR * irr["om_poa"]
        e = e.drop(columns="falla_sensor").merge(irr[["plant_id", "date_local", "falla_sensor"]],
                                                 on=["plant_id", "date_local"], how="left")
    decide = (e["e_esp"] >= MIN_FRAC_ESPERADA * p90) & ~e["falla_sensor"]
    e["residuo_rel"] = (e["residuo"] / e["e_esp"]).where(decide)
    return e


def calibrar(residuo_rel_sano: pd.Series, z: float = 3.0, k_sigma: float = 0.5, h_sigma: float = 4.0) -> dict:
    """Parámetros del detector a partir de residuos de días sanos (fuera de muestra).
    sigma robusta = 1,4826 × MAD. Umbral: mediana − z·sigma. CUSUM: k = 0,5σ, h = 4σ."""
    r = residuo_rel_sano.dropna()
    med = float(r.median())
    sigma = float(1.4826 * (r - med).abs().median())
    return {"mediana": med, "sigma": sigma, "umbral": med - z * sigma, "k": k_sigma * sigma, "h": h_sigma * sigma}


def alarmas_umbral(r: pd.Series, p: dict) -> pd.Series:
    return (r < p["umbral"]).fillna(False)


def alarmas_cusum(r: pd.Series, p: dict) -> pd.Series:
    """CUSUM unilateral hacia abajo sobre el residuo centrado. Acumula los días por debajo de
    lo normal (mediana − k) y alarma cuando la suma pasa de −h. Los días sin decisión (NaN) no suman.
    La suma tiene un piso en −1,5·h: así, cuando la falla termina, la alarma se apaga en unos
    días (0,5·h/k = 4 días normales) en vez de arrastrar la memoria de una caída grande."""
    s, out = 0.0, []
    for x in (r - p["mediana"]).to_numpy():
        if not np.isnan(x):
            s = max(-1.5 * p["h"], min(0.0, s + x + p["k"]))
        out.append(s < -p["h"])
    return pd.Series(out, index=r.index)


def detectar(e: pd.DataFrame, params: dict) -> pd.DataFrame:
    """Agrega alerta_umbral y alerta_cusum por planta. `params` = {plant_id: calibrar(...)}."""
    e = e.sort_values(["plant_id", "date_local"]).copy()
    e["alerta_umbral"] = False
    e["alerta_cusum"] = False
    for p, idx in e.groupby("plant_id").groups.items():
        if p in params:
            e.loc[idx, "alerta_umbral"] = alarmas_umbral(e.loc[idx, "residuo_rel"], params[p]).to_numpy()
            e.loc[idx, "alerta_cusum"] = alarmas_cusum(e.loc[idx, "residuo_rel"], params[p]).to_numpy()
    return e


# ----------------------------------------------------------------------------- vecinas
def distancias_km(lat: pd.Series, lon: pd.Series) -> pd.DataFrame:
    """Matriz de distancias (haversine) entre los elementos indexados por el índice de lat/lon."""
    la, lo = np.radians(lat.to_numpy()), np.radians(lon.to_numpy())
    a = (np.sin((la[:, None] - la) / 2) ** 2
         + np.cos(la[:, None]) * np.cos(la) * np.sin((lo[:, None] - lo) / 2) ** 2)
    return pd.DataFrame(6371 * 2 * np.arcsin(np.sqrt(a)), index=lat.index, columns=lat.index)


def vecinas_por_distancia(dist: pd.DataFrame, referencias, radio_km: float = 100) -> dict:
    """{planta: [vecinas]}: plantas de referencia (sanas, del entrenamiento) a menos de `radio_km`."""
    return {p: [q for q in referencias if q != p and dist.loc[p, q] <= radio_km] for p in dist.index}


def indice_relativo(e: pd.DataFrame, vecinas: dict, normal: dict | None = None) -> pd.DataFrame:
    """indice = real / esperado (solo días con decisión). indice_rel = indice / mediana del
    índice de las vecinas ese día, dividido por el "normal" de la planta (su mediana histórica
    de ese cociente), así 1 = "rinde como siempre respecto de sus vecinas". Sin vecinas con
    dato ese día (station01 no tiene ninguna a menos de 100 km) se usa el índice propio / normal.
    Agrega `cambio` = diferencia diaria de indice_rel (para Isolation Forest)."""
    e = e.sort_values(["plant_id", "date_local"]).copy()
    e["indice"] = (e["e_real"] / e["e_esp"]).where(e["residuo_rel"].notna())
    tabla = e.pivot_table(index="date_local", columns="plant_id", values="indice")
    med = pd.Series(np.nan, index=e.index)
    for p, idx in e.groupby("plant_id").groups.items():
        vs = [v for v in vecinas.get(p, []) if v in tabla.columns]
        if vs:
            med.loc[idx] = e.loc[idx, "date_local"].map(tabla[vs].median(axis=1)).to_numpy()
    e["con_vecinas"] = med.notna()
    e["indice_rel"] = e["indice"] / med.fillna(1.0)
    if normal is None:
        normal = e.groupby("plant_id")["indice_rel"].median().to_dict()
    e["indice_rel"] = e["indice_rel"] / e["plant_id"].map(normal)
    e["cambio"] = e.groupby("plant_id")["indice_rel"].diff().fillna(0)
    return e


def calibrar_combinado(e_sano: pd.DataFrame, contaminacion: float = 0.01, semilla: int = 0) -> dict:
    """Parámetros de las alertas combinadas a partir de días sanos con indice_rel ya calculado:
    CUSUM por planta sobre (indice_rel − 1) e Isolation Forest común a todas las plantas."""
    ok = e_sano.dropna(subset=FEATS_ISO)
    cusum = {p: calibrar(g["indice_rel"] - 1) for p, g in ok.groupby("plant_id")}
    iso = IsolationForest(n_estimators=300, contamination=contaminacion, random_state=semilla).fit(ok[FEATS_ISO])
    return {"cusum": cusum, "cusum_generico": calibrar(ok["indice_rel"] - 1), "iso": iso}


def alertas_combinadas(e: pd.DataFrame, cal: dict) -> pd.DataFrame:
    """Falla grave (indice_rel < 0,5), pérdida sostenida (CUSUM) y día anómalo (Isolation
    Forest, solo si además rinde menos de 0,95). `alerta` = cualquiera de las tres."""
    e = e.sort_values(["plant_id", "date_local"]).copy()
    e["alerta_grave"] = (e["indice_rel"] < UMBRAL_GRAVE).fillna(False)
    e["alerta_cusum_rel"] = False
    for p, idx in e.groupby("plant_id").groups.items():
        par = cal["cusum"].get(p, cal["cusum_generico"])
        e.loc[idx, "alerta_cusum_rel"] = alarmas_cusum(e.loc[idx, "indice_rel"] - 1, par).to_numpy()
    e["alerta_iso"] = False
    ok = e[FEATS_ISO].notna().all(axis=1)
    if ok.any():
        e.loc[ok, "alerta_iso"] = (cal["iso"].predict(e.loc[ok, FEATS_ISO]) == -1) & (e.loc[ok, "indice_rel"] < 0.95)
    e["alerta"] = e["alerta_grave"] | e["alerta_cusum_rel"] | e["alerta_iso"]
    e["tipo_alerta"] = np.select([e["alerta_grave"], e["alerta_cusum_rel"], e["alerta_iso"]],
                                 ["Falla grave", "Pérdida sostenida", "Día anómalo"], "")
    return e


# ----------------------------------------------------------------------------- para la app
def _cargar():
    meta = joblib.load(MODELS / "modelo_potencia.pkl")
    det = joblib.load(MODELS / "detector.pkl")
    return meta, det


def _esperado(d: pd.DataFrame, meta: dict, limpia: bool) -> pd.Series:
    """Modelo propio para las plantas del entrenamiento; 'planta típica' para el resto."""
    out = pd.Series(np.nan, index=d.index)
    propias = d["plant_id"].isin(meta["modelo"].plantas_)
    if propias.any():
        out[propias] = meta["modelo"].predict(d[propias], limpia=limpia)
    if (~propias).any():
        out[~propias] = meta["modelo_generico"].predict(d[~propias], limpia=limpia)
    return out


def diario_flota(desde: str, hasta: str, plantas=None) -> pd.DataFrame:
    """Tabla diaria de toda la flota (o de `plantas`): energía real y esperada con la planta
    limpia (MWh), residuo, índice relativo a las vecinas y alertas. Las vecinas siempre se
    calculan con la flota completa, aunque se pida una sola planta."""
    meta, det = _cargar()
    A = pd.read_parquet(DATA_PROCESSED / "dataset_A_pvod_hourly.parquet")
    A = A[A["date_local"].astype(str).between(desde, hasta)]
    if A.empty:
        raise ValueError(f"Sin datos entre {desde} y {hasta}")
    d = preparar(A, meta["escenario"])
    d = d[~d["dato_congelado"]]
    d["esperado"] = _esperado(d, meta, limpia=True)
    e = residuo_diario(d, d["esperado"], det["ref_e_esp"])
    e = detectar(e, {p: det["propio"].get(p, det["propio_generico"]) for p in e["plant_id"].unique()})
    e = alertas_combinadas(indice_relativo(e, det["vecinas"], det["normal"]), det["combinado"])
    e["propio_umbral_o_cusum"] = e["alerta_umbral"] | e["alerta_cusum"]
    e["combinado_vecinas"] = e["alerta"]
    e["alerta_elegida"] = e[det["metodo"]]  # el detector elegido en 04_deteccion
    e["modelo"] = np.where(e["plant_id"].isin(meta["modelo"].plantas_), "propio", "planta típica")
    e["energia_real_mwh"] = e["e_real"] * e["cap_mw"]
    e["energia_esperada_mwh"] = e["e_esp"] * e["cap_mw"]
    e["perdida_mwh"] = (-e["residuo"] * e["cap_mw"]).clip(lower=0).where(e["residuo_rel"].notna(), 0.0)
    if plantas is not None:
        e = e[e["plant_id"].isin(plantas)]
    return e.reset_index(drop=True)


def serie_planta(planta: str, desde: str, hasta: str):
    """Para el dashboard: lo real, lo esperado, el residuo y las alertas de una planta.
    Devuelve (horario, diario):
    - horario: timestamp, real y esperado (MW, con la planta limpia) y residuo (MW y fracción de capacidad)
    - diario: energía real y esperada (MWh), pérdida, índice relativo y alertas (diario_flota)"""
    meta, _ = _cargar()
    A = pd.read_parquet(DATA_PROCESSED / "dataset_A_pvod_hourly.parquet")
    A = A[(A["plant_id"] == planta) & A["date_local"].astype(str).between(desde, hasta)]
    if A.empty:
        raise ValueError(f"Sin datos para {planta} entre {desde} y {hasta}")
    d = preparar(A, meta["escenario"])
    esp = _esperado(d, meta, limpia=True)
    cap = d["plant_capacity_mw"].iloc[0]
    horario = pd.DataFrame({"timestamp": d["timestamp_local_utc8"], "real_mw": d["pvod_power"],
                            "esperado_mw": esp * cap, "residuo_norm": d["pvod_power_norm"] - esp,
                            "dato_congelado": d["dato_congelado"]})
    horario["residuo_mw"] = horario["real_mw"] - horario["esperado_mw"]
    return horario.reset_index(drop=True), diario_flota(desde, hasta, plantas=[planta])


def semaforo(e: pd.DataFrame, fecha: str, precio_usd_mwh: float = PRECIO_USD_MWH, dias: int = 3) -> pd.DataFrame:
    """Estado de cada planta a `fecha` a partir de la tabla de diario_flota (últimos 7 días).
    Rojo: falla grave hoy o rendimiento relativo de los últimos `dias` < 0,8 -> visita técnica hoy.
    Amarillo: cualquier otra alerta hoy o rendimiento < 0,95 -> revisar esta semana.
    Verde: nada. Pérdida en USD/día = promedio de los últimos `dias` × precio."""
    fecha = str(fecha)
    ult = e[(e["date_local"].astype(str) <= fecha)
            & (e["date_local"].astype(str) > str((pd.Timestamp(fecha) - pd.Timedelta(days=7)).date()))]
    filas = []
    for p, g in ult.sort_values("date_local").groupby("plant_id"):
        hoy = g.iloc[-1]
        rend = g["indice_rel"].dropna().tail(dias).mean()
        alerta = hoy["tipo_alerta"] if hoy["alerta"] else ""
        if alerta == "Falla grave" or rend < 0.8:
            color, accion = "rojo", "Visita técnica hoy"
        elif alerta or rend < 0.95:
            color, accion = "amarillo", "Revisar esta semana"
        else:
            color, accion = "verde", "Nada"
        if g["falla_sensor"].tail(dias).any():
            accion += " (sensor de irradiancia caído: revisar el piranómetro)"
        filas.append({"plant_id": p, "fecha_dato": hoy["date_local"], "estado": color, "accion": accion,
                      "alerta": alerta or "—", "rendimiento_vs_vecinas": rend,
                      "perdida_usd_dia": g["perdida_mwh"].tail(dias).mean() * precio_usd_mwh,
                      "modelo": hoy["modelo"]})
    return pd.DataFrame(filas)


def semaforo_flota(fecha: str, precio_usd_mwh: float = PRECIO_USD_MWH) -> pd.DataFrame:
    """Semáforo de la flota para una fecha (verde, amarillo o rojo, con acción y USD/día)."""
    desde = str((pd.Timestamp(fecha) - pd.Timedelta(days=60)).date())  # historia para el CUSUM
    return semaforo(diario_flota(desde, str(fecha)), fecha, precio_usd_mwh)
