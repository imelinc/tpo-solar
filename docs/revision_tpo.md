# Revisión del TPO solar

Fecha: 29/10/2026. Alcance: cumplimiento de la consigna, metodología, coherencia de resultados, reproducibilidad y lógica de la aplicación.

## Dictamen

El proyecto tiene una base sólida y gran parte del desarrollo necesario. Los resultados principales son reproducibles y la conclusión parcial de la hipótesis es honesta. **Todavía no está listo para considerarlo cerrado:** hay errores en la evaluación por simulación, diferencias entre el detector evaluado y el semáforo, problemas en el recorrido de descarga y entregables de exposición que no aparecen en el repositorio.

Esta revisión no cambia modelos, notebooks, datos ni la aplicación. Las ejecuciones de comprobación y el reentrenamiento se hicieron con resultados temporales, fuera del proyecto.

## 1. Cumplimiento de la consigna

Fuente: PDF «Ciencia de Datos - Trabajo Práctico Obligatorio», entregables en página 6, exposición en páginas 3–5 y condiciones en páginas 7–9.

| Requisito | Estado | Evidencia y pendiente |
|---|---|---|
| Dominio, problema y valor para el negocio | Cubierto, con ajustes | README, plan de modelado y guion. La decisión de priorizar plantas es clara. Presentar la revisión mensual como supuesto, también al introducir el problema. |
| Arquitectura: diagrama de la tubería | Pendiente en los archivos revisados | La arquitectura está explicada en texto en CLAUDE.md, pero no encontré el diagrama exigido. Una estructura de carpetas no lo reemplaza. |
| Análisis exploratorio | Cubierto | Notebook 02: cobertura, anomalías, sensores, estaciones, comparación de fuentes y contexto argentino. Se ejecutó completo sin errores. |
| Técnica de minería y justificación | Cubierto, con ajustes | Notebook 03 compara física, Ridge, RF, XGBoost e híbrido. La elección implementada coincide con la documentada. Falta separar con más claridad la evaluación original de los experimentos posteriores. |
| Conclusiones, visualización y storytelling | Parcial | Hay guion, gráficos programados y conclusión parcial coherente. Faltan cerrar los problemas de validación y de interpretación económica. No encontré un archivo de diapositivas. |
| Aplicación funcional | Parcialmente verificado | Datos, dependencias locales, fórmulas y generación de tablas comprobados. Hay fallos de lógica del semáforo. No se pudo verificar visualmente el navegador. |
| Excelencia en algún aspecto | Evidencia favorable | Múltiples fuentes, comparación y combinación de modelos, dashboard navegable y relación con decisiones. No es necesario implementar todas las opciones enumeradas en la consigna. |
| Grupo de 5–6 integrantes y todos exponen | Pendiente de documentar/verificar | Los responsables del README están vacíos. El ejemplo de reparto del guion contempla tres oradores; ajustarlo al grupo real. |
| Defensa de 15 minutos | Planificado, sin ensayo verificado | El guion suma 13:45 más 1:15 de margen. Falta medir la exposición real y preparar la copia de respaldo. |
| Presentación y ejecución disponibles sin red | Parcial | El dashboard incluye datos y Plotly locales. Los notebooks tienen salidas vacías y los modelos no se versionan; se necesita dejar preparados el entorno, los modelos y los gráficos en la computadora de exposición. |

La fecha de entrega no está definida en el PDF. La ausencia de diapositivas o integrantes en el repositorio no prueba que no existan en otro lugar: requieren verificación con el equipo.

## 2. Resultados comprobados

Se ejecutaron las celdas de análisis de los notebooks 02, 03 y 05 en procesos Python, omitiendo las celdas de configuración de Colab. Para 03, el destino del modelo se cambió solo en el proceso de auditoría a una carpeta temporal. Esto verifica los cálculos locales, no la instalación desde cero ni el comportamiento de Colab.

