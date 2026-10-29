# Diccionario de datos – TPO Ciencia de Datos (energía solar)

Objetivo del TPO: **estimar cuánta energía generaría un parque solar en Argentina según su ubicación, el año y su potencia**, a partir del clima del mes.

La precipitación (`om_precip_mm_mes` y `om_dias_lluvia_5mm`) se agregó el 22/10/2026 con `TPO_DIR=data/processed python src/build_datasets.py precipitacion`, que solo baja la lluvia de Open-Meteo y la une al dataset ya armado, sin tocar el resto de las columnas. Una corrida completa del script ya la incluye.

Todo se arma con `build_datasets.py` (corre en Colab: `pip install pandas pyarrow openpyxl requests py7zr tabulate`). Las descargas se guardan en `raw/` y no se vuelven a pedir si ya están.

| Archivo | Qué es | Granularidad |
|---|---|---|
| `dataset_B_argentina_mensual.csv` / `.parquet` | Generación mensual de cada parque solar argentino (CAMMESA) + potencia + coordenadas + clima mensual Open-Meteo | 1 fila = parque × mes |
| `parques_coordenadas.csv` | Coordenadas usadas para cada parque y de dónde salen | parque |
| `reporte_calidad.md` | Conteos, rangos, % de faltantes, correlaciones de control | — |

---

## Dataset B – Argentina mensual (CAMMESA)

**Fuentes:**
1. **CAMMESA – "Energías Renovables – Base de Datos" (2026-09)**, hoja *Base de Datos*, filas con fuente = SOLAR. Trae 97 centrales solares con generación mensual desde 2011-01 hasta 2026-09. https://cammesaweb.cammesa.com/download/energia-renovables-base-de-datos/
2. **CAMMESA – "Generación Renovable Variable – Base de Datos" (2025-09)**, hoja *Generación*, tecnología FOTOVOLTAICA. Tiene la **Potencia Habilitada [MW]** de cada parque y mes, de 2022-01 a 2025-09 (75 parques). https://cammesaweb.cammesa.com/informe-generacion-renovable-variable-2025/
3. **Coordenadas:** ver `coord_source` más abajo.
4. **Open-Meteo Historical** (diario, sumado a mensual) en la coordenada de cada parque.

**Join:** se unió ERB con GRV por `central` (nemotécnico CAMMESA, por ejemplo `CAU1FV`) y `fecha` (mes). La energía coincide entre los dos archivos (la mediana de la diferencia es 0%). El clima se unió por ubicación y mes.

| Columna | Descripción | Unidad |
|---|---|---|
| fecha | Primer día del mes (AAAA-MM-01) | — |
| anio, mes, dias_mes | Año, mes y días del mes | — |
| estacion_hs | Estación del hemisferio sur (verano = dic a feb) | — |
| central | Nemotécnico CAMMESA (clave del parque) | — |
| central_descripcion | Nombre en la base ERB | — |
| grv_nombre_parque, grv_agente | Nombre del parque y del agente (empresa) en la base GRV (solo 2022-01 a 2025-09) | — |
| provincia, region | Provincia y región eléctrica (CAMMESA) | — |
| tipo_contrato | Programa o mercado: RENOVAR, MATER, Resto, RenMDI, etc. ("Nueva Generación" en CAMMESA) | — |
| lat, lon | Coordenadas usadas para pedir el clima | grados decimales |
| coord_source | Precisión de la coordenada (ver tabla de abajo) | — |
| energia_gwh, energia_mwh | **Energía generada en el mes (target)** | GWh, MWh |
| potencia_mw | Potencia habilitada. Se toma la del mismo mes en GRV y, si no hay, la del mes más cercano del mismo parque. | MW |
| potencia_source | `GRV_mismo_mes`, `GRV_mes_mas_cercano(AAAA-MM)` o `sin_dato` | — |
| grv_mes_en_ensayo | 1 si CAMMESA marcó el mes como "aportes descartados – ensayos" | 0/1 |
| grv_generacion_neta_mwh, grv_factor_carga | Generación neta y factor de carga según GRV (control cruzado) | MWh, fracción |
| factor_capacidad | `energia_mwh / (potencia_mw × horas del mes)` | fracción |
| rendimiento_especifico_kwh_kw | `energia_mwh / potencia_mw`, es decir kWh por kW instalado en el mes | kWh/kW |
| performance_ratio_aprox | `rendimiento_especifico / om_ghi_kwh_m2_mes`. **No es un PR técnico.** Usa irradiación horizontal (no la del plano del panel) y potencia AC, por eso suele dar más de 1 (por la inclinación, los seguidores y una potencia DC mayor que la AC). Sirve para **comparar** un parque con sí mismo en el tiempo o con parques parecidos. | adimensional |
| om_ghi_kwh_m2_mes | Irradiación global horizontal del mes. Es la suma de `shortwave_radiation_sum` diario (MJ/m²) dividido 3,6. Es NaN si faltan días. | kWh/m² |
| om_ghi_kwh_m2_dia_prom | Promedio diario del mes | kWh/m²/día |
| om_temp_media_c, om_temp_max_media_c | Temperatura media y promedio de las máximas diarias | °C |
| om_nubosidad_media_pct | Nubosidad media | % |
| om_horas_sol_mes | Horas de sol del mes (`sunshine_duration`) | h |
| om_precip_mm_mes | Precipitación del mes (suma de `precipitation_sum` diario). Es NaN si faltan días. | mm |
| om_dias_lluvia_5mm | Días del mes con 5 mm o más de lluvia (los que lavan los paneles) | conteo |
| om_dias_con_dato | Días con dato de Open-Meteo en el mes | conteo |

