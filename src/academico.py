"""Defensa: generación mensual de un parque solar argentino.

Estima el factor de capacidad con la ubicación y el clima del mes.
La energía en MWh es factor × potencia instalada × horas del mes.
Entrena solo con mediciones reales. El año elige el clima; no es una causa física.
"""
from __future__ import annotations

import calendar
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold
from sklearn.tree import DecisionTreeRegressor

from src.config import DATA_PROCESSED

SEED = 42
UMBRAL_KM = 150
PASO = 0.2
NUM = ["om_ghi_kwh_m2_mes", "lat", "lon", "om_temp_max_media_c", "om_nubosidad_media_pct"]
ORDEN = ["lineal_simple", "lineal_multiple", "arbol", "rf", "xgb"]
MODELOS = {"lineal_simple": "Regresión lineal simple", "lineal_multiple": "Regresión lineal múltiple",
           "arbol": "Árbol de regresión", "rf": "Random Forest", "xgb": "XGBoost"}
COORDS_OK = ["SE_CAMMESA_via_WRI", "osm_parque", "WikiSolar_via_GPPD_aprox", "osm_localidad_inferida_del_nombre"]
POTENCIA_DUDOSA = ["CUM2FV", "PINFFV", "VANGFV"]
ENTRADAS = {"om_ghi_kwh_m2_mes": "irradiación mensual", "lat": "latitud", "lon": "longitud",
            "om_temp_max_media_c": "temperatura máxima", "om_nubosidad_media_pct": "nubosidad", "mes": "mes"}


def preparar(b: pd.DataFrame) -> pd.DataFrame:
    """Deja meses comparables. Conserva ceros posteriores al primer mes con generación."""
    d = b.copy()
    d["fecha"] = pd.to_datetime(d["fecha"]).dt.strftime("%Y-%m-%d")
    d["mes"] = pd.to_datetime(d["fecha"]).dt.month.astype(int)
    d["anio"] = pd.to_datetime(d["fecha"]).dt.year.astype(int)
    ok = d["coord_source"].isin(COORDS_OK) & d["potencia_mw"].gt(0) & d["factor_capacidad"].between(0, 0.45)
    ok &= d[NUM].notna().all(axis=1)
    ventana = d["fecha"].between("2022-01-01", "2025-09-01")
    ok &= ~d["central"].isin(POTENCIA_DUDOSA) | ventana
    d = d.loc[ok].copy()
    inicio = d.loc[d["energia_mwh"].gt(0)].groupby("central")["fecha"].min()
    d = d.loc[d["fecha"].ge(d["central"].map(inicio))].copy()
    return d.sort_values(["central", "fecha"]).reset_index(drop=True)


def meses_dummies(tipo: str) -> list[int]:
    # Enero queda como referencia de la recta. Con las doce columnas y el intercepto, la lineal es singular.
    if tipo == "lineal_simple":
        return []
    if tipo.startswith("lineal"):
        return list(range(2, 13))
    return list(range(1, 13))


def nombres_columnas(tipo: str) -> list[str]:
    if tipo == "lineal_simple":
        return ["om_ghi_kwh_m2_mes"]
    return NUM + [f"mes_{m}" for m in meses_dummies(tipo)]


def crear_modelo(tipo: str):
    if tipo.startswith("lineal"):
        return LinearRegression()
    if tipo == "arbol":
        return DecisionTreeRegressor(max_depth=8, min_samples_leaf=10, random_state=SEED)
    if tipo == "rf":
        return RandomForestRegressor(n_estimators=80, min_samples_leaf=5, max_features=0.8,
                                     n_jobs=1, random_state=SEED)
    if tipo == "xgb":
        from xgboost import XGBRegressor
        return XGBRegressor(n_estimators=120, max_depth=4, learning_rate=0.08,
                            subsample=0.8, colsample_bytree=0.8, n_jobs=1, random_state=SEED)
    raise ValueError("Modelo fuera del alcance curricular")


