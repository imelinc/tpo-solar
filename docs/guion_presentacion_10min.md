# Presentación: 10 minutos + 5 de demostración

Defensa: 12/11/2026. Equipo: Ignacio Melinc, Matias Young, Francisco Fabrello y Malena Garcia Moraglio. El reparto es de exposición. El trabajo es compartido.

Diapositivas (14): artefacto Slides «Detector Solar», https://claude.ai/artifact/AEDgX4KSzRftquSmVdBWGJ (privado hasta compartirlo; se descarga como PPTX o PDF). Portada, 3 por integrante y «Muchas gracias». Cada diapositiva tiene notas con lo que se dice y con respuestas por si preguntan.

Las cifras salen de `data/processed/defensa_evidencia.json`. Si se reentrena, se actualizan las diapositivas antes de exponer.

## Diapositivas — 10:00

Poco texto y palabras comunes. Decir «rendimiento» en vez de «factor de capacidad», y «error» en vez de RMSE o MAE. Lo técnico se dice si preguntan.

| N.º | Título | Duración | Acumulado | Expositor |
|---|---|---:|---:|---|
| 1 | Encontramos la energía que falta en los parques solares argentinos | 0:20 | 0:20 | Ignacio |
| 2 | USD 12 M en juego, 87 % en tres parques | 0:50 | 1:10 | Ignacio |
| 3 | Un mes bajo no dice nada. Comparado, sí. | 0:55 | 2:05 | Ignacio |
| 4 | Un número para comparar parques | 0:45 | 2:50 | Ignacio |
| 5 | Todo sale de datos públicos | 0:50 | 3:40 | Matias |
| 6 | En junio se rinde la mitad que en enero | 0:40 | 4:20 | Matias |
| 7 | Jujuy rinde casi el doble que Córdoba (K-Means) | 0:50 | 5:10 | Matias |
| 8 | Probamos seis modelos: ganó XGBoost | 0:50 | 6:00 | Francisco |
| 9 | Lo probamos con meses que no vio | 0:50 | 6:50 | Francisco |
| 10 | Cuándo un parque entra en la lista | 0:45 | 7:35 | Francisco |
| 11 | La lista de a quién llamar primero | 0:55 | 8:30 | Malena |
| 12 | También sirve antes de construir | 0:40 | 9:10 | Malena |
| 13 | Qué se lleva la gerencia, y paso a la demostración | 0:40 | 9:50 | Malena |
| 14 | Muchas gracias | 0:10 | 10:00 | Malena |

Cambios de expositor en 2:50, 5:10 y 7:35. La demostración va entre la 13 y la 14.

Apertura: «Cuando un parque solar rinde menos de lo que debería, desde afuera nadie se entera. Este es Detector Solar».

Las aclaraciones se dicen igual: una señal no es una falla confirmada, y la plata en juego usa un precio supuesto y no es un ahorro. El test es retrospectivo y, en él, Random Forest queda apenas mejor que XGBoost.

## Términos por si preguntan

En la presentación se evitan. Si preguntan, se responde en una frase, con el ejemplo de la derecha.

