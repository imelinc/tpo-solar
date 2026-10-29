# Protocolo de modelado

## Pregunta

¿Cuánta energía mensual generaría un parque solar en un lugar de Argentina, en un año dado, con una potencia instalada?

El año elige el clima. No pronostica el tiempo de un año que todavía no ocurrió.

## Datos

- Generación mensual CAMMESA y potencia habilitada.
- Coordenadas del parque. Se excluye el centroide de provincia.
- Clima mensual Open-Meteo en esas coordenadas: irradiación, temperatura máxima y nubosidad.
- Target: factor de capacidad, energía / (potencia × horas del mes).
- Se dejan afuera factores mayores a 0,45 y los meses en que CUM2FV, PINFFV o VANGFV no tienen la potencia del período 2022–septiembre 2025.
- Los meses anteriores a la primera generación se quitan. Los ceros posteriores se conservan en la evaluación. El entrenamiento usa meses con generación.

## Modelos

Entradas: irradiación, latitud, longitud, temperatura máxima, nubosidad y mes. El mes va en one-hot. En la regresión lineal, enero es la referencia. La regresión simple usa solo la irradiación. El identificador del parque no entra.

Se comparan regresión lineal simple, lineal múltiple, árbol de regresión, Random Forest y XGBoost. Gana el menor RMSE de validación. Si empatan, queda el más simple.

- Entrenamiento: hasta 2023.
- Validación: 2024.
- Prueba retrospectiva: desde 2025.
- Además, cinco grupos por parque sobre el entrenamiento. Ese RMSE describe un parque que no entró al ajuste. No se usa para elegir.

## Consulta de un sitio

1. La potencia tiene que ser mayor que cero.
2. El punto se acerca a la celda de 0,2° más próxima dentro del rectángulo de entrenamiento.
3. El clima de esa celda es el del parque más cercano. Si el año pedido está en el archivo, se usa ese año y, si falta un mes, el promedio. Si el año no está, todo el año usa el promedio anterior a 2024.
4. El modelo devuelve doce factores de capacidad. La energía del mes es factor × MW × horas. El total anual suma esos meses.
5. Fuera del rectángulo, la pantalla marca el caso límite y muestra la celda del borde.

## Límites

La evaluación es retrospectiva. Un R² de la prueba temporal describe los mismos parques en años posteriores. El RMSE por parque describe lugares no vistos, con clima de la región que otros parques sí pudieron aportar. La energía estimada no es un ingreso ni una producción ya medida.
