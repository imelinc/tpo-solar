"""Parámetros y cuentas de negocio (05_negocio y semáforo del dashboard). Editables.

PRECIO_USD_MWH: precio promedio adjudicado a la solar fotovoltaica en RenovAr Ronda 2
  (incluye Fase 2): USD 42,84/MWh. Fuente: Energía Estratégica, 23/01/2018,
  https://energiaestrategica.com/energiaestrategica/en/notes/solo-dos-empresas-ganadoras-la-licitacion-energias-renovables-argentinas
  Es el precio de contrato de un parque solar argentino típico de esa ronda, no el precio spot.

COSTO_LIMPIEZA_USD_MW: SUPUESTO, sin fuente argentina. Se toma USD 800 por MW por limpieza,
  el valor del notebook de referencia del equipo. Techo de contexto: NREL estima el O&M total
  de una planta de estructura fija en USD 9,1/kW/año sin reemplazo de inversores (= USD 9.100/MW/año,
  limpieza incluida). Fuente: Reuters Events, https://www.reutersevents.com/renewables/node/60975
  Reemplazar por una cotización real antes de usar los resultados.

DIAS_REVISION_MANUAL: SUPUESTO. Hoy alguien mira los números una vez por mes.

T_BASE_LIMPIEZA_DIAS: SUPUESTO. Línea base del ahorro por limpieza óptima: hoy se limpia una vez por año.
"""
import numpy as np

PRECIO_USD_MWH = 42.84
COSTO_LIMPIEZA_USD_MW = 800.0
DIAS_REVISION_MANUAL = 30
T_BASE_LIMPIEZA_DIAS = 365


def t_optimo_limpieza(costo_usd_mw: float, precio_usd_mwh: float, energia_mwh_dia_mw: float, tasa_dia: float) -> float:
    """Intervalo óptimo entre limpiezas T* = sqrt(2C / (P·E·r)), en días.

    Con suciedad lineal r (fracción por día), la pérdida acumulada en T días es P·E·r·T²/2.
    El costo por día es C/T + P·E·r·T/2, y se minimiza en T* (C por MW, E en MWh/día por MW).
    """
    if tasa_dia <= 0:
        return np.inf
    return float(np.sqrt(2 * costo_usd_mw / (precio_usd_mwh * energia_mwh_dia_mw * tasa_dia)))


def costo_anual_limpieza(t_dias, costo_usd_mw: float, precio_usd_mwh: float, energia_mwh_dia_mw: float, tasa_dia: float):
    """Costo anual por MW (limpiezas + energía perdida por suciedad) si se limpia cada t días."""
    t = np.asarray(t_dias, dtype=float)
    return 365 * (costo_usd_mw / t + precio_usd_mwh * energia_mwh_dia_mw * tasa_dia * t / 2)


def ahorro_anual_limpieza(costo_usd_mw: float, precio_usd_mwh: float, energia_mwh_dia_mw: float, tasa_dia: float,
                          t_base_dias: float = T_BASE_LIMPIEZA_DIAS) -> float:
    """Ahorro anual por MW de limpiar cada T* días en lugar de cada `t_base_dias` (>= 0, porque T* es el mínimo)."""
    t = t_optimo_limpieza(costo_usd_mw, precio_usd_mwh, energia_mwh_dia_mw, tasa_dia)
    if not np.isfinite(t):
        return 0.0
    args = (costo_usd_mw, precio_usd_mwh, energia_mwh_dia_mw, tasa_dia)
    return float(costo_anual_limpieza(t_base_dias, *args) - costo_anual_limpieza(t, *args))
