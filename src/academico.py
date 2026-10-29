"""Versión de defensa: modelos, gráficos y métricas respaldados por los apuntes.

Entrena exclusivamente con observaciones reales. Los escenarios sintéticos se usan
solo para comprobar una regla de boxplot aplicada a residuos (clases 4, 9 y 12).
No depende del híbrido físico ni de los detectores experimentales anteriores.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import confusion_matrix, mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.tree import DecisionTreeRegressor

from src.config import DATA_PROCESSED, ROOT

SEED = 42
TRAIN_END = "2019-04-01"
TEST_START = "2019-05-01"
MODELOS = {"lineal_simple": "Regresión lineal simple", "lineal_multiple": "Regresión lineal múltiple",
           "arbol": "Árbol de regresión", "rf": "Random Forest", "xgb": "XGBoost"}
FEATURES = ["irradiancia", "temperatura", "viento", "hora", "mes", "dia_del_anio"]
CLASES = {
    "etl": {"clase": 2, "tema": "Pipeline y ETL", "url": "https://www.notion.so/3bb096bfe0b280e59278f280f481a77a"},
    "calidad": {"clase": 3, "tema": "Calidad de datos", "url": "https://www.notion.so/3c9096bfe0b280f3bafef6695b024471"},
    "eda": {"clase": 4, "tema": "CRISP-DM, EDA y boxplot", "url": "https://www.notion.so/3c9096bfe0b28052a107eb1c1ebe53b7"},
    "arbol": {"clase": 6, "tema": "Árboles de decisión y regresión", "url": "https://www.notion.so/3d6096bfe0b2807fba88e0b0a48ff2d4"},
    "ensambles": {"clase": 7, "tema": "Random Forest y XGBoost", "url": "https://www.notion.so/3ec096bfe0b2806b96d9e1d626263337"},
    "clasificacion": {"clase": 9, "tema": "Matriz de confusión y métricas", "url": "https://www.notion.so/3ec096bfe0b280ab83c7d946b9984f5f"},
    "features": {"clase": 10, "tema": "Variables derivadas y One-Hot Encoding", "url": "https://www.notion.so/3f3096bfe0b28065aa31d0f0b43d729b"},
    "validacion": {"clase": 11, "tema": "Train/test, cross-validation y leakage", "url": "https://www.notion.so/3fb096bfe0b281a595a4fa720f25134e"},
    "regresion": {"clase": 12, "tema": "Regresión, residuos, MAE, RMSE y R²", "url": "https://www.notion.so/401096bfe0b280d98850da56a4101d05"},
}


def preparar_horario(a: pd.DataFrame, escenario: str = "sensor") -> pd.DataFrame:
    """Deriva fechas; conserva ceros para evaluar y marca datos inválidos sin borrarlos."""
    d = a.sort_values(["plant_id", "timestamp_local_utc8"]).copy()
    ts = pd.to_datetime(d["timestamp_local_utc8"])
    d["fecha"] = ts.dt.strftime("%Y-%m-%d")
    d["hora"], d["mes"], d["dia_del_anio"] = ts.dt.hour, ts.dt.month, ts.dt.dayofyear
    d["grupo_mes"] = ts.dt.strftime("%Y-%m")
    def congelados(s):
        tramo = s.ne(s.shift()).cumsum()
        return s.ne(0) & s.groupby(tramo).transform("size").ge(3)
    d["congelado"] = d.groupby("plant_id")["pvod_power"].transform(congelados)
    if escenario == "sensor":
        cols = ["pvod_lmd_totalirrad", "pvod_lmd_temperature", "pvod_lmd_windspeed"]
    elif escenario == "externo":
        cols = ["om_shortwave_radiation", "om_temperature_2m", "om_wind_speed_10m_ms"]
    else:
        raise ValueError("Escenario desconocido")
    for dest, src in zip(["irradiancia", "temperatura", "viento"], cols):
        d[dest] = d[src]
    d["target"] = d["pvod_power"] / d["plant_capacity_mw"]
    d["apagon"] = (d["pvod_lmd_totalirrad"] > 500) & (d["target"] < 0.05)
    d["valido"] = ~d["congelado"] & d[FEATURES + ["target"]].notna().all(axis=1)
    return d[d["is_daylight"].eq(1)].reset_index(drop=True)


def crear_modelo(tipo: str, con_planta: bool = True, features=None):
    fs = features or FEATURES
    if tipo == "lineal_simple":
        fs = [fs[0]]
        con_planta = False
    transformers = [("numericas", SimpleImputer(strategy="median"), fs)]
    if con_planta:
        transformers.append(("planta", OneHotEncoder(handle_unknown="ignore", sparse_output=False), ["plant_id"]))
    pre = ColumnTransformer(transformers)
    if tipo.startswith("lineal"):
        estimator = LinearRegression()
    elif tipo == "arbol":
        estimator = DecisionTreeRegressor(max_depth=8, min_samples_leaf=10, random_state=SEED)
    elif tipo == "rf":
        estimator = RandomForestRegressor(n_estimators=150, min_samples_leaf=5, max_features=0.8,
                                          n_jobs=-1, random_state=SEED)
    elif tipo == "xgb":
        from xgboost import XGBRegressor
        estimator = XGBRegressor(n_estimators=250, max_depth=5, learning_rate=0.05,
                                 subsample=0.8, colsample_bytree=0.8, n_jobs=4, random_state=SEED)
    else:
        raise ValueError("Modelo fuera del alcance curricular")
    return make_pipeline(pre, estimator)


def predecir(modelo, d):
    return np.clip(modelo.predict(d), 0, None)


def metricas_regresion(y, pred):
    """Métricas de clase 12. La unidad es la de y; no se llama accuracy al R²."""
    return {"mae": float(mean_absolute_error(y, pred)),
            "mse": float(mean_squared_error(y, pred)),
            "rmse": float(np.sqrt(mean_squared_error(y, pred))),
            "r2": float(r2_score(y, pred)), "n": int(len(y))}


def metricas_confusion(tn: int, fp: int, fn: int, tp: int):
    n = tn + fp + fn + tp
    div = lambda a, b: a / b if b else None
    return {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp), "n": int(n),
            "accuracy": div(tp + tn, n), "precision": div(tp, tp + fp),
            "recall": div(tp, tp + fn), "f1": div(2 * tp, 2 * tp + fp + fn)}


def umbral_boxplot(residuos: pd.Series):
    r = residuos.dropna()
    if len(r) < 10:
        raise ValueError("Calibración insuficiente")
    q1, q3 = r.quantile([0.25, 0.75])
    return {"q1": float(q1), "q3": float(q3), "iqr": float(q3 - q1),
            "umbral": float(q1 - 1.5 * (q3 - q1)), "n": len(r)}


def tabla_diaria(d, pred, referencia=None):
    x = d.assign(pred=np.asarray(pred), sensor=d["pvod_lmd_totalirrad"], externo=d["om_shortwave_radiation"])
    e = x.groupby(["plant_id", "fecha"], as_index=False).agg(
        real=("target", "sum"), esperada=("pred", "sum"), capacidad=("plant_capacity_mw", "first"),
        sensor=("sensor", "sum"), externo=("externo", "sum"), horas=("target", "size"),
        validas=("valido", "sum"))
    if referencia is None:
        referencia = e.groupby("plant_id")["esperada"].quantile(0.9).to_dict()
    e["sensor_caido"] = e["sensor"] < 0.3 * e["externo"]
    e["cobertura_ok"] = e["validas"] == e["horas"]
    e["poca_senal"] = e["esperada"] < 0.25 * e["plant_id"].map(referencia)
    e["decide"] = ~e["sensor_caido"] & e["cobertura_ok"] & ~e["poca_senal"] & e["esperada"].gt(0)
    e["residuo"] = (e["real"] - e["esperada"]) / e["esperada"].where(e["esperada"].gt(0))
    e["residuo"] = e["residuo"].where(e["decide"])
    return e


def agregar_alertas(e, calibracion, generica):
    e = e.copy()
    e["umbral"] = e["plant_id"].map({p: v["umbral"] for p, v in calibracion.items()}).fillna(generica["umbral"])
    e["alerta"] = e["decide"] & e["residuo"].lt(e["umbral"])
    e["estado"] = np.select([e["plant_id"].eq("station04"), ~e["decide"], e["alerta"]],
                             ["capacidad", "sin_dato", "alerta"], default="normal")
    e["deficit_mwh"] = ((e["esperada"] - e["real"]) * e["capacidad"]).clip(lower=0).where(e["decide"], np.nan)
    e.loc[e["plant_id"].eq("station04"), "deficit_mwh"] = np.nan
    return e


def evaluar_simulaciones(base: pd.DataFrame, calibracion: dict, generica: dict):
    """Una identidad por planta/nivel/duración/semilla; ninguna inyección entrena un modelo."""
    resultados = []
    for planta, g in base.groupby("plant_id"):
        g = g.sort_values("fecha").reset_index(drop=True)
        if len(g) < 12:
            continue
        for fraccion in [0.10, 0.25, 0.50, 1.0]:
            for duracion in [1, 3, 7]:
                for semilla in range(5):
                    etiqueta = f"{planta}-{fraccion}-{duracion}-{semilla}"
                    # Semilla estable entre procesos; no se usa hash() de Python.
                    rng = np.random.default_rng(int(hashlib.sha256(etiqueta.encode()).hexdigest()[:8], 16))
                    ini = int(rng.integers(1, len(g) - duracion))
                    inicio = pd.Timestamp(g.loc[ini, "fecha"])
                    fin = inicio + pd.Timedelta(days=duracion)
                    fechas = pd.to_datetime(g["fecha"])
                    positiva = fechas.ge(inicio) & fechas.lt(fin)
                    x = g.copy()
                    x.loc[positiva, "real"] *= 1 - fraccion
                    x["residuo"] = ((x["real"] - x["esperada"]) / x["esperada"]).where(x["decide"])
                    x = agregar_alertas(x, calibracion, generica)
                    dec = x["decide"]
                    tn, fp, fn, tp = confusion_matrix(positiva[dec], x.loc[dec, "alerta"], labels=[False, True]).ravel()
                    detectados = x.loc[positiva & dec & x["alerta"], "fecha"]
                    demora = (pd.Timestamp(detectados.iloc[0]) - inicio).days if len(detectados) else None
                    resultados.append({"id": etiqueta, "planta": planta, "caida": fraccion,
                                       "duracion": duracion, "semilla": semilla, "inicio": str(inicio.date()),
                                       **metricas_confusion(tn, fp, fn, tp), "demora": demora,
                                       "sin_decision": int((~dec).sum()), "dias": len(x),
                                       "positivos_sin_decision": int((positiva & ~dec).sum())})
    return resultados


def ajustar_y_evaluar(a):
    d = preparar_horario(a)
    candidatas = ~d["plant_id"].isin(["station04", "station09"])
    sano = candidatas & d["valido"] & ~d["apagon"]
    train = d[sano & d["fecha"].lt(TRAIN_END)]
    conocidas = sorted(train["plant_id"].unique())
    # Para evaluar se conservan los apagones; no se usa la máscara de entrenamiento sano.
    evaluable = d["plant_id"].isin(conocidas) & d["valido"]
    validacion = d[evaluable & d["fecha"].ge(TRAIN_END) & d["fecha"].lt(TEST_START)]
    test = d[evaluable & d["fecha"].ge(TEST_START)]
    modelos, comparacion = {}, []
    for tipo, nombre in MODELOS.items():
        print("Entrenando", nombre, flush=True)
        m = crear_modelo(tipo).fit(train, train["target"])
        modelos[tipo] = m
        comparacion.append({"id": tipo, "nombre": nombre,
                            "train": metricas_regresion(train["target"], predecir(m, train)),
                            "validacion": metricas_regresion(validacion["target"], predecir(m, validacion))})
    # Regla previa al test: mínimo RMSE de validación; empate relativo <1% favorece RF.
    orden = sorted(comparacion, key=lambda r: r["validacion"]["rmse"])
    elegido = orden[0]["id"]
    rf = next(r for r in comparacion if r["id"] == "rf")
    if rf["validacion"]["rmse"] <= orden[0]["validacion"]["rmse"] * 1.01:
        elegido = "rf"
    modelo = modelos[elegido]
    for row in comparacion:
        row["test"] = metricas_regresion(test["target"], predecir(modelos[row["id"]], test))
    print("Elegido por validación:", elegido, flush=True)
    # Calibrar con predicciones fuera de muestra, agrupadas por mes, solo de train.
    oof, gen_oof = pd.Series(index=train.index, dtype=float), pd.Series(index=train.index, dtype=float)
    notas_cv = []
    for tr, va in GroupKFold(5).split(train, groups=train["grupo_mes"]):
        trd, vad = train.iloc[tr], train.iloc[va]
        m = crear_modelo(elegido).fit(trd, trd["target"])
        mg = crear_modelo(elegido, con_planta=False).fit(trd, trd["target"])
        oof.loc[vad.index], gen_oof.loc[vad.index] = predecir(m, vad), predecir(mg, vad)
        notas_cv.append(metricas_regresion(vad["target"], oof.loc[vad.index]))
    e_train = tabla_diaria(train, oof)
    ref = e_train.groupby("plant_id")["esperada"].quantile(0.9).to_dict()
    cal = {p: umbral_boxplot(g["residuo"]) for p, g in e_train.groupby("plant_id")}
    gen = umbral_boxplot(tabla_diaria(train, gen_oof)["residuo"])
    generico = crear_modelo(elegido, con_planta=False).fit(train, train["target"])
    todas = predecir(generico, d)
    conocidas_mask = d["plant_id"].isin(conocidas)
    todas[conocidas_mask] = predecir(modelo, d[conocidas_mask])
    ref.update({p: float(np.median(list(ref.values()))) for p in d["plant_id"].unique() if p not in ref})
    e = agregar_alertas(tabla_diaria(d, todas, ref), cal, gen)
    e["particion"] = np.select([e["fecha"].lt(TRAIN_END), e["fecha"].lt(TEST_START)],
                               ["entrenamiento", "validación"], default="prueba")
    e["referencia"] = np.where(e["plant_id"].isin(conocidas), "modelo con planta", "modelo genérico")
    base_test = tabla_diaria(test, predecir(modelo, test), ref)
    simulaciones = evaluar_simulaciones(base_test, cal, gen)
    resumen = {"elegido": elegido, "nombre": MODELOS[elegido], "comparacion": comparacion,
               "cv": notas_cv, "calibracion": cal, "calibracion_generica": gen,
               "particiones": {"entrenamiento": {"desde": train["fecha"].min(), "hasta": train["fecha"].max(), "n": len(train)},
                                "validacion": {"desde": validacion["fecha"].min(), "hasta": validacion["fecha"].max(), "n": len(validacion)},
                                "prueba": {"desde": test["fecha"].min(), "hasta": test["fecha"].max(), "n": len(test)}},
               "plantas_entrenamiento": conocidas, "features": FEATURES + ["plant_id (One-Hot)"],
               "unidad_target": "potencia / potencia nominal (MW/MW)",
               "protocolo": "Evaluación retrospectiva; selección por RMSE de abril; test mayo–junio ya explorado en versiones previas.",
               "regla_eleccion": "Mínimo RMSE de validación; si RF queda a menos del 1% del mínimo se prefiere RF.",
               "detector": "Boxplot de residuos: Q1 − 1,5 × IQR, calibrado con 5 folds por mes de entrenamiento.",
               "hiperparametros": modelo[-1].get_params()}
    if hasattr(modelo[-1], "feature_importances_"):
        names = modelo[0].get_feature_names_out()
        resumen["importancias"] = sorted([{"variable": str(n.split("__")[-1]), "valor": float(v)}
                                            for n, v in zip(names, modelo[-1].feature_importances_)], key=lambda r: -r["valor"])
    else:
        resumen["importancias"] = []
    # Nube de prueba con muestreo determinista; las métricas siempre usan la muestra completa.
    pos = np.linspace(0, len(test) - 1, min(len(test), 700), dtype=int)
    yt = predecir(modelo, test)
    resumen["nube"] = [{"real": float(test.iloc[i]["target"]), "pred": float(yt[i]),
                         "planta": test.iloc[i]["plant_id"]} for i in pos]
    diario_test = agregar_alertas(base_test, cal, gen)
    resumen["regresion_diaria"] = metricas_regresion(base_test["real"], base_test["esperada"])
    resumen["baseline_sin_inyeccion"] = {"alertas": int(diario_test["alerta"].sum()),
                                        "dias_con_decision": int(diario_test["decide"].sum()),
                                        "dias_sin_decision": int((~diario_test["decide"]).sum()),
                                        "nota": "Alertas sin inyección; no hay etiquetas operativas para llamarlas falsas alarmas confirmadas."}
    return d, e, resumen, simulaciones


def argentina(b):
    """Regresión mensual sin sensores: ceros conservados y evidencia distinta de China."""
    b = b.copy()
    b["fecha"] = pd.to_datetime(b["fecha"]).dt.strftime("%Y-%m-%d")
    coords = ["SE_CAMMESA_via_WRI", "osm_parque", "WikiSolar_via_GPPD_aprox", "osm_localidad_inferida_del_nombre"]
    ok = b["coord_source"].isin(coords) & b["potencia_mw"].gt(0) & b["factor_capacidad"].between(0, 0.45)
    ampliadas = b["central"].isin(["CUM2FV", "PINFFV", "VANGFV"])
    ok &= ~ampliadas | b["fecha"].between("2022-01-01", "2025-09-01")
    feats = ["om_ghi_kwh_m2_mes", "om_temp_max_media_c", "om_nubosidad_media_pct", "mes"]
    b["plant_id"] = b["central"]
    d = b[ok & b[feats].notna().all(axis=1)].copy()
    # Quitar meses anteriores al primer mes con generación, conservando paradas posteriores.
    inicio = d[d["energia_mwh"].gt(0)].groupby("central")["fecha"].min()
    d = d[d["fecha"].ge(d["central"].map(inicio))].copy()
    train = d[d["fecha"].lt("2024-01-01") & d["energia_mwh"].gt(0)]
    val = d[d["fecha"].between("2024-01-01", "2024-12-31")]
    test = d[d["fecha"].ge("2025-01-01")]
    comparacion, modelos = [], {}
    # Sin ID de parque: estima un parque típico y permite incluir parques nuevos.
    for tipo in ["lineal_multiple", "arbol", "rf"]:
        m = crear_modelo(tipo, con_planta=False, features=feats).fit(train, train["factor_capacidad"])
        modelos[tipo] = m
        comparacion.append({"id": tipo, "nombre": MODELOS[tipo],
                            "train": metricas_regresion(train["factor_capacidad"], predecir(m, train)),
                            "validacion": metricas_regresion(val["factor_capacidad"], predecir(m, val))})
    elegido = min(comparacion, key=lambda r: r["validacion"]["rmse"])["id"]
    for r in comparacion:
        r["test"] = metricas_regresion(test["factor_capacidad"], predecir(modelos[r["id"]], test))
    d["pred"] = predecir(modelos[elegido], d)
    d["ratio"] = d["factor_capacidad"] / d["pred"].where(d["pred"].gt(0))
    # La referencia se aprende en train, no se centra utilizando el año de prueba.
    normal = d[d["fecha"].lt("2024-01-01")].groupby("central")["ratio"].median()
    d["normal"] = d["central"].map(normal)
    d["indice"] = d["ratio"] / d["normal"].where(d["normal"].gt(0))
    cal = {}
    for p, g in d[d["fecha"].lt("2024-01-01")].groupby("central"):
        if g["indice"].notna().sum() >= 12:
            cal[p] = umbral_boxplot(g["indice"] - 1)
    d["umbral"] = d["central"].map({p: v["umbral"] for p, v in cal.items()})
    d["decide"] = d["umbral"].notna() & d["indice"].notna()
    d["alerta"] = d["decide"] & (d["indice"] - 1).lt(d["umbral"])
    d["particion"] = np.select([d["fecha"].lt("2024-01-01"), d["fecha"].lt("2025-01-01")], ["entrenamiento", "validación"], default="prueba")
    # Referencia calibrada dentro de muestra: se declara; no hay matriz con etiquetas reales.
    resumen = {"elegido": elegido, "nombre": MODELOS[elegido], "comparacion": comparacion,
               "features": feats, "unidad_target": "factor de capacidad (MWh / MW / horas del mes)",
               "protocolo": "Train hasta 2023; selección en 2024; prueba retrospectiva 2025–septiembre 2026.",
               "limite": "Calibración histórica descriptiva por parque. Sin etiquetas de fallas: no se informa matriz de confusión real ni causa confirmada.",
               "ceros_conservados": int(d["energia_mwh"].eq(0).sum()), "n": len(d), "parques": d["central"].nunique()}
    return d, resumen


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
    a = pd.read_parquet(DATA_PROCESSED / "dataset_A_pvod_hourly.parquet")
    b = pd.read_parquet(DATA_PROCESSED / "dataset_B_argentina_mensual.parquet")
    d, diario, regresion, sims = ajustar_y_evaluar(a)
    arg, reg_arg = argentina(b)
    diario.to_parquet(destino / "defensa_diario.parquet", index=False)
    arg.to_parquet(destino / "defensa_argentina.parquet", index=False)
    plantas = []
    for p, g in a.groupby("plant_id"):
        plantas.append({"id": p, "mw": float(g["plant_capacity_mw"].iloc[0]),
                        "lat": float(g["plant_lat"].iloc[0]), "lon": float(g["plant_lon"].iloc[0]),
                        "desde": str(g["date_local"].min()), "hasta": str(g["date_local"].max()), "horas": len(g)})
    corr_cols = ["pvod_power_norm", "pvod_lmd_totalirrad", "pvod_lmd_temperature", "om_shortwave_radiation"]
    muestra = d.sample(min(1000, len(d)), random_state=SEED)
    datos = {"version": 1, "fecha_datos": "2026-10-22", "fecha_evaluacion": "2026-10-29",
             "defensa": "2026-11-12", "clases": CLASES, "plantas": plantas,
             "regresion": regresion, "simulaciones": sims, "regresion_argentina": reg_arg,
             "diario": diario.to_dict("records"),
             "argentina": arg[["central", "central_descripcion", "provincia", "fecha", "lat", "lon", "energia_gwh",
                                "factor_capacidad", "pred", "indice", "umbral", "decide", "alerta", "particion",
                                "potencia_mw", "coord_source"]].to_dict("records"),
             "eda": {"n_horario": len(a), "n_mensual": len(b), "plantas_argentina": b["central"].nunique(),
                     "duplicados_horario": int(a.duplicated(["plant_id", "timestamp_utc"]).sum()),
                     "duplicados_mensual": int(b.duplicated(["central", "fecha"]).sum()),
                     "faltantes_horario": int(a.isna().sum().sum()),
                     "correlacion": a[a["is_daylight"].eq(1)][corr_cols].corr().values.tolist(), "correlacion_columnas": corr_cols,
                     "nube": muestra[["plant_id", "irradiancia", "target", "temperatura"]].to_dict("records")},
             "economia": {"precio": 42.84, "nota": "Precio ilustrativo RenovAr Ronda 2; no es el ingreso real de plantas chinas. Déficit respecto del modelo, no energía recuperable demostrada."},
             "nacional": b.groupby("anio", as_index=False).agg(gwh=("energia_gwh", "sum"), parques=("central", "nunique"), meses=("mes", "nunique")).to_dict("records")}
    datos = serializable(datos)
    ruta = destino / "defensa_evidencia.json"
    ruta.write_text(json.dumps(datos, ensure_ascii=False, allow_nan=False, separators=(",", ":")))
    print("Evidencia guardada:", ruta, flush=True)
    return datos


if __name__ == "__main__":
    construir()
