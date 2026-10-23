# Reporte de calidad - datasets TPO solar
Generado: 2026-10-22 20:32 (hora Buenos Aires)

## Dataset A 15 min
- Filas: 271,967 | columnas: 34 | plantas: 10
- Período (UTC): 2018-06-30 16:00:00 a 2019-06-13 15:45:00
- Timestamps duplicados eliminados: 1

| plant_id   |   filas | desde               | hasta               |   cap_mw |   p_max |   p_max/cap |   corr_power_vs_lmd_ghi |   corr_power_vs_nwp_ghi |   potencia_nocturna_media_mw |
|:-----------|--------:|:--------------------|:--------------------|---------:|--------:|------------:|------------------------:|------------------------:|-----------------------------:|
| station00  |   28895 | 2018-08-15 16:00:00 | 2019-06-13 15:45:00 |      6.6 |  5.523  |        0.84 |                   0.978 |                   0.926 |                        0     |
| station01  |   33408 | 2018-06-30 16:00:00 | 2019-06-13 15:45:00 |     20   | 19.9975 |        1    |                   0.957 |                   0.896 |                        0.057 |
| station02  |   30432 | 2018-07-22 16:00:00 | 2019-06-10 15:45:00 |     17   | 16.0482 |        0.94 |                   0.974 |                   0.917 |                        0     |
| station03  |   14688 | 2019-01-11 16:00:00 | 2019-06-13 15:45:00 |     20   | 17.4193 |        0.87 |                   0.984 |                   0.938 |                        0     |
| station04  |   33408 | 2018-06-30 16:00:00 | 2019-06-13 15:45:00 |     20   | 26.768  |        1.34 |                   0.973 |                   0.881 |                        0     |
| station05  |    9696 | 2019-03-04 16:00:00 | 2019-06-13 15:45:00 |     35   | 35.1181 |        1    |                   0.991 |                   0.937 |                        0.001 |
| station06  |   31104 | 2018-07-13 16:00:00 | 2019-06-13 15:45:00 |     15   | 11.741  |        0.78 |                   0.953 |                   0.888 |                        0     |
| station07  |   32928 | 2018-06-30 16:00:00 | 2019-06-13 15:45:00 |     20   | 17.2806 |        0.86 |                   0.954 |                   0.894 |                        0     |
| station08  |   33120 | 2018-06-30 16:00:00 | 2019-06-13 15:45:00 |     20   | 17.866  |        0.89 |                   0.985 |                   0.902 |                        0     |
| station09  |   24288 | 2018-09-25 16:00:00 | 2019-06-13 15:45:00 |     20   | 12.045  |        0.6  |                   0.902 |                   0.929 |                        0     |

## Dataset A horario
- Filas: 67,992 | columnas: 44
- Horas con 4 registros de 15 min: 100.00%

Correlaciones (Pearson, todas las horas):
| plant_id   |   corr_power_vs_om_ghi |   corr_power_vs_nasa_ghi |   corr_power_vs_lmd_ghi |   corr_lmd_ghi_vs_om_ghi |   corr_temp_lmd_vs_om |   corr_temp_lmd_vs_nasa |
|:-----------|-----------------------:|-------------------------:|------------------------:|-------------------------:|----------------------:|------------------------:|
| station00  |                  0.955 |                    0.96  |                   0.981 |                    0.956 |                 0.987 |                   0.976 |
| station01  |                  0.926 |                    0.937 |                   0.961 |                    0.965 |                 0.994 |                   0.988 |
| station02  |                  0.946 |                    0.952 |                   0.982 |                    0.929 |                 0.99  |                   0.976 |
| station03  |                  0.955 |                    0.957 |                   0.987 |                    0.952 |                 0.985 |                   0.97  |
| station04  |                  0.938 |                    0.943 |                   0.982 |                    0.921 |                 0.972 |                   0.975 |
| station05  |                  0.964 |                    0.976 |                   0.993 |                    0.961 |                 0.975 |                   0.956 |
| station06  |                  0.95  |                    0.967 |                   0.955 |                    0.943 |                 0.991 |                   0.977 |
| station07  |                  0.945 |                    0.955 |                   0.964 |                    0.951 |                 0.987 |                   0.98  |
| station08  |                  0.939 |                    0.949 |                   0.988 |                    0.938 |                 0.988 |                   0.972 |
| station09  |                  0.948 |                    0.966 |                   0.903 |                    0.899 |                 0.984 |                   0.973 |

