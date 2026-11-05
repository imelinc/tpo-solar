# Presentación: 10 minutos + 5 de demostración

Defensa: 12/11/2026. Equipo: Ignacio Melinc, Matias Young, Francisco Fabrello y Malena Garcia Moraglio. El reparto es de exposición. El trabajo es compartido.

Diapositivas (16): artefacto Slides «Qué parque solar mirar primero», https://claude.ai/artifact/AEDgX4KSzRftquSmVdBWGJ (privado hasta compartirlo; se descarga como PPTX o PDF). Cada diapositiva tiene notas de exposición con expositor, tiempo y fuentes.

Las cifras salen de `data/processed/defensa_evidencia.json` y `maui_evidencia.json`. Si se reentrena, se actualizan las diapositivas antes de exponer.

## Diapositivas — 10:00

| N.º | Tema | Duración | Acumulado | Expositor |
|---|---|---:|---:|---|
| 1 | Pregunta: qué parque conviene mirar primero | 0:30 | 0:30 | Ignacio |
| 2 | Respuesta adelantada: 14 sitios, 200,5 GWh, USD 12,0 M a un precio supuesto | 0:40 | 1:10 | Ignacio |
| 3 | Tres términos: potencia, energía y factor de capacidad | 0:45 | 1:55 | Ignacio |
| 4 | Datos: 56 parques, CAMMESA y Open-Meteo, tubería | 0:35 | 2:30 | Ignacio |
| 5 | Calidad: tres decisiones (de 5.036 a 3.610 meses) | 0:35 | 3:05 | Matias |
| 6 | Exploración: más sol, más energía (correlación 0,68) | 0:35 | 3:40 | Matias |
| 7 | Cómo se evalúa: train, validation y test | 0:40 | 4:20 | Matias |
| 8 | Seis modelos, de simple a complejo | 0:35 | 4:55 | Francisco |
| 9 | Elección: menor RMSE de validation; la polinómica sobreajusta | 0:30 | 5:25 | Francisco |
| 10 | Resultados en el test: MAE, RMSE y R² | 0:35 | 6:00 | Francisco |
| 11 | Regla de la señal: modelo, vecinos y dos meses seguidos | 0:40 | 6:40 | Francisco |
| 12 | A quién mirar primero: ranking y Tocota III | 0:45 | 7:25 | Malena |
| 13 | Sin etiquetas: K-Means, PCA y DBSCAN | 0:30 | 7:55 | Malena |
| 14 | Con datos por hora: Maui, aviso en horas, inversor 11 | 0:50 | 8:45 | Malena |
| 15 | Sitio nuevo: la energía de 10 MW en Catamarca | 0:35 | 9:20 | Malena |
| 16 | Conclusiones, recomendación y paso a la demostración | 0:40 | 10:00 | Malena |

Estilo de las diapositivas: el mismo «informe sobre papel milimetrado» de la aplicación. Tinta negra para lo observado, azul para lo estimado, fondo azul en el cierre. Cambios de expositor en 2:30, 4:20 y 6:40.

Apertura: «Si hay un equipo y una semana, ¿a qué parque lo mandamos primero?».

MAE, RMSE y R² están en factor de capacidad. R² no es un porcentaje de acierto. El RMSE de parque nuevo no se usó para elegir el modelo. Una señal no es una falla confirmada y la plata en juego no es un ahorro. Un año sin clima medido usa el promedio mensual anterior a 2024: no es un pronóstico.

## Términos para explicar antes de usarlos

El público no conoce estos términos. Cada uno se dice **la primera vez que aparece**, en una frase, con el ejemplo de la derecha. En la materia los vimos en inglés (train, validation, test, RMSE, MAE, R²); se dejan así.

