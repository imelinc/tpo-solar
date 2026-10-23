"""Dashboard del TPO. Lee SOLO de data/processed (nada de APIs en vivo, ni de models/*.pkl).

Las tablas que muestra las genera 04_deteccion (`guardar_precalculado` y `app_argentina.parquet`).
Correr con: streamlit run app/app.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parents[1]))
from src.config import DATA_PROCESSED  # noqa: E402
from src.deteccion import diario_flota, semaforo_flota, serie_planta  # noqa: E402
from src.negocio import (COSTO_LIMPIEZA_USD_MW, PRECIO_USD_MWH, T_BASE_LIMPIEZA_DIAS,  # noqa: E402
                         ahorro_anual_limpieza, costo_anual_limpieza, t_optimo_limpieza)

st.set_page_config(page_title="Detector de bajo rendimiento solar", layout="wide")

COLORES = {"verde": "#2ca02c", "amarillo": "#e6b800", "rojo": "#d62728", "gris": "#8c8c8c"}
INICIO, FIN = pd.Timestamp("2018-07-01").date(), pd.Timestamp("2019-06-13").date()


@st.cache_data
def flota(desde, hasta):
    return diario_flota(str(desde), str(hasta), precalculado=True)


@st.cache_data
def sem(fecha, precio):
    return semaforo_flota(str(fecha), precio, precalculado=True)


@st.cache_data
def serie(planta, desde, hasta):
    return serie_planta(planta, str(desde), str(hasta), precalculado=True)


@st.cache_data
def plantas():
    return pd.read_csv(DATA_PROCESSED / "pvod_plantas_metadata.csv")


@st.cache_data
def argentina():
    return pd.read_parquet(DATA_PROCESSED / "app_argentina.parquet")


TOPOJSON = {"config": {"topojsonURL": "app/static/"}}  # topojson de plotly guardado en el repo: el mapa anda offline


def mapa(df, color, texto, titulo, scope, lon, lat, **kw):
    """Mapa con fondo (costas y países) dibujado con el topojson de app/static (asia_50m, south-america_50m)."""
    fig = px.scatter_geo(df, lat="lat", lon="lon", color=color, text=texto, title=titulo, height=420, scope=scope, **kw)
    fig.update_traces(marker_size=12, textposition="top center", textfont_color="#333")
    fig.update_geos(resolution=50, lonaxis_range=lon, lataxis_range=lat, showcountries=True, showland=True, landcolor="#f2efe6",
                    showocean=True, oceancolor="#dcebf5", showlakes=False)
    fig.update_layout(margin=dict(l=0, r=0, t=40, b=0))
    return fig


st.title("Detector de bajo rendimiento solar")
st.caption("Lo esperado sale de un modelo híbrido (física + Random Forest) con la planta limpia. Error de energía diaria: "
           "**6,04%** (evaluación ciega, may-jun 2019). Precio USD 42,84/MWh (RenovAr Ronda 2), aplicado como ilustración.")
t_resumen, t_detalle, t_arg, t_negocio = st.tabs(["Resumen de flota", "Detalle de planta", "Argentina", "Negocio"])

# ----------------------------------------------------------------------------- 1. Resumen
with t_resumen:
    c1, c2 = st.columns(2)
    fecha = c1.date_input("Fecha del semáforo", pd.Timestamp("2019-05-10").date(), INICIO, FIN)
    periodo = c2.date_input("Período para la energía perdida", (INICIO, FIN), INICIO, FIN)
    if len(periodo) != 2:
        st.stop()
    s = sem(fecha, PRECIO_USD_MWH)
    e = flota(*periodo)
    perdida = e.loc[e["alerta_elegida"], "perdida_mwh"].sum()
    k = st.columns(6)
    for col, estado in zip(k, ["verde", "amarillo", "rojo", "gris"]):
        col.metric(f"En {estado}", int((s["estado"] == estado).sum()))
    k[4].metric("MWh perdidos", f"{perdida:,.0f}", help="Energía perdida en los días con alerta del período")
    k[5].metric("USD perdidos", f"{perdida * PRECIO_USD_MWH:,.0f}", help="A USD 42,84/MWh (RenovAr Ronda 2, ilustrativo)")
    st.caption("Gris = capacidad no confiable (la potencia pico real supera 1,1 × la nominal o la ficha): no se evalúa. "
               "La pérdida se mide contra la planta limpia en los días con alerta del detector elegido.")
    m = plantas()[["plant_id", "plant_lat", "plant_lon", "plant_capacity_mw"]].rename(columns={"plant_lat": "lat", "plant_lon": "lon"})
    m = m.merge(s, on="plant_id", how="left")
    a, b = st.columns([2, 3])
    a.plotly_chart(mapa(m, "estado", "plant_id", f"Semáforo al {fecha} (Hebei, China)", "asia", (110, 122), (34, 42), color_discrete_map=COLORES,
                        hover_data=["accion", "plant_capacity_mw"]), use_container_width=True, **TOPOJSON)
    b.dataframe(s[["plant_id", "estado", "accion", "alerta", "rendimiento_vs_vecinas", "perdida_usd_dia", "modelo"]]
                .style.format({"rendimiento_vs_vecinas": "{:.2f}", "perdida_usd_dia": "{:,.0f}"}, na_rep="—"),
                hide_index=True, use_container_width=True)

# ----------------------------------------------------------------------------- 2. Detalle
with t_detalle:
    c1, c2 = st.columns(2)
    planta = c1.selectbox("Planta", plantas()["plant_id"], index=9)
    rango = c2.date_input("Rango de fechas", (pd.Timestamp("2019-04-01").date(), FIN), INICIO, FIN, key="rango_planta")
    if len(rango) != 2:
        st.stop()
    try:
        horario, d = serie(planta, *rango)
    except ValueError as err:
        st.warning(str(err))
        st.stop()
    d = d.assign(fecha=pd.to_datetime(d["date_local"]))
    fig = go.Figure()
    fig.add_bar(x=d["fecha"], y=d["energia_real_mwh"], name="Real", marker_color="#1f77b4")
    fig.add_scatter(x=d["fecha"], y=d["energia_esperada_mwh"], name="Esperada (planta limpia)", mode="lines",
                    line=dict(color="black"))
    marcas = [("alerta_grave", "Falla grave", "x", "#d62728"), ("alerta_umbral", "Alerta umbral", "circle", "#ff7f0e"),
              ("baja_confianza", "Baja confianza", "triangle-up", "#8c8c8c"),
              ("falla_sensor", "Sin decisión: sensor caído", "square", "#9467bd")]
    tope = d["energia_esperada_mwh"].max() * 1.08
    for i, (col, nombre, simbolo, color) in enumerate(marcas):
        x = d[d[col] & (d["alerta"] | d["alerta_umbral"])] if col == "baja_confianza" else d[d[col]]  # alertas en baja confianza
        fig.add_scatter(x=x["fecha"], y=[tope * (1 + 0.05 * i)] * len(x), name=nombre, mode="markers",
                        marker=dict(symbol=simbolo, size=9, color=color))
    fig.update_layout(title=f"{planta}: energía diaria real vs. esperada", yaxis_title="MWh", height=420,
                      legend=dict(orientation="h", y=-0.15))
    st.plotly_chart(fig, use_container_width=True)
    r = px.bar(d, x="fecha", y="residuo_rel", title="Residuo diario (real − esperado) / esperado",
               color=d["residuo_rel"] < 0, color_discrete_map={True: "#d62728", False: "#2ca02c"}, height=280)
    r.update_layout(showlegend=False, yaxis_tickformat=".0%")
    st.plotly_chart(r, use_container_width=True)
    k = st.columns(4)
    k[0].metric("Días con alerta", int(d["alerta_elegida"].sum()))
    k[1].metric("Energía perdida (días con alerta)", f"{d.loc[d['alerta_elegida'], 'perdida_mwh'].sum():,.0f} MWh")
    k[2].metric("Días sin decisión (sensor caído)", int(d["falla_sensor"].sum()))
    k[3].metric("Días de baja confianza", int(d["baja_confianza"].sum()))
    if d["baja_confianza"].any():
        st.info("Baja confianza: station06 pierde rendimiento de enero a marzo (sombra o nieve) y el modelo, con un solo "
                "año de datos, no lo aprende. Las alertas se muestran pero no implican una falla.")
    if (rango[1] - rango[0]).days <= 14:
        h = px.line(horario, x="timestamp", y=["real_mw", "esperado_mw"], title="Potencia horaria (MW)", height=300)
        st.plotly_chart(h, use_container_width=True)
    else:
        st.caption("Elegí un rango de 14 días o menos para ver la potencia horaria.")

# ----------------------------------------------------------------------------- 3. Argentina
with t_arg:
    st.warning("**Comparación mensual entre parques de CAMMESA, no detección en tiempo real.** Cada parque se compara "
               "con un parque típico con la misma irradiación y clima, y con los de su región ese mes.")
    B = argentina()
    meses = sorted(B["fecha"].dt.date.unique())
    mes = st.select_slider("Mes", meses, value=meses[-1], format_func=lambda f: f"{f:%Y-%m}")
    bm = B[B["fecha"].dt.date == mes].sort_values("factor_capacidad", ascending=False).reset_index(drop=True)
    bm.insert(0, "ranking", bm.index + 1)
    k = st.columns(3)
    k[0].metric("Parques con dato", len(bm))
    k[1].metric("Con alerta", int(bm["alerta"].sum()))
    k[2].metric("Bajo su percentil 10 histórico", int(bm["bajo_p10"].sum()))
    a, b = st.columns([2, 3])
    a.plotly_chart(mapa(bm.assign(estado=np.where(bm["alerta"], "alerta", np.where(bm["bajo_p10"], "bajo su p10", "normal"))),
                        "estado", None, f"Parques solares {mes:%Y-%m}", "south america", (-75, -52), (-56, -21),
                        color_discrete_map={"alerta": "#d62728", "bajo su p10": "#e6b800", "normal": "#2ca02c"},
                        hover_data=["central", "central_descripcion", "factor_capacidad", "indice_rel"]),
                   use_container_width=True, **TOPOJSON)
    b.dataframe(bm[["ranking", "central", "central_descripcion", "provincia", "factor_capacidad", "fc_esp", "indice_rel",
                    "alerta", "bajo_p10"]].style.format({"factor_capacidad": "{:.3f}", "fc_esp": "{:.3f}", "indice_rel": "{:.2f}"}),
                hide_index=True, use_container_width=True, height=420)
    parques = sorted(B["central"].unique())
    p = st.selectbox("Historia de un parque", parques, index=parques.index("ULL4FV") if "ULL4FV" in parques else 0)
    u = B[B["central"] == p]
    fig = go.Figure()
    fig.add_scatter(x=u["fecha"], y=u["factor_capacidad"], name="FC real", mode="lines+markers")
    fig.add_scatter(x=u["fecha"], y=u["fc_esp"], name="FC esperado (parque típico)", mode="lines")
    fig.add_scatter(x=u.loc[u["alerta"], "fecha"], y=u.loc[u["alerta"], "factor_capacidad"], name="alerta", mode="markers",
                    marker=dict(color="#d62728", size=10))
    fig.update_layout(title=f"{p}: factor de capacidad mensual", height=340, yaxis_title="factor de capacidad")
    st.plotly_chart(fig, use_container_width=True)

# ----------------------------------------------------------------------------- 4. Negocio
with t_negocio:
    st.caption("El precio de RenovAr Ronda 2 (2017) se aplica a las plantas chinas como ilustración del valor en un "
               "contexto argentino, no como su ingreso real. El costo de limpieza es un supuesto.")
    c1, c2, c3 = st.columns(3)
    costo = c1.slider("Costo de limpieza (USD por MW) — supuesto", 200, 2000, int(COSTO_LIMPIEZA_USD_MW), 50)
    precio = c2.slider("Precio de la energía (USD/MWh)", 20.0, 120.0, PRECIO_USD_MWH, 0.5)
    tasa_pct = c3.slider("Tasa de ensuciamiento (%/día) — medida: 0,049", 0.01, 0.20, 0.049, 0.001, format="%.3f")
    e = flota(INICIO, FIN)
    e_mw = e.loc[e["modelo"] == "propio", "e_esp"].mean()  # MWh por día por MW esperados (igual que 05_negocio)
    tasa = tasa_pct / 100
    t_opt = t_optimo_limpieza(costo, precio, e_mw, tasa)
    k = st.columns(3)
    k[0].metric("Intervalo óptimo entre limpiezas (T*)", f"{t_opt:.0f} días")
    k[1].metric(f"Ahorro anual vs. limpiar cada {T_BASE_LIMPIEZA_DIAS} días", f"USD {ahorro_anual_limpieza(costo, precio, e_mw, tasa):,.0f} por MW")
    k[2].metric("Costo anual en el óptimo", f"USD {costo_anual_limpieza(t_opt, costo, precio, e_mw, tasa):,.0f} por MW")
    t = np.arange(5, 366)
    fig = px.line(x=t, y=costo_anual_limpieza(t, costo, precio, e_mw, tasa), height=320,
                  labels={"x": "días entre limpiezas", "y": "USD por MW por año"},
                  title="Costo anual: limpiezas + energía perdida por suciedad")
    fig.add_vline(x=t_opt, line_dash="dash", line_color="red")
    st.plotly_chart(fig, use_container_width=True)
    st.subheader("Caso station09: bajo rendimiento crónico")
    s9 = e[(e["plant_id"] == "station09") & e["alerta_elegida"]]
    k = st.columns(3)
    k[0].metric("Días con alerta", len(s9))
    k[1].metric("Energía perdida", f"{s9['perdida_mwh'].sum():,.0f} MWh")
    k[2].metric("Valor al precio elegido", f"USD {s9['perdida_mwh'].sum() * precio:,.0f}")
    st.caption("Una planta que rinde mal todo el tiempo no se ve comparándola con su propio mes anterior: "
               "hace falta compararla con lo esperado o con sus vecinas.")
