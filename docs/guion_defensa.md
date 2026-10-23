# Guion de la defensa (15 minutos)

Los números salen de `03_modelos`, `04_deteccion` y `05_negocio`. El dashboard se abre **antes de empezar**
(doble clic en `app/index.html`), ya en la vista **Flota hoy** con fecha 10/5/2019, y anda sin internet.

**Objetivo: terminar en 13:45** y dejar 1:15 de margen para los cambios de orador, alguna pregunta en el medio o un problema con la demo. Si a las 7:00 no arrancaron el bloque 5, recorten el bloque 5 a lo marcado como *(imprescindible)*.

| Bloque | Tiempo | Acumulado |
|---|---|---|
| 1. Problema de negocio | 1:30 | 1:30 |
| 2. Datos | 1:15 | 2:45 |
| 3. Hipótesis con umbrales | 1:15 | 4:00 |
| 4. Modelos | 1:45 | 5:45 |
| 5. Detector: umbral vs. CUSUM | 1:30 | 7:15 |
| 6. Resultados contra la hipótesis | 1:30 | 8:45 |
| 7. Valor en USD | 1:15 | 10:00 |
| 8. Demo del dashboard | 2:45 | 12:45 |
| 9. Limitaciones y cierre | 1:00 | 13:45 |
| *Margen* | *1:15* | *15:00* |

Reparto sugerido: cada integrante toma bloques seguidos (por ejemplo 1-3, 4-6, 7-9) para que haya solo dos cambios de orador. Quien hace la demo no habla en el bloque anterior, así ya tiene la app en pantalla.

---

## 1. Problema de negocio (0:00 – 1:30)

- Una planta solar que rinde de menos no avisa: sigue generando, solo que menos. Hoy alguien mira los números **una vez por mes**.
- Con revisión mensual, una falla que aparece un día cualquiera se descubre en promedio unos 15 días después. Esa energía no se recupera.
- **Pregunta:** ¿podemos saber, cada día, cuánto *debería* haber generado la planta según el clima, y avisar cuando genera menos?
- Mensaje: "no queremos predecir el clima, queremos saber cuánto se perdió y cuándo mandar a alguien".

## 2. Datos (1:30 – 2:45)

- **PVOD:** 10 plantas reales en Hebei (China), jul-2018 a jun-2019, potencia, irradiancia del sensor de la planta y ficha técnica (usamos datos horarios).
- **Open-Meteo:** irradiancia satelital, temperatura y lluvia (para `dias_desde_lluvia` y para plantas sin sensor).
- **Argentina:** generación mensual de los parques solares de CAMMESA + clima de Open-Meteo.
- Lo que condiciona todo: un solo año, sensores caídos (station09 desde junio, station06 en invierno) y station04 con la ficha mal.

## 3. Hipótesis con umbrales (2:45 – 4:00)

> La potencia esperada se puede estimar con el clima con un error chico; si ese error es menor que las pérdidas que nos interesan, comparar real vs. esperado detecta fallas y cuantifica la energía perdida.

Umbrales **fijados antes de mirar los meses reservados** (mayo y junio de 2019):

1. Error de energía diaria **< 8%** (sensor de planta).
2. Precisión y recall **≥ 0,8** por día para caídas de 10%, 25%, 50% y 100%.
3. Marca los casos reales: **station09** y **ULL4FV** (Argentina, 2025).

(El "por qué 8% y no 5%" va a preguntas, no se dice acá salvo que pregunten.)

## 4. Modelos (4:00 – 5:45)

Validación cruzada dejando un mes entero afuera, error de energía diaria:

| Modelo | Sensor de planta | Open-Meteo |
|---|---|---|
| Física (pvlib) | 13,6% | 22,3% |
| Ridge | 8,0% | 17,1% |
| Random Forest | 6,5% | 16,4% |
| XGBoost | 6,4% | 17,0% |
| **Híbrido física + RF** | **6,0%** | — |

- **Por qué el híbrido:** la física da la forma y el Random Forest solo corrige el factor real/físico de cada planta. Además permite calcular lo esperado **con la planta limpia** (`dias_desde_lluvia = 0`), así el residuo es pérdida.
- **Número principal: 6,04%** de error en mayo-junio (evaluación ciega).
- Con Open-Meteo el error es ~16%: la detección fina **necesita el sensor en la planta**.

## 5. Detector: umbral vs. CUSUM (5:45 – 7:15)

- *(imprescindible)* **Residuo diario** = (real − esperado) / esperado. Alerta si cae debajo de mediana − 3σ robusta de la planta: **0,17 falsas alarmas por planta y por mes**.
- *(imprescindible)* **Por qué no CUSUM:** supone ruido independiente, pero nuestro residuo está **autocorrelado** (lag 1 ≈ 0,4). Con la regla de libro daba **6-7 falsas alarmas por planta y por mes**; calibrado para 1 por mes, casi no detecta.
- Días muy nublados o con el sensor caído quedan **sin decisión**.
- (Vecinas e Isolation Forest: solo si preguntan.)