| Término | Qué decir (una frase) | Con qué número o ejemplo | Cuándo |
|---|---|---|---|
| **Potencia (MW) y energía (GWh)** | La potencia es lo máximo que el parque puede entregar en un instante; la energía es lo que entregó en un período. 1 GWh = 1.000 MWh. | Un parque de 10 MW produce 22,44 GWh en un año. | Diap. 3 |
| **Factor de capacidad** (*capacity factor*) | Qué parte de su potencia máxima entrega un parque en promedio. Saca el tamaño de la comparación: queda solo lo que depende del lugar y del clima. | Un parque típico entrega cerca de un cuarto de su máximo (mediana de 0,25). En enero 0,33 y en junio 0,17. | Diap. 3 y 6 |
| **Cuenta de la energía** | La energía sale de multiplicar el factor por la potencia y por las horas. | 10 MW × 8.760 h × 25,6 % = 22,44 GWh. | Diap. 3 y 15 |
| **Irradiación** (kWh/m²) | Cuánto sol llegó a la superficie en el mes. Es la entrada principal del modelo. | Más sol, más factor: relación de 0,68. | Diap. 6 |
| **Temperatura máxima y nubosidad** | Son las otras dos variables del clima. Temperatura máxima: el promedio de las máximas diarias del mes, en °C. Nubosidad: el porcentaje promedio del cielo cubierto de nubes. | Nubosidad: más nubes, menos generación (relación de −0,30). | Diap. 6 |
| **Latitud y longitud** | La posición del parque: latitud es qué tan al norte o al sur; longitud, qué tan al este o al oeste. Entran al modelo como ubicación. | Jujuy, al norte, encabeza el factor medio por provincia (0,30). | Diap. 6 |
| **Correlación** | Qué tanto dos variables suben o bajan juntas, de −1 a 1. Cerca de 1: suben juntas; cerca de −1: una sube y la otra baja; cerca de 0: no se relacionan. No prueba que una cause a la otra. | Irradiación y factor: 0,68. | Diap. 6 |
| **CAMMESA y Open-Meteo** | CAMMESA informa cuánto generó cada parque; Open-Meteo, el clima de cada lugar. | 56 parques, 3.610 meses. | Diap. 4 |
| **Train, validation y test** | Train: los meses con los que el modelo aprende. Validation: los meses con los que se compara y elige el modelo. Test: los meses que no vio, para medir el error. | Train hasta 2023, validation 2024, test desde 2025. | Diap. 7 |
| **Regresión lineal, polinómica, árbol, Random Forest y XGBoost** | Regresión lineal: una recta. Polinómica: una curva, con cuadrados y cruces de las variables. Árbol: una cadena de preguntas. Random Forest: muchos árboles que se promedian. XGBoost: árboles en secuencia, cada uno corrige el error del anterior. | Se compararon seis modelos y quedó XGBoost. | Diap. 8 |
| **RMSE y MAE** | Los dos miden cuánto se equivoca el modelo, en puntos de factor de capacidad. El MAE es el error promedio; el RMSE castiga más los errores grandes. Menos es mejor. | En test: MAE 0,0425 (unos 4 puntos de factor) y RMSE 0,0664. | Diap. 9–10 |
| **R²** | Qué parte de la variación entre meses explica el modelo. No es un porcentaje de acierto. | R² de 0,487: explica cerca de la mitad. | Diap. 10 |
| **Retrospectivo** | El test son meses que ya pasaron y que el equipo ya había explorado: no es una prueba ciega. | Test desde 2025. | Diap. 7 y 10 |
| **Rango del train set y «no extrapola»** | El modelo solo estima dentro de la zona donde hay parques de entrenamiento. Afuera repite lo que sabe del borde, así que no es confiable. La aplicación no deja elegir un punto afuera. | El recuadro punteado de la carta. | Diap. 15 |
| **Celda de 0,2°** | La consulta cae en la celda de la grilla más cercana (unos 22 km de lado). | Se marca en la carta de Sitio. | Diap. 15 |
| **Clima medido y clima promedio** | Si el año tiene clima medido, se usa; si no (un año futuro), se usa el promedio mensual anterior a 2024. No es un pronóstico. | Las barras rayadas de Sitio. | Diap. 15 |
| **Cero operativo** | Un mes con generación cero real (parada del parque). Se conserva; no es un mes sin dato. | Los 13 ceros que se conservan. Si un parque está parado, cuenta como bajo. | Diap. 5 y 11 |
| **Boxplot** | Una caja con la mitad central de los datos, una línea con la mediana y bigotes hasta los extremos que no son atípicos. | La mediana del factor es 0,33 en enero y 0,17 en junio. | Solo en la app |
| **Leakage** | Que el modelo vea información del futuro al aprender y el resultado salga demasiado optimista. Por eso se divide por fecha y no al azar. | Train hasta 2023, test desde 2025. | Diap. 7 |
| **One-hot** | El mes entra como 12 columnas de sí o no, en vez de un número del 1 al 12. | Julio y junio pesan casi tanto como el sol. | Diap. 8 |
| **Importancia de variables** | Cuánto ayuda cada variable a reducir el error dentro de los árboles. | Irradiación 0,20; julio 0,19; junio 0,12. | Solo si preguntan |
| **Parque nuevo (validación por grupos)** | El error con parques que el modelo no vio al ajustarse: cinco grupos de parques, solo con años de train. No eligió el modelo. | Promedio 0,0592; un grupo llega a 0,085. | Diap. 11, solo si preguntan |
| **Señal** | Dos meses seguidos por debajo del 80 % del modelo y de los vecinos de provincia. Dice a quién mirar primero, no qué falló. | 14 sitios, 109 meses-parque. | Diap. 2 y 11 |
| **Lo esperado (fuera de muestra)** | Lo que estima para un parque un modelo que nunca lo vio. Si lo hubiera visto, aprendería a esperar poco de un parque que rinde poco. | Tocota III rinde el 54 % de lo esperado. | Diap. 11 |
| **Plata en juego** | Energía faltante por un precio supuesto de USD 60/MWh. Se cambia en la app. No es un ahorro demostrado. | 200,5 GWh, unos USD 12,0 M. | Diap. 2 |
| **K-Means, silueta, PCA y DBSCAN** | K-Means arma grupos; la silueta mide qué tan separados quedan; PCA reduce dimensiones para dibujar; DBSCAN aparta lo que queda fuera del grupo denso. | k = 2, silueta 0,41. DBSCAN: solo 27 de 109 señales afuera. | Diap. 13 |
| **Inversor** | El equipo que convierte la energía de los paneles para entregarla a la red. Una planta tiene varios y se pueden comparar entre sí. | Maui: 9 inversores contados, 190 kW. | Diap. 14 |
| **Hora de sol** | Una hora del día con generación apreciable. El aviso se cuenta en horas de sol, no de reloj. | Apagado: 2 h. Cae 30 %: 4 h. | Diap. 14 |
| **Falla inyectada** | Una caída que se aplica a mano sobre un equipo sano, solo para medir cuánto tarda el aviso. No entrena nada. | 80 por tipo. | Diap. 11 y 14 |

