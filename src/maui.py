"""Zoom horario: con la potencia de cada inversor, el aviso baja de meses a horas.

Planta Maui Ocean Center (NREL PVDAQ 2105). Compara cada inversor con la mediana de sus vecinos a la
misma hora: todos ven el mismo cielo. Sin modelo de clima y sin etiquetas: es una regla medible.
Los crudos van en data/raw/maui; la evidencia que usa la app queda en maui_evidencia.json.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from src.config import DATA_PROCESSED, DATA_RAW

URL = "https://oedi-data-lake.s3.amazonaws.com/pvdaq/2023-solar-data-prize/2105_OEDI/data/"
RAW = DATA_RAW / "maui"
INVERSORES = [f"inv{k:02d}" for k in range(1, 12)]
BASE_HASTA, PRUEBA_DESDE = "2021-12-31", "2022-01-01"
APAGADO, HORAS_APAGADO = 0.2, 2
PARCIAL, HORAS_PARCIAL = 0.8, 4
SOL_MIN = 0.2
SEED = 42
USD_KWH = 0.06


def bajar() -> None:
    import requests
    RAW.mkdir(parents=True, exist_ok=True)
    for n in [f"2105_{i}_data.csv" for i in INVERSORES] + ["2105_irradiance_data.csv"]:
        if not (RAW / n).exists():
            r = requests.get(URL + n, timeout=300)
            r.raise_for_status()
            (RAW / n).write_bytes(r.content)


def leer(inv: str) -> pd.DataFrame:
    x = pd.read_csv(RAW / f"2105_{inv}_data.csv", parse_dates=["measured_on"])
    x.columns = ["ts", "kw", "fp", "vac", "vdc", "temp"]
    return x.sort_values("ts").drop_duplicates("ts")


def copia_exacta(a: pd.DataFrame, b: pd.DataFrame) -> dict:
    """Empareja lecturas de dos equipos y mide cuántas son idénticas."""
    m = pd.merge_asof(a, b, on="ts", tolerance=pd.Timedelta("150s"), direction="nearest", suffixes=("_a", "_b"))
    m = m[m["kw_a"].gt(1) & m["kw_b"].notna()]
    out = {"lecturas": int(len(m))}
    for c in ("kw", "fp", "vac", "temp"):
        out[c] = float(np.isclose(m[f"{c}_a"], m[f"{c}_b"], atol=0.002).mean())
    return out


def horario(crudos: dict[str, pd.DataFrame]) -> pd.DataFrame:
    return pd.DataFrame({k: v.set_index("ts")["kw"].resample("1h").mean() for k, v in crudos.items()})


def rendimiento(kw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
    """Rendimiento de cada inversor contra sus vecinos, corregido por su forma habitual."""
    cap = kw.quantile(0.995)
    p = kw / cap
    med = p.median(axis=1)
    p = p.where(med > SOL_MIN)
    ratio = pd.DataFrame({c: p[c] / p.drop(columns=c).median(axis=1) for c in p}).replace([np.inf, -np.inf], np.nan)
    base = ratio.loc[:BASE_HASTA]
    tipico = base.groupby([base.index.month, base.index.hour]).median()
    claves = pd.MultiIndex.from_arrays([ratio.index.month, ratio.index.hour])
    ref = tipico.reindex(claves).set_axis(ratio.index)
    return ratio / ref, ref, cap


def primer_aviso(r: np.ndarray) -> tuple[int | None, str | None]:
    """Índice de la primera hora de sol con aviso. `r` contiene solo horas de sol."""
    bajo_a = bajo_p = 0
    for i, v in enumerate(r):
        if np.isnan(v):
            continue
        bajo_a = bajo_a + 1 if v < APAGADO else 0
        bajo_p = bajo_p + 1 if v < PARCIAL else 0
        if bajo_a >= HORAS_APAGADO:
            return i, "apagado"
        if bajo_p >= HORAS_PARCIAL:
            return i, "parcial"
    return None, None


def episodios(rel: pd.DataFrame, cap: pd.Series, kw: pd.DataFrame, ref: pd.DataFrame) -> pd.DataFrame:
    """Tramos de días por debajo del 80 %, con la energía que faltó. Un hueco de hasta 7 días no corta el tramo."""
    medn = (kw / cap).median(axis=1)
    filas = []
    for c in rel:
        d = rel[c].dropna().resample("1D").median().dropna()
        bajos = d[d < PARCIAL]
        if bajos.empty:
            continue
        tramo = (bajos.index.to_series().diff() > pd.Timedelta(days=7)).cumsum()
        for _, g in bajos.groupby(tramo.to_numpy()):
            desde, hasta = g.index[0], g.index[-1] + pd.Timedelta(hours=23)
            w = rel[c].loc[desde:hasta].dropna()
            esperado = (medn.loc[w.index] * ref[c].loc[w.index] * cap[c])
            faltante = (esperado - kw[c].loc[w.index]).clip(lower=0).sum()
            filas.append({"inversor": c, "desde": desde.strftime("%Y-%m-%d"), "hasta": g.index[-1].strftime("%Y-%m-%d"),
                          "dias": len(g), "rinde": float(g.median()), "kwh_faltante": float(faltante)})
    return pd.DataFrame(filas).sort_values("kwh_faltante", ascending=False)


def medir_detector(rel: pd.DataFrame, sanos: list[str], n: int = 80) -> dict:
    """Inyecta fallas sobre inversores sanos y cuenta horas de sol hasta el aviso. No entrena nada."""
    rng = np.random.default_rng(SEED)
    prueba = rel.loc[PRUEBA_DESDE:]
    casos = {"apagado": (0.0, 3), "parcial_30": (0.7, 21), "parcial_15": (0.85, 21)}
    out = {}
    for nombre, (factor, dias) in casos.items():
        horas, hecho = [], 0
        while hecho < n:
            c = rng.choice(sanos)
            s = prueba[c].dropna()
            ini = int(rng.integers(0, len(s) - 12 * dias))
            w = s.iloc[max(0, ini - 8):ini]
            if len(w) < 8 or (w < PARCIAL).any():
                continue
            h, _ = primer_aviso(s.iloc[ini:ini + 12 * dias].to_numpy() * factor)
            horas.append(np.nan if h is None else h + 1)
            hecho += 1
        v = np.array(horas, float)
        out[nombre] = {"n": n, "detectadas": float(np.isfinite(v).mean()),
                       "mediana_horas": float(np.nanmedian(v)) if np.isfinite(v).any() else None}
    return out


def avisos_sin_falla(rel: pd.DataFrame, ep: pd.DataFrame, sanos: list[str]) -> dict:
    """Avisos por inversor y por mes en equipos sanos, fuera de episodios largos (2022-2023)."""
    largos = ep[ep["dias"].ge(5)]
    total, meses = 0, 0.0
    for c in sanos:
        s = rel[c].loc[PRUEBA_DESDE:].dropna()
        for f in largos[largos["inversor"].eq(c)].itertuples():
            s = s[(s.index < f.desde) | (s.index > pd.Timestamp(f.hasta) + pd.Timedelta(days=1))]
        meses += s.index.normalize().nunique() / 30.4
        i = 0
        v = s.to_numpy()
        while i < len(v):
            h, _ = primer_aviso(v[i:])
            if h is None:
                break
            total += 1
            i += h + 12  # un aviso nuevo recién al día siguiente
    return {"avisos": total, "inversor_meses": meses, "por_inversor_mes": total / meses}


def ventana_demo(rel: pd.DataFrame, sanos: list[str]) -> dict:
    """Tres semanas sanas para probar el detector en la app, con los mismos números que acá."""
    d = rel.loc[PRUEBA_DESDE:, sanos].dropna(how="all")
    dias = d.resample("1D").median().dropna()
    malos = (dias < 0.9).sum(axis=1).rolling(21).sum()
    fin = malos.idxmin()
    w = d.loc[fin - pd.Timedelta(days=20): fin + pd.Timedelta(hours=23)]
    rinde = {c: [None if np.isnan(v) else round(float(v), 4) for v in w[c]] for c in sanos}
    # La app recalcula la regla en el navegador: estos casos prueban que da lo mismo que acá.
    control = []
    for factor in (0.0, 0.7, 0.85, 1.0):
        r = np.array([np.nan if v is None else v for v in rinde[sanos[0]]], float)[40:] * factor
        h, _ = primer_aviso(r)
        control.append({"inversor": sanos[0], "inicio": 40, "factor": factor, "horas": None if h is None else h + 1})
    return {"horas": [t.strftime("%Y-%m-%d %H:00") for t in w.index], "inversores": sanos, "rinde": rinde, "control": control}


def desfase_sensor(kw: pd.Series) -> dict:
    g = pd.read_csv(RAW / "2105_irradiance_data.csv", parse_dates=["measured_on"]).set_index("measured_on").sort_index()
    g = g[~g.index.duplicated()].iloc[:, 0].resample("1h").mean()
    corr = {int(l): float(kw.corr(g.shift(l))) for l in range(-15, 16)}
    return {"sin_correr": corr[0], "mejor_horas": max(corr, key=corr.get), "mejor_corr": max(corr.values())}


OTRAS = {"Arbuckle, California": ("2107_OEDI/data/2107_electrical_data.csv", r"^inv_\d+_ac_power"),
         "Kersey, Colorado": ("9068_OEDI/data/9068_dc_combiner_data.csv", r"^combiner_dc_output_.*current")}


def otra_planta(nombre: str, archivo: str, patron: str) -> dict:
    """Mismo código y mismos umbrales en otra planta. Una columna por equipo: potencia o corriente."""
    import re
    import requests
    destino = RAW / archivo.split("/")[-1]
    if not destino.exists():
        with requests.get(URL.split("2105_OEDI")[0] + archivo, stream=True, timeout=600) as r:
            r.raise_for_status()
            with open(destino, "wb") as f:
                for parte in r.iter_content(1 << 20):
                    f.write(parte)
    cols = pd.read_csv(destino, nrows=0).columns
    uso = ["measured_on"] + [c for c in cols if re.search(patron, c)]
    x = pd.read_csv(destino, usecols=uso, parse_dates=["measured_on"]).set_index("measured_on").sort_index()
    kw = x[~x.index.duplicated()].clip(lower=0).resample("1h").mean()
    kw = kw.loc[:, kw.quantile(0.995) > 0]
    # El mismo chequeo que encontró la copia de Maui: dos equipos con la misma serie.
    h = kw.where(kw > 0).round(3)
    copias = [(a, b) for i, a in enumerate(h) for b in h.columns[i + 1:]
              if np.isclose(h[a], h[b], atol=1e-3, equal_nan=False).sum() > 0.9 * h[[a, b]].notna().all(axis=1).sum() > 0]
    kw = kw.drop(columns=[b for _, b in copias])
    rel, ref, cap = rendimiento(kw)
    ep = episodios(rel, cap, kw, ref)
    largos = ep[ep["dias"].ge(5)]
    sanos = [c for c in rel if c not in set(largos.loc[largos["desde"].ge(PRUEBA_DESDE), "inversor"])]
    if len(sanos) < 3:  # plantas con muchas fallas: los que menos días pierden
        dias = largos[largos["desde"].ge(PRUEBA_DESDE)].groupby("inversor")["dias"].sum()
        sanos = list(dias.reindex(rel.columns).fillna(0).sort_values().index[:5])
    return {"planta": nombre, "equipos": int(kw.shape[1]), "copias": len(copias), "sanos": len(sanos),
            "detector": medir_detector(rel, sanos), "avisos_sin_falla": avisos_sin_falla(rel, ep, sanos),
            "episodios_largos": int(len(largos))}


def agregar_otras_plantas() -> None:
    ruta = DATA_PROCESSED / "maui_evidencia.json"
    datos = json.loads(ruta.read_text())
    datos["otras_plantas"] = [otra_planta(n, *v) for n, v in OTRAS.items()]
    ruta.write_text(json.dumps(datos, ensure_ascii=False, allow_nan=False, separators=(",", ":")))
    print(json.dumps(datos["otras_plantas"], ensure_ascii=False))


def construir() -> dict:
    bajar()
    crudos = {i: leer(i) for i in INVERSORES}
    copia = copia_exacta(crudos["inv04"], crudos["inv11"])
    control = copia_exacta(crudos["inv04"], crudos["inv10"])
    if copia["kw"] < 0.99:
        raise ValueError("inv11 ya no es copia de inv04: revisar la exclusión")
    max06 = float(crudos["inv06"]["kw"].max())
    kw = horario({k: v for k, v in crudos.items() if k not in ("inv06", "inv11")})
    rel, ref, cap = rendimiento(kw)
    ep = episodios(rel, cap, kw, ref)
    largos = ep[ep["dias"].ge(5)]
    sanos = [c for c in rel if c not in set(largos.loc[largos["desde"].ge(PRUEBA_DESDE), "inversor"])]
    if len(sanos) < 3:
        raise ValueError("Pocos inversores sanos para medir")
    semanal = rel.resample("7D").median()
    energia_kwh = float(kw.clip(lower=0).sum().sum())
    datos = {
        "planta": "Maui Ocean Center (Hawái)", "fuente": "NREL PVDAQ, sistema 2105",
        "desde": kw.dropna(how="all").index.min().strftime("%Y-%m-%d"), "hasta": kw.dropna(how="all").index.max().strftime("%Y-%m-%d"),
        "calidad": {"inv11_copia_de_inv04": copia, "control_inv04_inv10": control, "inv06_kw_max": max06,
                    "sensor": desfase_sensor(kw["inv10"])},
        "reglas": {"apagado": APAGADO, "horas_apagado": HORAS_APAGADO, "parcial": PARCIAL, "horas_parcial": HORAS_PARCIAL},
        "capacidad_kw": {k: float(v) for k, v in cap.items()}, "potencia_kw": float(cap.sum()),
        "sanos": sanos, "detector": medir_detector(rel, sanos), "avisos_sin_falla": avisos_sin_falla(rel, ep, sanos),
        "episodios": largos.round(3).to_dict("records"),
        "energia_kwh": energia_kwh, "faltante_kwh": float(largos["kwh_faltante"].sum()), "usd_kwh": USD_KWH,
        "mapa": {"semanas": [t.strftime("%Y-%m-%d") for t in semanal.index], "inversores": list(semanal.columns),
                 "z": [[None if np.isnan(v) else round(float(v), 3) for v in semanal[c]] for c in semanal]},
        "demo": ventana_demo(rel, sanos),
        "nota": "Sin etiquetas reales: las causas no se verificaron en la planta. Las fallas inyectadas solo miden el tiempo de aviso.",
    }
    ruta = DATA_PROCESSED / "maui_evidencia.json"
    ruta.write_text(json.dumps(datos, ensure_ascii=False, allow_nan=False, separators=(",", ":")))
    print("Evidencia Maui:", ruta, f"{ruta.stat().st_size / 1e3:.0f} KB")
    return datos


if __name__ == "__main__":
    construir()
    agregar_otras_plantas()