| Comprobación | Resultado |
|---|---|
| Pruebas existentes, `python tests/test_features.py` | 14 pruebas correctas. |
| Dataset A horario | 67.992 filas; sin duplicados por planta y timestamp. |
| Dataset B mensual | 5.036 filas; sin duplicados por central y fecha. |
| RF sin lluvia, meses reservados | Error de energía diaria 6,0427628548%, coincide con 6,04%. |
| Híbrido sin lluvia, validación por mes | 5,992%, coincide con 5,99%. |
| Híbrido con lluvia, validación por mes | 6,0456547773%, coincide con 6,05%. |
| Híbrido con lluvia, meses reservados | 5,0378713320%, coincide con 5,04%. Es evaluación posterior a la primera mirada. |
| Modelo elegido al volver a ejecutar 03 | Híbrido con lluvia, como está documentado. |
| Falsas alarmas del umbral en la evaluación preparada | 0,1724137931 por planta por 30 días, coincide con 0,17. |
| station09, pérdida estimada en días con alerta elegida | 4.723,992 MWh; USD 202.375,82 al precio ilustrativo. |
| ULL4FV en 2025 | 11 meses con alerta de 12, coincide con el texto. |
| Tablas diarias precalculadas frente al modelo y detector locales | Energía real idéntica; diferencia máxima de energía esperada menor a 6 × 10⁻¹⁴ MWh; cero diferencias en alerta elegida. |
| Datos JS frente a las funciones actuales de construcción | Coinciden las estructuras completas de flota y Argentina. |
| Sintaxis de `app/tablero.js` | `node --check` correcto. |
| Scripts del HTML | Los cuatro archivos referenciados están presentes y son locales. |

Para el detector se recalcularon las simulaciones abruptas de mayo–junio para 10%, 25%, 50% y 100%, duraciones de 1, 3 y 7 días y cinco semillas, usando el modelo ajustado en desarrollo y la calibración guardada. Se reprodujeron precisión y recall. No se reejecutó completo el notebook 04, su búsqueda de detectores ni el entrenamiento mensual argentino.

## 3. Hallazgos prioritarios

### A. Error en la identidad de las simulaciones

**Prioridad alta.** Notebook 04, celda de código con `simular` y `evaluar` (índice 17, contando desde cero).

`simular` identifica cada corrida como `planta-semilla`, aunque cambia la duración y el inicio. Después, al concatenar duraciones, `evaluar` agrupa por ese identificador. Así mezcla tres episodios distintos en un grupo y usa el inicio de una de esas corridas para medir alarmas de otras.

Hay **120 simulaciones independientes por nivel**, pero la evaluación por episodio trabaja con 40 grupos mezclados.

| Caída | Detectadas publicadas | Detectadas con identidad única por corrida |
|---|---:|---:|
| 10% | 20,00% | 15,83% |
| 25% | 77,50% | 77,50% |
| 50% | 97,50% | 96,67% |
| 100% | 95,00% | 98,33% |

En 10%, la demora mediana pasa de 1,5 a 1 día. **Precisión y recall por día no cambian** al corregir solamente la identidad, porque se calculan sobre filas, sin ese agrupamiento.

**Corrección:** incluir tipo, nivel, duración, planta, semilla e inicio en la identidad; calcular detección y demora por corrida; regenerar `evaluacion_detector.csv` y los números económicos derivados. Mantener también la proporción sin decisión. No reemplazar silenciosamente los resultados históricos: registrar la corrección.

### B. El semáforo no representa al detector que se evaluó

**Prioridad alta.** `src/deteccion.py`, funciones `diario_flota` y `semaforo`; notebook 04; `app/build_dashboard.py`.

El detector elegido es `alerta_umbral`. La serie y las pérdidas en días de alerta usan `alerta_elegida`. Sin embargo, el semáforo usa `alerta`, `tipo_alerta` y umbrales de 0,80/0,95 sobre el índice relativo a vecinas. Es una política de decisión adicional que no tiene las métricas publicadas del detector de umbral.

En la auditoría de las fechas disponibles, desde la séptima fecha de flota, aparecieron **3 casos planta-fecha con alerta elegida y semáforo verde**. Ejemplo: station08, 28/12/2018.

**Corrección:** definir explícitamente la relación entre detección y prioridad operativa. Si se conserva una política adicional, documentarla y evaluarla por separado. No atribuir al semáforo la precisión y el recall del umbral.

### C. El verde puede significar falta de información

