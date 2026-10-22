"""Funciones de limpieza y features reutilizables (completar)."""
import pandas as pd


def agregar_features_tiempo(df: pd.DataFrame, col: str = "timestamp") -> pd.DataFrame:
    """Agrega hora, día del año y mes. La dimensión tiempo siempre tiene que estar."""
    df = df.copy()
    ts = pd.to_datetime(df[col])
    df["hora"] = ts.dt.hour
    df["dia_del_anio"] = ts.dt.dayofyear
    df["mes"] = ts.dt.month
    return df
