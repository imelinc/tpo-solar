# Guion de la defensa (15 minutos)

Los números salen de `03_modelos`, `04_deteccion` y `05_negocio`. El dashboard se abre antes de empezar
(`streamlit run app/app.py`) y anda sin internet.

| Bloque | Tiempo | Acumulado |
|---|---|---|
| 1. Problema de negocio | 1:30 | 1:30 |
| 2. Datos | 1:30 | 3:00 |
| 3. Hipótesis con umbrales | 1:30 | 4:30 |
| 4. Modelos | 2:00 | 6:30 |
| 5. Detector: umbral vs. CUSUM | 2:00 | 8:30 |
| 6. Resultados contra la hipótesis | 1:30 | 10:00 |
| 7. Valor en USD | 1:30 | 11:30 |
| 8. Demo del dashboard | 2:30 | 14:00 |
| 9. Limitaciones y cierre | 1:00 | 15:00 |

---

## 1. Problema de negocio (0:00 – 1:30)

- Una planta solar que rinde de menos no avisa: sigue generando, solo que menos. Hoy alguien mira los números **una vez por mes**.
- Una falla que aparece un día cualquiera se descubre, en promedio, 15 días después. Esa energía no se recupera.
- **Pregunta:** ¿podemos saber, cada día, cuánto *debería* haber generado la planta según el clima, y avisar cuando genera menos?
- Mensaje: "no queremos predecir el clima, queremos saber cuánto se perdió y cuándo mandar a alguien".

## 2. Datos (1:30 – 3:00)

- **PVOD:** 10 plantas en Hebei (China), jul-2018 a jun-2019, cada 15 minutos (se usa horario): potencia, irradiancia del sensor de la planta y ficha técnica.
- **Open-Meteo:** irradiancia satelital, temperatura y lluvia, para las plantas sin sensor y para `dias_desde_lluvia`.
- **Argentina:** generación mensual de los parques solares de CAMMESA + clima de Open-Meteo en sus coordenadas.
- Hallazgos del EDA que condicionan todo: un solo año, sensores con problemas (station09 desde junio de 2019, station06 en invierno), station04 con la ficha mal.

## 3. Hipótesis con umbrales (3:00 – 4:30)

> La potencia esperada se puede estimar con el clima con un error chico; si ese error es menor que las pérdidas que nos interesan, comparar real vs. esperado detecta fallas y cuantifica la energía perdida.

Umbrales **fijados antes de mirar los meses reservados** (mayo y junio de 2019):

1. Error de energía diaria **< 8%** (sensor de planta).
2. Precisión y recall **≥ 0,8** por día para caídas de 10%, 25%, 50% y 100%.
3. Marca los casos reales: **station09** y **ULL4FV** (Argentina, 2025).

Por qué 8% y no 5%: en la validación cruzada ningún modelo bajó de 6%, y 8% queda por debajo de la pérdida más chica que queríamos detectar.

## 4. Modelos (4:30 – 6:30)

Validación cruzada dejando un mes entero afuera (jul-2018 a abr-2019), error de energía diaria:

| Modelo | Sensor de planta | Open-Meteo |
|---|---|---|
| Física (pvlib) | 13,6% | 22,3% |
| Ridge | 8,0% | 17,1% |
| Random Forest | 6,5% | 16,4% |
| XGBoost | 6,4% | 17,0% |
| **Híbrido física + RF** | **6,0%** | — |

- **Por qué el híbrido:** la física da la forma (irradiancia y temperatura) y el Random Forest solo corrige el factor real/físico (nivel y estación de cada planta). Tiene menos para aprender, se despliega sin dependencias extra y permite calcular lo esperado **con la planta limpia** (`dias_desde_lluvia = 0`), así el residuo es pérdida.
- **Número principal: 6,04%** de error en mayo-junio (evaluación ciega). El híbrido final da 5,04% en esos meses, pero se agregó después de mirarlos: no lo usamos como resultado.
- Con Open-Meteo el error es ~16%: la detección fina **necesita el sensor en la planta**.

## 5. Detector: umbral vs. CUSUM (6:30 – 8:30)

- **Residuo diario** = (real − esperado) / esperado. Días muy nublados y días con el sensor caído quedan **sin decisión**.
- **Umbral:** alerta si el residuo cae debajo de mediana − 3σ robusta de la planta. 0,17 falsas alarmas por planta y por mes.
- **CUSUM:** acumula los días malos; en teoría detecta antes las pérdidas chicas y sostenidas.
- **Por qué falla el CUSUM acá:** supone ruido independiente día a día, pero el residuo está **autocorrelado** (lag 1 ≈ 0,4: un día malo viene con otros, el nivel cambia de un mes a otro). Con la regla de libro (h = 4σ) da **6-7 falsas alarmas por planta y por mes**. Para bajarlas a 1 por mes hubo que subir h a ~40σ, y ahí ya casi no detecta.
- Comparar con las plantas vecinas tampoco ayudó: con el sensor propio casi no hay error común entre plantas (correlación 0,12).
- Elegido: **umbral sobre el residuo propio**.

