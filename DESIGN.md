---
name: Solar / Datos
description: Evidencia científica clara, minimalista y sobria.
colors:
  ground: "#f4f6f7"
  surface: "#fff"
  raised: "#f5f8f9"
  active: "#e7edef"
  border: "#e3eaed"
  rule: "#edf1f3"
  text: "#18252d"
  muted: "#52636d"
  accent: "#227a6c"
  positive: "#1d7353"
  negative: "#b4313b"
  warning: "#815619"
  secondary-data: "#2f70bb"
  reference-data: "#91a7b2"
  field-border: "#b9c9d0"
  focus: "#347e97"
  evidence: "#eff5f7"
  evidence-text: "#1b4d5d"
  matrix: "#edf5f6"
  matrix-error: "#fbf0f0"
typography:
  headline:
    fontFamily: "Plex, 'Helvetica Neue', sans-serif"
    fontSize: "28px"
    fontWeight: 500
    lineHeight: 1.25
    letterSpacing: "-.025em"
  title:
    fontFamily: "Plex, 'Helvetica Neue', sans-serif"
    fontSize: "17px"
    fontWeight: 500
    lineHeight: 1.35
  body:
    fontFamily: "Plex, 'Helvetica Neue', sans-serif"
    fontSize: "15px"
    lineHeight: 1.5
  label:
    fontFamily: "Plex, 'Helvetica Neue', sans-serif"
    fontSize: "12px"
    lineHeight: 1.5
  metric:
    fontFamily: "Plex, 'Helvetica Neue', sans-serif"
    fontSize: "28px"
    fontWeight: 400
    lineHeight: 1.4
rounded:
  tag: "4px"
  matrix: "5px"
  control: "6px"
  panel: "8px"
  sheet: "16px"
spacing:
  inline: "7px"
  control: "8px 12px"
  field: "7px 11px"
  panel: "21px 22px"
  evidence: "14px 18px"
  block: "24px"
components:
  button-quiet:
    backgroundColor: "{colors.raised}"
    textColor: "{colors.text}"
    rounded: "{rounded.control}"
    padding: "{spacing.control}"
  button-quiet-hover:
    backgroundColor: "{colors.active}"
  field:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    rounded: "{rounded.control}"
    padding: "{spacing.field}"
  nav-active:
    backgroundColor: "{colors.active}"
    textColor: "{colors.text}"
    rounded: "{rounded.control}"
    padding: "10px 14px"
  tag:
    backgroundColor: "{colors.raised}"
    textColor: "{colors.muted}"
    rounded: "{rounded.tag}"
    padding: "5px 9px"
  panel:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.panel}"
    padding: "{spacing.panel}"
  evidence-strip:
    backgroundColor: "{colors.evidence}"
    textColor: "{colors.muted}"
    rounded: "{rounded.control}"
    padding: "{spacing.evidence}"
  matrix-cell:
    backgroundColor: "{colors.matrix}"
    textColor: "{colors.text}"
    rounded: "{rounded.matrix}"
    padding: "18px 15px"
  matrix-cell-error:
    backgroundColor: "{colors.matrix-error}"
---

# Design System: Solar / Datos

## Overview

**Creative North Star: "Laboratorio comparativo"**

Laboratorio comparativo organiza el análisis como una hoja de trabajo clara, minimalista y sobria. El marco frío y la hoja blanca sostienen la información; la jerarquía depende de tipografía, alineación y espacio. El color identifica datos y estados.

Los controles son discretos y familiares. La evidencia conserva el modelo, las métricas, la unidad y el alcance junto a la lectura; los estados desconocidos se expresan con texto. La precisión visual acompaña la precisión de las cifras.

**Key Characteristics:**

- Hoja enmarcada sobre fondo frío.
- Tipografía Plex local y cifras tabulares.
- Paneles planos con bordes suaves.
- Color funcional para series, selección y estados.

La dirección fue elegida por el usuario el 29/10/2026: `.impeccable/mocks/decision/laboratorio.html`, referencia `seed:6a8420f350ea078c`; base de app Framed sheet, semilla 1409239049. El frontmatter captura los valores actuales de `app/estilos.css`; las series se contrastaron con `app/tablero.js` y los componentes con `app/index.html`. Alcance: inspección de fuente. **Pendiente: verificación visual del render y uso real**; no se obtuvieron capturas porque la apertura de `file://` fue bloqueada. Este documento no certifica que la interfaz esté lista para entrega.