| Término | Qué decir (una frase) | Con qué número o ejemplo |
|---|---|---|
| **Potencia (MW) y energía (GWh)** | La potencia es lo máximo que el parque puede entregar en un instante; la energía es lo que entregó en un período. 1 GWh = 1.000 MWh. | Un parque de 10 MW produce 22,44 GWh en un año. |
| **Factor de capacidad** (*capacity factor*) | Qué parte de su potencia máxima entrega un parque en promedio. Saca el tamaño de la comparación: queda solo lo que depende del lugar y del clima. | Un parque típico entrega cerca de un cuarto de su máximo (mediana de 0,25). En enero 0,33 y en junio 0,17. |
| **Cuenta de la energía** | La energía sale de multiplicar el factor por la potencia y por las horas. | 10 MW × 8.760 h × 25,6 % = 22,44 GWh. |
| **Irradiación** (kWh/m²) | Cuánto sol llegó a la superficie en el mes. Es la entrada principal del modelo. | Más sol, más factor: relación de 0,68. |
| **Temperatura máxima y nubosidad** | Son las otras dos variables del clima. Temperatura máxima: el promedio de las máximas diarias del mes, en °C. Nubosidad: el porcentaje promedio del cielo cubierto de nubes. | Nubosidad: más nubes, menos generación (relación de −0,30). |
| **Latitud y longitud** | La posición del parque: latitud es qué tan al norte o al sur; longitud, qué tan al este o al oeste. Entran al modelo como ubicación. | Jujuy, al norte, encabeza el factor medio por provincia (0,30). |
| **Correlación** | Qué tanto dos variables suben o bajan juntas, de −1 a 1. Cerca de 1: suben juntas; cerca de −1: una sube y la otra baja; cerca de 0: no se relacionan. No prueba que una cause a la otra. | Irradiación y factor: 0,68. |
| **CAMMESA y Open-Meteo** | CAMMESA informa cuánto generó cada parque; Open-Meteo, el clima de cada lugar. | 56 parques, 3.610 meses. |
| **Train, validation y test** | Train: los meses con los que el modelo aprende. Validation: los meses con los que se compara y elige el modelo. Test: los meses que no vio, para medir el error. | Train hasta 2023, validation 2024, test desde 2025. |
| **Regresión lineal, polinómica, árbol, Random Forest y XGBoost** | Regresión lineal: una recta. Polinómica: una curva, con cuadrados y cruces de las variables. Árbol: una cadena de preguntas. Random Forest: muchos árboles que se promedian. XGBoost: árboles en secuencia, cada uno corrige el error del anterior. | Se compararon seis modelos y quedó XGBoost. |
| **RMSE y MAE** | Los dos miden cuánto se equivoca el modelo, en puntos de factor de capacidad. El MAE es el error promedio; el RMSE castiga más los errores grandes. Menos es mejor. | En test: MAE 0,0425 (unos 4 puntos de factor) y RMSE 0,0664. |
| **R²** | Qué parte de la variación entre meses explica el modelo. No es un porcentaje de acierto. | R² de 0,487: explica cerca de la mitad. |
| **Retrospectivo** | El test son meses que ya pasaron y que el equipo ya había explorado: no es una prueba ciega. | Test desde 2025. |
| **Rango del train set y «no extrapola»** | El modelo solo estima dentro de la zona donde hay parques de entrenamiento. Afuera repite lo que sabe del borde, así que no es confiable. La aplicación no deja elegir un punto afuera. | El recuadro punteado de la carta. |
| **Celda de 0,2°** | La consulta cae en la celda de la grilla más cercana (unos 22 km de lado). | Se marca en la carta de Sitio. |
| **Clima medido y clima promedio** | Si el año tiene clima medido, se usa; si no (un año futuro), se usa el promedio mensual anterior a 2024. No es un pronóstico. | Las barras rayadas de Sitio. |
| **Cero operativo** | Un mes con generación cero real (parada del parque). Se conserva; no es un mes sin dato. | Los 13 ceros que se conservan. Si un parque está parado, cuenta como bajo. |
| **Boxplot** | Una caja con la mitad central de los datos, una línea con la mediana y bigotes hasta los extremos que no son atípicos. | La mediana del factor es 0,33 en enero y 0,17 en junio. |
| **Leakage** | Que el modelo vea información del futuro al aprender y el resultado salga demasiado optimista. Por eso se divide por fecha y no al azar. | Train hasta 2023, test desde 2025. |
| **One-hot** | El mes entra como 12 columnas de sí o no, en vez de un número del 1 al 12. | Julio y junio pesan casi tanto como el sol. |
| **Importancia de variables** | Cuánto ayuda cada variable a reducir el error dentro de los árboles. | Irradiación 0,20; julio 0,19; junio 0,12. |
| **Parque nuevo (validación por grupos)** | El error con parques que el modelo no vio al ajustarse: cinco grupos de parques, solo con años de train. No eligió el modelo. | Promedio 0,0592; un grupo llega a 0,085. |
| **Señal** | Dos meses seguidos por debajo del 80 % del modelo y de los vecinos de provincia. Dice a quién mirar primero, no qué falló. | 14 sitios, 109 meses-parque. |
| **Lo esperado (fuera de muestra)** | Lo que estima para un parque un modelo que nunca lo vio. Si lo hubiera visto, aprendería a esperar poco de un parque que rinde poco. | Tocota III rinde el 54 % de lo esperado. |
| **Plata en juego** | Energía faltante por un precio supuesto de USD 60/MWh. Se cambia en la app. No es un ahorro demostrado. | 200,5 GWh, unos USD 12,0 M. |
| **K-Means, silueta, PCA y DBSCAN** | K-Means arma grupos; la silueta mide qué tan separados quedan; PCA reduce dimensiones para dibujar; DBSCAN aparta lo que queda fuera del grupo denso. | k = 2, silueta 0,41. DBSCAN: solo 27 de 109 señales afuera. |
| **Inversor** | El equipo que convierte la energía de los paneles para entregarla a la red. Una planta tiene varios y se pueden comparar entre sí. | Maui: 9 inversores contados, 190 kW. |
| **Hora de sol** | Una hora del día con generación apreciable. El aviso se cuenta en horas de sol, no de reloj. | Apagado: 2 h. Cae 30 %: 4 h. |
| **Falla inyectada** | Una caída que se aplica a mano sobre un equipo sano, solo para medir cuánto tarda el aviso. No entrena nada. | 80 por tipo. |

## Demostración — 5:00

Abrir `app/index.html`; arranca en A revisar. Una persona maneja la máquina. «Modo exposición» agranda el texto para el proyector.

| Tiempo | Vista y acción | Qué decir |
|---|---|---|
| 0:00–2:00 | A revisar → cambiar el precio; abrir Tocota III | El ranking ordena a quién llamar primero. Cambiar los USD/MWh recalcula la plata, porque es un supuesto. La serie de Tocota III muestra lo que generó contra lo esperado por un modelo que no lo vio. Botón para ver los otros sitios. |
| 2:00–3:30 | Sitio nuevo → clic dentro del recuadro, Año 2023 y luego 2028; clic fuera | La cuenta: MW × horas × rendimiento = GWh. 2028 usa el clima promedio. Fuera del recuadro la app no estima. |
| 3:30–4:30 | Modelos | La tabla de los seis modelos. XGBoost elegido; la polinómica se dispara en la prueba. |
| 4:30–5:00 | Datos | De dónde sale todo: los parques y la exploración. |

Cierre: «Con datos públicos sabemos a quién llamar primero. Para saber por qué bajó hacen falta los datos del parque.»

## Ensayo

1. Una pasada leyendo las notas y otra sin leerlas, con cronómetro. Practicar los cambios de expositor en 2:50, 5:10 y 7:35.
2. Si la aplicación no responde en quince segundos, seguir con `docs/respaldo/index.html`.
3. Preguntas esperables: en `guion_defensa.md`.