## 6. Resultados contra la hipótesis (8:30 – 10:00)

| Condición | Resultado | ¿Cumple? |
|---|---|---|
| 1. Error < 8% | 6,04% (ciego) | ✅ |
| 2. P y R ≥ 0,8 | ≥ 50%: sí (P ≥ 0,93, R ≥ 0,95); 25%: R 0,73; 10%: R 0,12 | ❌ |
| 3. Casos reales | station09 desde su 2.º día; ULL4FV 11 de 12 meses de 2025 | ✅ |

**Se sostiene parcialmente.** Sirve para pérdidas **≥ 50%** (el mismo día) y para **casos crónicos** (station09, ULL4FV). Las caídas de **25% quedan en el límite** (recall 0,73). **No detecta caídas de 10% día a día**, porque el error diario del modelo (5% a 16% según la planta) es del mismo orden que la pérdida. La suciedad gradual tampoco se ve con una alerta diaria: se maneja con limpieza programada.

## 7. Valor en USD (10:00 – 11:30)

Precio: USD 42,84/MWh (RenovAr Ronda 2, 2017), **como ilustración** del valor en un parque argentino, no como el ingreso real de las plantas chinas.

- **Ahorro por falla** frente a revisar cada 30 días: una caída de 50% se atiende en 1,4 días en vez de 16 → **USD 1.099 por MW**. Un apagón total: USD 2.141 por MW.
- **station09:** el caso que más plata pierde (≈ 4.700 MWh, unos USD 200 mil en días con alerta). No se ve si se compara la planta solo con su mes anterior.
- **Limpieza:** con la tasa de ensuciamiento medida (0,049%/día) y USD 800/MW por limpieza (**supuesto**), conviene limpiar cada **~148 días**. La tabla de sensibilidad (05) muestra cuánto cambia con el costo: el dato que más falta es una cotización real.

## 8. Demo del dashboard (11:30 – 14:00)

1. **Resumen de flota** (40 s): fecha 10/5/2019. station09 en rojo, station04 en **gris** (capacidad no confiable: la ficha dice 20 MW y mide 24,8 MW). KPIs de energía perdida.
2. **Detalle de planta** (50 s): station09, abril a junio. Barras real vs. línea esperada, alertas marcadas y los días sin decisión desde el 4/6 (sensor caído). Cambiar a station06 en enero-marzo: alertas de **baja confianza** (pérdida invernal que el modelo no aprende).
3. **Argentina** (30 s): aclarar en voz alta que es **comparación mensual**, no tiempo real. Historia de ULL4FV en 2025.
4. **Negocio** (30 s): mover el costo de limpieza de 800 a 1.600 y mostrar cómo cambia T*.

Plan B si algo falla: capturas del dashboard y los gráficos de `03`, `04` (5.2 y 6.1) y `05`.

## 9. Limitaciones y cierre (14:00 – 15:00)

- Un solo año de datos: la estación se confunde con la suciedad y con las pérdidas invernales.
- Sensores de planta caídos: esos días no se decide; el respaldo satelital tiene ~16% de error.
- Costo de limpieza y frecuencia de revisión son supuestos; el precio es ilustrativo.
- **Cierre:** "Con un sensor en la planta, el sistema avisa el mismo día cuando se pierde la mitad o más, y encuentra las plantas que rinden mal siempre. Para pérdidas chicas, el próximo paso es más historia y registros de limpieza."

---

## Preguntas probables del jurado

1. **¿Por qué subieron el umbral de 5% a 8%? ¿No es acomodar el resultado?**
   Se fijó con la validación cruzada y antes de mirar mayo y junio (commit `a061d3e`). En CV ningún modelo bajaba de 6%, y 8% sigue por debajo de la pérdida más chica que queríamos detectar.

2. **¿Por qué reportan 6,04% si el modelo final da 5,04%?**
   Porque 6,04% es la única evaluación ciega. El híbrido se agregó después de mirar esos meses, así que su 5,04% está contaminado.

3. **¿Por qué no usaron CUSUM, que es el método estándar para cambios chicos?**
   Supone ruido independiente y nuestro residuo está autocorrelado (lag 1 ≈ 0,4). Con h = 4σ daba 6-7 falsas alarmas por planta y por mes; calibrado para 1 por mes, casi no detecta.

4. **¿El ahorro en USD es real?**
   Es una estimación con supuestos explícitos: precio de RenovAr como ilustración, revisión cada 30 días y reparación al día siguiente. Los parámetros están en `src/negocio.py` y en el dashboard se pueden mover.

5. **¿Esto sirve para Argentina?**
   Con datos mensuales de CAMMESA solo se puede comparar parques entre sí por mes (marcó ULL4FV en 2025). Para alertas diarias hace falta la potencia horaria y un sensor de irradiancia en cada parque.
