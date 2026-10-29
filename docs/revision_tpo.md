# Estado de la revisión del TPO

Actualizado: 29/10/2026. Este archivo reemplaza el diagnóstico inicial para reflejar el alcance curricular confirmado por el usuario.

## Requisitos y evidencia necesaria

| Requisito | Evidencia verificable |
|---|---|
| Problema y valor de negocio | Hipótesis en el plan, resumen de la aplicación y guion. |
| Diagrama de arquitectura | Fuentes → preparación → modelo → evaluación → aplicación, vinculado a clases 2 y 4. |
| Análisis exploratorio | Notebook 02 con cobertura, histogramas, boxplots, dispersión y correlación. |
| Técnica y justificación | Comparación de modelos de clase, selección por validación y métricas con unidades. |
| Conclusiones y storytelling | Resultados reproducibles, límites explícitos y exposición de 15 minutos. |
| Aplicación funcional | Navegación, filtros, gráficos, matriz de confusión y evidencia curricular visible. |
| Presentación sin red | Scripts, datos, tipografía y biblioteca locales; copia de gráficos y entorno preparado. |
| Participación | Cuatro integrantes con trabajo compartido y participación oral. La consigna pide 5–6: confirmar excepción con el docente. |

## Correcciones que exige la revisión

- Una identidad por simulación para no mezclar duraciones o semillas al medir demora.
- La misma regla evaluada debe alimentar los estados de la aplicación.
- Un dato ausente o inválido no puede aparecer como funcionamiento normal.
- Separar entrenamiento sano y evaluación, conservando apagones y ceros operativos al evaluar.
- Seleccionar modelos con validación; declarar la reutilización retrospectiva de períodos previamente explorados.
- No anunciar ahorro o recuperación demostrados a partir de una diferencia con el modelo.
- Ejecutar realmente la descarga desde 01, con rutas canónicas y dependencias declaradas.
- Mostrar las fuentes y clases que respaldan cada herramienta, sin técnicas ajenas a los apuntes.

## Evidencia vigente

El cálculo reproducible de la defensa está en `src/academico.py`; produce `defensa_evidencia.json`, `defensa_diario.parquet` y `defensa_argentina.parquet`. Los notebooks 01–05 explican y ejecutan ese recorrido. Las pruebas de decisiones y matrices están en `tests/test_academico.py`.

La revisión visual e interactiva del resultado final debe registrarse por separado; una verificación de sintaxis no prueba el comportamiento del navegador ni la legibilidad en proyector.
