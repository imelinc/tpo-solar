"""Inyección de fallas sintéticas para validar el detector (04_deteccion).

Se aplican sobre una serie de potencia "sana" de UNA planta (índice = timestamp) y
devuelven (potencia_con_falla, perdida_fraccion). `perdida_fraccion` es la etiqueta
verdadera: 0 = sin falla, 0,25 = se perdió el 25% de lo que debía generar.
"""
import numpy as np
import pandas as pd


def inyectar_caida_abrupta(p: pd.Series, inicio, dias: float, fraccion: float):
    """Pérdida constante de `fraccion` (0-1) durante `dias` desde `inicio`.
    Simula un inversor o un grupo de strings fuera de servicio."""
    ini = pd.Timestamp(inicio)
    en_falla = (p.index >= ini) & (p.index < ini + pd.Timedelta(days=dias))
    perdida = pd.Series(np.where(en_falla, fraccion, 0.0), index=p.index)
    return p * (1 - perdida), perdida


def inyectar_soiling(p: pd.Series, inicio, dias: float, tasa_diaria: float):
    """Pérdida que crece linealmente `tasa_diaria` (ej. 0,002 = 0,2%/día) desde `inicio`
    durante `dias` y vuelve a 0 al final (limpieza o lluvia)."""
    ini = pd.Timestamp(inicio)
    t = (p.index - ini) / pd.Timedelta(days=1)
    en_falla = (t >= 0) & (t < dias)
    perdida = pd.Series(np.where(en_falla, np.clip(t * tasa_diaria, 0, 1), 0.0), index=p.index)
    return p * (1 - perdida), perdida
