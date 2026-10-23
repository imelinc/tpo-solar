# Diccionario de datos – TPO Ciencia de Datos (energía solar)

Objetivo del TPO: **predecir cuánta energía debería generar una planta solar según el clima y detectar cuándo genera de menos** (falla, suciedad, recorte).

La precipitación (`om_precipitacion_mm` en A; `om_precip_mm_mes` y `om_dias_lluvia_5mm` en B) se agregó el 22/10/2026 con `TPO_DIR=data/processed python src/build_datasets.py precipitacion`, que solo baja la lluvia de Open-Meteo y la une a los datasets ya armados, sin tocar el resto de las columnas. Una corrida completa del script ya la incluye.

Todo se arma con `build_datasets.py` (corre en Colab: `pip install pandas pyarrow openpyxl requests py7zr tabulate`). Las descargas se guardan en `raw/` y no se vuelven a pedir si ya están.

| Archivo | Qué es | Granularidad |
|---|---|---|
| `dataset_A_pvod_15min.csv` | PVOD crudo (10 plantas de China) + metadatos de planta + variables de tiempo. Sin clima externo. | 1 fila = planta × 15 min |
| `dataset_A_pvod_hourly.csv` / `.parquet` | PVOD agregado a hora + clima de Open-Meteo + NASA POWER | 1 fila = planta × hora |
| `pvod_plantas_metadata.csv` | 1 fila por planta (incluye ficha de módulos/inversores en texto) | planta |
| `dataset_B_argentina_mensual.csv` / `.parquet` | Generación mensual de cada parque solar argentino (CAMMESA) + potencia + coordenadas + clima mensual Open-Meteo | 1 fila = parque × mes |
| `parques_coordenadas.csv` | Coordenadas usadas para cada parque y de dónde salen | parque |
| `reporte_calidad.md` | Conteos, rangos, % de faltantes, correlaciones de control | — |

---

## Dataset A – PVOD (China, Hebei)

**Fuente:** PVOD v1.0 (Yao et al., 2021), Science Data Bank, doi:10.11922/sciencedb.01094. 10 plantas, registros cada 15 min, ~jul-2018 a jun-2019 (cada planta tiene su propio período, ver reporte). Trae dos fuentes: **NWP** (pronóstico numérico del tiempo que usaba la planta) y **LMD** (mediciones en la planta), más la potencia generada.

**Zona horaria:** los CSV originales están en **UTC**. Lo confirman el toolkit oficial (convierte de UTC a UTC+8 con `utc_2_pk`) y los datos: el pico medio de potencia cae a las 04:00-04:30 UTC, que es el mediodía solar local. Se agregó `timestamp_local_utc8` (hora de China, que no tiene horario de verano).

**Limpieza:** se ordenó por planta y fecha y se eliminó 1 timestamp duplicado (station00). No se imputó nada. Los huecos de días faltantes en PVOD quedan como filas ausentes, no como NaN.

### Columnas comunes (15 min y horario)

| Columna | Descripción | Unidad |
|---|---|---|
| plant_id | Planta (`station00` … `station09`) | — |
| timestamp_utc | Inicio del intervalo, UTC. En 15 min es el timestamp original. En horario es el inicio de la hora, y agrupa los registros [H:00, H:45]. | — |
| timestamp_local_utc8 | Lo mismo en hora local de China (UTC+8) | — |
| date_local, hour_local, minute (solo 15 min), day_of_year, month | Variables de calendario en hora local | — |
| solar_elevation_deg | Elevación del sol en la mitad del intervalo (fórmula NOAA aproximada, error de alrededor de 0,5° o menos) | grados |
| is_daylight | 1 si `solar_elevation_deg` > 0 | 0/1 |
| pvod_nwp_globalirrad | Irradiancia global (GHI) pronosticada (NWP) | W/m² |
| pvod_nwp_directirrad | Irradiancia directa pronosticada (NWP). En el original se llama `nwp_directirrad` y en el toolkit aparece con el typo `dirrect`. | W/m² |
| pvod_nwp_temperature | Temperatura pronosticada | °C |
| pvod_nwp_humidity | Humedad relativa pronosticada | % |
| pvod_nwp_windspeed | Viento pronosticado | m/s |
| pvod_nwp_winddirection | Dirección del viento pronosticada. En el horario es el promedio vectorial. | grados |
| pvod_nwp_pressure | Presión pronosticada | hPa |
| pvod_lmd_totalirrad | GHI **medida** en la planta (piranómetro) | W/m² |
| pvod_lmd_diffuseirrad | Irradiancia difusa medida | W/m² |
| pvod_lmd_temperature | Temperatura medida | °C |
| pvod_lmd_pressure | Presión medida | hPa |
| pvod_lmd_winddirection | Dirección del viento medida. En el horario es el promedio vectorial. | grados |
| pvod_lmd_windspeed | Viento medido | m/s |
| pvod_power | **Potencia generada (target).** En el horario es el promedio de los 4 registros. | MW |
| pvod_power_norm | `pvod_power / plant_capacity_mw`. Sirve para comparar plantas de distinto tamaño. | fracción (0 a 1, ver advertencias) |
| plant_capacity_mw | Capacidad instalada (metadata en kW, convertida a MW) | MW |
| plant_pv_technology | Poly-Si / Mono-Si | — |
| plant_panel_size_m2, plant_panel_number, plant_array_area_m2 | Tamaño de panel, cantidad de paneles y área total (tamaño × cantidad) | m², unidades, m² |
| plant_array_tilt_deg, plant_array_azimuth | Inclinación y orientación de los paneles (todas miran al sur) | grados, texto |
| plant_lat, plant_lon | Coordenadas de la planta (metadata PVOD) | grados decimales |

