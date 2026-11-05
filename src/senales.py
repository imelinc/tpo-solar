"""Parques a revisar: cuánto debería generar cada parque y cuáles rinden menos.

Una señal no es una falla confirmada: es un parque que conviene mirar primero.
Lo esperado de un parque sale de un modelo que nunca lo vio (se entrena hasta 2023, sin ese parque).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN, KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.model_selection import GroupKFold
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

from src.academico import NUM, SEED, crear_modelo, matriz

UMBRAL = 0.8
MESES_SEGUIDOS = 2
MESES_ARRANQUE = 6
VECINOS_MIN = 3
USD_MWH = 60  # supuesto de orden de magnitud; la app deja cambiarlo
# Una ampliación es parte del mismo sitio: en el ranking se suman.
MISMO_SITIO = {"UL42FV": "ULL4FV"}


def esperado_fuera_de_muestra(d: pd.DataFrame, tipo: str) -> np.ndarray:
    """Predice cada parque con un modelo entrenado hasta 2023 y sin ese parque."""
    pred = np.full(len(d), np.nan)
    pos = np.arange(len(d))
    for _, grupo in GroupKFold(5).split(d, groups=d["central"]):
        afuera = d.iloc[grupo]["central"].unique()
        tr = d[(d["fecha"] < "2024-01-01") & d["energia_mwh"].gt(0) & ~d["central"].isin(afuera)]
        med = tr[NUM].median().to_dict()
        est = crear_modelo(tipo).fit(matriz(tr, med, tipo), tr["factor_capacidad"])
        pred[pos[grupo]] = np.clip(est.predict(matriz(d.iloc[grupo], med, tipo)), 0, 1)
    return pred


def meses_desde(f: pd.Series, inicio: pd.Series) -> pd.Series:
    return (f.dt.year - inicio.dt.year) * 12 + f.dt.month - inicio.dt.month


def marcar(d: pd.DataFrame, umbral: float = UMBRAL) -> pd.DataFrame:
    """Agrega rendimiento contra el modelo y contra los vecinos, y el estado de cada mes.

    Espera `pred_oof`, `factor_capacidad`, `provincia`, `central`, `potencia_mw`, `fecha`.
    Estados: normal, parque, zona, arranque, sin_vecinos. Sin vecinos no es normal: no se sabe.
    """
    s = d.copy()
    f = pd.to_datetime(s["fecha"])
    s["sitio"] = s["central"].replace(MISMO_SITIO)
    s["rinde_modelo"] = s["factor_capacidad"] / s["pred_oof"].where(s["pred_oof"] > 0)
    # Un parque en arranque no entra a la mediana: bajaría la vara de sus vecinos.
    orden = s.assign(_f=f).sort_values(["central", "_f"])
    cambio = orden.groupby("central")["potencia_mw"].transform(lambda p: p.ne(p.shift()))
    ultimo = orden["_f"].where(cambio).groupby(orden["central"]).ffill()
    s["arranque"] = meses_desde(f, ultimo.reindex(s.index)) < MESES_ARRANQUE
    base = s.loc[~s["arranque"]].groupby(["provincia", "fecha"])["rinde_modelo"]
    med = base.transform("median").groupby([s["provincia"], s["fecha"]]).first()
    n = base.transform("count").groupby([s["provincia"], s["fecha"]]).first()
    claves = pd.MultiIndex.from_frame(s[["provincia", "fecha"]])
    s["mediana_vecinos"] = med.reindex(claves).to_numpy()
    s["n_vecinos"] = n.reindex(claves).fillna(0).astype(int).to_numpy()
    s["rinde_vecinos"] = s["rinde_modelo"] / s["mediana_vecinos"]
    con_vecinos = s["n_vecinos"].ge(VECINOS_MIN)
    bajo = s["rinde_modelo"].lt(umbral)
    s["estado"] = np.select(
        [s["arranque"], ~con_vecinos, bajo & s["rinde_vecinos"].lt(umbral), s["mediana_vecinos"].lt(umbral)],
        ["arranque", "sin_vecinos", "parque", "zona"], default="normal")
    # Una señal exige dos meses seguidos: un mes solo puede ser clima.
    s = s.assign(_f=f).sort_values(["central", "_f"])
    mes = s["_f"].dt.year * 12 + s["_f"].dt.month
    tramo = (s["estado"].ne(s.groupby("central")["estado"].shift()) | mes.diff().ne(1)).cumsum()
    largo = s.groupby(tramo)["estado"].transform("size")
    s["senal"] = s["estado"].eq("parque") & largo.ge(MESES_SEGUIDOS)
    s["gwh_esperada"] = s["pred_oof"] * s["potencia_mw"] * s["_f"].dt.days_in_month * 24 / 1000
    s["gwh_faltante"] = (s["gwh_esperada"] - s["energia_gwh"]).clip(lower=0)
    return s.drop(columns="_f").sort_index()


def ranking(s: pd.DataFrame, desde: str = "2025-01-01") -> list[dict]:
    """Sitios con señal desde `desde`, de mayor a menor energía faltante."""
    t = s[s["senal"] & s["fecha"].ge(desde)]
    filas = []
    for sitio, g in t.groupby("sitio"):
        propio = s[s["central"].eq(sitio)]
        nombre = (propio["central_descripcion"].iloc[0] if len(propio) else g["central_descripcion"].iloc[0])
        filas.append({"central": sitio, "nombre": nombre, "provincia": g["provincia"].iloc[0],
                      "desde": g["fecha"].min(), "hasta": g["fecha"].max(), "meses": int(g["fecha"].nunique()),
                      "rinde_modelo": float(g["rinde_modelo"].median()), "rinde_vecinos": float(g["rinde_vecinos"].median()),
                      "gwh_faltante": float(g["gwh_faltante"].sum())})
    return sorted(filas, key=lambda r: -r["gwh_faltante"])


def sensibilidad_umbral(d: pd.DataFrame, umbrales=(0.75, 0.8, 0.85)) -> list[dict]:
    out = []
    for u in umbrales:
        t = marcar(d, u)
        t = t[t["fecha"].ge("2025-01-01")]
        f = t[t["senal"]]
        out.append({"umbral": u, "meses_marcados": int(len(f)), "sitios": int(f["sitio"].nunique()),
                    "gwh_faltante": float(f["gwh_faltante"].sum())})
    return out


def probar_caidas(s: pd.DataFrame, caidas=(0.1, 0.2, 0.3, 0.5), n: int = 200) -> list[dict]:
    """Baja tres meses de un parque normal y mide si la regla lo marca.

    Solo mide la regla: estas caídas simuladas no entrenan nada. Los vecinos no se recalculan,
    porque un parque solo casi no mueve la mediana de su provincia.
    """
    rng = np.random.default_rng(SEED)
    t = s[s["fecha"].ge("2024-01-01")].sort_values(["central", "fecha"])
    ventanas = []
    for _, g in t.groupby("central"):
        norm = g["estado"].eq("normal").to_numpy()
        for i in range(len(g) - 2):
            if norm[i:i + 3].all():
                ventanas.append(g.iloc[i:i + 3][["rinde_modelo", "mediana_vecinos"]].to_numpy())
    out = []
    for caida in caidas:
        pos = 0
        for k in rng.integers(0, len(ventanas), n):
            r, med = ventanas[k][:, 0] * (1 - caida), ventanas[k][:, 1]
            marca = (r < UMBRAL) & (r / med < UMBRAL)
            pos += bool((marca[:-1] & marca[1:]).any())
        out.append({"caida": caida, "detectadas": pos / n, "n": n})
    return out


def tipos_de_parque(d: pd.DataFrame) -> dict:
    """K-Means sobre el perfil anual de cada parque; PCA solo para dibujarlo."""
    perfil = d.pivot_table(index="central", columns="mes", values="factor_capacidad", aggfunc="mean").dropna()
    X = StandardScaler().fit_transform(perfil)
    silueta = {k: float(silhouette_score(X, KMeans(k, n_init=10, random_state=SEED).fit_predict(X))) for k in range(2, 7)}
    k = max(silueta, key=silueta.get)
    etiquetas = KMeans(k, n_init=10, random_state=SEED).fit_predict(X)
    pca = PCA(2, random_state=SEED).fit(X)
    xy = pca.transform(X)
    grupos = []
    for g in range(k):
        m = etiquetas == g
        anual, invierno = perfil[m].mean(axis=1).mean(), perfil[m][[6, 7]].mean(axis=1).mean()
        prov = d[d["central"].isin(perfil.index[m])].groupby("provincia")["central"].nunique().sort_values(ascending=False)
        grupos.append({"grupo": g, "parques": int(m.sum()), "factor_medio": float(anual), "factor_invierno": float(invierno),
                       "provincias": {k: int(v) for k, v in prov.head(4).items()}})
    return {"k": k, "silueta": silueta, "grupos": sorted(grupos, key=lambda r: -r["factor_medio"]),
            "pca_varianza": [float(v) for v in pca.explained_variance_ratio_],
            "puntos": [{"central": c, "x": float(a), "y": float(b), "grupo": int(g)}
                       for c, (a, b), g in zip(perfil.index, xy, etiquetas)], "excluidos": int(d["central"].nunique() - len(perfil))}


def meses_raros(s: pd.DataFrame) -> dict:
    """DBSCAN aparta lo que queda fuera del grupo denso, sin mirar la regla. Se compara después con ella."""
    t = s[s["fecha"].ge("2025-01-01") & s["rinde_modelo"].notna() & s["rinde_vecinos"].notna()]
    X = StandardScaler().fit_transform(t[["rinde_modelo", "rinde_vecinos"]])
    dist = NearestNeighbors(n_neighbors=5).fit(X).kneighbors(X)[0][:, -1]
    eps = float(np.quantile(dist, 0.9))
    grupos = DBSCAN(eps=eps, min_samples=5).fit_predict(X)
    principal = np.bincount(grupos[grupos >= 0]).argmax()
    fuera = grupos != principal
    marcados = t["senal"].to_numpy()
    return {"meses": int(len(t)), "eps": eps, "fuera_del_grupo": int(fuera.sum()), "senales": int(marcados.sum()),
            "senales_fuera": int((fuera & marcados).sum()),
            "fuera_y_altos": int((fuera & (t["rinde_modelo"].to_numpy() >= 1)).sum())}


def evidencia(d: pd.DataFrame, tipo: str) -> tuple[pd.DataFrame, dict]:
    """`d` trae las columnas de `preparar`. Devuelve el detalle por mes y el resumen."""
    d = d.assign(pred_oof=esperado_fuera_de_muestra(d, tipo))
    s = marcar(d)
    t = s[s["fecha"].ge("2025-01-01")]
    f = t[t["senal"]]
    filas = ranking(s)
    total = float(t["energia_gwh"].sum())
    faltante = float(f["gwh_faltante"].sum())
    conteo = t["estado"].value_counts().to_dict()
    return s, {
        "umbral": UMBRAL, "meses_seguidos": MESES_SEGUIDOS, "meses_arranque": MESES_ARRANQUE,
        "vecinos_min": VECINOS_MIN, "usd_mwh": USD_MWH, "ranking": filas,
        "resumen": {"meses": int(len(t)), "marcados": int(len(f)), "sitios": len(filas),
                    "gwh_faltante": faltante, "gwh_generada": total, "pct": faltante / (total + faltante) * 100,
                    "usd_millones": faltante * USD_MWH / 1000, "estados": {k: int(v) for k, v in conteo.items()},
                    "desde": t["fecha"].min(), "hasta": t["fecha"].max()},
        "sensibilidad": sensibilidad_umbral(d), "caidas": probar_caidas(s),
        "tipos_parque": tipos_de_parque(d), "meses_raros": meses_raros(s),
        "nota": "Señal: dos meses seguidos por debajo del 80 % del modelo y de los vecinos de provincia. "
                "No es una falla confirmada: faltan datos del parque para saber la causa."}
