#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TPO Ciencia de Datos (UADE) - Construcción de datasets para
"predecir la generación solar esperada según el clima y detectar plantas que rinden de menos".

Genera:
  dataset_A_pvod_15min.csv              PVOD (10 plantas, China) cada 15 min, sin clima externo
  dataset_A_pvod_hourly.csv/.parquet    PVOD agregado a hora + Open-Meteo + NASA POWER
  dataset_B_argentina_mensual.csv/.parquet  CAMMESA (parques solares AR, mensual) + potencia + coordenadas + Open-Meteo mensual
  parques_coordenadas.csv               tabla de coordenadas de parques (con coord_source)
  reporte_calidad.md                    reporte rápido de calidad

Uso (local o Colab):
  !pip install pandas pyarrow openpyxl requests py7zr
  !python build_datasets.py            # descarga lo que falte en ./raw y arma todo
Las descargas se cachean en ./raw/, así que volver a correr no vuelve a pedir nada.
"""
import io, json, math, os, re, sys, time, unicodedata, zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import requests

BASE = Path(os.environ.get("TPO_DIR", Path(__file__).resolve().parent))
RAW = BASE / "raw"
for d in ["pvod", "cammesa", "openmeteo_A", "nasa_A", "openmeteo_B", "geocode"]:
    (RAW / d).mkdir(parents=True, exist_ok=True)

UA = {"User-Agent": "UADE-TPO-CienciaDeDatos/1.0 (proyecto academico)"}

URL_PVOD = ("https://download.scidb.cn/download?fileId=591c58f20a621dbc4526dc91c0214cf6"
            "&path=/V5/PVODdatasets_v1.0.zip&fileName=PVODdatasets_v1.0.zip")
URL_CAMMESA_ERB = ("https://microfe.cammesa.com/static-content/CammesaWeb/download-manager-files/"
                   "historica renovables/Energía Renovables - Base de Datos 2026-09.zip")
URL_CAMMESA_GRV = ("https://microfe.cammesa.com/static-content/CammesaWeb/download-manager-files/"
                   "RenovablesIMGRV/Generación Renovable Variable - Base de Datos - Septiembre 2025.7z")
ERB_XLSX = RAW / "cammesa" / "Energía Renovables - Base de Datos 2026-09.xlsx"
GRV_XLSX = RAW / "cammesa" / "Generación Renovable Variable - Base de Datos 2025-09.xlsx"

OM_HOURLY_VARS = ["shortwave_radiation", "direct_radiation", "diffuse_radiation", "temperature_2m",
                  "cloud_cover", "relative_humidity_2m", "wind_speed_10m"]
OM_RAD_VARS = ["shortwave_radiation", "direct_radiation", "diffuse_radiation"]  # promedio de la hora PREVIA
NASA_VARS = ["ALLSKY_SFC_SW_DWN", "T2M"]


def log(*a):
    print(*a, flush=True)


def get(url, params=None, tries=6, timeout=180):
    for i in range(tries):
        try:
            r = requests.get(url, params=params, headers=UA, timeout=timeout)
            if r.status_code == 429:
                wait = 65 * (i + 1)
                log(f"  429 rate limit, espero {wait}s ...")
                time.sleep(wait)
                continue
            r.raise_for_status()
            return r
        except requests.RequestException as e:
            if i == tries - 1:
                raise
            log(f"  error {e}; reintento")
            time.sleep(5 * (i + 1))


# ----------------------------------------------------------------------------- utilidades
def solar_elevation_deg(ts_utc: pd.Series, lat, lon):
    """Elevación solar aproximada (algoritmo NOAA simplificado, error < ~0.5°)."""
    ts = pd.to_datetime(ts_utc)
    doy = ts.dt.dayofyear.values
    hr = (ts.dt.hour + ts.dt.minute / 60 + ts.dt.second / 3600).values
    g = 2 * np.pi / 365 * (doy - 1 + (hr - 12) / 24)
    eqt = 229.18 * (0.000075 + 0.001868 * np.cos(g) - 0.032077 * np.sin(g)
                    - 0.014615 * np.cos(2 * g) - 0.040849 * np.sin(2 * g))
    decl = (0.006918 - 0.399912 * np.cos(g) + 0.070257 * np.sin(g) - 0.006758 * np.cos(2 * g)
            + 0.000907 * np.sin(2 * g) - 0.002697 * np.cos(3 * g) + 0.00148 * np.sin(3 * g))
    tst = hr * 60 + eqt + 4 * np.asarray(lon)          # tiempo solar verdadero (min)
    ha = np.radians(tst / 4 - 180)
    latr = np.radians(np.asarray(lat))
    cosz = np.sin(latr) * np.sin(decl) + np.cos(latr) * np.cos(decl) * np.cos(ha)
    return np.degrees(np.arcsin(np.clip(cosz, -1, 1)))


def norm_txt(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().upper()
    return re.sub(r"\s+", " ", s).strip()


# ============================================================================= DATASET A
def load_pvod():
    zp = RAW / "pvod" / "pvod.zip"
    if not (RAW / "pvod" / "metadata.csv").exists():
        if not zp.exists():
            log("Descargando PVOD (ScienceDB)...")
            zp.write_bytes(get(URL_PVOD).content)
        zipfile.ZipFile(zp).extractall(RAW / "pvod")
    meta = pd.read_csv(RAW / "pvod" / "metadata.csv")
    frames = []
    for _, m in meta.iterrows():
        d = pd.read_csv(RAW / "pvod" / f"{m.Station_ID}.csv")
        d.insert(0, "plant_id", m.Station_ID)
        frames.append(d)
    df = pd.concat(frames, ignore_index=True)
    # Los CSV originales están en UTC (el toolkit oficial los convierte a UTC+8 con utc_2_pk);
    # verificado: el pico medio de potencia ocurre ~04:00-04:30 UTC = mediodía solar local (~12:20 hora China).
    df["timestamp_utc"] = pd.to_datetime(df.pop("date_time"))
    n0 = len(df)
    df = df.sort_values(["plant_id", "timestamp_utc"]).drop_duplicates(["plant_id", "timestamp_utc"], keep="first")
    dups = n0 - len(df)
    df = df.rename(columns={c: "pvod_" + c for c in df.columns if c not in ("plant_id", "timestamp_utc")})
    df = df.rename(columns={"pvod_nwp_dirrectirrad": "pvod_nwp_directirrad"})
    md = pd.DataFrame({
        "plant_id": meta.Station_ID,
        "plant_capacity_mw": meta.Capacity / 1000.0,          # metadata en kW
        "plant_pv_technology": meta.PV_Technology,
        "plant_panel_size_m2": meta.Panel_Size,
        "plant_panel_number": meta.Panel_Number,
        "plant_array_area_m2": meta.Panel_Size * meta.Panel_Number,
        "plant_array_tilt_deg": meta.Array_Tilt.str.extract(r"(\d+)").astype(float)[0],
        "plant_array_azimuth": meta.Array_Tilt.str.extract(r"^(\w+)")[0].str.lower(),
        "plant_lat": meta.Latitude, "plant_lon": meta.Longitude,
        "plant_module_info": meta.Module.str.replace(r"\s*\n\s*", " | ", regex=True),
        "plant_inverter_info": meta.Inverters.str.replace(r"\s*\n\s*", " | ", regex=True),
    })
    return df, md, dups


def add_time_features(df, ts_col, lat, lon, interval_minutes):
    t = df[ts_col]
    loc = t + pd.Timedelta(hours=8)   # hora local China (UTC+8, sin horario de verano)
    df["timestamp_local_utc8"] = loc
    df["hour_local"] = loc.dt.hour
    df["minute"] = loc.dt.minute
    df["day_of_year"] = loc.dt.dayofyear
    df["month"] = loc.dt.month
    df["date_local"] = loc.dt.date.astype(str)
    mid = t + pd.Timedelta(minutes=interval_minutes / 2)
    df["solar_elevation_deg"] = solar_elevation_deg(mid, lat, lon).round(2)
    df["is_daylight"] = (df["solar_elevation_deg"] > 0).astype(int)
    return df


def fetch_openmeteo_hourly(pid, lat, lon, start, end):
    f = RAW / "openmeteo_A" / f"{pid}.json"
    if not f.exists():
        log(f"  Open-Meteo horario {pid}")
        r = get("https://archive-api.open-meteo.com/v1/archive", params=dict(
            latitude=lat, longitude=lon, start_date=start, end_date=end,
            hourly=",".join(OM_HOURLY_VARS), timezone="GMT"))
        f.write_text(r.text)
        time.sleep(2)
    j = json.loads(f.read_text())
    d = pd.DataFrame(j["hourly"])
    d["time"] = pd.to_datetime(d["time"])
    d.attrs["grid"] = (j["latitude"], j["longitude"], j.get("elevation"))
    return d


def fetch_nasa_hourly(pid, lat, lon, start, end):
    f = RAW / "nasa_A" / f"{pid}.json"
    if not f.exists():
        log(f"  NASA POWER horario {pid}")
        r = get("https://power.larc.nasa.gov/api/temporal/hourly/point", params=dict(
            parameters=",".join(NASA_VARS), community="RE", longitude=lon, latitude=lat,
            start=start.replace("-", ""), end=end.replace("-", ""), format="JSON", **{"time-standard": "UTC"}))
        f.write_text(r.text)
        time.sleep(1)
    j = json.loads(f.read_text())
    p = j["properties"]["parameter"]
    d = pd.DataFrame({k: pd.Series(v) for k, v in p.items()})
    d.index = pd.to_datetime(d.index, format="%Y%m%d%H")
    d = d.replace(-999.0, np.nan).reset_index().rename(columns={"index": "time"})
    return d


def best_lag(a: pd.Series, b: pd.Series, lags=range(-3, 4)):
    """Devuelve el corrimiento (horas) de b que maximiza la correlación con a (ambos indexados por hora)."""
    res = {L: a.corr(b.shift(L, freq="h").reindex(a.index)) for L in lags}
    return max(res, key=lambda k: res[k]), res


def build_A():
    log("== Dataset A (PVOD)")
    df, md, dups = load_pvod()
    df = df.merge(md, on="plant_id", how="left")
    df["power_norm"] = df["pvod_power"] / df["plant_capacity_mw"]
    parts = []
    for pid, g in df.groupby("plant_id", sort=True):
        g = add_time_features(g.copy(), "timestamp_utc", g.plant_lat.iloc[0], g.plant_lon.iloc[0], 15)
        parts.append(g)
    a15 = pd.concat(parts, ignore_index=True)
    md.to_csv(BASE / "pvod_plantas_metadata.csv", index=False)
    lead = ["plant_id", "timestamp_utc", "timestamp_local_utc8", "date_local", "hour_local", "minute",
            "day_of_year", "month", "solar_elevation_deg", "is_daylight"]
    pv_cols = [c for c in a15.columns if c.startswith("pvod_")]
    plant_cols = [c for c in md.columns if c not in ("plant_id", "plant_module_info", "plant_inverter_info")]
    a15 = a15[lead + pv_cols + ["power_norm"] + plant_cols]
    a15 = a15.rename(columns={"power_norm": "pvod_power_norm"})

    # --- agregación horaria: intervalo [H, H+1) etiquetado al inicio de la hora (UTC)
    num = [c for c in pv_cols + ["pvod_power_norm"]]
    a15["hour_utc"] = a15["timestamp_utc"].dt.floor("h")
    agg = {c: "mean" for c in num}
    # dirección del viento: promedio vectorial
    h = a15.groupby(["plant_id", "hour_utc"]).agg(agg)
    for wd in ["pvod_nwp_winddirection", "pvod_lmd_winddirection"]:
        rad = np.radians(a15[wd])
        tmp = pd.DataFrame({"s": np.sin(rad), "c": np.cos(rad), "plant_id": a15.plant_id, "hour_utc": a15.hour_utc})
        tmp = tmp.groupby(["plant_id", "hour_utc"]).mean()
        h[wd] = (np.degrees(np.arctan2(tmp.s, tmp.c)) % 360).round(1)
    h["pvod_n_obs_15min"] = a15.groupby(["plant_id", "hour_utc"]).size()
    h["pvod_energy_mwh"] = h["pvod_power"] * h["pvod_n_obs_15min"] * 0.25  # energía medida en la hora
    h = h.reset_index().rename(columns={"hour_utc": "timestamp_utc"})
    h = h.merge(md, on="plant_id", how="left")

    lag_info = {}
    hourly = []
    for pid, g in h.groupby("plant_id", sort=True):
        g = g.copy()
        lat, lon = g.plant_lat.iloc[0], g.plant_lon.iloc[0]
        start = (g.timestamp_utc.min() - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
        end = (g.timestamp_utc.max() + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
        om = fetch_openmeteo_hourly(pid, lat, lon, start, end).set_index("time")
        nasa = fetch_nasa_hourly(pid, lat, lon, start, end).set_index("time")
        # Open-Meteo: radiación = promedio de la hora anterior (etiqueta = fin de hora) -> se corre -1h
        #             para que la etiqueta sea el inicio de la hora, como en la agregación de PVOD.
        #             Variables instantáneas (temp, nubes, humedad, viento): valor a la hora H+0:30 aprox ->
        #             promedio de los instantes H y H+1.
        om_al = pd.DataFrame(index=om.index)
        for v in OM_RAD_VARS:
            om_al[v] = om[v].shift(-1)
        for v in [x for x in OM_HOURLY_VARS if x not in OM_RAD_VARS]:
            om_al[v] = (om[v] + om[v].shift(-1)) / 2
        om_al["wind_speed_10m"] = om_al["wind_speed_10m"] / 3.6   # km/h -> m/s
        om_al.columns = ["om_" + c for c in om_al.columns]
        om_al = om_al.rename(columns={"om_wind_speed_10m": "om_wind_speed_10m_ms"})
        # NASA POWER: se determina empíricamente el corrimiento contra la irradiancia medida en planta
        meas = g.set_index("timestamp_utc")["pvod_lmd_totalirrad"]
        lag_n, res_n = best_lag(meas, nasa["ALLSKY_SFC_SW_DWN"])
        lag_o, res_o = best_lag(meas, om["shortwave_radiation"])
        lag_info[pid] = dict(nasa_lag_h=lag_n, nasa_corr=round(res_n[lag_n], 3), nasa_corr_lag0=round(res_n[0], 3),
                             om_lag_h=lag_o, om_corr=round(res_o[lag_o], 3),
                             om_grid=om.attrs.get("grid") if hasattr(om, "attrs") else None)
        nasa_al = nasa.shift(lag_n, freq="h")
        nasa_al.columns = ["nasa_" + c for c in nasa_al.columns]
        g = g.set_index("timestamp_utc").join(om_al, how="left").join(nasa_al, how="left").reset_index()
        g = add_time_features(g, "timestamp_utc", lat, lon, 60)
        hourly.append(g)
    ah = pd.concat(hourly, ignore_index=True)
    ah = ah.drop(columns=["minute"])
    lead_h = ["plant_id", "timestamp_utc", "timestamp_local_utc8", "date_local", "hour_local", "day_of_year",
              "month", "solar_elevation_deg", "is_daylight"]
    pv_h = [c for c in ah.columns if c.startswith("pvod_")]
    om_h = [c for c in ah.columns if c.startswith("om_")]
    na_h = [c for c in ah.columns if c.startswith("nasa_")]
    ah = ah[lead_h + pv_h + om_h + na_h + plant_cols]
    a15 = a15.drop(columns=["hour_utc"])
    # redondeo para tamaño
    for d in (a15, ah):
        for c in d.select_dtypes("float").columns:
            if not c.startswith("plant_lat") and not c.startswith("plant_lon"):
                d[c] = d[c].round(4)
    return a15, ah, lag_info, dups


# ============================================================================= DATASET B
PROV_CENTROIDS = {  # centroides aproximados de provincia (fallback de última instancia)
}


def ensure_cammesa():
    if not ERB_XLSX.exists():
        log("Descargando CAMMESA Energías Renovables (zip)...")
        z = zipfile.ZipFile(io.BytesIO(get(URL_CAMMESA_ERB).content))
        n = [x for x in z.namelist() if x.endswith(".xlsx")][0]
        ERB_XLSX.write_bytes(z.read(n))
    if not GRV_XLSX.exists():
        log("Descargando CAMMESA Generación Renovable Variable (7z)...")
        import py7zr
        p = RAW / "cammesa" / "grv.7z"
        p.write_bytes(get(URL_CAMMESA_GRV).content)
        with py7zr.SevenZipFile(p) as z:
            z.extractall(RAW / "cammesa")
        x = [f for f in (RAW / "cammesa").rglob("*.xlsx") if "Variable" in f.name][0]
        x.rename(GRV_XLSX)


def load_cammesa():
    ensure_cammesa()
    e = pd.read_excel(ERB_XLSX, sheet_name="Base de Datos", header=1)
    e = e[e["FUENTE DE ENERGÍA"].astype(str).str.strip() == "SOLAR"].copy()
    e["fecha"] = pd.to_datetime(e["MES"])
    b = pd.DataFrame({
        "fecha": e.fecha.dt.strftime("%Y-%m-01"), "anio": e.fecha.dt.year, "mes": e.fecha.dt.month,
        "central": e.CENTRAL.str.strip(), "central_descripcion": e["CENTRAL DESCRIPCIÓN"].str.strip(),
        "maquina": e.MAQUINA.str.strip(), "provincia": e.PROVINCIA.str.strip(), "region": e["REGIÓN"].str.strip(),
        "tipo_contrato": e["Nueva Generación"].astype(str).str.strip(),
        "energia_gwh": pd.to_numeric(e["ENERGÍA GENERADA [GWh]"], errors="coerce"),
    })
    b["energia_mwh"] = b.energia_gwh * 1000
    # una fila por central-mes (en el archivo ya es así: 1 máquina por central)
    b = (b.groupby(["fecha", "anio", "mes", "central"], as_index=False)
         .agg(central_descripcion=("central_descripcion", "last"), provincia=("provincia", "first"),
              region=("region", "first"), tipo_contrato=("tipo_contrato", "first"),
              energia_gwh=("energia_gwh", "sum"), energia_mwh=("energia_mwh", "sum")))

    g = pd.read_excel(GRV_XLSX, sheet_name="Generación", header=3)
    g = g[g["Tecnología"] == "FOTOVOLTAICA"].copy()
    raw_mw = g["Potencia Habilitada [MW]"].astype(str)
    g["grv_potencia_habilitada_mw"] = pd.to_numeric(raw_mw.str.extract(r"^\s*([\d.]+)")[0], errors="coerce")
    g["grv_mes_en_ensayo"] = raw_mw.str.contains("Ensayo", case=False).astype(int)
    g["fecha"] = pd.to_datetime(g["Fecha"]).dt.strftime("%Y-%m-01")
    gg = g.rename(columns={"Nemotécnico": "central", "Nombre Parque": "grv_nombre_parque",
                           "Nombre Agente": "grv_agente", "Generación Neta [MWh]": "grv_generacion_neta_mwh",
                           "Factor de Carga [%]": "grv_factor_carga"})
    gg["grv_generacion_neta_mwh"] = pd.to_numeric(gg.grv_generacion_neta_mwh, errors="coerce")
    gg["grv_factor_carga"] = pd.to_numeric(gg.grv_factor_carga, errors="coerce")
    gg = gg[["central", "fecha", "grv_nombre_parque", "grv_agente", "grv_potencia_habilitada_mw",
             "grv_mes_en_ensayo", "grv_generacion_neta_mwh", "grv_factor_carga"]]
    return b, gg


def nominatim(q, cache):
    if q in cache:
        return cache[q]
    time.sleep(1.1)  # política de uso de Nominatim: <= 1 req/s
    try:
        r = get("https://nominatim.openstreetmap.org/search",
                params=dict(q=q, countrycodes="ar", format="json", limit=5, addressdetails=1), tries=3, timeout=60)
        res = r.json()
    except Exception as ex:
        log("  nominatim error", ex)
        res = []
    cache[q] = res
    return res


# Localidad inferida a partir del nombre del parque (solo se usa si no se encuentra el parque en OSM).
LOCALIDAD_POR_NOMBRE = [
    (r"TINOG", "Tinogasta"), (r"V(ILLA)?\.? ?ANGELA|VAN\dFV|VANGFV", "Villa Ángela"), (r"CHARATA", "Charata"),
    (r"CAFAYATE", "Cafayate"), (r"CHEPES", "Chepes"), (r"NONOGASTA", "Nonogasta"), (r"SAUJIL", "Saujil"),
    (r"FIAMBALA", "Fiambalá"), (r"ULL[UÚ]M|ULLUM", "Ullum"), (r"ZONDA", "Zonda"), (r"CUTRAL", "Cutral Có"),
    (r"VICTORICA", "Victorica"), (r"JUNIN", "Junín"), (r"LINCOLN", "Lincoln"), (r"QUITILIPI", "Quitilipi"),
    (r"ESQUINA", "Esquina"), (r"BELLA VISTA", "Bella Vista"), (r"PAMPA DEL INFIERNO", "Pampa del Infierno"),
    (r"JUAREZ", "Ingeniero Guillermo N. Juárez"), (r"TRES ISLETAS", "Tres Isletas"),
    (r"CAUCHARI", "Cauchari"), (r"BROCHERO", "Villa Cura Brochero"), (r"V\.?DE MARIA|VILLA MARIA", "Villa de María"),
    (r"SAN RAFAEL", "San Rafael"), (r"PALOMAR", "El Palomar"), (r"RECREO", "Recreo"), (r"CALERA|C\.A\. LA CALERA", "La Calera"),
    (r"LA PUNTA", "La Punta"), (r"SANTA ROSA", "Santa Rosa"), (r"TAMBER", "Tamberías"), (r"ANCHIPURAC", "Anchipurac"),
    (r"CAÑADA HONDA|C\.?HOND|CANADA HONDA", "Cañada Honda"), (r"TOCOTA", "Tocota"), (r"IGLESIA|GUANI|GUAÑI|CORDILLERA SOLAR", "Iglesia"),
    (r"SAN CARLOS", "San Carlos"),
]

# Coordenadas puntuales tomadas de fuentes publicadas (ver diccionario):
#  - SE/CAMMESA: capa "Centrales de Generación" de la Secretaría de Energía, copia incluida en el repo de WRI
#    (raw_source_files/ARG/argentina_power_plants_general.csv). Mismo nemotécnico/descripción que CAMMESA.
#  - Wiki-Solar vía Global Power Plant Database v1.3 (WRI): coordenadas aproximadas (redondeadas a ~0.01°).
COORD_FUENTES = {
    "HON1FV": (-31.98578, -68.538851, "SE_CAMMESA_via_WRI", "C.HOND 1 FOTOVO (Sarmiento, San Juan)"),
    "HON2FV": (-31.98578, -68.538851, "SE_CAMMESA_via_WRI", "C.HOND 2 FOTOVO (Sarmiento, San Juan)"),
    "CHI1FV": (-31.988089, -68.54017, "SE_CAMMESA_via_WRI", "CHIMBE 1 FOTOVO (Sarmiento, San Juan)"),
    "SJUAFV": (-31.38913, -68.675205, "SE_CAMMESA_via_WRI", "S.JUAN I FOTOVO (Ullum, San Juan)"),
    "IGLEFV": (-30.34, -69.27, "WikiSolar_via_GPPD_aprox", "Iglesia-Guañizuil (GPPD v1.3)"),
    "GZ2AFV": (-30.34, -69.27, "WikiSolar_via_GPPD_aprox", "Iglesia-Guañizuil (GPPD v1.3)"),
}
GENERIC = {"PARQUE", "SOLAR", "FV", "F", "V", "P", "S", "FOTOVOLTAICO", "FOTOVOLTAICA", "I", "II", "III", "IV", "V",
           "DE", "DEL", "LA", "LAS", "LOS", "EL", "AMP", "PQUE", "Y"}


def name_tokens(s):
    return {t for t in re.split(r"[^A-Z0-9]+", norm_txt(s)) if t and t not in GENERIC and not t.isdigit()}


PROV_NOMINATIM = {"NEUQUÉN": "Neuquén", "CORDOBA": "Córdoba", "TUCUMAN": "Tucumán", "RIO NEGRO": "Río Negro",
                  "ENTRE RIOS": "Entre Ríos"}


def geocode_parks(b, gg):
    out = BASE / "parques_coordenadas.csv"
    if out.exists():
        return pd.read_csv(out)
    cache_f = RAW / "geocode" / "nominatim_cache.json"
    cache = json.loads(cache_f.read_text()) if cache_f.exists() else {}
    names = gg.groupby("central").grv_nombre_parque.first()
    parks = b.groupby("central").agg(central_descripcion=("central_descripcion", "last"),
                                     provincia=("provincia", "first")).reset_index()
    rows = []
    for _, p in parks.iterrows():
        prov = p.provincia
        prov_q = PROV_NOMINATIM.get(prov, prov.title())
        prov_n = norm_txt(prov_q)
        grv = names.get(p.central)
        cands = []
        if isinstance(grv, str):
            base = re.sub(r"^F\.V\.\s*", "", grv).strip()
            cands += [f"Parque Solar {base}", f"Parque Fotovoltaico {base}", f"{base} solar"]
        desc = re.sub(r"^(PQUE|PARQUE|P\.S\.F\.V\.|P\.S\.|P\. S\.|P\.SOLAR|PQUE\.|PARQUE FOTOV\.|PQUE FOTOV\.?|C\.FOTOV\.|Pque\.)\s*"
                      r"(SOLAR|FOTOV\.?|FTV|FV)?\s*", "", p.central_descripcion, flags=re.I).strip()
        cands += [f"Parque Solar {desc.title()}"]
        found = None
        if p.central in COORD_FUENTES:
            la, lo, src, desc_src = COORD_FUENTES[p.central]
            found = (la, lo, src, None, desc_src)
        want = name_tokens(grv if isinstance(grv, str) else p.central_descripcion)
        for q in ([] if found else dict.fromkeys(cands)):
            for res in nominatim(q, cache):
                dn = norm_txt(res.get("display_name", ""))
                nm = norm_txt(res.get("name", ""))
                is_plant = res.get("class") in ("power", "landuse", "man_made")
                overlap = bool(want & name_tokens(nm)) if want else False
                if prov_n in dn and is_plant and overlap and ("SOLAR" in nm or "FOTOVOLT" in nm or res.get("class") == "power"):
                    found = (float(res["lat"]), float(res["lon"]), "osm_parque", q, res.get("display_name"))
                    break
            if found:
                break
        if not found:
            txt = norm_txt(f"{p.central_descripcion} {grv or ''}")
            for pat, loc in LOCALIDAD_POR_NOMBRE:
                if re.search(norm_txt(pat), txt):
                    q = f"{loc}, {prov_q}, Argentina"
                    for res in nominatim(q, cache):
                        if prov_n in norm_txt(res.get("display_name", "")):
                            found = (float(res["lat"]), float(res["lon"]), "osm_localidad_inferida_del_nombre", q,
                                     res.get("display_name"))
                            break
                    break
        if not found:
            for q in (f"Provincia de {prov_q}, Argentina", f"{prov_q}, Argentina"):
                for res in nominatim(q, cache):
                    if res.get("addresstype") in ("state", "province"):
                        found = (float(res["lat"]), float(res["lon"]), "osm_centroide_provincia", q, res.get("display_name"))
                        break
                if found:
                    break
        rows.append(dict(central=p.central, central_descripcion=p.central_descripcion, provincia=prov,
                         grv_nombre_parque=grv, lat=found[0] if found else np.nan, lon=found[1] if found else np.nan,
                         coord_source=found[2] if found else "sin_coordenadas",
                         geocode_query=found[3] if found else None, geocode_match=found[4] if found else None))
        cache_f.write_text(json.dumps(cache, ensure_ascii=False))
        log(f"  {p.central:8s} {rows[-1]['coord_source']:35s} {rows[-1]['geocode_match']}")
    df = pd.DataFrame(rows)
    df.to_csv(out, index=False)
    return df


def fetch_openmeteo_daily(key, lat, lon, start, end):
    f = RAW / "openmeteo_B" / f"{key}_{start}_{end}.json"
    if not f.exists():
        log(f"  Open-Meteo diario {key} {start}..{end}")
        r = get("https://archive-api.open-meteo.com/v1/archive", params=dict(
            latitude=round(lat, 4), longitude=round(lon, 4), start_date=start, end_date=end,
            daily="shortwave_radiation_sum,temperature_2m_mean,temperature_2m_max,cloud_cover_mean,sunshine_duration",
            timezone="America/Argentina/Buenos_Aires"))
        f.write_text(r.text)
        time.sleep(3)
    j = json.loads(f.read_text())
    d = pd.DataFrame(j["daily"])
    d["time"] = pd.to_datetime(d["time"])
    return d


def build_B():
    log("== Dataset B (CAMMESA)")
    b, gg = load_cammesa()
    b = b.merge(gg, on=["central", "fecha"], how="left")
    # potencia: mismo mes en GRV; si no, valor del mes más cercano del mismo parque en GRV
    b = b.sort_values(["central", "fecha"]).reset_index(drop=True)
    b["potencia_mw"] = b.grv_potencia_habilitada_mw
    b["potencia_source"] = np.where(b.potencia_mw.notna(), "GRV_mismo_mes", None)
    gcap = gg.dropna(subset=["grv_potencia_habilitada_mw"]).copy()
    gcap["f"] = pd.to_datetime(gcap.fecha)
    for i in b.index[b.potencia_mw.isna()]:
        c = gcap[gcap.central == b.at[i, "central"]]
        if len(c):
            f = pd.to_datetime(b.at[i, "fecha"])
            j = (c.f - f).abs().idxmin()
            b.at[i, "potencia_mw"] = c.at[j, "grv_potencia_habilitada_mw"]
            b.at[i, "potencia_source"] = "GRV_mes_mas_cercano(" + c.at[j, "fecha"][:7] + ")"
    b["potencia_source"] = b.potencia_source.fillna("sin_dato")
    b["dias_mes"] = pd.to_datetime(b.fecha).dt.days_in_month
    b["horas_mes"] = b.dias_mes * 24
    b["factor_capacidad"] = b.energia_mwh / (b.potencia_mw * b.horas_mes)
    b["estacion_hs"] = b.mes.map({12: "verano", 1: "verano", 2: "verano", 3: "otoño", 4: "otoño", 5: "otoño",
                                  6: "invierno", 7: "invierno", 8: "invierno", 9: "primavera", 10: "primavera",
                                  11: "primavera"})

    coords = geocode_parks(b, gg)
    b = b.merge(coords[["central", "lat", "lon", "coord_source"]], on="central", how="left")

    # Open-Meteo diario -> mensual, por ubicación única (lat/lon redondeado a 0.01°), sólo período activo
    b["loc_key"] = b.lat.round(2).astype(str) + "_" + b.lon.round(2).astype(str)
    today = pd.Timestamp.now(tz="America/Argentina/Buenos_Aires").tz_localize(None).normalize()
    om_rows = []
    for key, g in b.dropna(subset=["lat"]).groupby("loc_key"):
        start = pd.to_datetime(g.fecha).min()
        end = min(pd.to_datetime(g.fecha).max() + pd.offsets.MonthEnd(0), today - pd.Timedelta(days=6))
        d = fetch_openmeteo_daily(key, g.lat.iloc[0], g.lon.iloc[0], start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
        d["fecha"] = d.time.dt.strftime("%Y-%m-01")
        m = d.groupby("fecha").agg(
            om_ghi_kwh_m2_mes=("shortwave_radiation_sum", lambda s: s.sum(min_count=1) / 3.6),
            om_ghi_kwh_m2_dia_prom=("shortwave_radiation_sum", lambda s: s.mean() / 3.6),
            om_temp_media_c=("temperature_2m_mean", "mean"), om_temp_max_media_c=("temperature_2m_max", "mean"),
            om_nubosidad_media_pct=("cloud_cover_mean", "mean"),
            om_horas_sol_mes=("sunshine_duration", lambda s: s.sum(min_count=1) / 3600),
            om_dias_con_dato=("shortwave_radiation_sum", "count")).reset_index()
        m["loc_key"] = key
        om_rows.append(m)
    om = pd.concat(om_rows, ignore_index=True)
    b = b.merge(om, on=["loc_key", "fecha"], how="left")
    b.loc[b.om_dias_con_dato < b.dias_mes, ["om_ghi_kwh_m2_mes", "om_horas_sol_mes"]] = np.nan  # mes incompleto
    # rendimiento específico y "performance ratio" aproximado (energía / (potencia * irradiación horizontal))
    b["rendimiento_especifico_kwh_kw"] = b.energia_mwh / b.potencia_mw  # = kWh/kWp
    b["performance_ratio_aprox"] = b.rendimiento_especifico_kwh_kw / b.om_ghi_kwh_m2_mes
    cols = ["fecha", "anio", "mes", "estacion_hs", "dias_mes", "central", "central_descripcion", "grv_nombre_parque",
            "grv_agente", "provincia", "region", "tipo_contrato", "lat", "lon", "coord_source",
            "energia_gwh", "energia_mwh", "potencia_mw", "potencia_source", "grv_mes_en_ensayo",
            "grv_generacion_neta_mwh", "grv_factor_carga", "factor_capacidad", "rendimiento_especifico_kwh_kw",
            "performance_ratio_aprox", "om_ghi_kwh_m2_mes", "om_ghi_kwh_m2_dia_prom", "om_temp_media_c",
            "om_temp_max_media_c", "om_nubosidad_media_pct", "om_horas_sol_mes", "om_dias_con_dato"]
    b = b[cols].sort_values(["central", "fecha"]).reset_index(drop=True)
    for c in b.select_dtypes("float").columns:
        if c not in ("lat", "lon"):
            b[c] = b[c].round(5)
    return b, coords


# ============================================================================= REPORTE
def miss_table(df):
    m = (df.isna().mean() * 100).round(2)
    return "\n".join(f"| {c} | {v} |" for c, v in m.items())


def report(a15, ah, lag_info, dups, b, coords):
    L = ["# Reporte de calidad - datasets TPO solar", f"Generado: {pd.Timestamp.now():%Y-%m-%d %H:%M} (hora Buenos Aires)", ""]
    L += ["## Dataset A 15 min", f"- Filas: {len(a15):,} | columnas: {a15.shape[1]} | plantas: {a15.plant_id.nunique()}",
          f"- Período (UTC): {a15.timestamp_utc.min()} a {a15.timestamp_utc.max()}",
          f"- Timestamps duplicados eliminados: {dups}", ""]
    per = a15.groupby("plant_id").agg(filas=("pvod_power", "size"), desde=("timestamp_utc", "min"),
                                      hasta=("timestamp_utc", "max"), cap_mw=("plant_capacity_mw", "first"),
                                      p_max=("pvod_power", "max"))
    per["p_max/cap"] = (per.p_max / per.cap_mw).round(2)
    per["corr_power_vs_lmd_ghi"] = a15.groupby("plant_id").apply(lambda g: g.pvod_power.corr(g.pvod_lmd_totalirrad)).round(3)
    per["corr_power_vs_nwp_ghi"] = a15.groupby("plant_id").apply(lambda g: g.pvod_power.corr(g.pvod_nwp_globalirrad)).round(3)
    per["potencia_nocturna_media_mw"] = a15[a15.is_daylight == 0].groupby("plant_id").pvod_power.mean().round(3)
    L += [per.to_markdown(), ""]
    L += ["## Dataset A horario", f"- Filas: {len(ah):,} | columnas: {ah.shape[1]}",
          f"- Horas con 4 registros de 15 min: {(ah.pvod_n_obs_15min == 4).mean() * 100:.2f}%", ""]
    per = ah.groupby("plant_id").apply(lambda g: pd.Series({
        "corr_power_vs_om_ghi": g.pvod_power.corr(g.om_shortwave_radiation),
        "corr_power_vs_nasa_ghi": g.pvod_power.corr(g.nasa_ALLSKY_SFC_SW_DWN),
        "corr_power_vs_lmd_ghi": g.pvod_power.corr(g.pvod_lmd_totalirrad),
        "corr_lmd_ghi_vs_om_ghi": g.pvod_lmd_totalirrad.corr(g.om_shortwave_radiation),
        "corr_temp_lmd_vs_om": g.pvod_lmd_temperature.corr(g.om_temperature_2m),
        "corr_temp_lmd_vs_nasa": g.pvod_lmd_temperature.corr(g.nasa_T2M)})).round(3)
    lag = pd.DataFrame(lag_info).T[["om_lag_h", "om_corr", "nasa_lag_h", "nasa_corr", "nasa_corr_lag0"]]
    L += ["Correlaciones (Pearson, todas las horas):", per.to_markdown(), "",
          "Verificación de alineación temporal (corrimiento en horas que maximiza corr. con la irradiancia medida en planta):",
          "om_lag_h sobre la serie cruda de Open-Meteo (se espera -1 porque la radiación es promedio de la hora previa; "
          "en el dataset ya está corregido). nasa_lag_h es el corrimiento aplicado a NASA POWER.",
          lag.to_markdown(), "", "% faltantes por columna (horario):", "", "| columna | % NA |", "|---|---|", miss_table(ah), ""]
    L += ["## Dataset B Argentina mensual", f"- Filas: {len(b):,} | columnas: {b.shape[1]} | parques: {b.central.nunique()}",
          f"- Período: {b.fecha.min()} a {b.fecha.max()}",
          f"- Filas con potencia: {b.potencia_mw.notna().mean() * 100:.1f}% (mismo mes GRV: {(b.potencia_source == 'GRV_mismo_mes').mean() * 100:.1f}%)",
          f"- coord_source: {coords.coord_source.value_counts().to_dict()}",
          f"- Corr. energía/potencia vs irradiación mensual Open-Meteo (filas con FC entre 0.02 y 0.45): "
          f"{b[(b.factor_capacidad > 0.02) & (b.factor_capacidad < 0.45)][['rendimiento_especifico_kwh_kw', 'om_ghi_kwh_m2_mes']].corr().iloc[0, 1]:.3f}",
          f"- Factor de capacidad: mediana {b.factor_capacidad.median():.3f}; filas con FC > 0.45 (sospechosas): {(b.factor_capacidad > 0.45).sum()}; "
          f"con energía = 0: {(b.energia_mwh == 0).sum()}",
          f"- Diferencia CAMMESA ERB vs GRV (energía, filas con ambos): mediana |dif| = "
          f"{((b.energia_mwh - b.grv_generacion_neta_mwh).abs() / b.grv_generacion_neta_mwh.replace(0, np.nan)).median() * 100:.2f}%",
          "", "| columna | % NA |", "|---|---|", miss_table(b)]
    (BASE / "reporte_calidad.md").write_text("\n".join(L), encoding="utf-8")
    log("\n".join(L[:12]))


def main():
    a15, ah, lag_info, dups = build_A()
    a15.to_csv(BASE / "dataset_A_pvod_15min.csv", index=False)
    ah.to_csv(BASE / "dataset_A_pvod_hourly.csv", index=False)
    ah.to_parquet(BASE / "dataset_A_pvod_hourly.parquet", index=False)
    b, coords = build_B()
    b.to_csv(BASE / "dataset_B_argentina_mensual.csv", index=False)
    b.to_parquet(BASE / "dataset_B_argentina_mensual.parquet", index=False)
    report(a15, ah, lag_info, dups, b, coords)
    for f in ["dataset_A_pvod_15min.csv", "dataset_A_pvod_hourly.csv", "dataset_B_argentina_mensual.csv"]:
        mb = (BASE / f).stat().st_size / 1e6
        log(f"{f}: {mb:.1f} MB")
        if mb > 100:
            with zipfile.ZipFile(BASE / (f + ".zip"), "w", zipfile.ZIP_DEFLATED) as z:
                z.write(BASE / f, f)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "A":
        build_A()
    else:
        main()