**Prioridad alta.** `src/deteccion.py`, líneas 299–318, y textos de `app/tablero.js`.

El código no obliga a que haya decisión válida en la fecha para asignar verde. Usa observaciones anteriores y puede terminar en verde aun con `residuo_rel = NaN`. Si no hay índices válidos, las comparaciones con NaN tampoco disparan amarillo o rojo.

En el mismo barrido se encontraron **142 casos planta-fecha sin decisión diaria y con verde**, de los cuales **24 tenían fallo de sensor**.

Ejemplo real: station08, 10/07/2018. El residuo no permite decidir y `falla_sensor=True`, pero el semáforo dice verde y su acción es «Nada (sensor de irradiancia caído: revisar el piranómetro)». La interfaz presenta las plantas verdes como «En orden».

Además, una planta sin registros recientes puede desaparecer de la lista porque solo se recorren las plantas presentes en los últimos siete días. `fecha_dato` existe en los datos, pero la lista no la muestra.

**Corrección:** representar «sin decisión», «sensor caído» y «dato atrasado» de forma explícita; mostrar fecha del último dato; conservar las plantas esperadas aunque falten registros. Un estado desconocido no debe comunicar normalidad comprobada. Distinguir cualquier recomendación basada en historia de una evaluación del día.

### D. El recorrido documentado de descarga está incompleto

**Prioridad alta.** `notebooks/01_descarga.ipynb`, `src/build_datasets.py`, `src/config.py` y `requirements.txt`.

El notebook 01 tiene solo dos celdas: una descripción y la configuración/importación de rutas. **No llama al constructor de datasets.** Por eso ejecutar 01 no reproduce las descargas que promete el README.

El script constructor sí existe, pero su destino predeterminado es `src/`, con crudos en `src/raw/`, mientras los notebooks esperan procesados en `data/processed/` y la configuración define `data/raw/`. `TPO_DIR` permite cambiar la base, pero ese recorrido no está conectado ni explicado en 01.

También faltan en requirements las dependencias que usa el constructor:

- `openpyxl`, para leer los Excel.
- `py7zr`, para extraer el archivo de CAMMESA.
- `tabulate`, para generar el reporte con `to_markdown`.

Las tres están ausentes del entorno local revisado. El funcionamiento actual se apoya en datasets ya preparados. Eso permite continuar el análisis, pero no demuestra reproducción desde las fuentes.

**Corrección:** implementar 01, unificar rutas y cachés, declarar dependencias y probar el recorrido desde un entorno limpio con una carpeta de salida temporal. Mantener una copia descargada para la defensa. No hace falta descargar todo durante la exposición.

### E. El ahorro por falla requiere una simulación económica consistente

**Prioridad alta para las cifras de negocio.** Notebook 05, sección 2.

Los USD 1.099/MW y USD 2.141/MW se reproducen con el CSV actual. Sin embargo:

1. Consumen porcentajes y demoras afectados por el error A.
2. Las fallas usadas para evaluar duran 1, 3 o 7 días, pero la cuenta de ahorro supone que la pérdida continúa hasta la intervención, comparando con 16 días sin atender. Sin una hipótesis explícita de falla persistente, se puede contabilizar energía posterior a su finalización.
3. Se pondera una demora **mediana** para estimar un costo esperado; esa operación no equivale al promedio de costos de los episodios.
4. El detector puede quedar peor que la revisión mensual en la fórmula de suciedad. Si ambos mecanismos conviven, debe actuar el primero que detecta, no esperar al más lento.

**Corrección:** simular cada episodio con su duración y disponibilidad de datos; sortear la posición de la próxima revisión; calcular el momento de intervención de cada alternativa y sumar solo la energía evitable mientras la falla sigue activa. Si se quiere evaluar fallas persistentes, generar y declarar ese escenario. Mostrar beneficio bruto estimado y qué costos no se incluyen, como visitas y falsas alarmas.

Hasta entonces, presentar esas cifras como escenarios ilustrativos pendientes de corregir, no como ahorro validado.

## 4. Ajustes metodológicos y de interpretación

### F. La evaluación original y el sistema final son experimentos distintos