def matriz(df: pd.DataFrame, medianas: dict, tipo: str) -> np.ndarray:
    cols = nombres_columnas(tipo)
    parts = []
    for c in cols:
        if c.startswith("mes_"):
            parts.append((df["mes"].astype(int) == int(c.split("_")[1])).to_numpy(dtype=float))
        else:
            parts.append(df[c].fillna(medianas[c]).to_numpy(dtype=float))
    return np.column_stack(parts)


def metricas_regresion(y, pred) -> dict:
    y, pred = np.asarray(y, float), np.asarray(pred, float)
    return {"mae": float(mean_absolute_error(y, pred)), "mse": float(mean_squared_error(y, pred)),
            "rmse": float(np.sqrt(mean_squared_error(y, pred))), "r2": float(r2_score(y, pred)), "n": int(len(y))}


def km(lat1, lon1, lat2, lon2) -> float:
    x = np.radians(lon2 - lon1) * np.cos(np.radians((lat1 + lat2) / 2))
    y = np.radians(lat2 - lat1)
    return float(6371.0 * np.hypot(x, y))


def entradas_de(tipo: str) -> list[str]:
    if tipo == "lineal_simple":
        return [ENTRADAS["om_ghi_kwh_m2_mes"]]
    return [ENTRADAS[c] for c in NUM] + ["mes"]


def entrenar(d: pd.DataFrame):
    train = d[(d["fecha"] < "2024-01-01") & d["energia_mwh"].gt(0)]
    val = d[d["fecha"].between("2024-01-01", "2024-12-31")]
    test = d[d["fecha"] >= "2025-01-01"]
    if train.empty or val.empty or test.empty:
        raise ValueError("Falta alguna partición")
    medianas = train[NUM].median().to_dict()
    comparacion, ajustados = [], {}
    for tipo in ORDEN:
        print("Entrenando", MODELOS[tipo], flush=True)
        est = crear_modelo(tipo).fit(matriz(train, medianas, tipo), train["factor_capacidad"])
        ajustados[tipo] = est
        fila = {"id": tipo, "nombre": MODELOS[tipo]}
        for nombre, parte in (("train", train), ("validacion", val), ("test", test)):
            pred = np.clip(est.predict(matriz(parte, medianas, tipo)), 0, 1)
            fila[nombre] = metricas_regresion(parte["factor_capacidad"], pred)
        comparacion.append(fila)
    elegido = sorted(comparacion, key=lambda r: (r["validacion"]["rmse"], ORDEN.index(r["id"])))[0]["id"]
    est = ajustados[elegido]
    pred = np.clip(est.predict(matriz(d, medianas, elegido)), 0, 1)
    notas = []
    for tr, va in GroupKFold(5).split(train, groups=train["central"]):
        trd, vad = train.iloc[tr], train.iloc[va]
        med = trd[NUM].median().to_dict()
        m = crear_modelo(elegido).fit(matriz(trd, med, elegido), trd["factor_capacidad"])
        p = np.clip(m.predict(matriz(vad, med, elegido)), 0, 1)
        notas.append(metricas_regresion(vad["factor_capacidad"], p))
    parques_train = train.groupby("central")[["lat", "lon"]].first()
    resumen = {"elegido": elegido, "nombre": MODELOS[elegido], "comparacion": comparacion,
               "entradas": entradas_de(elegido), "unidad_target": "factor de capacidad (MWh / MW / horas del mes)",
               "protocolo": "Entrenamiento hasta 2023, solo meses con generación. Selección por RMSE en 2024. Prueba retrospectiva desde 2025.",
               "cv_parques": {"rmse": float(np.mean([n["rmse"] for n in notas])),
                              "mae": float(np.mean([n["mae"] for n in notas])), "folds": notas,
                              "nota": "Cinco grupos por parque, solo con años de entrenamiento. Describe un parque que no entró a ese ajuste. No se usó para elegir el modelo."},
               "rango": {"lat_min": float(parques_train.lat.min()), "lat_max": float(parques_train.lat.max()),
                         "lon_min": float(parques_train.lon.min()), "lon_max": float(parques_train.lon.max())},
               "ceros_conservados": int(d["energia_mwh"].eq(0).sum()), "n": int(len(d)),
               "parques": int(d["central"].nunique()), "umbral_km": UMBRAL_KM}
    if hasattr(est, "feature_importances_"):
        nombres = nombres_columnas(elegido)
        resumen["importancias"] = sorted(
            [{"variable": n, "valor": float(v)} for n, v in zip(nombres, est.feature_importances_)],
            key=lambda r: -r["valor"])[:8]
    print("Elegido por validación:", MODELOS[elegido], flush=True)
    return est, {k: float(v) for k, v in medianas.items()}, resumen, pred


