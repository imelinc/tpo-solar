---
version: 1
slug: "app-index-html"
primary_target: "app/index.html"
related_targets: ["app/estilos.css","app/tablero.js"]
---

Scope: dashboard de defensa de Ciencia de Datos, modo Operate. Solo Argentina. Audiencia: jurado y cuatro integrantes en aula con luces prendidas, 12/11/2026, demo de cinco minutos. Recorrido: Atlas (datos y exploración) → Modelos → Sitio → Parque. Sin bandera ni selector de país. La página no enlaza apuntes. Rediseño total pedido el 01/11/2026: el mundo oscuro de carta estelar y la tipografía (Garamond itálica + Plex) quedan descartados; se conservan datos, ids, funciones y límites de PRODUCT.md.

## Direction contract

THESIS: El dashboard es la hoja de un informe de laboratorio sobre papel milimetrado, corregida con birome: lo medido se escribe en tinta negra, lo que estima el modelo en azul y lo que el docente marca (fuera de rango, ceros, modelo elegido) en rojo. Rechaza el tablero oscuro de tarjetas con acento de neón y la carta estelar anterior.

OWN-WORLD: Fondo de papel milimetrado verde muy pálido (#F5F9F4, grilla verde #2E9C6A de 16 px y 80 px), marcos de lámina en tinta negro-verdosa (#111B16) de 1 px sin radio, cajetín de plano técnico arriba con celdas rotuladas. Tres tintas con papel funcional fijo: negro = observado, azul birome (#1F3FBF) = estimado, rojo corrección (#CF1F19) = alerta/cero/elegido. Barlow Condensed 700 para títulos y rótulos, Barlow para cuerpo y cifras tabulares. Sin itálica. La carta de Argentina se dibuja sobre graticula verde, puntos de relevamiento negros con anillo para ≥50 MW.

STORY: El jurado lee primero la hoja: cajetín con el modelo elegido y su error de prueba; ve dónde están los 56 parques; entiende por qué ese modelo ganó y con qué error; apunta un sitio y lee la energía como resultado de un cálculo con su límite; cierra con un parque real, observado contra estimado.

FIRST VIEWPORT: Barra fija con marca, cuatro vistas como celdas y los controles Grilla y Modo exposición. Debajo el cajetín: a la izquierda el título de la vista (Barlow Condensed 700, ~60 px) con su bajada; a la derecha una grilla de celdas rotuladas con Modelo, RMSE de prueba, MAE, R², RMSE de parque nuevo y alcance. Más abajo la carta de Argentina a la izquierda a altura de pantalla y el índice de parques a la derecha.

FORM: Informe de laboratorio sobre papel milimetrado, candidato 4 de la lista propia (1 carta IGN, 2 boletín SMN, 3 tabla de mareas, 4 informe milimetrado, 5 despacho CAMMESA, 6 mapa del subte, 7 almanaque), seed 2ab30e04. Raise de crouwel-grid-specimen (grilla visible como estado real): el botón Grilla muestra u oculta el papel milimetrado, y el cálculo de Sitio ya cae en la celda de 0,2° más próxima.

Señal: clic en la carta coloca el retículo rojo, traza la línea punteada al parque cuyo clima se copia y recalcula la energía. Un solo momento de movimiento: las figuras de cada vista entran escalonadas al cambiar de vista.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