### Columnas solo del horario

| Columna | Descripción | Unidad / fuente |
|---|---|---|
| pvod_n_obs_15min | Cuántos registros de 15 min entraron en la hora (siempre 4 en esta versión) | conteo |
| pvod_energy_mwh | Energía de la hora = potencia media × n_obs × 0,25 h | MWh |
| om_shortwave_radiation | GHI modelada (reanálisis), promedio de la hora | W/m², Open-Meteo |
| om_direct_radiation | Radiación directa sobre plano horizontal | W/m², Open-Meteo |
| om_diffuse_radiation | Radiación difusa | W/m², Open-Meteo |
| om_temperature_2m | Temperatura a 2 m | °C, Open-Meteo |
| om_cloud_cover | Nubosidad total | %, Open-Meteo |
| om_relative_humidity_2m | Humedad relativa a 2 m | %, Open-Meteo |
| om_wind_speed_10m_ms | Viento a 10 m (convertido de km/h) | m/s, Open-Meteo |
| om_precipitacion_mm | Precipitación de la hora (suma). Como la radiación, el valor de Open-Meteo con etiqueta T es la suma de la hora anterior, así que se corrió 1 hora hacia atrás. Se usa para `dias_desde_lluvia` (lluvia ≥ 5 mm en el día = paneles lavados). | mm, Open-Meteo |
| nasa_ALLSKY_SFC_SW_DWN | GHI en superficie (cielo real) | W/m², NASA POWER |
| nasa_T2M | Temperatura a 2 m | °C, NASA POWER |

### Cómo se unió el clima externo (dataset horario)

- **Por ubicación:** a cada planta se le pidió la serie de su lat/lon de la metadata PVOD.
  - Open-Meteo devuelve la celda de grilla más cercana (ERA5/ERA5-Land, de unos 9 a 25 km).
  - NASA POWER usa una grilla de alrededor de 0,5° × 0,625° (unos 50 km), así que es mucho más gruesa.
- **Por tiempo:** se pidió todo en UTC. Convención final: la etiqueta H representa el intervalo [H, H+1).
  - **PVOD:** se promedian los 4 registros de 15 min de esa hora.
  - **Open-Meteo radiación y precipitación:** el valor con etiqueta T es el promedio (radiación) o la suma (precipitación) de la hora anterior (T-1 a T), así que se corrió 1 hora hacia atrás.
  - **Open-Meteo temp, humedad, nubes y viento:** son valores instantáneos, así que se tomó el promedio entre H y H+1.
  - **NASA POWER:** se verificó empíricamente que el corrimiento de 0 h maximiza la correlación con la GHI medida en planta en las 10 plantas, así que se usa sin correr.
- **Verificación:** el reporte de calidad muestra, para cada planta, el corrimiento óptimo (Open-Meteo crudo = -1 h, como se esperaba; NASA = 0 h). Tras la alineación, la correlación entre la potencia y la GHI externa queda entre 0,93 y 0,98.
- El dataset de 15 min **no** tiene clima externo, porque habría que inventar valores intermedios (interpolar o repetir). Para modelar con clima externo usen el horario.

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

