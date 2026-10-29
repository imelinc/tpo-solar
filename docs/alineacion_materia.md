# Alcance académico de la defensa

Fuente curricular: apuntes de **Ciencia de Datos**, **2do CUATRI 2026**, consultados el 29/10/2026. Se leyeron las doce clases devueltas por la base «Clases y Apuntes» de esa materia y «Criterios para los exámenes». Las fechas de edición de Notion no se tomaron como prueba de precedencia: se contrastaron las secciones, incluida la actualización de regresión de la clase 12.

Defensa: **12/11/2026**. Equipo informado por el usuario: **4 integrantes**. La consigna escrita solicita 5–6; confirmar con el docente la aceptación de cuatro. Nombres y responsabilidades pendientes de respuesta del equipo.

## Decisiones

El dashboard está dirigido principalmente a la defensa. Mantiene China (observaciones horarias) y Argentina (comparación mensual), con diseño claro, minimalista y sobrio. Cada visualización debe identificar fuente, población, período, modelo y tipo de evaluación. Las métricas de regresión y clasificación se muestran por separado.

| Contenido aplicado | Evidencia en los apuntes | Uso en el proyecto |
|---|---|---|
| Pipelines, ETL, latencia y frecuencia | [Clase 2](https://www.notion.so/3bb096bfe0b280e59278f280f481a77a) | Diagrama desde fuentes hasta dashboard; distinguir frecuencia horaria y mensual. |
| Calidad: completitud, consistencia y validez | [Clase 3](https://www.notion.so/3c9096bfe0b280f3bafef6695b024471) | Duplicados, sensores, capacidades y datos ausentes; desconocido no significa normal. |
| CRISP-DM y EDA | [Clase 4](https://www.notion.so/3c9096bfe0b28052a107eb1c1ebe53b7) | Recorrido de negocio, datos, preparación, modelado, evaluación y aplicación. |
| Histograma, boxplot, dispersión, correlación y heatmap | [Clase 4](https://www.notion.so/3c9096bfe0b28052a107eb1c1ebe53b7) | Exploración interactiva y distribución de residuos. |
| Supervisado vs no supervisado | [Clase 5](https://www.notion.so/3d0096bfe0b280dd9808caf91e24708e) | Potencia medida real como target de regresión. |
| Árbol CART, poda, promedio en hojas | [Clase 6](https://www.notion.so/3d6096bfe0b2807fba88e0b0a48ff2d4) | Árbol de regresión interpretable, comparado con ensambles. |
| Random Forest, bagging, importancia y XGBoost | [Clase 7](https://www.notion.so/3ec096bfe0b2806b96d9e1d626263337) | Comparación de modelos con los mismos datos y particiones. |
| Matriz de confusión, accuracy, precision, recall, F1 | [Clase 9](https://www.notion.so/3ec096bfe0b280ab83c7d946b9984f5f) | Evaluación del detector sobre casos de prueba con etiqueta conocida; matriz calculada desde filas, nunca inventada. |
| Variables derivadas y One-Hot Encoding | [Clase 10](https://www.notion.so/3f3096bfe0b28065aa31d0f0b43d729b) | Hora, mes y día del año; planta como categoría sin orden artificial. |
| Split, cross-validation, leakage y bias-variance | [Clase 11](https://www.notion.so/3fb096bfe0b281a595a4fa720f25134e) | Separar selección y evaluación; mostrar train/validación/test y límites de reutilizar historia ya explorada. |
| Regresión simple/múltiple, residuos, MAE, MSE, RMSE y R² | [Clase 12](https://www.notion.so/401096bfe0b280d98850da56a4101d05) | Línea base, comparación de regresores y diagnóstico del error con unidades explícitas. |
| Interpretar y comparar, no entrenar con datos sintéticos | [Criterios del docente](https://www.notion.so/401096bfe0b2817db3f6c84d61adc01f) | Entrenamiento solo con mediciones reales. Inyecciones de caída únicamente como prueba controlada del detector, claramente identificadas. |

## Técnicas que se retiran de la versión de defensa

No se encontró desarrollo curricular de PVWatts/híbrido físico, CUSUM, Isolation Forest, MAD como detector o optimización de intervalos de limpieza. No se presentan como técnicas de la materia ni se mantienen como motor del nuevo dashboard. Ridge/Lasso aparecen mencionados como remedio a multicolinealidad, pero no desarrollados: se prefiere la regresión lineal enseñada explícitamente.

La regla de boxplot **Q1 − 1,5 × IQR**, sí explicada en clase 4, permite señalar residuos bajos. Es una regla de detección sobre un regressor, no un clasificador supervisado entrenado sobre etiquetas artificiales. Se debe validar con su propia matriz de confusión y explicar la diferencia.

Los cálculos de energía, fechas, unidades y traducción a USD son transformaciones de datos y cuentas del dominio, no nuevos algoritmos de minería. Toda cifra monetaria debe decir «estimación ilustrativa» y mostrar precio y alcance; no se presenta como ingreso real ni ahorro demostrado.

## Reglas de honestidad

- Los meses de 2019 ya se examinaron en el trabajo anterior. La nueva evaluación será **retrospectiva**, aunque cada ajuste respete sus particiones. No se anuncia como una nueva prueba ciega.
- Las fallas sintéticas son pruebas controladas sobre observaciones reales; no prueban la causa de los casos reales ni la precisión en producción.
- En las matrices, los días sin datos suficientes se excluyen con un contador visible; nunca se convierten en verdaderos negativos.
- Los modelos de árbol no extrapolan fuera del rango observado. Se declara el único año y la estacionalidad incompleta.
- Argentina conserva ceros operativos como observaciones; una ausencia de reporte y un cero no son equivalentes.
- El informe `revision_tpo.md` es el diagnóstico de la versión anterior. Los nuevos resultados deben tener su propia evidencia y no heredar cifras del híbrido.
