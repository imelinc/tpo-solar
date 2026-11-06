# Defensa del 12/11/2026

Para los 10 minutos de exposición y los 5 de demo, usar [guion_presentacion_10min.md](guion_presentacion_10min.md). Acá quedan las respuestas cortas.

Equipo: Ignacio Melinc, Matias Young, Francisco Fabrello y Malena Garcia Moraglio.

## ¿Por qué Tocota III primero?

Porque es el sitio con más energía faltante desde 2025: 99 GWh en 14 meses con señal. Rindió el 54 % del modelo y el 52 % de sus vecinos: las dos comparaciones coinciden. No sabemos la causa. Puede ser una falla, una restricción de la red, un contrato o una potencia mal informada.

## ¿Por qué lo esperado sale de un modelo que no vio ese parque?

Si lo hubiera visto, aprendería a esperar poco de un parque que rinde poco, y la señal se apagaría sola. Se entrenan cinco modelos hasta 2023, cada uno sin un grupo de parques, y se usa el que no vio al parque.

## ¿Es plata que se pierde?

No se afirma. Es energía faltante por un precio supuesto de USD 60/MWh: unos USD 12,0 M en total. Sirve para ordenar la prioridad y el precio se cambia en la app. No es un ahorro demostrado.

## ¿Por qué 80 %?

Es un umbral fijado por criterio, no optimizado. Entre 75 % y 85 % se mantienen 11 a 14 sitios y 191 a 216 GWh. Con caídas simuladas de 10/20/30/50 % detecta 1/10,5/61,5/82,5 %: ve problemas grandes, no chicos.

## ¿Qué pasa si faltan vecinos?

194 meses del test quedan en «sin vecinos»: no se sabe. No se los cuenta como normales.

## ¿No entrenaron con fallas simuladas?

No. El docente dijo «fuerte no» a entrenar con datos sintéticos. Las caídas simuladas solo miden la sensibilidad de la regla. Por eso no hay clasificador de causas.

## ¿Por qué no usar DBSCAN para señalar?

Apartó 127 meses, 91 de ellos con rendimiento alto, y solo 27 de las 109 señales quedaron afuera. Separa lo raro, no lo malo.

## ¿Por qué no regresión logística?

Es un clasificador y el target es un número. Además no hay fallas etiquetadas con las que entrenarla.

## ¿Puede estimar un parque que todavía no existe?

Sí, si se dan tres cosas: el lugar (se elige con un clic en el mapa), el año y la potencia en MW, y el punto cae dentro del rectángulo de parques usados para entrenar (el train set). La aplicación no deja elegir un punto fuera de ese rectángulo.

El modelo devuelve el factor de capacidad de cada mes. La energía es factor × MW × horas del mes. Sin la potencia solo hay rendimiento, no MWh.

El año no se entrena como causa. Si 2023 está en el clima, se usa el clima de 2023 del parque más cercano. Si el año es 2028, se usa el promedio mensual anterior a 2024. Por eso dos años futuros, en el mismo lugar y con la misma potencia, dan casi la misma energía. Un bisiesto suma un día de febrero.

La consulta de la aplicación cae en una celda de 0,2°. El clima de esa celda es el del parque más cercano. A más de 150 km, conviene decir que la copia es débil.

Un punto fuera del rectángulo, como Ushuaia, la aplicación no lo deja elegir: el mapa está velado fuera del recuadro, el cursor pasa a «no permitido» y un aviso explica que el modelo no extrapola. Un árbol no extrapola: repite el comportamiento del borde.

## Qué no afirma

- El test desde 2025 es retrospectivo.
- El RMSE de los grupos por parque no eligió al modelo. Mide parques que no entraron a ese ajuste.
- Un cero de generación se conserva. No es un mes sin reporte.
- No hay etiquetas de fallas en CAMMESA, así que no hay matriz de confusión.
- Una señal no es una falla confirmada y ninguna causa se verificó en campo.
- Una suciedad pareja en toda una planta no se ve: la comparación con vecinos la cancela.
- La energía estimada no es producción ya cobrada ni un ahorro.

## Recorrido de la demo

A revisar (precio, Tocota III) → Sitio nuevo (2023, 2028, un clic fuera del recuadro) → Modelos → Datos.
