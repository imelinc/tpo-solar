#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TPO Ciencia de Datos (UADE) - Construcción de datasets para
"estimar la generación mensual argentina según lugar y clima".

Genera:
  dataset_B_argentina_mensual.csv/.parquet  CAMMESA (parques solares AR, mensual) + potencia + coordenadas + Open-Meteo mensual
  parques_coordenadas.csv               tabla de coordenadas de parques (con coord_source)
  reporte_calidad.md                    reporte rápido de calidad

Uso (local o Colab):
  !pip install pandas pyarrow openpyxl requests py7zr
  !python -m src.build_datasets       # descarga a data/raw y procesa en data/processed
Las descargas se cachean en data/raw/. TPO_DIR y TPO_RAW permiten salidas temporales.
"""
import io, json, os, re, sys, time, unicodedata, zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.config import DATA_PROCESSED, DATA_RAW

BASE = Path(os.environ.get("TPO_DIR", DATA_PROCESSED))
RAW = Path(os.environ.get("TPO_RAW", DATA_RAW))
BASE.mkdir(parents=True, exist_ok=True)
for d in ["cammesa", "openmeteo_B", "geocode"]:
    (RAW / d).mkdir(parents=True, exist_ok=True)

UA = {"User-Agent": "UADE-TPO-CienciaDeDatos/1.0 (proyecto academico)"}

URL_CAMMESA_ERB = ("https://microfe.cammesa.com/static-content/CammesaWeb/download-manager-files/"
                   "historica renovables/Energía Renovables - Base de Datos 2026-09.zip")
URL_CAMMESA_GRV = ("https://microfe.cammesa.com/static-content/CammesaWeb/download-manager-files/"
                   "RenovablesIMGRV/Generación Renovable Variable - Base de Datos - Septiembre 2025.7z")
ERB_XLSX = RAW / "cammesa" / "Energía Renovables - Base de Datos 2026-09.xlsx"
GRV_XLSX = RAW / "cammesa" / "Generación Renovable Variable - Base de Datos 2025-09.xlsx"

OM_DAILY_VARS = ["shortwave_radiation_sum", "temperature_2m_mean", "temperature_2m_max", "cloud_cover_mean",
                 "sunshine_duration", "precipitation_sum"]
MM_LLUVIA_LIMPIA = 5  # mm/día: umbral de lluvia que se considera que limpia los paneles


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


def norm_txt(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().upper()
    return re.sub(r"\s+", " ", s).strip()


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
    if not f.exists() or any(v not in json.loads(f.read_text())["daily"] for v in OM_DAILY_VARS):
        log(f"  Open-Meteo diario {key} {start}..{end}")
        r = get("https://archive-api.open-meteo.com/v1/archive", params=dict(
            latitude=round(lat, 4), longitude=round(lon, 4), start_date=start, end_date=end,
            daily=",".join(OM_DAILY_VARS),
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
            om_precip_mm_mes=("precipitation_sum", lambda s: s.sum(min_count=1)),
            om_dias_lluvia_5mm=("precipitation_sum", lambda s: (s >= MM_LLUVIA_LIMPIA).sum()),
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
            "om_temp_max_media_c", "om_nubosidad_media_pct", "om_horas_sol_mes", "om_precip_mm_mes",
            "om_dias_lluvia_5mm", "om_dias_con_dato"]
    b = b[cols].sort_values(["central", "fecha"]).reset_index(drop=True)
    for c in b.select_dtypes("float").columns:
        if c not in ("lat", "lon"):
            b[c] = b[c].round(5)
    return b, coords


# ============================================================================= REPORTE
def miss_table(df):
    m = (df.isna().mean() * 100).round(2)
    return "\n".join(f"| {c} | {v} |" for c, v in m.items())


def report(b, coords):
    L = ["# Reporte de calidad - dataset TPO solar", f"Generado: {pd.Timestamp.now():%Y-%m-%d %H:%M} (hora Buenos Aires)", ""]
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


def agregar_precipitacion():
    """Suma la precipitación de Open-Meteo al dataset ya armado SIN rehacer el resto
    (no vuelve a bajar CAMMESA). Usa las mismas ubicaciones y fechas que build_B. Uso: TPO_DIR=data/processed python src/build_datasets.py precipitacion"""
    log("== Precipitación Open-Meteo -> dataset B (mensual)")
    b = pd.read_parquet(BASE / "dataset_B_argentina_mensual.parquet").drop(
        columns=["om_precip_mm_mes", "om_dias_lluvia_5mm"], errors="ignore")
    b["loc_key"] = b.lat.round(2).astype(str) + "_" + b.lon.round(2).astype(str)
    today = pd.Timestamp.now(tz="America/Argentina/Buenos_Aires").tz_localize(None).normalize()
    filas = []
    for key, g in b.dropna(subset=["lat"]).groupby("loc_key"):
        start = pd.to_datetime(g.fecha).min()
        end = min(pd.to_datetime(g.fecha).max() + pd.offsets.MonthEnd(0), today - pd.Timedelta(days=6))
        d = fetch_openmeteo_daily(key, g.lat.iloc[0], g.lon.iloc[0], start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
        d["fecha"] = d.time.dt.strftime("%Y-%m-01")
        m = d.groupby("fecha").agg(om_precip_mm_mes=("precipitation_sum", lambda s: s.sum(min_count=1)),
                                   om_dias_lluvia_5mm=("precipitation_sum", lambda s: (s >= MM_LLUVIA_LIMPIA).sum()),
                                   n=("precipitation_sum", "count")).reset_index()
        m["loc_key"] = key
        filas.append(m)
    pm = pd.concat(filas, ignore_index=True)
    b = b.merge(pm, on=["loc_key", "fecha"], how="left")
    b.loc[b.n < b.dias_mes, "om_precip_mm_mes"] = np.nan  # mes incompleto, igual que la irradiación
    cols = [c for c in b.columns if c not in ("loc_key", "n", "om_precip_mm_mes", "om_dias_lluvia_5mm")]
    i = cols.index("om_horas_sol_mes") + 1
    b = b[cols[:i] + ["om_precip_mm_mes", "om_dias_lluvia_5mm"] + cols[i:]]
    b.to_csv(BASE / "dataset_B_argentina_mensual.csv", index=False)
    b.to_parquet(BASE / "dataset_B_argentina_mensual.parquet", index=False)
    log(f"B: {b.om_precip_mm_mes.notna().mean():.1%} meses con precipitación")


def main():
    b, coords = build_B()
    b.to_csv(BASE / "dataset_B_argentina_mensual.csv", index=False)
    b.to_parquet(BASE / "dataset_B_argentina_mensual.parquet", index=False)
    report(b, coords)
    log(f"dataset_B_argentina_mensual.csv: {(BASE / 'dataset_B_argentina_mensual.csv').stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "precipitacion":
        agregar_precipitacion()
    else:
        main()