### `coord_source` (precisión de coordenadas)

| Valor | Significado | Precisión aprox. |
|---|---|---|
| SE_CAMMESA_via_WRI | Capa oficial "Centrales de Generación" de la Secretaría de Energía (coordenadas georreferenciadas por la DIE con registros CAMMESA). Se usó la copia publicada en el repo de la Global Power Plant Database de WRI (`raw_source_files/ARG/argentina_power_plants_general.csv`). | nivel planta |
| osm_parque | El polígono del parque está cargado en OpenStreetMap (búsqueda Nominatim). Se exigió que coincidan la provincia, una palabra distintiva del nombre y la etiqueta de planta o uso industrial. | nivel planta |
| WikiSolar_via_GPPD_aprox | Coordenada redondeada de Wiki-Solar, tomada de la Global Power Plant Database v1.3 (WRI) | ~1 km |
| osm_localidad_inferida_del_nombre | El parque no está en OSM. Se usó el centro de la localidad que aparece en el nombre (por ejemplo, "Tinogasta", "Villa Ángela" o "Ullum"). | ~1-20 km |
| osm_centroide_provincia | No se pudo ubicar el parque. Se usó el centroide de la provincia. | **cientos de km, el clima de esa fila es solo indicativo** |
| sin_coordenadas | No se encontró ni la provincia (en la versión actual no queda ninguno) | — |

Para análisis de rendimiento conviene **filtrar `coord_source` en (SE_CAMMESA_via_WRI, osm_parque, WikiSolar_via_GPPD_aprox, osm_localidad_inferida_del_nombre)**. Si consiguen la ubicación exacta de un parque, la pueden corregir a mano en `parques_coordenadas.csv` y volver a correr el script.

---

## Advertencias (leer antes de modelar)

**Dataset B**
- La potencia por mes solo existe de 2022-01 a 2025-09 (archivo GRV). Para otros meses se usa la del mes más cercano. Si el parque se amplió (por ejemplo CUM2FV pasa de 4 a 35,2 MW, PINFFV de 16,2 a 130 y VANGFV de 14,7 a 40), el factor de capacidad de los meses anteriores a 2022 o posteriores a 2025-09 puede estar mal. Ver `potencia_source`.
- 22 centrales (en su mayoría chicas, de autogeneración o muy nuevas) no aparecen en GRV, por eso `potencia_mw = NaN` (alrededor del 7% de las filas).
- Hay meses con energía = 0, que corresponden a parques en ensayo, antes de la habilitación comercial o en una falla, y 35 filas con factor de capacidad mayor a 0,45 (sobre todo CHI1FV, HON1FV y TAMBFV; puede deberse a que la potencia habilitada es AC y menor que la DC, a seguidores, o a que se usó la potencia de un mes cercano). No son errores de armado, pero conviene tratarlos como outliers o como casos a explicar.
- El primer y el último mes de cada parque suelen estar incompletos (entrada en servicio a mitad de mes).
- CAMMESA publica GWh con muchos decimales y se mantuvieron tal cual.
- El clima de Open-Meteo de 2026-09 es reciente y puede tener correcciones posteriores.

---

## Licencias y cómo citar

- **CAMMESA:** datos públicos del Mercado Eléctrico Mayorista. Citar "Fuente: CAMMESA – Base de Datos Energías Renovables (2026-09) y Generación Renovable Variable (2025-09)", con el link y la fecha de descarga (22/10/2026).
- **Open-Meteo:** datos bajo **CC BY 4.0**. Citar "Weather data by Open-Meteo.com" (https://open-meteo.com/) y el reanálisis base: Hersbach et al. (2020), ERA5, Copernicus Climate Change Service.
- **OpenStreetMap / Nominatim:** © OpenStreetMap contributors, **ODbL 1.0**.
- **Secretaría de Energía / WRI Global Power Plant Database:** GPPD está bajo CC BY 4.0. Citar a Global Energy Observatory, Google, KTH Royal Institute of Technology in Stockholm, Enipedia y World Resources Institute (2021), *Global Power Plant Database v1.3*, y a la Secretaría de Energía de la Nación como fuente original de la capa argentina.
