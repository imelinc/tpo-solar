# Presentación: 10 minutos + 5 de demostración

Defensa: 12/11/2026. Equipo: Ignacio Melinc, Matias Young, Francisco Fabrello y Malena Garcia Moraglio. El reparto es de exposición. El trabajo es compartido.

Diapositivas: artefacto Slides «Generación solar en Argentina», https://claude.ai/artifact/AEDgX4KSzRftquSmVdBWGJ (privado hasta compartirlo; se descarga como PPTX o PDF). Cada diapositiva tiene notas de exposición con expositor, tiempo y fuentes.

Las cifras salen de `data/processed/defensa_evidencia.json`. Si se reentrena, se actualizan las diapositivas antes de exponer.

## Diapositivas — 10:00

| N.º | Tema | Duración | Acumulado | Expositor |
|---|---|---:|---:|---|
| 1 | Pregunta: energía de un parque según lugar y clima | 0:50 | 0:50 | Ignacio |
| 2 | Datos: 56 parques, CAMMESA y Open-Meteo, tubería | 1:05 | 1:55 | Ignacio |
| 3 | Calidad y exploración: irradiación contra factor, tres decisiones | 1:10 | 3:05 | Matias |
| 4 | Cinco modelos, XGBoost elegido por RMSE de validation (2024) | 1:40 | 4:45 | Matias |
| 5 | Test retrospectivo desde 2025 y parque nuevo | 1:40 | 6:25 | Francisco |
| 6 | Consulta de un sitio y su límite: solo dentro del rango del train set | 1:20 | 7:45 | Francisco |
| 7 | Un parque real: Chepes rinde menos de lo estimado en 2026 | 1:00 | 8:45 | Malena |
| 8 | Conclusiones, límites y paso a la demo | 0:55 | 9:40 | Malena |

Apertura: «Si alguien quiere un parque en un punto de Argentina, en un año, de tantos MW, ¿cuánta energía corresponde?».

MAE, RMSE y R² están en factor de capacidad. R² no es un porcentaje de acierto. El RMSE de parque nuevo no se usó para elegir el modelo. Un año sin clima medido usa el promedio mensual anterior a 2024: no es un pronóstico.

## Demostración — 5:00

Abrir `app/index.html`; arranca en Datos. Una persona maneja la máquina. «Modo exposición» agranda el texto para el proyector.

| Tiempo | Vista y acción | Qué decir |
|---|---|---|
| 0:00–1:00 | Datos | La carta: cada punto negro es un parque y su tamaño es la potencia (con anillo desde 50 MW). La mancha azul es el factor típico estimado; el rectángulo punteado azul es el rango del train set. Bajar a la exploración: el boxplot muestra el invierno bajo y la dispersión la relación con el sol. |
| 1:00–2:00 | Modelos | La tabla de los cinco modelos con RMSE de train, validation y test. XGBoost elegido por el RMSE de validation; Random Forest casi empata en test. Leer «Por qué XGBoost», abajo. |
| 2:00–3:15 | Sitio → clic dentro del recuadro punteado, Año 2023 y luego 2028 | El clic mueve el retículo y marca la celda de 0,2° del cálculo. La línea punteada va al parque real que presta el clima. Leer la cuenta: MW × horas × factor = GWh. 2028 usa el clima promedio y las barras quedan rayadas. |
| 3:15–4:00 | Sitio → clic fuera del recuadro | El mapa está velado y el cursor pasa a «no permitido». Un aviso explica que el modelo no extrapola y el sitio no cambia. |
| 4:00–5:00 | Parque | Chepes: observado contra estimado, el test sombreado y el cero de marzo de 2026 marcado. Abajo, la grilla de los 56 parques para abrir otro. |

Cierre: «Dentro del rango de los parques, con la potencia en MW, el modelo estima la energía del año a partir del clima de ese lugar. Fuera de ese rango, o muy lejos del parque más cercano, la estimación deja de ser confiable.»

## Ensayo

1. Una pasada leyendo las notas y otra sin leerlas, con cronómetro. Practicar los cambios de expositor en 1:55, 4:45 y 7:45.
2. Si la aplicación no responde en quince segundos, seguir con `docs/respaldo/index.html`.
3. Preguntas esperables: año futuro, lugar nuevo, ceros, test retrospectivo, parques de Chaco fuera del rango del train set, por qué no hay matriz de confusión.