El repositorio conserva una distinción correcta: **6,04% corresponde al RF sin lluvia de la primera evaluación**, y 5,04% al híbrido posterior. El historial consultado contiene el umbral de 8% en `a061d3e` y el código original en `ab3630b`.

Pero el notebook 04 actual usa el híbrido elegido después de mirar los meses reservados. Aunque lo vuelva a entrenar solo con desarrollo para predecir esos meses, eso **no restablece la independencia de la selección del modelo**. Las métricas actuales del detector son reproducibles, pero no constituyen una nueva evaluación completamente ciega del sistema final.

La app también usa un modelo reentrenado sobre todos los datos limpios. Su recorrido histórico es retrospectivo; no representa lo que habría sabido el sistema en cada fecha del pasado.

**Acción:** etiquetar las métricas por modelo, fecha de elección y tipo de evaluación. Para una nueva prueba independiente hace falta otro período o conjunto que no haya guiado el desarrollo. Si no está disponible, declarar ese límite sin prometer una prueba ciega que los datos actuales ya no permiten.

La validación dejando un mes afuera es útil para examinar meses no vistos, pero puede entrenar con meses posteriores al mes evaluado; no equivale a una simulación cronológica de producción. Mantener clara esa diferencia.

### G. Los casos reales son hallazgos retrospectivos, no fallas confirmadas

station09 y ULL4FV muestran desvíos fuertes y son buenos casos para contar. Sin embargo, no se encontraron etiquetas operativas independientes, órdenes de reparación ni comprobación de la causa física. El EDA ya los había identificado.

En ULL4FV, **9 de los 12 meses de 2025 pertenecen al período de entrenamiento/calibración**, que llega hasta septiembre. «11 de 12 meses con alerta» es correcto como descripción retrospectiva, pero no equivale a 11 aciertos independientes sobre una falla confirmada.

**Acción:** llamarlos casos candidatos de bajo rendimiento, conservar alternativas como capacidad incorrecta o puesta en marcha, y verificar los datos de habilitación pendientes en el guion. Una alarma puede justificar una inspección sin demostrar su causa.

### H. Los ceros se eliminan también de la comparación argentina

`filtro_rendimiento_argentina` exige energía mayor que cero. El notebook 04 aplica ese filtro antes de construir toda la serie, por lo que esos meses desaparecen también de las alertas y del dashboard.

El EDA identifica **20 meses con cero generación en medio de la operación**. Un caso son los diez meses de UL42FV entre febrero y noviembre de 2025. Que un cero no sea apropiado para aprender comportamiento sano no implica que deba desaparecer de la evaluación.

**Acción:** separar la máscara de entrenamiento sano de la máscara de observación/evaluación. Conservar ceros operativos válidos; distinguir parques no habilitados y ausencia de reporte. Si la comparación los excluye deliberadamente, explicarlo como límite de cobertura.

### I. «Planta limpia» y «tasa de suciedad» son estimaciones condicionadas

Poner `dias_desde_lluvia=0` en un modelo produce una predicción bajo ese valor de la variable. Por sí solo no prueba cuál habría sido la producción con una limpieza real, especialmente cuando lluvia, estación, nieve y otras pérdidas se confunden. El trabajo ya reconoce parte de este límite.

La pendiente de 0,049%/día se reproduce, pero se calcula a partir de un índice que usa el propio modelo con lluvia, sobre datos usados para el ajuste final. No es una medición independiente de suciedad ni permite atribuir toda diferencia a una pérdida recuperable limpiando. El error estándar de `polyfit` tampoco aborda explícitamente la dependencia temporal que el trabajo detectó en los residuos.

La fórmula de intervalo óptimo es consistente con el costo lineal supuesto de un ciclo seco. No modela explícitamente las lluvias que ya limpian, aunque la exposición habla de limpiezas «además de las lluvias».

**Acción:** presentarlo como análisis exploratorio y escenario económico. Evaluar la sensibilidad de la tasa con predicciones fuera de muestra y bloques temporales; buscar registros de limpieza para validar la interpretación; si se quiere una frecuencia operativa, simular también los reinicios por lluvia. El valor de 148 días no debe presentarse como recomendación de campo comprobada.

### J. El contador de días sin lluvia cuenta registros, no calendario

