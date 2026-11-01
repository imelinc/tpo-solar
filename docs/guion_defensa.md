# Defensa del 12/11/2026

Para los 10 minutos de exposición y los 5 de demo, usar [guion_presentacion_10min.md](guion_presentacion_10min.md). Acá quedan las respuestas cortas.

Equipo: Ignacio Melinc, Matias Young, Francisco Fabrello y Malena Garcia Moraglio.

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
- La energía estimada no es producción ya cobrada ni un ahorro.

## Recorrido de la demo

Datos → Modelos → Sitio (2023, 2028, un clic fuera del recuadro) → Parque real (Chepes).