## Colors

Paleta fría y contenida; los neutros forman la estructura y los acentos comunican evidencia.

### Primary

- **Verde petróleo** (`accent`): datos observados, modelo elegido, enlaces y selección de planta.

### Secondary

- **Azul analítico** (`secondary-data`): segunda serie de métricas, como recall.
- **Gris de referencia** (`reference-data`): línea del valor esperado, distinta del observado.

### Neutral

- **Marco frío** (`ground`) y **hoja blanca** (`surface`): fondo exterior y área principal.
- **Niebla de apoyo** (`raised`) y **selección gris** (`active`): controles, notas y navegación activa.
- **Tinta** (`text`) y **pizarra** (`muted`): lectura principal y contexto.
- **Borde** (`border`), **regla** (`rule`) y **borde de campo** (`field-border`): separación estructural.
- **Banda de evidencia** (`evidence`, `evidence-text`): agrupa contexto y nombre del modelo.

Los colores semánticos `positive`, `negative` y `warning` conservan roles de estado; `warning` está declarado en CSS y no tiene uso visible asignado en los componentes inspeccionados. `matrix` y `matrix-error` distinguen celdas de aciertos y errores; `focus` señala interacción por teclado.

La defensa usa el marco de Argentina: fondo `#c5dff3` y franja celeste `#74acdf`. Las series siguen en verde petróleo y azul.

**The Color With Evidence Rule.** Todo estado debe llevar texto o etiqueta además del color.

## Typography

**Headline / Body Font:** IBM Plex Sans, registrada localmente como `Plex`, con Helvetica Neue y sans-serif como respaldo. Archivos en `app/fonts/`, pesos disponibles 400, 500 y 600; licencia OFL local. No hay familia mono separada.

La jerarquía de títulos, cuerpo, etiquetas y métricas figura en el frontmatter. Cifras tabulares en todo el cuerpo; negritas de énfasis en peso 600. El título principal baja a 25 px hasta 850 px y a 24 px hasta 640 px. Las cifras se mueven entre 25 y 30 px según componente. Textos de contexto usan 12–14 px, con algunas etiquetas móviles de 11 px.

Los párrafos de cabecera tienen un máximo de 75ch; notas y alcances usan 65–70ch. El modo exposición aumenta el cuerpo a 17 px, referencias a 14 px y banda de evidencia a 15 px; en móvil el cuerpo vuelve a 15 px.

**The Stable Numbers Rule.** Las cifras conservan alineación tabular y se actualizan sin contadores animados.

## Layout

Hoja enmarcada: barra lateral fija de 228 px, barra superior de 64 px y hoja blanca de ancho máximo 1680 px. La hoja usa relleno de 30 px 32 px 24 px, con separación de bloques tomada de `spacing.block`. Los paneles comparten bordes y líneas de lectura; no flotan sobre el marco.

El recorrido es Modelos → Sitio → Serie. Modelos pone la comparación a la izquierda y la lectura del modelo a la derecha. Sitio y Serie usan la grilla principal. Se apilan a 1100 px. Los gráficos permiten zoom, desplazamiento y hover. La página no muestra enlaces a los apuntes.

- Desde 1600 px: relleno principal de 36 px 42 px; gráficos estándar de 340 px de alto.
- Hasta 1100 px: lateral de 192 px, relleno principal de 24 px y paneles de 17 px; se reduce densidad horizontal.
- Hasta 850 px: navegación horizontal desplazable, lateral en flujo y sin margen izquierdo; hoja con esquinas de 12 px.
- Hasta 640 px: hoja sin radio ni margen exterior, relleno de 24 px 16 px y grillas principales de una columna. Selectores y fecha alcanzan 44 px; botón discreto de 40 px. La matriz conserva dos columnas de predicción y una de etiquetas. Las tablas mantienen un mínimo de 480 px dentro del contenedor con scroll.