`src/features.py`, `agregar_dias_desde_lluvia`, usa `cumcount`. Reproducción mínima: una lluvia el 01/01 seguida del próximo dato el 10/01 devuelve 1 día sin lluvia, en lugar de 9. El comentario del código reconoce la simplificación, pero afecta precisamente a una variable usada para inferir suciedad.

**Acción:** usar diferencia entre fechas calendario y representar la incertidumbre si falta la lluvia de los días intermedios. Recalcular modelos y tasa si cambia esta feature.

### K. Varias conclusiones escritas necesitan sincronización

- Notebook 05, sección 3: un párrafo conserva el rango de T* de **33–206 días**, mientras la grilla actual devuelve **82–266 días**. El párrafo siguiente sí da el rango correcto.
- El guion introduce «hoy alguien mira los números una vez por mes» como hecho; en el notebook económico es un supuesto. Mantener esa condición al contar el problema.
- La demostración plantea «el mismo día» a partir de energía diaria agregada. Explicar que la decisión usa los datos al cierre del día, sin prometer aviso intradiario.
- El error medio global de 6,04% no garantiza poder detectar una pérdida de 10% en cada planta/día. El resultado observado ya lo desmiente: corregir la justificación demasiado fuerte del umbral en el plan.
- El período de prueba de regresión también aplica la máscara de entrenamiento que excluye apagones: una hora de station05 en mayo queda fuera. El 6,04% describe la muestra filtrada, no el desempeño sobre cualquier situación operativa.
- La pérdida agregada de 5.501 MWh incluye unos **156 MWh / USD 6.687 de station04**, aunque la ficha se considera no confiable. Excluirla del total económico utilizable o desglosarla explícitamente como no interpretable; revisar también el porcentaje de station09 sobre el total.
- El README dice que 01 descarga y que el modelo puede ir en Git si es chico; el flujo actual usa modelos ignorados y 01 no descarga. Sincronizar las instrucciones con el comportamiento real.

## 5. Lo que conviene conservar

- El problema se entiende y conduce a una decisión concreta.
- La comparación con una línea base física y varios modelos tiene justificación.
- La validación separa meses y evita partir horas del mismo día al azar.
- Se reconoce el peor desempeño del clima externo y la importancia del sensor.
- La hipótesis tiene umbrales y una conclusión parcial; que no se cumpla por completo no invalida el trabajo.
- Los supuestos de precio, costo de limpieza y revisión están declarados en el análisis económico.
- Los datos precalculados y la biblioteca local favorecen la presentación sin red.
- La distinción entre Argentina mensual y la flota diaria está explícita en la app.

## 6. Orden sugerido para cerrar el trabajo

1. Corregir las identidades de simulación y evaluar la política real de semáforo, incluidos estados sin información.
2. Recalcular demoras, detección por episodio y escenarios económicos con duración coherente.
3. Resolver 01, las rutas y las dependencias; comprobar instalación y ejecución desde una copia limpia.
4. Sincronizar cifras, etiquetas de evaluación y límites en notebooks, app y guion.
5. Incorporar el diagrama obligatorio y la presentación; asignar los 5–6 roles y la participación oral real.
6. Ensayar 15 minutos, preparar capturas/gráficos exportados y verificar todo en la computadora de exposición con la red desconectada.

## 7. Límites de esta revisión

No se descargaron nuevamente las fuentes externas, no se verificó la habilitación comercial de ULL4FV ni se validaron precios o causas de fallas con fuentes externas. Tampoco se probaron Colab o un entorno instalado desde cero.

La apertura visual de `app/index.html` fue bloqueada por la política del navegador de la herramienta: no admite el protocolo `file://`. Se continuó con comprobaciones de código, archivos, datos, fórmulas y construcción, sin sustituir eso por una afirmación de que la interfaz o sus mapas fueron verificados visualmente. Queda pendiente la prueba interactiva y visual sin conexión en la computadora de exposición.

**Conclusión de la revisión:** desarrollo avanzado y resultados centrales reproducibles; cierre metodológico, operativo y de exposición todavía pendiente. La prioridad es corregir evaluación y decisiones antes de pulir la presentación.
