"""Funciones de limpieza y features reutilizables por notebooks y app."""
import numpy as np
import pandas as pd
import pvlib

# Parques que se ampliaron: su potencia solo es confiable dentro de la ventana GRV.
PARQUES_AMPLIADOS = ["CUM2FV", "PINFFV", "VANGFV"]
VENTANA_GRV = ("2022-01-01", "2025-09-01")
COORDS_CONFIABLES = ["SE_CAMMESA_via_WRI", "osm_parque", "WikiSolar_via_GPPD_aprox",
                     "osm_localidad_inferida_del_nombre"]
AZIMUT_GRADOS = {"north": 0, "northeast": 45, "east": 90, "southeast": 135,
                 "south": 180, "southwest": 225, "west": 270, "northwest": 315}


def agregar_features_tiempo(df: pd.DataFrame, col: str = "timestamp") -> pd.DataFrame:
    """Agrega hora, día del año y mes. La dimensión tiempo siempre tiene que estar."""
    df = df.copy()
    ts = pd.to_datetime(df[col])
    df["hora"] = ts.dt.hour
    df["dia_del_anio"] = ts.dt.dayofyear
    df["mes"] = ts.dt.month
    # Versión cíclica para modelos lineales (las 23 h están cerca de las 0 h).
    df["hora_sin"] = np.sin(2 * np.pi * df["hora"] / 24)
    df["hora_cos"] = np.cos(2 * np.pi * df["hora"] / 24)
    df["doy_sin"] = np.sin(2 * np.pi * df["dia_del_anio"] / 365.25)
    df["doy_cos"] = np.cos(2 * np.pi * df["dia_del_anio"] / 365.25)
    return df


def marcar_valores_congelados(s: pd.Series, min_repeticiones: int = 3) -> pd.Series:
    """True donde un valor distinto de 0 se repite idéntico `min_repeticiones` veces seguidas.

    Detecta el logger "colgado" (station01 repite 15,522 MW durante ~24 h, de noche incluida).
    Aplicarlo por planta: df.groupby("plant_id")[col].transform(marcar_valores_congelados).
    """
    tramo = (s != s.shift()).cumsum()
    largo = s.groupby(tramo).transform("size")
    return (largo >= min_repeticiones) & (s != 0)


def agregar_features_solares(df: pd.DataFrame, ghi: str = "om_shortwave_radiation",
                             dhi: str = "om_diffuse_radiation", temp: str = "om_temperature_2m",
                             viento: str = "om_wind_speed_10m_ms", prefijo: str = "om") -> pd.DataFrame:
    """Geometría solar, irradiancia en el plano del panel (POA), índice de cielo claro y
    temperatura de celda, con pvlib. Espera el dataset A horario (una o varias plantas).

    Por defecto usa Open-Meteo (GHI horizontal). No transponer `pvod_lmd_totalirrad`: el EDA
    muestra que en invierno supera al cielo claro horizontal (hasta ~2x), o sea que el sensor
    de planta ya mide en el plano inclinado; usarlo directo como irradiancia POA.
    """
    df = df.copy()
    az_txt = df["plant_array_azimuth"]
    azimut = pd.to_numeric(az_txt, errors="coerce").fillna(
        az_txt.astype(str).str.lower().str.replace(" ", "").map(AZIMUT_GRADOS)).to_numpy(float)
    if np.isnan(azimut).any():
        raise ValueError(f"Azimut no reconocido: {sorted(az_txt[np.isnan(azimut)].astype(str).unique())}")
    # La etiqueta H representa [H, H+1): la posición solar se calcula en la mitad de la hora.
    t = pd.DatetimeIndex(df["timestamp_utc"]).tz_localize("UTC") + pd.Timedelta(minutes=30)
    pos = pvlib.solarposition.get_solarposition(t, df["plant_lat"].to_numpy(), df["plant_lon"].to_numpy())
    zen = pos["apparent_zenith"].to_numpy()
    cos_z = np.cos(np.radians(zen))
    g = df[ghi].clip(lower=0).to_numpy()
    d = np.minimum(df[dhi].clip(lower=0).to_numpy(), g)
    # DNI a partir de GHI y difusa; se anula con el sol muy bajo para no dividir por ~0.
    dni = np.where(cos_z > 0.087, (g - d) / np.maximum(cos_z, 0.087), 0.0)
    tilt = df["plant_array_tilt_deg"].to_numpy()
    poa = pvlib.irradiance.get_total_irradiance(
        surface_tilt=tilt, surface_azimuth=azimut,
        solar_zenith=zen, solar_azimuth=pos["azimuth"].to_numpy(), dni=dni, ghi=g, dhi=d)
    with np.errstate(divide="ignore", invalid="ignore"):  # de noche el airmass es NaN
        cs = pvlib.clearsky.ineichen(zen, pvlib.atmosphere.get_relative_airmass(zen), linke_turbidity=3)
        cs_poa = pvlib.irradiance.get_total_irradiance(
            surface_tilt=tilt, surface_azimuth=azimut, solar_zenith=zen, solar_azimuth=pos["azimuth"].to_numpy(),
            dni=np.nan_to_num(cs["dni"]), ghi=np.nan_to_num(cs["ghi"]), dhi=np.nan_to_num(cs["dhi"]))["poa_global"]
    # ponytail: Linke turbidity fija (3); usar pvlib.clearsky.lookup_linke_turbidity si hace falta precisión.

    df["sol_zenit_deg"] = zen
    df["sol_azimut_deg"] = pos["azimuth"].to_numpy()
    df[f"{prefijo}_poa"] = np.nan_to_num(np.asarray(poa["poa_global"], dtype=float))
    df[f"{prefijo}_kt_cielo_claro"] = np.where(cs["ghi"] > 50, g / np.where(cs["ghi"] > 50, cs["ghi"], 1), np.nan)
    df[f"{prefijo}_temp_celda"] = pvlib.temperature.faiman(df[f"{prefijo}_poa"], df[temp], df[viento])
    df[f"{prefijo}_frac_difusa"] = np.where(g > 10, d / np.where(g > 10, g, 1), np.nan)
    df["poa_cielo_claro"] = np.nan_to_num(np.asarray(cs_poa, dtype=float))
    return df


