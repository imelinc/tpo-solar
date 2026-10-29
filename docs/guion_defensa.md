# Defensa del 12/11/2026 · 15 minutos

Equipo de trabajo compartido: **Ignacio Melinc, Matias Young, Francisco Fabrello y Malena Garcia Moraglio**. Este reparto es solo de exposición y se puede intercambiar al ensayar.

| Expositor propuesto | Clics | Duración |
|---|---|---:|
| Ignacio | Resumen: pregunta, recorrido de cuatro pasos, China frente a Argentina y matriz del 50% | 3:00 |
| Matias | Datos: diagrama de cinco pasos, station04 y un gráfico de EDA | 3:00 |
| Francisco | Modelos: validación, luego prueba; China y un cambio a Argentina | 3:30 |
| Malena | Evaluación al 50% y al 10%; Casos en station09 y un parque | 4:00 |
| Todos | Margen para transición y cierre | 1:30 |

## Apertura

«Una planta puede seguir generando mientras rinde por debajo de una referencia. ¿Podemos estimar cuánto debería producir según el clima y señalar qué conviene revisar?»

La hipótesis es acotada: estimar generación y señalar desvíos. No se promete diagnosticar la causa ni demostrar ahorro por reparación.

## Datos y arquitectura

Clases 2–4: extracción, limpieza, transformación, modelado, evaluación y presentación. PVOD entrega potencia horaria y sensores de diez plantas chinas. CAMMESA permite comparación mensual argentina. Open-Meteo aporta contexto meteorológico. No se mezclan frecuencias ni unidades.

En Resumen, el recorrido de cuatro pasos alcanza para la apertura. El diagrama de cinco pasos está en Datos: Fuentes → Preparación → Modelado → Evaluación → Aplicación. Ahí también está la capacidad inconsistente de station04 y, en Exploración, el boxplot y la dispersión irradiancia/potencia. Un outlier indica dónde investigar; no demuestra una causa.

## Modelos

La potencia es numérica: es regresión. Comparar la línea base simple, la múltiple, el árbol, RF y XGBoost. El modelo se elige con abril, no con la prueba de mayo–junio. Leer el resultado desde la tabla generada, no memorizar números de otra versión.

- Árbol: reglas interpretables, riesgo de sobreajuste.
- RF: promedio de árboles, menor varianza y mayor costo de memoria.
- XGBoost: correcciones secuenciales, requiere validación.
- Regresión múltiple: referencia sencilla; en Argentina puede competir o ganar.

MAE y RMSE tienen unidades del target. R² no es accuracy. Mostrar train, validación y prueba para hablar de generalización, como en clases 11–12.

## Evaluación

La regla es el límite inferior del boxplot de residuos (clase 4). La matriz de confusión pertenece a esa regla, no a la regresión.

Elegir una caída controlada de 50%. Leer TP, FN, FP y TN; explicar precision, recall y F1 con sus denominadores. Cambiar a 10% para mostrar el límite real. Los días sin decisión se excluyen con un contador visible.

Las caídas se inyectan solamente para evaluar: el entrenamiento utiliza mediciones reales. La prevalencia y los experimentos repetidos pertenecen al benchmark; no son una tasa de fallas observada en campo.

## Casos y cierre

station09: referencia genérica porque no se usa para aprender producción sana. Mostrar observación, esperado y avisos. Hablar de desvío estimado, no de causa confirmada.

Argentina: mostrar su modelo y sus propias métricas, frecuencia mensual y un parque con meses de cero. No hay etiquetas operativas: no inventar una matriz de confusión de fallas reales.

«La aplicación organiza evidencia para decidir qué revisar. Su utilidad y sus límites dependen del error del modelo, la calidad de los sensores y la evaluación de sus alertas. Para confirmar causas hacen falta registros técnicos independientes.»

## Preguntas para ensayar

1. ¿Por qué es regresión si hay alertas? La primera etapa estima un número; la regla posterior produce la señal binaria.
2. ¿Por qué no alcanza con accuracy? Puede ocultar una clase minoritaria; leer precision, recall y matriz.
3. ¿La prueba es ciega? Es retrospectiva: esos meses ya se exploraron. Los ajustes actuales respetan las particiones, pero no se inventa una nueva independencia.
4. ¿Se entrenó con datos sintéticos? No; se usan escenarios controlados solo después del entrenamiento para evaluar la regla.
5. ¿La importancia de una variable demuestra causa? No, expresa uso predictivo del modelo.
6. ¿Se puede anunciar ahorro? Se muestra déficit respecto de una referencia y, si se convierte a USD, un valor ilustrativo con precio explícito.
7. ¿Qué pasa sin sensor? No se toma una decisión confiable y eso se muestra; no se pinta verde.

## Ensayo sin conexión

Abrir `app/index.html` antes de empezar. Recorrer Resumen → Datos → Modelos → Evaluación → Casos. En Modelos, leer la fila elegida y abrir el detalle para MAE, MSE, RMSE y R². En Evaluación, pasar de 50% a 10%. En Casos, station09 y después Argentina. Si algo no se resuelve en quince segundos, abrir `docs/respaldo/index.html`.

El respaldo tiene ocho pantallas y seis figuras. Cubren la pregunta, el diagrama, el EDA, la elección del modelo, la matriz, el límite de la regla, los dos casos y la conclusión. Eso alcanza los requisitos de problema, arquitectura, exploración, técnica, conclusiones y aplicación de `revision_tpo.md`. No afirma que el docente haya aceptado el grupo de cuatro: la consigna escrita pide 5–6.
