# Protocolo de modelado

## Pregunta

¿Qué parque solar argentino conviene mirar primero? Para responderla hace falta saber cuánta energía mensual debería generar un parque en un lugar, en un año dado, con una potencia instalada.

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

Se comparan regresión lineal simple, lineal múltiple, polinómica de grado 2, árbol de regresión, Random Forest y XGBoost. Gana el menor RMSE de validación. Si empatan, queda el más simple.

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

## Parques a revisar

1. Lo esperado de cada parque sale de cinco modelos, cada uno entrenado hasta 2023 sin un grupo de parques. Se usa el modelo que no vio ese parque.
2. Rinde contra el modelo = factor observado / factor esperado. Rinde contra los vecinos = ese valor / la mediana de la provincia ese mes.
3. Estados de cada mes: `arranque` (primeros 6 meses o tras cambiar la potencia), `sin_vecinos` (menos de 3 parques comparables), `parque` (ambos por debajo del 80 %), `zona` (la mediana de la provincia por debajo del 80 %) o `normal`.
4. Señal: dos meses seguidos en estado `parque`. Una ampliación se suma a su sitio.
5. Plata en juego: energía faltante × USD 60/MWh, un supuesto editable.
6. Sensibilidad: umbrales de 75 %, 80 % y 85 %, y caídas inyectadas de 10 a 50 % en tres meses. Las caídas solo miden la regla.

## Límites

La evaluación es retrospectiva. Un R² de la prueba temporal describe los mismos parques en años posteriores. El RMSE por parque describe lugares no vistos, con clima de la región que otros parques sí pudieron aportar. La energía estimada no es un ingreso ni una producción ya medida. La energía faltante es una diferencia con el modelo: no prueba una falla ni un ahorro.