def tablas_clima(d: pd.DataFrame) -> tuple[list, list, list]:
    """Un parque, su clima mensual y el promedio anterior a 2024.

    ponytail: un sitio nuevo copia el clima del parque más cercano. Una grilla
    meteorológica local haría falta si la distancia entre parques importa.
    """
    base = d.groupby("central", as_index=False).agg(
        nombre=("central_descripcion", "first"), provincia=("provincia", "first"),
        lat=("lat", "first"), lon=("lon", "first"), potencia_mw=("potencia_mw", "median"),
        coord_source=("coord_source", "first"))
    base["nombre"] = base["nombre"].fillna(base["central"])
    base["provincia"] = base["provincia"].fillna("")
    base["i"] = np.arange(len(base))
    idx = dict(zip(base["central"], base["i"]))
    clima = []
    for r in d.itertuples(index=False):
        clima.append({"i": int(idx[r.central]), "anio": int(r.anio), "mes": int(r.mes),
                      "ghi": float(r.om_ghi_kwh_m2_mes), "temp": float(r.om_temp_max_media_c),
                      "nub": float(r.om_nubosidad_media_pct)})
    # ponytail: si el parque cercano no tiene historia anterior a 2024, el promedio usa todos sus años.
    tipico = []
    for central, g in d.groupby("central"):
        hist = g[g["fecha"] < "2024-01-01"]
        uso = hist if len(hist) else g
        for mes, m in uso.groupby("mes"):
            tipico.append({"i": int(idx[central]), "mes": int(mes), "ghi": float(m.om_ghi_kwh_m2_mes.mean()),
                           "temp": float(m.om_temp_max_media_c.mean()), "nub": float(m.om_nubosidad_media_pct.mean())})
    parques = base.to_dict("records")
    for p in parques:
        p["i"] = int(p["i"])
        p["potencia_mw"] = float(p["potencia_mw"])
        p["lat"], p["lon"] = float(p["lat"]), float(p["lon"])
    return parques, clima, tipico


def _eje(a: float, b: float, paso: float) -> np.ndarray:
    n = int(np.floor((b - a) / paso + 1e-9)) + 1
    xs = a + np.arange(n) * paso
    if xs[-1] < b - 1e-6:
        xs = np.append(xs, b)
    return np.round(xs, 5)


def _indice_clima(clima, tipico):
    return ({(r["i"], r["anio"], r["mes"]): r for r in clima}, {(r["i"], r["mes"]): r for r in tipico})


