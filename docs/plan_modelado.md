# Plan de modelado y validación

Propuesta para `03_modelos` y `04_deteccion`, basada en lo que encontró `02_eda`.

## 1. Hipótesis

> **La potencia que una planta debería generar se puede estimar con el clima (irradiancia y temperatura) con un error chico. Si ese error es bastante menor que las pérdidas que nos interesan, comparar lo real con lo esperado permite detectar fallas abruptas y pérdida gradual por soiling, y cuantificar la energía perdida.**

### Umbral fijado (22/10/2026, antes de mirar mayo y junio de 2019)

La hipótesis se considera **sostenida** si se cumplen las tres condiciones. Se evalúan **una sola vez**, en los meses reservados (mayo y junio de 2019), con el modelo y el detector elegidos en validación cruzada:

1. **Error de energía diaria < 8%** con el escenario de sensor de planta (LMD). La métrica es `Σ|E_real,d − E_esperada,d| / Σ E_real,d` sobre todos los días-planta (`src/modelos.metricas`).
2. **Precisión y recall ≥ 0,8 por día** para las caídas abruptas sintéticas de 10%, 25%, 50% y 100%. Se evalúa **cada nivel por separado**, juntando las duraciones de 1, 3 y 7 días, todas las plantas de prueba y las semillas. El recall se calcula sobre los días con decisión. Los días muy nublados (energía esperada < 25% del p90 de la planta) quedan sin decisión, y se informa qué porcentaje representan.
3. El detector marca los casos reales: el período de bajo rendimiento de station09 y ULL4FV en 2025 (este último en la comparación mensual de Argentina).

**Por qué 8% y no 5%.** El objetivo original era 5%, pero en la validación cruzada por mes (jul-2018 a abr-2019, 8 plantas de entrenamiento) ningún modelo baja de 6%:

| Escenario | Física | Ridge | Random Forest | XGBoost |
|---|---|---|---|---|
| Sensor de planta (LMD) | 13,6% | 8,0% | 6,5% | 6,4% |
| Open-Meteo | 22,3% | 17,1% | 16,4% | 17,0% |

El piso viene del dato: una sola medición de irradiancia por planta, promedios horarios y sensores con problemas (A.7 del EDA). Exigir 5% sería exigir algo que los datos no permiten. Se fija **8%** por dos razones: (a) queda por debajo de la menor pérdida que queremos detectar (10%), así que una caída sostenida de 10% se separa del error típico de un día; (b) deja margen sobre el 6,4% de la validación cruzada para meses que el modelo no vio. Mayo y junio son además de los más nublados del período (A.5).

**Open-Meteo no entra en el criterio:** con ~16-17% de error diario no alcanza para detectar caídas de 10% día a día. Se informa como escenario de respaldo, y la conclusión para la gerencia es que **la detección fina requiere el sensor en la planta**.

**Regla de elección del modelo (fijada antes del holdout):** gana el de menor error de energía diaria en la validación cruzada. Si la diferencia con el siguiente es menor a 0,5 puntos, se elige el más simple de desplegar en el dashboard offline (sin dependencias extra y con el archivo más chico).

## 2. Features (`src/features.py`)

| Feature | Función | Por qué (hallazgo del EDA) |
|---|---|---|
| `hora`, `dia_del_anio`, `mes` + `hora_sin/cos`, `doy_sin/cos` | `agregar_features_tiempo` | El tiempo siempre tiene que estar. Las versiones cíclicas son para los modelos lineales (A.5: perfil diario y estacional marcado). |
| `sol_zenit_deg`, `sol_azimut_deg` | `agregar_features_solares` | Explican el perfil diario y las sombras con el sol bajo (pérdida invernal de station00 y station06, A.6). |
| `om_poa` (irradiancia en el plano del panel, pvlib) | idem | Pasa el GHI horizontal de Open-Meteo al plano inclinado. Mejora la correlación en 6 de 10 plantas (A.3). |
| `om_kt_cielo_claro` (GHI / GHI de cielo claro) | idem | Separa día nublado de día claro. Sirve para filtrar las horas donde el residuo es confiable. |
| `om_temp_celda` (Faiman) | idem | Pérdida por temperatura. El efecto fue débil en el EDA (A.4), pero tiene base física. |
| `om_frac_difusa` | idem | Proporción de difusa: los días con mucha difusa rinden distinto. |
| `pvod_lmd_totalirrad` sin transformar | — | Variante con el sensor de planta. **No transponer**: en invierno lee hasta ~1,9 veces el GHI horizontal, así que el sensor ya está inclinado (A.7). |
| `dato_congelado` | `limpiar_pvod` / `marcar_valores_congelados` | Sacar del entrenamiento los tramos con el registrador colgado (station01, 8-9/12/2018). |
| filtro de filas Argentina | `filtro_rendimiento_argentina` | Coordenada confiable, con potencia, sin energía 0, FC ≤ 0,45 y parques ampliados solo dentro de la ventana GRV. |

