# Protocolo de modelado de la defensa

## Problema e hipótesis

**Estimar la producción solar a partir del clima permite identificar desvíos que justifican una revisión técnica.** El destinatario de negocio es la Gerencia Comercial y Técnica. El dashboard de la defensa muestra la evidencia y los límites de esa decisión.

Las técnicas y sus clases de origen están en [alineacion_materia.md](alineacion_materia.md).

## China: regresión horaria

- Observaciones reales de 10 plantas, entre julio de 2018 y junio de 2019.
- Target continuo: potencia medida / capacidad nominal (MW/MW).
- Features: irradiancia del sensor, temperatura, viento, hora, mes, día del año y planta como One-Hot Encoding.
- Se comparan regresión lineal simple, lineal múltiple, árbol de regresión, Random Forest y XGBoost.
- Entrenamiento: fechas anteriores al 01/04/2019. Selección: abril. Prueba: mayo–junio.
- Regla de selección: mínimo RMSE de validación. Si RF está a menos del 1% del mínimo, se prefiere RF.
- El preprocesamiento se ajusta dentro del pipeline. Las categorías de prueba no se usan para ajustar el codificador.
- station04 no se usa por su capacidad inconsistente. station09 se reserva como caso de aplicación de una referencia genérica.
- Entrenar producción sana excluye registros congelados y apagones con sol. La evaluación no elimina los apagones.
- MAE y RMSE se expresan en MW/MW. MSE tiene esas unidades al cuadrado. R² es adimensional; no es accuracy.

## Detector

Se agrega energía diaria a partir de potencia horaria. El residuo relativo es `(real − esperada) / esperada`. Una regla de boxplot señala valores debajo de `Q1 − 1,5 × IQR`.

La calibración usa predicciones fuera de muestra de entrenamiento, con cinco folds agrupados por mes. Es una adaptación de cross-validation para no repartir horas del mismo mes entre train y validación. Esa calibración no es una simulación cronológica: algunos folds entrenan con meses posteriores al evaluado.

Se excluyen de la decisión días con sensor demasiado bajo frente al clima externo, registros inválidos o referencia muy pequeña. Son reglas de calidad del proyecto, no nuevos modelos de minería. Todos esos días se cuentan y muestran como sin decisión. Una planta con capacidad no confiable no produce estimaciones económicas utilizables.

Para comprobar la regla se inyectan pérdidas en los registros de prueba, después de ajustar los modelos: 10%, 25%, 50% y 100%, duraciones de 1, 3 y 7 días, cinco semillas por combinación y planta. Cada episodio conserva identidad propia. **No se entrena con datos sintéticos.**

La matriz se calcula con días-planta con decisión. Las cifras agregan experimentos independientes, de modo que un día base puede aparecer en varios escenarios. Se muestran tamaño, prevalencia, exclusiones, precision, recall, F1 y accuracy. Las proporciones de falla las fija el benchmark y no equivalen a la prevalencia operativa real.

## Argentina

Se utiliza generación mensual CAMMESA y clima mensual Open-Meteo. Target: factor de capacidad. Se comparan regresión múltiple, árbol y RF sin identificar el parque como feature, para formar una referencia de parque típico.

- Train hasta 2023, validación 2024, prueba retrospectiva 2025–septiembre de 2026.
- Coordenadas provinciales y capacidades inválidas se excluyen.
- Los ceros posteriores al primer mes con producción se conservan para evaluación.
- La normalización por parque y el boxplot se calculan con su historia de entrenamiento; esa calibración es descriptiva y dentro de muestra.
- Parques sin al menos doce meses de referencia quedan sin decisión.
- No existen etiquetas operativas: **no se presenta una matriz de confusión sobre supuestas fallas argentinas confirmadas**.

## Alcance de las conclusiones

Los períodos ya se exploraron en versiones anteriores: toda nueva evaluación se presenta como retrospectiva, aunque se respete la separación de ajustes. Un R² alto no garantiza detectar pérdidas pequeñas. La matriz del benchmark evalúa la regla de alertas, no al regressor ni una política adicional de prioridad.

El déficit es energía observada por debajo de una referencia estimada. No confirma causa ni recuperación posible. Su traducción a USD utiliza un precio ilustrativo, no un ingreso observado ni un ahorro validado.
