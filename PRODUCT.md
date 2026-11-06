# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

HTML, CSS y JavaScript estáticos, Plotly local, fuentes IBM Plex Sans locales. Python genera evidencia JSON y parquet. El dashboard abre sin conexión; no consulta APIs.

## Users

Principal: jurado y equipo en la defensa de Ciencia de Datos de UADE, 12/11/2026. La pregunta es qué parque solar conviene mirar primero, y cuánta energía debería generar un parque en un lugar y un año. Trabajo compartido de Ignacio Melinc, Matias Young, Francisco Fabrello y Malena Garcia Moraglio.

## Product Purpose

Señalar qué parques solares argentinos rinden menos de lo esperado y cuánta plata está en juego, y estimar la energía de un sitio nuevo. Éxito: la gerencia sabe a qué parque mirar primero, y el jurado ve el modelo, las particiones, el error y los límites.

## Operating Context

Proyección en aula, computadora con datos locales. El recorrido es Parques, Sitio nuevo, Modelos y Datos.

## Capabilities and Constraints

- Recorrido: Parques → Sitio nuevo → Modelos → Datos. Cuatro vistas: la conclusión primero.
- Target: factor de capacidad mensual. La energía usa la potencia ingresada y las horas del mes.
- Modelos de los apuntes: regresión simple/múltiple/polinómica, árbol, Random Forest y XGBoost.
- La clase de matriz de confusión no se aplica: no hay fallas etiquetadas.
- El modelo, la unidad y las métricas de prueba quedan visibles. La página no enlaza apuntes ni páginas externas.
- Entrenamiento solo con mediciones reales.
- Un cero operativo se conserva. Un punto fuera del rango de parques se marca como caso límite.
- Toda evaluación es retrospectiva porque los períodos ya se exploraron.

## Evidence on Hand

`src/academico.py` produce `data/processed/defensa_evidencia.json` y la tabla de Argentina. `docs/alineacion_materia.md` contiene las fuentes curriculares. Las métricas se leen de la evidencia generada.

## Product Principles

1. Primero la evidencia y su alcance, luego la interpretación.
2. Una sola variable para una cifra que aparece en varios lugares.
3. Comparar es más útil que decorar; incertidumbre visible.
4. Decir cuándo el lugar o el año salen de lo observado.
5. Lenguaje argentino, unidades completas y gráficos legibles.

## Accessibility & Inclusion

Contraste alto, texto e indicadores además de color, controles nativos, foco visible, navegación por teclado, movimiento reducido y composición responsive. Modo exposición aumenta el texto auxiliar. Los gráficos tienen alternativas en tablas y textos.