**Target A:** `pvod_power_norm` horario, solo con sol (`is_daylight == 1`), **un modelo por planta** o un modelo global con `plant_id` como categoría. La capacidad declarada de station04 y station09 no es confiable, así que la normalización sirve para la escala pero el modelo aprende el nivel de cada planta.

**Target B:** `factor_capacidad` mensual. Features: `om_ghi_kwh_m2_mes`, `om_temp_max_media_c`, `om_nubosidad_media_pct`, `mes` y el nivel histórico del parque (mediana del PR aproximado en meses de entrenamiento, como codificación por parque).

**Limpieza del set de entrenamiento:** el modelo tiene que aprender cómo genera la planta **sana**. Por eso se sacan los datos congelados, las horas con sol y potencia < 5% de la capacidad (A.8), los meses de arranque y el período de bajo rendimiento de station09 (hasta 2019-05-18) cuando se entrene esa planta. Esos mismos casos después se usan para validar el detector.

## 3. Modelos a comparar (`03_modelos`)

| # | Modelo | Qué aporta |
|---|---|---|
| 0 | **Línea base física:** `P = k · POA · (1 + γ·(T_celda − 25))`, con k ajustado por planta y γ fijo de ficha | Piso que cualquier modelo de ML tiene que superar. Interpretable para la gerencia técnica. Usa pvlib, que ya está en `requirements.txt`. |
| 1 | **Regresión lineal / Ridge** sobre las features de la sección 2 | Rápida, interpretable, y muestra cuánto suman la temperatura y la geometría solar. |
| 2 | **Random Forest** | Captura no linealidades (recorte del inversor, sombras con el sol bajo) sin mucha calibración. |
| 3 | **XGBoost** | Suele ser el mejor en datos tabulares. En Mac local requiere `brew install libomp`; en Colab funciona directo. |

Cada modelo se corre en dos escenarios de irradiancia: **(a) sensor de planta** y **(b) Open-Meteo**. El escenario (b) es el que se puede llevar a Argentina y a plantas sin sensor. La diferencia entre (a) y (b) es un resultado de negocio en sí mismo.

Para Argentina (mensual) alcanza con 0 (PR histórico del parque × irradiación), 1 y 2/3.

### Métricas
- **MAE y RMSE** en fracción de capacidad (nMAE, nRMSE), para comparar plantas de distinto tamaño. RMSE castiga más los errores grandes, que son los que generan falsas alarmas.
- **R²**, para comunicar.
- **Sesgo de energía** (Σ real − Σ esperada) / Σ real: es lo que se traduce en MWh y plata.

### Validación temporal
- Hay un solo año, así que un corte "entreno en el pasado, pruebo en el futuro" dejaría estaciones sin ver. La propuesta es **validación cruzada por mes** (`GroupKFold` con grupo = mes calendario): cada fold deja un mes entero afuera, y así nunca hay horas del mismo día en entrenamiento y prueba.
- Además, un **holdout final** con los últimos meses (2019-05 y 2019-06), que no se tocan hasta elegir el modelo.
- Argentina: entrenar hasta 2025-09 y probar en 2025-10 a 2026-09.
- Ningún feature puede usar información del futuro. Por ejemplo, la mediana por parque se calcula solo con los meses de entrenamiento.

## 4. Fallas sintéticas para validar la detección (`04_deteccion`)

Las funciones ya están en `src/fallas.py`. Ambas devuelven la potencia con la falla y la etiqueta verdadera (`perdida_fraccion`).

| Tipo | Función | Parámetros a barrer | Qué simula |
|---|---|---|---|
| **Caída abrupta** | `inyectar_caida_abrupta(p, inicio, dias, fraccion)` | fracción ∈ {0,05; 0,10; 0,25; 0,50; 1,0}, duración ∈ {1, 3, 7} días | Inversor o strings fuera de servicio, apagón total. |
| **Soiling** | `inyectar_soiling(p, inicio, dias, tasa_diaria)` | tasa ∈ {0,1; 0,2; 0,5}%/día, durante 30 a 60 días, y vuelta a 0 (limpieza o lluvia) | Acumulación gradual de polvo. Las tasas son parámetros de simulación: conviene justificarlas con bibliografía en el informe. |

**Procedimiento:**
1. Se toma el período de prueba (meses fuera del entrenamiento) de plantas con datos limpios (station01, 05, 07 y 08 son las más estables en A.6).
2. Para cada combinación de parámetros y para varias semillas, se elige un inicio al azar, se inyecta la falla sobre la potencia real, se calcula el residuo contra el modelo y se corre el detector.
3. Las etiquetas se arman **por día**: un día es "con falla" si la pérdida media inyectada en sus horas con sol es ≥ 3%. Por debajo de ese valor no es razonable exigir detección.