def construir_grilla(est, tipo: str, medianas: dict, parques: list, clima: list, tipico: list, rango: dict) -> dict:
    """Factor de capacidad en celdas de 0,2°. El navegador lee esta tabla; no reimplementa el modelo.

    ponytail: paso fijo de 0,2°. Una celda más fina si la defensa necesita un punto intermedio.
    """
    lats, lons = _eje(rango["lat_min"], rango["lat_max"], PASO), _eje(rango["lon_min"], rango["lon_max"], PASO)
    clat, clon = np.meshgrid(lats, lons, indexing="ij")
    clat, clon = clat.ravel(), clon.ravel()
    plat = np.array([p["lat"] for p in parques])
    plon = np.array([p["lon"] for p in parques])
    lat1, lon1 = np.radians(clat)[:, None], np.radians(clon)[:, None]
    lat2, lon2 = np.radians(plat)[None, :], np.radians(plon)[None, :]
    dist = 6371 * np.hypot((lon2 - lon1) * np.cos((lat1 + lat2) / 2), lat2 - lat1)
    cercano = dist.argmin(axis=1)
    obs, tip = _indice_clima(clima, tipico)
    anios = sorted({r["anio"] for r in clima})
    n, factores = len(clat), {}
    for anio in [0, *anios]:
        ghi = np.full(n * 12, np.nan)
        temp, nub, mes = ghi.copy(), ghi.copy(), np.zeros(n * 12)
        lat = np.repeat(clat, 12)
        lon = np.repeat(clon, 12)
        for c in range(n):
            park = int(parques[int(cercano[c])]["i"])
            for m in range(1, 13):
                fila = obs.get((park, anio, m)) if anio else None
                if fila is None:
                    fila = tip.get((park, m))
                if fila is None:
                    continue
                k = c * 12 + (m - 1)
                ghi[k], temp[k], nub[k], mes[k] = fila["ghi"], fila["temp"], fila["nub"], m
        df = pd.DataFrame({"om_ghi_kwh_m2_mes": ghi, "lat": lat, "lon": lon,
                           "om_temp_max_media_c": temp, "om_nubosidad_media_pct": nub, "mes": mes})
        valid = df[NUM].notna().all(axis=1) & df["mes"].gt(0)
        pred = np.full(len(df), np.nan)
        if valid.any():
            pred[valid.to_numpy()] = np.clip(est.predict(matriz(df.loc[valid], medianas, tipo)), 0, 1)
        factores[str(anio)] = [None if not np.isfinite(v) else round(float(v), 6) for v in pred]
        print("Grilla", anio or "típico", flush=True)
    return {"paso": PASO, "lats": lats.tolist(), "lons": lons.tolist(), "anios": anios, "factores": factores}


def consultar(grilla: dict, parques: list, clima: list, tipico: list, rango: dict,
              lat: float, lon: float, anio: int, potencia_mw: float) -> dict:
    if potencia_mw <= 0:
        raise ValueError("La potencia tiene que ser mayor que cero")
    anio = int(anio)
    lats, lons = np.asarray(grilla["lats"], float), np.asarray(grilla["lons"], float)
    i, j = int(np.argmin(np.abs(lats - lat))), int(np.argmin(np.abs(lons - lon)))
    slat, slon = float(lats[i]), float(lons[j])
    distancias = [km(slat, slon, p["lat"], p["lon"]) for p in parques]
    parque = parques[int(np.argmin(distancias))]
    obs, tip = _indice_clima(clima, tipico)
    clave = str(anio) if anio in grilla["anios"] else "0"
    base = (i * len(lons) + j) * 12
    tabla = grilla["factores"][clave]
    meses, modos = [], []
    energia = horas = 0.0
    for mes in range(1, 13):
        factor = tabla[base + mes - 1]
        fila = obs.get((parque["i"], anio, mes))
        modo = "observado" if fila is not None else "tipico"
        if fila is None and tip.get((parque["i"], mes)) is None:
            modo = None
        if factor is None or modo is None:
            continue
        h = calendar.monthrange(anio, mes)[1] * 24
        gwh = factor * potencia_mw * h / 1000
        energia += gwh
        horas += h
        modos.append(modo)
        meses.append({"mes": mes, "factor": factor, "gwh": gwh, "clima": modo})
    if not meses:
        raise ValueError("Ese sitio no tiene clima de referencia")
    modo = modos[0] if len(set(modos)) == 1 else "mixto"
    dentro = rango["lat_min"] <= lat <= rango["lat_max"] and rango["lon_min"] <= lon <= rango["lon_max"]
    return {"lat": float(lat), "lon": float(lon), "anio": anio, "potencia_mw": float(potencia_mw),
            "lat_celda": slat, "lon_celda": slon, "distancia_celda_km": km(lat, lon, slat, slon),
            "energia_gwh": energia, "factor": energia * 1000 / (potencia_mw * horas),
            "modo": modo, "dentro": bool(dentro), "distancia_km": float(min(distancias)),
            "nombre": parque["nombre"], "provincia": parque["provincia"], "central": parque["central"],
            "meses": meses, "incompleto": len(meses) < 12}


