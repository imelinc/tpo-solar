# Presentación: 10 minutos + 5 de demostración

Defensa: 12/11/2026. Equipo: Ignacio Melinc, Matias Young, Francisco Fabrello y Malena Garcia Moraglio. El reparto es de exposición. El trabajo es compartido.

Diapositivas (15): artefacto Slides «Generación solar en Argentina», https://claude.ai/artifact/AEDgX4KSzRftquSmVdBWGJ (privado hasta compartirlo; se descarga como PPTX o PDF). Cada diapositiva tiene notas de exposición con expositor, tiempo y fuentes.

Las cifras salen de `data/processed/defensa_evidencia.json`. Si se reentrena, se actualizan las diapositivas antes de exponer.

## Diapositivas — 10:00

| N.º | Tema | Duración | Acumulado | Expositor |
|---|---|---:|---:|---|
| 1 | Pregunta: energía de un parque solar en Argentina | 0:35 | 0:35 | Ignacio |
| 2 | Tres términos: potencia, energía y factor de capacidad, y la cuenta | 0:50 | 1:25 | Ignacio |
| 3 | Datos: 56 parques, CAMMESA y Open-Meteo, tubería | 0:40 | 2:05 | Ignacio |
| 4 | Calidad: tres decisiones (de 5.036 a 3.610 meses) | 0:40 | 2:45 | Matias |
| 5 | Exploración: más sol, más energía (correlación 0,68) | 0:45 | 3:30 | Matias |
| 6 | Exploración: cambia con el mes y con el lugar | 0:30 | 4:00 | Matias |
| 7 | Cómo se evalúa: train, validation y test | 0:45 | 4:45 | Matias |
| 8 | Cinco modelos, de simple a complejo | 0:40 | 5:25 | Francisco |
| 9 | Elección: menor RMSE de validation, XGBoost | 0:35 | 6:00 | Francisco |
| 10 | Resultados en el test: MAE, RMSE y R² | 0:50 | 6:50 | Francisco |
| 11 | Qué mira el modelo y cómo falla con un parque nuevo | 0:35 | 7:25 | Francisco |
| 12 | Consulta de un sitio: la energía de 10 MW en Catamarca | 0:45 | 8:10 | Malena |
| 13 | El límite: fuera del rango del train no se estima | 0:35 | 8:45 | Malena |
| 14 | Un parque real: Chepes | 0:35 | 9:20 | Malena |
| 15 | Conclusiones y paso a la demostración | 0:40 | 10:00 | Malena |

Estilo de las diapositivas: el mismo «informe sobre papel milimetrado» de la aplicación. Tinta negra para lo observado, azul para lo estimado, fondo azul en el cierre. Cambios de expositor en 2:05, 4:45 y 7:25.

Apertura: «Si alguien quiere un parque en un punto de Argentina, en un año, de tantos MW, ¿cuánta energía corresponde?».

MAE, RMSE y R² están en factor de capacidad. R² no es un porcentaje de acierto. El RMSE de parque nuevo no se usó para elegir el modelo. Un año sin clima medido usa el promedio mensual anterior a 2024: no es un pronóstico.

## Términos para explicar antes de usarlos

El público no conoce estos términos. Cada uno se dice **la primera vez que aparece**, en una frase, con el ejemplo de la derecha. En la materia los vimos en inglés (train, validation, test, RMSE, MAE, R²); se dejan así.