Verificación de alineación temporal (corrimiento en horas que maximiza corr. con la irradiancia medida en planta):
om_lag_h sobre la serie cruda de Open-Meteo (se espera -1 porque la radiación es promedio de la hora previa; en el dataset ya está corregido). nasa_lag_h es el corrimiento aplicado a NASA POWER.
|           |   om_lag_h |   om_corr |   nasa_lag_h |   nasa_corr |   nasa_corr_lag0 |
|:----------|-----------:|----------:|-------------:|------------:|-----------------:|
| station00 |         -1 |     0.956 |            0 |       0.966 |            0.966 |
| station01 |         -1 |     0.965 |            0 |       0.974 |            0.974 |
| station02 |         -1 |     0.929 |            0 |       0.939 |            0.939 |
| station03 |         -1 |     0.952 |            0 |       0.96  |            0.96  |
| station04 |         -1 |     0.921 |            0 |       0.924 |            0.924 |
| station05 |         -1 |     0.961 |            0 |       0.976 |            0.976 |
| station06 |         -1 |     0.943 |            0 |       0.958 |            0.958 |
| station07 |         -1 |     0.951 |            0 |       0.969 |            0.969 |
| station08 |         -1 |     0.938 |            0 |       0.952 |            0.952 |
| station09 |         -1 |     0.899 |            0 |       0.91  |            0.91  |

% faltantes por columna (horario):

| columna | % NA |
|---|---|
| plant_id | 0.0 |
| timestamp_utc | 0.0 |
| timestamp_local_utc8 | 0.0 |
| date_local | 0.0 |
| hour_local | 0.0 |
| day_of_year | 0.0 |
| month | 0.0 |
| solar_elevation_deg | 0.0 |
| is_daylight | 0.0 |
| pvod_nwp_globalirrad | 0.0 |
| pvod_nwp_directirrad | 0.0 |
| pvod_nwp_temperature | 0.0 |
| pvod_nwp_humidity | 0.0 |
| pvod_nwp_windspeed | 0.0 |
| pvod_nwp_winddirection | 0.0 |
| pvod_nwp_pressure | 0.0 |
| pvod_lmd_totalirrad | 0.0 |
| pvod_lmd_diffuseirrad | 0.0 |
| pvod_lmd_temperature | 0.0 |
| pvod_lmd_pressure | 0.0 |
| pvod_lmd_winddirection | 0.0 |
| pvod_lmd_windspeed | 0.0 |
| pvod_power | 0.0 |
| pvod_power_norm | 0.0 |
| pvod_n_obs_15min | 0.0 |
| pvod_energy_mwh | 0.0 |
| om_shortwave_radiation | 0.0 |
| om_direct_radiation | 0.0 |
| om_diffuse_radiation | 0.0 |
| om_temperature_2m | 0.0 |
| om_cloud_cover | 0.0 |
| om_relative_humidity_2m | 0.0 |
| om_wind_speed_10m_ms | 0.0 |
| nasa_ALLSKY_SFC_SW_DWN | 0.0 |
| nasa_T2M | 0.0 |
| plant_capacity_mw | 0.0 |
| plant_pv_technology | 0.0 |
| plant_panel_size_m2 | 0.0 |
| plant_panel_number | 0.0 |
| plant_array_area_m2 | 0.0 |
| plant_array_tilt_deg | 0.0 |
| plant_array_azimuth | 0.0 |
| plant_lat | 0.0 |
| plant_lon | 0.0 |

## Dataset B Argentina mensual
- Filas: 5,036 | columnas: 32 | parques: 97
- Período: 2011-01-01 a 2026-09-01
- Filas con potencia: 92.8% (mismo mes GRV: 46.1%)
- coord_source: {'osm_localidad_inferida_del_nombre': 51, 'osm_centroide_provincia': 29, 'osm_parque': 11, 'SE_CAMMESA_via_WRI': 4, 'WikiSolar_via_GPPD_aprox': 2}
- Corr. energía/potencia vs irradiación mensual Open-Meteo (filas con FC entre 0.02 y 0.45): 0.691
- Factor de capacidad: mediana 0.248; filas con FC > 0.45 (sospechosas): 35; con energía = 0: 208
- Diferencia CAMMESA ERB vs GRV (energía, filas con ambos): mediana |dif| = 0.00%

| columna | % NA |
|---|---|
| fecha | 0.0 |
| anio | 0.0 |
| mes | 0.0 |
| estacion_hs | 0.0 |
| dias_mes | 0.0 |
| central | 0.0 |
| central_descripcion | 0.0 |
| grv_nombre_parque | 53.87 |
| grv_agente | 53.87 |
| provincia | 0.0 |
| region | 0.0 |
| tipo_contrato | 0.0 |
| lat | 0.0 |
| lon | 0.0 |
| coord_source | 0.0 |
| energia_gwh | 0.0 |
| energia_mwh | 0.0 |
| potencia_mw | 7.21 |
| potencia_source | 0.0 |
| grv_mes_en_ensayo | 53.87 |
| grv_generacion_neta_mwh | 54.47 |
| grv_factor_carga | 54.47 |
| factor_capacidad | 7.21 |
| rendimiento_especifico_kwh_kw | 7.21 |
| performance_ratio_aprox | 7.21 |
| om_ghi_kwh_m2_mes | 0.0 |
| om_ghi_kwh_m2_dia_prom | 0.0 |
| om_temp_media_c | 0.0 |
| om_temp_max_media_c | 0.0 |
| om_nubosidad_media_pct | 0.0 |
| om_horas_sol_mes | 0.0 |
| om_dias_con_dato | 0.0 |