def _presets(grilla, parques, clima, tipico, rango) -> list:
    lats, lons = np.asarray(grilla["lats"], float), np.asarray(grilla["lons"], float)
    centro = min(parques, key=lambda p: (p["lat"] - float(np.median(lats))) ** 2 + (p["lon"] - float(np.median(lons))) ** 2)
    i, j = int(np.argmin(np.abs(lats - centro["lat"]))), int(np.argmin(np.abs(lons - centro["lon"])))
    j = min(j + 1, len(lons) - 1) if j + 1 < len(lons) else j - 1
    lat, lon = float(lats[i]), float(lons[j])
    base = [
        {"nombre": "Sitio nuevo, 2023", "lat": lat, "lon": lon, "anio": 2023, "potencia_mw": 10},
        {"nombre": "Mismo sitio, 2028", "lat": lat, "lon": lon, "anio": 2028, "potencia_mw": 10},
        {"nombre": "Mismo sitio, 2026", "lat": lat, "lon": lon, "anio": 2026, "potencia_mw": 10},
        {"nombre": "Ushuaia", "lat": -54.8, "lon": -68.3, "anio": 2023, "potencia_mw": 10},
        {"nombre": "Sitio nuevo, 20 MW", "lat": lat, "lon": lon, "anio": 2023, "potencia_mw": 20},
    ]
    for item in base:
        item["resultado"] = consultar(grilla, parques, clima, tipico, rango,
                                     item["lat"], item["lon"], item["anio"], item["potencia_mw"])
    return base


def serializable(x):
    if isinstance(x, dict):
        return {str(k): serializable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [serializable(v) for v in x]
    if isinstance(x, (float, np.floating)):
        return float(x) if np.isfinite(x) else None
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.bool_,)):
        return bool(x)
    if isinstance(x, pd.Timestamp):
        return x.isoformat()
    return x


def construir(destino: Path | None = None):
    destino = destino or DATA_PROCESSED
    destino.mkdir(parents=True, exist_ok=True)
    d = preparar(pd.read_parquet(DATA_PROCESSED / "dataset_B_argentina_mensual.parquet"))
    est, medianas, resumen, pred = entrenar(d)
    d = d.assign(pred=pred)
    d["particion"] = np.select([d["fecha"] < "2024-01-01", d["fecha"] < "2025-01-01"],
                               ["entrenamiento", "validación"], default="prueba")
    parques, clima, tipico = tablas_clima(d)
    grilla = construir_grilla(est, resumen["elegido"], medianas, parques, clima, tipico, resumen["rango"])
    presets = _presets(grilla, parques, clima, tipico, resumen["rango"])
    ceros = d[d["energia_mwh"].eq(0) & d["particion"].eq("prueba")]
    ejemplo_parque = ceros["central"].iloc[0] if len(ceros) else d["central"].iloc[0]
    serie = d[["central", "central_descripcion", "provincia", "fecha", "factor_capacidad", "pred",
               "energia_gwh", "particion", "potencia_mw"]].rename(columns={"central_descripcion": "nombre"})
    datos = {"version": 2, "pais": "Argentina", "fecha_evaluacion": "2026-10-29", "defensa": "2026-11-12",
             "regresion": resumen, "grilla": grilla, "parques": parques, "clima": clima, "tipico": tipico,
             "umbral_km": UMBRAL_KM, "rango": resumen["rango"], "presets": presets,
             "ejemplo_parque": ejemplo_parque,
             "serie": serie.to_dict("records"),
             "pregunta": "Con un lugar, un año y una potencia, estima la energía del año usando el clima de ese lugar."}
    datos = serializable(datos)
    ruta = destino / "defensa_evidencia.json"
    ruta.write_text(json.dumps(datos, ensure_ascii=False, allow_nan=False, separators=(",", ":")))
    d.to_parquet(destino / "defensa_argentina.parquet", index=False)
    print("Evidencia guardada:", ruta, flush=True)
    return datos


if __name__ == "__main__":
    construir()