def features_escenario(df: pd.DataFrame, escenario: str) -> pd.DataFrame:
    """Columnas comunes `poa`, `temp_celda`, `kt` y `frac_difusa` según la fuente de irradiancia.

    - "lmd": sensor de planta. Ya mide en el plano del panel, así que se usa TAL CUAL.
    - "om": Open-Meteo. Es horizontal, así que se usa la transposición de pvlib con la
      inclinación y el azimut de cada planta (`om_poa`, de agregar_features_solares).
    `kt` = POA / POA de cielo claro (en el mismo plano), indicador de nubosidad.
    """
    df = df if "om_poa" in df else agregar_features_solares(df)
    df = df.copy()
    if escenario == "lmd":
        poa = df["pvod_lmd_totalirrad"].clip(lower=0)
        frac = df["pvod_lmd_diffuseirrad"].clip(lower=0) / poa.where(poa > 10)
        temp, viento = df["pvod_lmd_temperature"], df["pvod_lmd_windspeed"]
    elif escenario == "om":
        poa, frac = df["om_poa"], df["om_frac_difusa"]
        temp, viento = df["om_temperature_2m"], df["om_wind_speed_10m_ms"]
    else:
        raise ValueError(f"escenario debe ser 'lmd' u 'om', no {escenario!r}")
    cs = df["poa_cielo_claro"]
    df["poa"] = poa
    df["temp_celda"] = pvlib.temperature.faiman(poa, temp, viento)
    df["kt"] = (poa / cs.where(cs > 50)).clip(upper=3)
    df["frac_difusa"] = frac.clip(0, 1)
    return df


def limpiar_pvod(df: pd.DataFrame) -> pd.DataFrame:
    """Potencia nocturna a 0 y bandera de datos congelados (no se borran filas)."""
    df = df.copy()
    # Primero la bandera: el congelamiento de station01 se ve justamente en la noche.
    df["dato_congelado"] = df.groupby("plant_id")["pvod_power"].transform(marcar_valores_congelados)
    df.loc[df["is_daylight"] == 0, "pvod_power"] = 0.0
    df["pvod_power_norm"] = df["pvod_power"] / df["plant_capacity_mw"]
    return df


def filtro_rendimiento_argentina(df: pd.DataFrame) -> pd.Series:
    """True en las filas del dataset B aptas para analizar o entrenar rendimiento:
    coordenada confiable, con potencia, sin energía 0, FC <= 0,45 y, para los parques
    ampliados, solo dentro de la ventana GRV."""
    fecha = pd.to_datetime(df["fecha"])
    en_ventana = fecha.between(*VENTANA_GRV)
    return (df["coord_source"].isin(COORDS_CONFIABLES)
            & df["potencia_mw"].notna()
            & (df["energia_mwh"] > 0)
            & (df["factor_capacidad"] <= 0.45)
            & (~df["central"].isin(PARQUES_AMPLIADOS) | en_ventana))
