"""Residuo real − esperado, detectores de bajo rendimiento y la función que usa el dashboard."""
import json

import joblib
import numpy as np
import pandas as pd

from src.config import DATA_PROCESSED, MODELS
from src.modelos import energia_diaria, preparar

MIN_FRAC_ESPERADA = 0.25  # días con menos del 25% de la energía de un día claro típico: sin decisión


def residuo_diario(d: pd.DataFrame, yhat, ref: dict | None = None) -> pd.DataFrame:
    """Por planta y día: energía real y esperada (MWh/MW), residuo normalizado por capacidad
    (real − esperado, MWh/MW) y residuo relativo (residuo / esperado). Los días muy nublados
    (esperado < 25% del p90 de la planta) quedan con residuo_rel NaN: ahí el error relativo
    del modelo es grande y no conviene decidir. `ref` = {plant_id: p90 de e_esp} guardado al
    calibrar; si no se pasa, se calcula con los mismos datos."""
    e = energia_diaria(d, yhat)
    e["residuo"] = e["e_real"] - e["e_esp"]
    p90 = (e["plant_id"].map(ref) if ref is not None
           else e.groupby("plant_id")["e_esp"].transform(lambda s: s.quantile(0.9)))
    e["residuo_rel"] = (e["residuo"] / e["e_esp"]).where(e["e_esp"] >= MIN_FRAC_ESPERADA * p90)
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


def serie_planta(planta: str, desde: str, hasta: str):
    """Para el dashboard: lo real, lo esperado, el residuo y las alertas de una planta.

    Lee solo data/processed y models/ (sin APIs). Devuelve (horario, diario):
    - horario: timestamp, real, esperado y residuo (MW y fracción de capacidad)
    - diario: energía real y esperada (MWh), residuo, residuo_rel y alertas
    """
    meta = joblib.load(MODELS / "modelo_potencia.pkl")
    det = json.loads((MODELS / "detector.json").read_text())
    A = pd.read_parquet(DATA_PROCESSED / "dataset_A_pvod_hourly.parquet")
    A = A[(A["plant_id"] == planta) & A["date_local"].astype(str).between(desde, hasta)]
    if A.empty:
        raise ValueError(f"Sin datos para {planta} entre {desde} y {hasta}")
    d = preparar(A, meta["escenario"])
    modelo = meta["modelo"] if planta in meta["modelo"].plantas_ else meta["modelo_generico"]
    d["esperado_norm"] = modelo.predict(d)
    cap = d["plant_capacity_mw"].iloc[0]
    horario = pd.DataFrame({"timestamp": d["timestamp_local_utc8"], "real_mw": d["pvod_power"],
                            "esperado_mw": d["esperado_norm"] * cap,
                            "residuo_norm": d["pvod_power_norm"] - d["esperado_norm"]})
    horario["residuo_mw"] = horario["real_mw"] - horario["esperado_mw"]
    params = det["plantas"].get(planta, det["generico"])
    diario = detectar(residuo_diario(d, d["esperado_norm"], {planta: params["ref_e_esp"]}), {planta: params})
    diario["alerta"] = diario[f"alerta_{det['metodo']}"]
    diario["energia_real_mwh"] = diario["e_real"] * cap
    diario["energia_esperada_mwh"] = diario["e_esp"] * cap
    diario["residuo_mwh"] = diario["residuo"] * cap
    return horario.reset_index(drop=True), diario.reset_index(drop=True)
