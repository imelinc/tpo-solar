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
| 4 | Cinco modelos, XGBoost elegido por RMSE de 2024 | 1:40 | 4:45 | Matias |
| 5 | Prueba retrospectiva desde 2025 y parque nuevo | 1:40 | 6:25 | Francisco |
| 6 | Consulta de un sitio y el caso límite de Ushuaia | 1:20 | 7:45 | Francisco |
| 7 | Un parque real: Chepes rinde menos de lo estimado en 2026 | 1:00 | 8:45 | Malena |
| 8 | Conclusiones, límites y paso a la demo | 0:55 | 9:40 | Malena |

Apertura: «Si alguien quiere un parque en un punto de Argentina, en un año, de tantos MW, ¿cuánta energía corresponde?».

MAE, RMSE y R² están en factor de capacidad. R² no es un porcentaje de acierto. El RMSE de parque nuevo no se usó para elegir el modelo. Un año sin clima medido usa el promedio mensual anterior a 2024: no es un pronóstico.

## Demostración — 5:00

Abrir `app/index.html`; arranca en Atlas. Una persona maneja la máquina. «Modo exposición» agranda el texto para el proyector.

| Tiempo | Vista y acción | Qué decir |
|---|---|---|
| 0:00–1:00 | Atlas | La carta: cada estrella es un parque y su tamaño es la potencia. El campo ámbar es el factor típico estimado; el rectángulo punteado es el rango de entrenamiento. Bajar a la exploración: el boxplot muestra el invierno bajo y la dispersión la relación con el sol. |
| 1:00–2:00 | Modelos | Validación (aro) contra prueba (punto) de los cinco modelos. XGBoost elegido; RF casi empata. Importancias y el RMSE de un parque no visto. |
| 2:00–3:15 | Sitio → «Sitio nuevo, 2023», luego «Mismo sitio, 2028» | Clic en la carta mueve el retículo. La línea roja va al parque que presta el clima. 2028 usa el clima promedio y las barras quedan rayadas. |
| 3:15–4:00 | Sitio → «Ushuaia» | Fuera del rango: el número sale tachado y el aviso explica que el modelo no extrapola. |
| 4:00–5:00 | Parque | Chepes: observado contra estimado, la prueba sombreada y el cero de marzo de 2026 marcado. Abajo, la grilla de los 56 parques para abrir otro. |

Cierre: «Dentro del rango de los parques, con la potencia en MW, el modelo estima la energía del año a partir del clima de ese lugar. Fuera de ese rango, o muy lejos del parque más cercano, la estimación deja de ser confiable.»

## Ensayo

1. Una pasada leyendo las notas y otra sin leerlas, con cronómetro. Practicar los cambios de expositor en 1:55, 4:45 y 7:45.
2. Si la aplicación no responde en quince segundos, seguir con `docs/respaldo/index.html`.
3. Preguntas esperables: año futuro, lugar nuevo, ceros, prueba retrospectiva, parques de Chaco fuera del rango de entrenamiento, por qué no hay matriz de confusión.