El modo exposición usa lateral de 200 px en escritorio y vuelve al flujo móvil. El modo impresión oculta navegación y controles. Estas reglas están comprobadas en fuente; el ajuste real a pantallas y proyección queda pendiente de render.

## Elevation & Depth

La interfaz es plana: no hay sombras de panel ni de control. La profundidad surge del marco, la hoja blanca, superficies de apoyo y bordes finos. El foco usa un contorno sólido de 3 px con desplazamiento de 3 px; es una señal de interacción, no una sombra.

**The Flat Sheet Rule.** Los paneles se distinguen por borde, espacio y tono; no por elevación decorativa.

## Shapes

Esquinas suaves según escala del frontmatter: hoja más abierta, paneles intermedios y controles más contenidos. Etiquetas y celdas conservan radios menores. Separadores de 1 px ordenan tablas, métricas y navegación explicativa. Puntos de estado circulares acompañan texto; no funcionan como única señal.

## Components

### Buttons

Botones discretos de superficie secundaria, texto de tinta y radio de control. Tipografía de 13 px; altura mínima de 36 px en escritorio. El hover usa la superficie activa únicamente con puntero fino. Presión: escala 0,98 durante 120 ms con la curva `cubic-bezier(.23,1,.32,1)`; se elimina con movimiento reducido. Los deshabilitados tienen opacidad 0,45. La implementación no tiene un botón sólido de acento.

### Inputs / Fields

Selectores y fecha nativos, hoja blanca, borde específico de campo y radio de control. Altura mínima de 38 px y tipografía de 14 px dentro de controles; foco compartido con enlaces, botones y desplegables. Cada campo tiene una etiqueta visible y el ancho se adapta al contenedor.

### Navigation

Tres enlaces —Modelos, Sitio y Serie— con iconos de trazo, texto secundario y selección identificada por `aria-current=page`, tono activo y peso 500. En móvil, los enlaces se desplazan horizontalmente; los iconos se ocultan hasta 640 px. El enlace de salto al contenido aparece al recibir foco.

### Chips

Etiquetas compactas de superficie secundaria para las entradas del modelo. La marca de modelo elegido añade texto explícito. Los chips informativos no se presentan como acciones. Los atajos de sitio son botones.

### Cards / Containers

Panel blanco con borde fino y relleno de panel; notas sobre superficie secundaria. La banda de evidencia permite salto de línea y conserva métricas, modelo y contexto en grupos separados. No sustituir esta relación por tarjetas decorativas aisladas.

### Confusion Matrix / Metrics

Matriz HTML con realidad en filas y predicción en columnas. Cada celda presenta conteo, sigla y nombre. Las celdas de error usan tono rojizo suave; los conteos desconocidos se muestran con raya. Las fórmulas de precision, recall, F1 y accuracy acompañan a las cifras; los días sin decisión se identifican fuera de los cuatro conteos.

### Charts / Tables

Plotly local, fuentes Plex y ejes con reglas claras; gráficos transparentes sobre hoja. El modelo elegido se resalta en verde y las alternativas en gris. Barras, series y puntos llevan unidades y títulos. Las tablas conservan columnas numéricas alineadas a la derecha y exportación CSV. Los errores de recursos se muestran en la página; los gráficos tienen texto de fallo y las exploraciones sin observaciones un mensaje vacío.

El cambio de vista usa únicamente opacidad 0,75 → 1 durante 160 ms con la curva indicada. El código lo omite si hubo teclado en los últimos 500 ms o si se solicita movimiento reducido; no detecta explícitamente el dispositivo que originó el cambio. No hay animación de números ni coreografía de gráficos.

## Do's and Don'ts

### Do:

- **Do** conservar modelo, unidad y alcance junto a las métricas.
- **Do** acompañar el color de estados con texto y etiquetas.
- **Do** mantener las cifras tabulares y las tablas desplazables dentro de su contenedor.
- **Do** respetar el foco visible, los controles nativos y movimiento reducido.

### Don't:

- **Don't** añadir sombras a los paneles ni animación de cifras.
- **Don't** representar un dato ausente como cero o como normalidad.
- **Don't** ocultar columnas para aparentar que una tabla cabe.
- **Don't** dar por verificada la composición sin inspección del render.
