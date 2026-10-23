# Plan de modelado y validación

Propuesta para `03_modelos` y `04_deteccion`, basada en lo que encontró `02_eda`.

## 1. Hipótesis

> **La potencia que una planta debería generar se puede estimar con el clima (irradiancia y temperatura) con un error chico. Si ese error es bastante menor que las pérdidas que nos interesan, comparar lo real con lo esperado permite detectar fallas abruptas y pérdida gradual por soiling, y cuantificar la energía perdida.**

Para que sea medible, la hipótesis se considera **sostenida** si se cumplen tres condiciones:

1. El modelo de potencia esperada, evaluado en meses que no vio, tiene un error mucho menor que una caída del 10%. El umbral concreto se fija con la línea base, antes de mirar los resultados del detector.
2. Sobre fallas sintéticas, el detector encuentra las caídas abruptas de 10% o más con *recall* alto y pocas falsas alarmas en días sanos.
3. El detector marca los casos reales que vimos en el EDA: station09 (bajo rendimiento crónico que se recupera en escalones), los apagones con sol y ULL4FV durante 2025.

Si (1) no se cumple con irradiancia externa pero sí con el sensor de planta, la conclusión cambia a "la detección requiere sensor en sitio". Ese también es un resultado válido para la gerencia.

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
