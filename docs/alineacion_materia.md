# Alcance académico de la defensa

Fuente curricular: apuntes de **Ciencia de Datos**, **2do CUATRI 2026**, consultados el 29/10/2026. Se leyeron las doce clases devueltas por la base «Clases y Apuntes» de esa materia y «Criterios para los exámenes». Las fechas de edición de Notion no se tomaron como prueba de precedencia: se contrastaron las secciones, incluida la actualización de regresión de la clase 12.

Defensa: **12/11/2026**. Equipo informado por el usuario: **4 integrantes**. La consigna escrita solicita 5–6; confirmar con el docente la aceptación de cuatro. Integrantes: Ignacio Melinc, Matias Young, Francisco Fabrello y Malena Garcia Moraglio. Trabajo compartido en todas las etapas; el reparto del guion es solo de exposición.

## Decisiones

La defensa estima la generación mensual de un parque solar en Argentina. El modelo usa ubicación y clima, y devuelve un factor de capacidad. La energía es ese factor por la potencia instalada y por las horas del mes. Cada vista identifica fuente, período, modelo y partición.

| Contenido aplicado | Evidencia en los apuntes | Uso en el proyecto |
|---|---|---|
| Pipelines, ETL, latencia y frecuencia | [Clase 2](https://www.notion.so/3bb096bfe0b280e59278f280f481a77a) | CAMMESA mensual y clima Open-Meteo, una sola frecuencia, hasta el dashboard local. |
| Calidad: completitud, consistencia y validez | [Clase 3](https://www.notion.so/3c9096bfe0b280f3bafef6695b024471) | Coordenadas, potencia ampliada y ceros. Un dato ausente no se trata como mes normal. |
| CRISP-DM y EDA | [Clase 4](https://www.notion.so/3c9096bfe0b28052a107eb1c1ebe53b7) | Pregunta, preparación, modelos, prueba y consulta de un sitio. |
| Histograma, boxplot, dispersión, correlación y heatmap | [Clase 4](https://www.notion.so/3c9096bfe0b28052a107eb1c1ebe53b7) | Serie observado contra estimado y mapa de parques. |
| Supervisado vs no supervisado | [Clase 5](https://www.notion.so/3d0096bfe0b280dd9808caf91e24708e) | Factor de capacidad medido como target de regresión. |
| Árbol CART, poda, promedio en hojas | [Clase 6](https://www.notion.so/3d6096bfe0b2807fba88e0b0a48ff2d4) | Árbol de regresión comparado con el resto. |
| Random Forest, bagging, importancia y XGBoost | [Clase 7](https://www.notion.so/3ec096bfe0b2806b96d9e1d626263337) | Misma partición para los cinco modelos. |
| Matriz de confusión, accuracy, precision, recall, F1 | [Clase 9](https://www.notion.so/3ec096bfe0b280ab83c7d946b9984f5f) | No se aplica: CAMMESA no trae fallas etiquetadas y no se inventa una matriz. |
| Variables derivadas y One-Hot Encoding | [Clase 10](https://www.notion.so/3f3096bfe0b28065aa31d0f0b43d729b) | Mes en one-hot. El parque no entra como categoría, para poder consultar un lugar nuevo. |
| Split, cross-validation, leakage y bias-variance | [Clase 11](https://www.notion.so/3fb096bfe0b281a595a4fa720f25134e) | 2024 elige el modelo. La prueba es desde 2025. Un grupo por parque mide un sitio no visto y no elige el modelo. |
| Regresión simple/múltiple, residuos, MAE, MSE, RMSE y R² | [Clase 12](https://www.notion.so/401096bfe0b280d98850da56a4101d05) | Línea base de irradiación, comparación y error en factor de capacidad. |
| Interpretar y comparar, no entrenar con datos sintéticos | [Criterios del docente](https://www.notion.so/401096bfe0b2817db3f6c84d61adc01f) | Entrenamiento solo con generación y clima observados. |

## Energía de un sitio nuevo

El año no entra como causa. Elige el clima: si ese año está medido, se copia el clima del parque más cercano; si no está, se usa el promedio mensual de los años de entrenamiento. La consulta del dashboard cae en una celda de 0,2°. Fuera del rectángulo de parques de entrenamiento, el número es un caso límite: un árbol no extrapola.

Pasar de factor de capacidad a MWh o GWh es una cuenta del dominio. Hace falta la potencia en MW.

## Reglas de honestidad

- La prueba ya fue explorada en versiones anteriores. Se presenta como retrospectiva.
- Los modelos de árbol no extrapolan fuera del rango de latitud y longitud visto en el entrenamiento.
- Los ceros operativos se conservan. Una ausencia de reporte y un cero no son equivalentes.
- El clima de un sitio nuevo es el del parque más cercano. A más de 150 km la copia es débil.
- `revision_tpo.md` diagnostica la versión anterior. Las cifras de esta defensa salen de `defensa_evidencia.json`.

[Diagrama de arquitectura y contrato de ejecución](arquitectura.md)
