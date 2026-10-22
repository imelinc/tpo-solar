"""Dashboard del TPO. Lee SOLO de data/processed y models/ (nada de APIs en vivo)."""
import sys
from pathlib import Path

import streamlit as st

sys.path.append(str(Path(__file__).resolve().parents[1]))
from src.config import DATA_PROCESSED, MODELS  # noqa: E402

st.set_page_config(page_title="Detector de bajo rendimiento solar", layout="wide")

portada, vista_global, vista_argentina = st.tabs(["🏠 Portada", "🌍 Global", "🇦🇷 Argentina"])

with portada:
    st.title("Detector de bajo rendimiento solar")
    st.markdown("**Hipótesis:** _(completar en una frase)_")
    st.info("Conclusión primero: cuánta energía y plata se pierde por fallas no detectadas.")

with vista_global:
    st.header("Generación esperada vs. real")
    st.write("Semáforo de plantas, detalle por planta y métricas de modelos. (completar)")

with vista_argentina:
    st.header("Parques solares en Argentina")
    st.write("Generación mensual por parque vs. radiación (CAMMESA + Open-Meteo). (completar)")