## Demostración — 5:00

Abrir `app/index.html`; arranca en A revisar. Una persona maneja la máquina. «Modo exposición» agranda el texto para el proyector.

| Tiempo | Vista y acción | Qué decir |
|---|---|---|
| 0:00–1:30 | A revisar → cambiar el precio; abrir Tocota III | El ranking ordena a quién mirar primero. Cambiar los USD/MWh recalcula la plata, porque es un supuesto. La serie de Tocota III muestra lo observado contra lo esperado por un modelo que no lo vio. Botón para ver los otros sitios. |
| 1:30–3:00 | Por hora → mapa de calor; probar una falla | Cada fila es un inversor. El 04 se ve a simple vista. La prueba aplica la misma regla de Python: un apagado avisa en 2 horas de sol y una caída de 15 % puede no llegar a avisar. Es una simulación: no entrena nada. |
| 3:00–4:00 | Sitio nuevo → clic dentro del recuadro, Año 2023 y luego 2028; clic fuera | La cuenta: MW × horas × factor = GWh. 2028 usa el clima promedio. Fuera del recuadro la app no estima: el modelo no extrapola. |
| 4:00–4:40 | Modelos | La tabla de los seis modelos con RMSE de train, validation y test. XGBoost elegido; la polinómica se dispara en test. |
| 4:40–5:00 | Datos | De dónde sale todo: los parques, el rango del train set y la exploración. |

Cierre: «Con datos públicos sabemos a quién llamar primero. Para saber por qué bajó y enterarse en horas hacen falta los datos del parque.»

## Ensayo

1. Una pasada leyendo las notas y otra sin leerlas, con cronómetro. Practicar los cambios de expositor en 2:30, 4:20 y 6:40.
2. Si la aplicación no responde en quince segundos, seguir con `docs/respaldo/index.html`.
3. Preguntas esperables: en `guion_defensa.md`.