## 6. Resultados contra la hipótesis (7:15 – 8:45)

| Condición | Resultado | ¿Cumple? |
|---|---|---|
| 1. Error < 8% | 6,04% (ciego) | ✅ |
| 2. P y R ≥ 0,8 | ≥ 50%: sí (P ≥ 0,93, R ≥ 0,95); 25%: R 0,73; 10%: R 0,12 | ❌ |
| 3. Casos reales | station09 desde su 2.º día; ULL4FV 11 de 12 meses de 2025 | ✅ |

**Se sostiene parcialmente.** Sirve para pérdidas **≥ 50%** (el mismo día) y para **casos crónicos**. Las caídas de **25% quedan en el límite**. **No detecta caídas de 10% día a día**, porque el error diario del modelo (5% a 16% según la planta) es del mismo orden que la pérdida. La suciedad gradual se maneja con limpieza programada, no con una alerta diaria.

## 7. Valor en USD (8:45 – 10:00)

Precio: USD 42,84/MWh (RenovAr Ronda 2, 2017), **como ilustración** del valor en un parque argentino.

- **Ahorro por falla** frente a revisar cada 30 días: una caída de 50% se atiende en 1,4 días en vez de 16 → **USD 1.099 por MW**; un apagón total, USD 2.141 por MW.
- **station09:** ≈ 4.700 MWh, unos **USD 200 mil en los días con alerta**. (Es el mismo número que muestra el dashboard: usar siempre este.)
- **Limpieza:** con la tasa medida (0,049%/día) y USD 800/MW por limpieza (**supuesto**), conviene limpiar cada **~148 días**. Esto se muestra en vivo en la demo, no hace falta detallar la tabla acá.

## 8. Demo del dashboard (10:00 – 12:45)

1. **Flota hoy** (40 s): fecha 10/5/2019. Leer la franja de arriba: "1 planta necesita un técnico hoy", station09 pierde USD 2.300 por día. Mostrar station04 en **gris** (la ficha dice 20 MW y mide 24,8 MW) y pasar el mouse por la lista para que se ilumine en el mapa.
2. **Una planta** (60 s): clic en "Ver planta" de station09, últimos 3 meses. Azul = lo que generó, rojo = lo que dejó de generar, línea = lo que debía generar. Abajo, las filas de avisos. Cambiar a station06 con fecha en marzo: aviso de **baja confianza**.
3. **Argentina** (30 s): leer en voz alta el aviso de arriba (**comparación mensual**, no tiempo real). Bajar a la historia de Ullúm 4 (ULL4FV) en 2025.
4. **Limpieza y plata** (35 s): mover el costo de limpieza de 800 a 1.600 y mostrar cómo cambia la franja ("Conviene limpiar cada … días"). Cerrar con el caso station09.

Plan B si algo falla: capturas del dashboard y los gráficos de `03`, `04` (5.2 y 6.1) y `05`, ya abiertas en otra pestaña. No intentar arreglar la app en vivo: pasar al plan B a los 15 segundos.

## 9. Limitaciones y cierre (12:45 – 13:45)

- Un solo año de datos: la estación se confunde con la suciedad y con las pérdidas invernales.
- Sensores caídos: esos días no se decide; el respaldo satelital tiene ~16% de error.
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

6. **En el notebook 04, station09 pierde ~10.150 MWh (USD 435 mil). ¿Por qué en la presentación dicen 200 mil?**
   Son dos medidas distintas: 10.150 MWh es todo lo que rindió de menos frente a una planta típica en el período; 4.700 MWh es solo la pérdida en los días en que el sistema dio alerta. En la presentación usamos la más conservadora.

7. **¿Por qué el historial de ULL4FV tiene alertas en 2019–2020?**
   Muy probablemente corresponden al arranque del parque (puesta en marcha con capacidad todavía incompleta), que con datos mensuales se ve como bajo rendimiento. El caso que evaluamos es 2025. **Pendiente antes de la defensa: confirmar la fecha de habilitación comercial de ULL4FV en CAMMESA.**

8. **¿Por qué usaron plantas chinas y no argentinas para el detector?**
   Porque no hay datos horarios públicos de parques argentinos con sensor de irradiancia. PVOD es un dataset abierto de plantas reales con ese nivel de detalle; para Argentina hicimos lo que permiten los datos mensuales.

9. **¿Comparten métricas la regresión y la clasificación?**
   No. Nuestro modelo de potencia es una regresión y se evalúa con error de energía (tipo MAE/RMSE relativo); el detector es una clasificación (falla / no falla) y se evalúa con precisión y recall.
