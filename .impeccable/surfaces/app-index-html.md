---
version: 1
slug: "app-index-html"
primary_target: "app/index.html"
related_targets: ["app/estilos.css","app/tablero.js"]
---

Scope: dashboard de defensa de Ciencia de Datos, modo Operate. Solo Argentina. Audiencia: jurado y cuatro integrantes en aula, 12/11/2026, demo de cinco minutos. Recorrido: Atlas (datos y exploración) → Modelos → Sitio → Parque. Sin bandera ni selector de país. La página no enlaza apuntes.

## Direction contract

THESIS: Los parques son estrellas de una carta: el lugar ordena todo y la consulta de un sitio es apuntar un retículo sobre la carta. Rechaza el tablero de tarjetas de KPI con gráficos genéricos.

OWN-WORLD: Fondo azul noche (#0A1021) con placas índigo (#16233D) y graticula de líneas finas; puntos de tiza (#F2F2E9) con diámetro por potencia en una escala fija con leyenda; anotaciones y retículo en rojo de linterna (#FF4D2E), brillo ámbar (#FFB36B) para el factor estimado. Nombres en EB Garamond itálica local; datos, rótulos y cifras en IBM Plex Sans tabular con versalitas espaciadas. Marcos de un pixel con nodos en las esquinas.

STORY: El jurado ve primero dónde están los 56 parques y qué dice el dato; después qué modelo se eligió y con qué error; después apunta un sitio y lee la energía con sus límites; al final ve un parque real contra su estimación.

FIRST VIEWPORT: Carta de Argentina a la izquierda, a toda la altura, con graticula rotulada, parques como estrellas y el campo de factor estimado como nebulosa ámbar dentro del rango de entrenamiento. A la derecha, el índice de parques y la ficha del modelo elegido con RMSE, MAE y R² de prueba.

FORM: Atlas estelar (challenger elegido por el usuario, catálogo notation-diagram-systems-star-atlas), seed 79f98652. Raises: estados por forma de línea (observado llena, estimado punteada), un único color de alerta para fuera de rango y ceros, aparato metodológico en el margen junto al dato, grilla de series por parque ligada a la carta.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

Señal: clic en la carta coloca el retículo, traza la línea punteada al parque cuyo clima se copia y recalcula la energía.