**Dataset A**
- **station04** llega a unos 26,8 MW (en 15 min; 25,7 MW en el promedio horario) con 20 MW de capacidad declarada, así que `pvod_power_norm` puede superar 1 (alrededor de 1,34). Puede ser que la metadata tenga la capacidad AC o un error. **station09** no pasa de 12 MW con 20 MW declarados (0,6). Revisen antes de comparar plantas con la potencia normalizada.
- **station01** tiene potencia nocturna media de alrededor de 0,06 MW, es decir valores distintos de 0 de noche (ruido o consumo del medidor). Filtren con `is_daylight` o recorten a 0.
- Las plantas no cubren el mismo período: station05 tiene unos 3 meses y station03 unos 5. Para comparar plantas usen la intersección de fechas.
- Hay días faltantes sueltos (saltos de 1 a 5 días en algunas plantas).
- Las variables NWP de PVOD son un **pronóstico**: sirven para la parte de "predecir mañana". Las LMD y las de Open-Meteo/NASA son **observadas o reanálisis**: sirven para estimar la generación esperada con el clima real y detectar bajo rendimiento.
- Open-Meteo y NASA son datos de grilla, no del sitio exacto. Por eso tienen algo más de error que el piranómetro de la planta (la correlación con la GHI medida está entre 0,90 y 0,97).

**Dataset B**
- La potencia por mes solo existe de 2022-01 a 2025-09 (archivo GRV). Para otros meses se usa la del mes más cercano. Si el parque se amplió (por ejemplo CUM2FV pasa de 4 a 35,2 MW, PINFFV de 16,2 a 130 y VANGFV de 14,7 a 40), el factor de capacidad de los meses anteriores a 2022 o posteriores a 2025-09 puede estar mal. Ver `potencia_source`.
- 22 centrales (en su mayoría chicas, de autogeneración o muy nuevas) no aparecen en GRV, por eso `potencia_mw = NaN` (alrededor del 7% de las filas).
- Hay meses con energía = 0, que corresponden a parques en ensayo, antes de la habilitación comercial o en una falla, y 35 filas con factor de capacidad mayor a 0,45 (sobre todo CHI1FV, HON1FV y TAMBFV; puede deberse a que la potencia habilitada es AC y menor que la DC, a seguidores, o a que se usó la potencia de un mes cercano). No son errores de armado, pero conviene tratarlos como outliers o como casos a explicar.
- El primer y el último mes de cada parque suelen estar incompletos (entrada en servicio a mitad de mes).
- CAMMESA publica GWh con muchos decimales y se mantuvieron tal cual.
- El clima de Open-Meteo de 2026-09 es reciente y puede tener correcciones posteriores.

---

## Licencias y cómo citar

- **PVOD:** uso **solo con fines de investigación o académicos**, y piden citar el paper. El código del toolkit es MIT.
  > Yao, T., Wang, J., Wu, H., Zhang, P., Li, S., Wang, Y., Chi, X., Shi, M. (2021). *A photovoltaic power output dataset: Multi-source photovoltaic power output dataset with Python toolkit*. Solar Energy, 230, 122–130. https://doi.org/10.1016/j.solener.2021.09.050 — Dataset: doi:10.11922/sciencedb.01094
- **CAMMESA:** datos públicos del Mercado Eléctrico Mayorista. Citar "Fuente: CAMMESA – Base de Datos Energías Renovables (2026-09) y Generación Renovable Variable (2025-09)", con el link y la fecha de descarga (22/10/2026).
- **Open-Meteo:** datos bajo **CC BY 4.0**. Citar "Weather data by Open-Meteo.com" (https://open-meteo.com/) y el reanálisis base: Hersbach et al. (2020), ERA5, Copernicus Climate Change Service.
- **NASA POWER:** "These data were obtained from the NASA Langley Research Center (LaRC) POWER Project funded through the NASA Earth Science/Applied Science Program" (https://power.larc.nasa.gov/). Uso libre.
- **OpenStreetMap / Nominatim:** © OpenStreetMap contributors, **ODbL 1.0**.
- **Secretaría de Energía / WRI Global Power Plant Database:** GPPD está bajo CC BY 4.0. Citar a Global Energy Observatory, Google, KTH Royal Institute of Technology in Stockholm, Enipedia y World Resources Institute (2021), *Global Power Plant Database v1.3*, y a la Secretaría de Energía de la Nación como fuente original de la capa argentina.