**Métricas del detector:**
- Precisión, recall y F1 por día.
- **Demora de detección**: días desde el inicio de la falla hasta la primera alarma. Es clave para el soiling.
- Para el soiling, **pérdida acumulada al detectar**: qué % se estaba perdiendo cuando sonó la alarma.
- **Falsas alarmas por planta y mes** en el período sin inyección, que es lo que le importa a operaciones.
- **Energía perdida estimada vs. inyectada** (MWh), para validar el número que va al dashboard.

**Detector propuesto (a comparar):** (a) umbral sobre el residuo diario normalizado (por ejemplo, z robusto < −3 con mediana y MAD por planta); (b) CUSUM o media móvil del residuo, que suele detectar antes las pérdidas graduales; (c) Isolation Forest sobre [residuo, kt, mes] como alternativa de ML.

**Argentina:** lo mismo a nivel mensual, restando un x% en meses al azar de parques del set filtrado y evaluando con los mismos indicadores.

## 5. Lo que no se cubre todavía
- Distinguir *soiling* de degradación, o de una falla parcial que se mantiene. Con un año de datos y sin registros de limpieza no es posible: se reporta como "pérdida gradual".
- La causa de las pérdidas invernales de station00 y station06 (¿sombra o nieve?). Habría que validarla con el área técnica.

## 6. Resultados de la etapa 2 (22/10/2026)

Todos los números salen de `03_modelos`, `04_deteccion` y `05_negocio`.

### Hipótesis

| Condición | Resultado | ¿Cumple? |
|---|---|---|
| 1. Error de energía diaria < 8% (sensor de planta, evaluación ciega en may-jun 2019) | 6,04% (Random Forest, primera mirada) | ✅ |
| 2. Precisión y recall ≥ 0,8 para caídas de 10%, 25%, 50% y 100% | 100%: 0,93 / 1,00; 50%: 0,94 / 0,95; 25%: 0,92 / 0,73; 10%: 0,68 / 0,12 | ❌ |
| 3. Marca station09 y ULL4FV | station09 desde el 2.º día con datos; ULL4FV con alerta en 11 de 12 meses de 2025 | ✅ |

**Se sostiene parcialmente:** detecta fallas grandes (≥ 50%) el mismo día y casos crónicos, pero no caídas de 10% ni suciedad gradual. El ruido diario del modelo (σ robusta de 5% a 16% según la planta) es del mismo orden que esas pérdidas.

### Lo que se sumó del notebook de referencia (método, aplicado a datos reales)

- **Híbrido físico + ML** (el Random Forest aprende el factor real / PVWatts): es el mejor en la validación cruzada (5,99%) y es el modelo final, en su variante con lluvia (6,05% en CV).
- **Precipitación y `dias_desde_lluvia`** (lluvia ≥ 5 mm limpia los paneles): se agregaron a los datasets A y B. Lo esperado se calcula con la planta limpia. No mejora la CV, porque con un año la época seca coincide con el invierno.
- **Comparación con vecinas** (índice / mediana de las plantas a < 100 km / normal de la planta): con el sensor de cada planta casi no hay error común (correlación 0,12), así que no mejora la detección. En Argentina se aplica por región y mes.
- **Alertas combinadas** (falla grave < 0,5, CUSUM e Isolation Forest): solo sirven para caídas grandes. Con la regla h = 4σ, el CUSUM da 6-7 falsas alarmas por planta y por mes, porque el residuo está autocorrelado. Calibrado (h ≈ 40σ) casi no detecta.
- **Valor de negocio** (`05_negocio`): USD 1.099 por MW ahorrados por cada caída de 50% y T* = 148 días con una tasa de ensuciamiento medida de 0,049%/día. El costo de limpieza es un supuesto.

### Limitaciones

- **Un solo año de datos.** La pérdida invernal de station06 (y en parte de station00) no se puede aprender al dejar el mes afuera: genera 59 días de alerta falsa de enero a marzo.
- **Los resultados en may-jun del híbrido y de las variantes con lluvia no son ciegos**: se agregaron después de la primera mirada.
- **station04:** la ficha técnica está mal. En el semáforo aparece siempre verde, porque se mide contra la planta típica.
- **Sensor de planta caído** (station09 desde el 4/6/2019; station06 en invierno): esos días quedan sin decisión, y el modelo con Open-Meteo como respaldo tiene un error de ~10-16%.
- **Argentina:** es una comparación mensual entre parques, no detección en tiempo real. Las coordenadas aproximadas se excluyen.
- **Costo de limpieza y frecuencia de revisión son supuestos.** El precio es el de RenovAr Ronda 2 (solar), no el spot.
