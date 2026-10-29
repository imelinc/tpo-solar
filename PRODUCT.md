# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

HTML, CSS y JavaScript estáticos, Plotly local, fuentes IBM Plex Sans locales. Python genera evidencia JSON y parquet. El dashboard abre sin conexión; no consulta APIs.

## Users

Principal: jurado y equipo en la defensa de Ciencia de Datos de UADE, 12/11/2026. Secundario: Gerencia Comercial y Técnica para entender desvíos de generación. Trabajo compartido de Ignacio Melinc, Matias Young, Francisco Fabrello y Malena Garcia Moraglio.

## Product Purpose

Explicar con evidencia de clase cómo estimar producción solar y evaluar una regla de alerta. Éxito: el jurado puede identificar datos, modelo, particiones, métricas, errores y límites en segundos, y navegar el análisis interactivo.

## Operating Context

Proyección en aula, defensa de 15 minutos, computadora con datos y recursos descargados. El usuario eligió diseño claro, minimalista y sobrio, y la composición **Laboratorio comparativo**: comparación de modelos junto a matriz de confusión.

## Capabilities and Constraints

- Recorrido: Resumen → Datos → Modelos → Evaluación → Casos.
- China: observación horaria, target numérico de potencia nominal y análisis diario de residuos.
- Argentina: comparación mensual de factor de capacidad. Sus métricas y modelo son distintos.
- Modelos limitados a los apuntes: regresión simple/múltiple, árbol, Random Forest y XGBoost.
- Clases 4 y 12 respaldan boxplot y residuos; clase 9 respalda matriz de confusión, accuracy, precision, recall y F1.
- El modelo, la unidad y las métricas de prueba se mantienen visibles. Cada vista enlaza a sus clases de Notion.
- No se entrena con datos sintéticos. Las inyecciones se identifican como experimentos de evaluación.
- No hay etiquetas operativas confirmadas para los casos reales. No se inventa una matriz para Argentina.
- Una observación inválida o ausente nunca equivale a normalidad.
- El déficit relativo al modelo y los USD ilustrativos no son recuperación ni ahorro demostrados.
- Toda evaluación es retrospectiva porque los períodos ya se exploraron.

## Evidence on Hand

`src/academico.py` produce `data/processed/defensa_evidencia.json` y las dos tablas parquet. `docs/alineacion_materia.md` contiene las fuentes curriculares. Las métricas se leen de la evidencia generada; no se tipean a mano en la aplicación.

## Product Principles

1. Primero la evidencia y su alcance, luego la interpretación.
2. Una sola variable para una cifra que aparece en varios lugares.
3. Comparar es más útil que decorar; incertidumbre visible.
4. Distinguir regresión, señal binaria y decisión de negocio.
5. Lenguaje argentino, unidades completas y gráficos legibles.

## Accessibility & Inclusion

Contraste alto, texto e indicadores además de color, controles nativos, foco visible, navegación por teclado, movimiento reducido y composición responsive. Modo exposición aumenta el texto auxiliar. Los gráficos tienen alternativas en tablas y textos.