| Término | Qué decir (una frase) | Con qué número o ejemplo | Cuándo |
|---|---|---|---|
| **Potencia (MW) y energía (GWh)** | La potencia es lo máximo que el parque puede entregar en un instante; la energía es lo que entregó en un período. 1 GWh = 1.000 MWh. | Un parque de 10 MW produce 22,44 GWh en un año. | Diap. 2 |
| **Factor de capacidad** (*capacity factor*) | Qué parte de su potencia máxima entrega un parque en promedio. Saca el tamaño de la comparación: queda solo lo que depende del lugar y del clima. | Un parque típico entrega cerca de un cuarto de su máximo (mediana de 0,25). En enero 0,33 y en junio 0,17. | Diap. 2 y 5 |
| **Cuenta de la energía** | La energía sale de multiplicar el factor por la potencia y por las horas. | 10 MW × 8.760 h × 25,6 % = 22,44 GWh. | Diap. 2 y 12 |
| **Irradiación** (kWh/m²) | Cuánto sol llegó a la superficie en el mes. Es la entrada principal del modelo. | Más sol, más factor: relación de 0,68. | Diap. 5 |
| **Temperatura máxima y nubosidad** | Son las otras dos variables del clima. Temperatura máxima: el promedio de las máximas diarias del mes, en °C. Nubosidad: el porcentaje promedio del cielo cubierto de nubes. | Nubosidad: más nubes, menos generación (relación de −0,30). | Diap. 5 |
| **Latitud y longitud** | La posición del parque: latitud es qué tan al norte o al sur; longitud, qué tan al este o al oeste. Entran al modelo como ubicación. | Jujuy, al norte, encabeza el factor medio por provincia (0,30). | Diap. 5–6 |
| **Correlación** | Qué tanto dos variables suben o bajan juntas, de −1 a 1. Cerca de 1: suben juntas; cerca de −1: una sube y la otra baja; cerca de 0: no se relacionan. No prueba que una cause a la otra. | Irradiación y factor: 0,68. | Diap. 5 |
| **CAMMESA y Open-Meteo** | CAMMESA informa cuánto generó cada parque; Open-Meteo, el clima de cada lugar. | 56 parques, 3.610 meses. | Diap. 3 |
| **Train, validation y test** | Train: los meses con los que el modelo aprende. Validation: los meses con los que se compara y elige el modelo. Test: los meses que no vio, para medir el error. | Train hasta 2023, validation 2024, test desde 2025. | Diap. 7 |
| **Regresión lineal, árbol, Random Forest y XGBoost** | Regresión lineal: una recta. Árbol: una cadena de preguntas. Random Forest: muchos árboles que se promedian. XGBoost: árboles en secuencia, cada uno corrige el error del anterior. | Se compararon cinco modelos y quedó XGBoost. | Diap. 8 |
| **RMSE y MAE** | Los dos miden cuánto se equivoca el modelo, en puntos de factor de capacidad. El MAE es el error promedio; el RMSE castiga más los errores grandes. Menos es mejor. | En test: MAE 0,0425 (unos 4 puntos de factor) y RMSE 0,0664. | Diap. 9–10 |
| **R²** | Qué parte de la variación entre meses explica el modelo. No es un porcentaje de acierto. | R² de 0,487: explica cerca de la mitad. | Diap. 10 |
| **Retrospectivo** | El test son meses que ya pasaron y que el equipo ya había explorado: no es una prueba ciega. | Test desde 2025. | Diap. 7 y 10 |
| **Rango del train set y «no extrapola»** | El modelo solo estima dentro de la zona donde hay parques de entrenamiento. Afuera repite lo que sabe del borde, así que no es confiable. La aplicación no deja elegir un punto afuera. | El recuadro punteado de la carta. | Diap. 13 |
| **Celda de 0,2°** | La consulta cae en la celda de la grilla más cercana (unos 22 km de lado). | Se marca en la carta de Sitio. | Diap. 12 |
| **Clima medido y clima promedio** | Si el año tiene clima medido, se usa; si no (un año futuro), se usa el promedio mensual anterior a 2024. No es un pronóstico. | Las barras rayadas de Sitio. | Diap. 12 |
| **Cero operativo** | Un mes con generación cero real (parada del parque). Se conserva; no es un mes sin dato. | El cero de marzo de 2026 en Chepes. | Diap. 4 y 14 |
| **Boxplot** | Una caja con la mitad central de los datos, una línea con la mediana y bigotes hasta los extremos que no son atípicos. | La mediana del factor es 0,33 en enero y 0,17 en junio. | Diap. 6 |
| **Leakage** | Que el modelo vea información del futuro al aprender y el resultado salga demasiado optimista. Por eso se divide por fecha y no al azar. | Train hasta 2023, test desde 2025. | Diap. 7 |
| **One-hot** | El mes entra como 12 columnas de sí o no, en vez de un número del 1 al 12. | Julio y junio pesan casi tanto como el sol. | Diap. 8 y 11 |
| **Importancia de variables** | Cuánto ayuda cada variable a reducir el error dentro de los árboles. | Irradiación 0,20; julio 0,19; junio 0,12. | Diap. 11 |
| **Parque nuevo (validación por grupos)** | El error con parques que el modelo no vio al ajustarse: cinco grupos de parques, solo con años de train. No eligió el modelo. | Promedio 0,0592; un grupo llega a 0,085. | Diap. 11 |

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

1. Una pasada leyendo las notas y otra sin leerlas, con cronómetro. Practicar los cambios de expositor en 2:05, 4:45 y 7:25.
2. Si la aplicación no responde en quince segundos, seguir con `docs/respaldo/index.html`.
3. Preguntas esperables: año futuro, lugar nuevo, ceros, test retrospectivo, parques de Chaco fuera del rango del train set, por qué no hay matriz de confusión.
