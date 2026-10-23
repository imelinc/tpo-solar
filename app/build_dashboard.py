"""Genera los datos del dashboard (app/datos.js y app/geo.js) a partir de data/processed.

El dashboard es una página estática (app/index.html) que se abre con doble clic y anda sin internet:
no tiene servidor, así que todo lo que muestra va precalculado en estos dos archivos.
Usa las mismas funciones que los notebooks (src/deteccion.py, src/negocio.py).

Correr después de 04_deteccion (que deja las tablas app_*.parquet):
    python app/build_dashboard.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

APP = Path(__file__).resolve().parent
sys.path.append(str(APP.parent))
from src.config import DATA_PROCESSED  # noqa: E402
from src.deteccion import capacidad_no_confiable, diario_flota, semaforo  # noqa: E402
from src.negocio import (COSTO_LIMPIEZA_USD_MW, PRECIO_USD_MWH, T_BASE_LIMPIEZA_DIAS,  # noqa: E402
                         ahorro_anual_limpieza, t_optimo_limpieza)

TASA_MEDIDA = 0.00049  # %/día medido en 05_negocio (0,049 %/día)
DESDE, HASTA = "2018-07-01", "2019-06-13"


def col(s, nd=3):
    """Serie -> lista JSON (NaN -> null), redondeada."""
    if s.dtype == bool:
        return [int(v) for v in s]
    return [None if pd.isna(v) else round(float(v), nd) for v in s]


def flota():
    e = diario_flota(DESDE, HASTA, precalculado=True)
    e["date_local"] = e["date_local"].astype(str)
    no_conf = capacidad_no_confiable()
    meta = pd.read_csv(DATA_PROCESSED / "pvod_plantas_metadata.csv").set_index("plant_id")
    plantas = {}
    for p, g in e.groupby("plant_id"):
        g = g.sort_values("date_local")
        plantas[p] = {
            "lat": float(meta.loc[p, "plant_lat"]), "lon": float(meta.loc[p, "plant_lon"]),
            "cap_mw": float(meta.loc[p, "plant_capacity_mw"]), "modelo": g["modelo"].iloc[0],
            "fecha": g["date_local"].tolist(), "real": col(g["energia_real_mwh"], 1),
            "esperada": col(g["energia_esperada_mwh"], 1), "perdida": col(g["perdida_mwh"], 2),
            "decide": col(g["residuo_rel"].notna()), "alerta": col(g["alerta_elegida"]),
            "grave": col(g["alerta_grave"]), "baja": col(g["baja_confianza"]), "sensor": col(g["falla_sensor"]),
        }
    fechas = sorted(e["date_local"].unique())
    tablero = {}
    for f in fechas[6:]:  # el semáforo mira los últimos 7 días
        s = semaforo(e, f, PRECIO_USD_MWH, no_confiables=no_conf)
        tablero[f] = [{"p": r.plant_id, "estado": r.estado, "accion": r.accion, "alerta": r.alerta,
                       "rend": None if pd.isna(r.rendimiento_vs_vecinas) else round(float(r.rendimiento_vs_vecinas), 3),
                       "usd": None if pd.isna(r.perdida_usd_dia) else round(float(r.perdida_usd_dia)),
                       "baja": bool(r.baja_confianza), "fecha_dato": str(r.fecha_dato)} for r in s.itertuples()]
    e_mw = float(e.loc[e["modelo"] == "propio", "e_esp"].mean())  # MWh por día por MW, igual que 05_negocio
    return {"plantas": plantas, "tablero": tablero, "e_mw": e_mw, "no_confiables": no_conf}


def argentina():
    """Parques comparables (app_argentina, de 04_deteccion) y contexto nacional con los 97 parques de CAMMESA."""
    todos = pd.read_parquet(DATA_PROCESSED / "dataset_B_argentina_mensual.parquet")
    todos["fecha"] = pd.to_datetime(todos["fecha"])
    b = pd.read_parquet(DATA_PROCESSED / "app_argentina.parquet").merge(
        todos[["central", "fecha", "om_ghi_kwh_m2_mes", "tipo_contrato"]], on=["central", "fecha"], how="left")
    b = b.sort_values(["central", "fecha"])
    b["fecha"] = b["fecha"].dt.strftime("%Y-%m")
    parques = {}
    for c, g in b.groupby("central"):
        pot = g["potencia_mw"].dropna()
        parques[c] = {"nombre": g["central_descripcion"].iloc[0], "provincia": g["provincia"].iloc[0].title(),
                      "region": g["region"].iloc[0].title(), "lat": round(float(g["lat"].iloc[0]), 4),
                      "lon": round(float(g["lon"].iloc[0]), 4), "contrato": g["tipo_contrato"].dropna().iloc[-1] if g["tipo_contrato"].notna().any() else None,
                      "mw": round(float(pot.iloc[-1]), 1) if len(pot) else None, "fecha": g["fecha"].tolist(),
                      "fc": col(g["factor_capacidad"]), "fc_esp": col(g["fc_esp"]), "rel": col(g["indice_rel"]),
                      "ghi": col(g["om_ghi_kwh_m2_mes"], 1), "gwh": col(g["energia_gwh"]),
                      "alerta": col(g["alerta"]), "bajo_p10": col(g["bajo_p10"])}
    fin = todos["fecha"].max()
    u12 = todos[todos["fecha"] > fin - pd.DateOffset(months=12)]
    ult = todos[todos["fecha"] == fin]
    anios = todos.groupby("anio").agg(gwh=("energia_gwh", "sum"), parques=("central", "nunique"), meses=("mes", "nunique"))
    nacional = {
        "anios": [{"anio": int(a), "gwh": round(float(r.gwh), 1), "parques": int(r.parques), "completo": bool(r.meses == 12)}
                  for a, r in anios.iterrows()],
        "u12": {"gwh": round(float(u12["energia_gwh"].sum())), "parques": int(u12["central"].nunique()),
                "desde": (fin - pd.DateOffset(months=11)).strftime("%Y-%m"), "hasta": fin.strftime("%Y-%m")},
        "provincias": [[k.title(), round(float(v), 1)] for k, v in
                       u12.groupby("provincia")["energia_gwh"].sum().sort_values(ascending=False).items() if v > 0.5],
        "mw": {"total": round(float(ult["potencia_mw"].sum())), "con_dato": int(ult["potencia_mw"].notna().sum()), "parques": len(ult)},
        "total_parques": int(todos["central"].nunique()),
    }
    return {"parques": parques, "meses": sorted(b["fecha"].unique()), "nacional": nacional}


def main():
    f = flota()
    datos = {
        "flota": f, "argentina": argentina(),
        "negocio": {"precio": PRECIO_USD_MWH, "costo": COSTO_LIMPIEZA_USD_MW, "tasa": TASA_MEDIDA,
                    "t_base": T_BASE_LIMPIEZA_DIAS, "e_mw": f["e_mw"],
                    # Control: la página recalcula T* y el ahorro en JS y avisa en la consola si no coincide con Python
                    "control": {"t": t_optimo_limpieza(COSTO_LIMPIEZA_USD_MW, PRECIO_USD_MWH, f["e_mw"], TASA_MEDIDA),
                                "ahorro": ahorro_anual_limpieza(COSTO_LIMPIEZA_USD_MW, PRECIO_USD_MWH, f["e_mw"], TASA_MEDIDA)}},
    }
    (APP / "datos.js").write_text("window.DATOS = " + json.dumps(datos, ensure_ascii=False, separators=(",", ":")) + ";\n")
    # Topojson de plotly precargado: así el mapa no lo baja de internet ni necesita servidor
    geo = {n: json.loads((APP / "geo" / f"{n}.json").read_text()) for n in ["asia_50m", "south-america_50m"]}
    (APP / "geo.js").write_text("window.PlotlyGeoAssets = window.PlotlyGeoAssets || {};\n"
                                "window.PlotlyGeoAssets.topojson = Object.assign(window.PlotlyGeoAssets.topojson || {}, "
                                + json.dumps(geo, separators=(",", ":")) + ");\n")
    for n in ["datos.js", "geo.js"]:
        print(f"{n}: {(APP / n).stat().st_size / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
