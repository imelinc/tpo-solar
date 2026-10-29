# Presentación: 10 minutos + 5 de demostración

Defensa: 12/11/2026. Equipo: Ignacio Melinc, Matias Young, Francisco Fabrello y Malena Garcia Moraglio. El reparto es de exposición. El trabajo es compartido.

Las cifras se leen de la pantalla. Salen de `data/processed/defensa_evidencia.json`. Si se reentrena, se vuelven a leer.

## Diapositivas — 10:00

| N.º | Tema | Duración | Expositor |
|---|---|---:|---|
| 1 | Pregunta: energía de un parque según lugar, año y potencia | 1:30 | Ignacio |
| 2 | Datos: CAMMESA, coordenadas, clima mensual, ceros | 2:00 | Matias |
| 3 | Cinco modelos y por qué elige la validación de 2024 | 2:30 | Francisco |
| 4 | Prueba desde 2025 y grupos por parque | 2:00 | Francisco |
| 5 | Qué puede contestar un sitio nuevo, y qué queda afuera | 2:00 | Malena |

Apertura: «Si alguien quiere un parque en un punto de Argentina, en un año, de tantos MW, ¿cuánta energía corresponde?».

El año elige el clima medido. Un año que no está en el archivo usa el promedio de los años de entrenamiento. En el mismo lugar, 2028 y 2030 comparten ese clima; un bisiesto solo suma el 29 de febrero.

MAE, RMSE y R² están en factor de capacidad. R² no es un porcentaje de acierto. El RMSE de parque nuevo no se usó para elegir el modelo.

## Demostración — 5:00

Abrir `app/index.html` en Modelos. Una persona maneja la máquina.

| Tiempo | Acción | Qué decir |
|---|---|---|
| 0:00–1:00 | Modelos | El elegido, el RMSE de prueba y el de parque nuevo. La unidad. |
| 1:00–2:30 | Sitio → Sitio nuevo, 2023 | Lugar dentro del rango, clima de 2023 copiado del parque más cercano, energía para 10 MW. |
| 2:30–3:30 | Mismo sitio, 2028 | El archivo no tiene 2028. El clima es el promedio. La potencia sigue en 10 MW. |
| 3:30–4:15 | Ushuaia | El punto queda fuera de los parques de entrenamiento. El número es el de la celda del borde. |
| 4:15–5:00 | Serie | Un parque real. Los meses en cero siguen dibujados. |

Cierre: «Dentro del rectángulo de parques, con la potencia en MW, el modelo estima la energía del año a partir del clima de ese lugar. Fuera de ese rectángulo, o muy lejos del parque más cercano, la estimación deja de ser confiable.»

## Ensayo

1. Una pasada con este guion y otra sin leerlo.
2. Si la aplicación no responde en quince segundos, seguir con `docs/respaldo/index.html`.
3. Preguntas esperables: año futuro, lugar nuevo, ceros, prueba retrospectiva, por qué no hay matriz de confusión.
