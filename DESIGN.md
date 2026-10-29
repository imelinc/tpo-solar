---
name: Solar / Datos · Atlas de parques
description: Carta estelar de los parques solares argentinos; el lugar ordena la lectura.
colors:
  sky: "#0a1021"
  plate: "#0f1729"
  plate-2: "#16233d"
  line: "#24374f"
  line-strong: "#3a4e6b"
  chalk: "#f2f2e9"
  muted: "#a9b3c6"
  faint: "#8590a6"
  red: "#ff4d2e"
  amber: "#ffb36b"
  negative-corr: "#5b8fd9"
typography:
  display:
    fontFamily: "Atlas (EB Garamond Italic, local), Georgia, serif"
    fontSize: "44px"
    fontWeight: 500
    fontStyle: italic
    lineHeight: 1.08
  title:
    fontFamily: "Plex (IBM Plex Sans, local)"
    fontSize: "18px"
    fontWeight: 600
    lineHeight: 1.25
  body:
    fontFamily: "Plex"
    fontSize: "15px"
    lineHeight: 1.5
  label:
    fontFamily: "Plex"
    fontSize: "11px"
    letterSpacing: ".12em–.16em"
    textTransform: uppercase
  figure:
    fontFamily: "Plex"
    fontSize: "26px"
    fontWeight: 400
rounded:
  plate: "3px"
  chip: "20px"
spacing:
  gap: "20px"
  plate: "18px 20px"
  page: "28px 32px"
---

# Design System: Solar / Datos · Atlas de parques

## Overview

**North Star: "Carta estelar de los parques".** El dashboard es una carta de cielo nocturno: cada parque es una estrella y la consulta de un sitio es apuntar un retículo. El lugar ordena la lectura; los números se leen como coordenadas. Dirección elegida por el usuario el 29/10/2026 (ronda de Impeccable, seed 79f98652, mundo *star atlas*).

## Colors

- **Cielo** (`sky`) es el fondo, con una trama de puntos muy tenue. **Placa** (`plate`) y **placa 2** (`plate-2`) separan bloques y estados activos.
- **Tiza** (`chalk`) para texto principal y para lo observado (estrellas, línea observada). **Ámbar** (`amber`) para lo estimado por el modelo: campo de factor en la carta, línea punteada, punto de prueba, barras de energía.
- **Rojo linterna** (`red`) es el único color de alerta y anotación: retículo, parque seleccionado, caso límite, ceros operativos, modelo elegido. No se usa como decoración.
- Correlaciones negativas usan `negative-corr`; las positivas, ámbar.
- Ningún estado depende solo del color: observado y estimado también difieren en la forma de línea (llena y punteada), validación y prueba en aro y punto, y cada alerta lleva texto.

## Typography

- **Itálica serif (Atlas, EB Garamond) solo en los títulos de cada vista y en la marca.** Pedido explícito del usuario: el resto del texto va derecho.
- IBM Plex Sans para títulos de placa (600), cuerpo, tablas y cifras, siempre con cifras tabulares.
- Rótulos en versalitas espaciadas de 11 px (`plate-meta`, encabezados de tabla, ejes de la carta). Cortos: nunca frases largas en mayúscula.
- Modo exposición agranda título, títulos de placa, rótulos e índice para el proyector.

## Layout

Barra superior fija con marca, cuatro vistas (Atlas, Modelos, Sitio, Parque; la activa con un rombo rojo) y Modo exposición. Debajo, título de la vista y una línea de lectura persistente con el modelo elegido y sus métricas de prueba.

- **Atlas:** carta a la altura de la pantalla (relación 600 × 887) más el índice ordenable; abajo, cuatro placas de exploración y la ficha de calidad.
- **Modelos:** partición temporal con ancho proporcional a los meses, gráfico de puntos de RMSE, ficha del modelo con importancias, observado contra estimado, validación por parque y tabla.
- **Sitio:** formulario y ejemplos; carta con retículo y línea al parque que presta el clima; lectura de energía, avisos y barras mensuales (rayadas si el clima es promedio).
- **Parque:** encabezado con coordenadas, serie con la prueba sombreada, residuos y la grilla de series de todos los parques.

A 1180 px las grillas pasan a una columna; a 860 px la navegación se desplaza en horizontal y la carta ocupa todo el ancho.

## Elevation & Depth

Plano. Las placas tienen borde de 1 px y dos rombos en las esquinas superiores, como los nodos de una carta. Solo las estrellas de 50 MW o más tienen un halo radial.

## Components

- **Carta (SVG propio):** contornos de Natural Earth 1:50m locales, graticula de 2° punteada, campo de factor típico estimado en celdas de 0,2° recortado a la Argentina, rectángulo de entrenamiento punteado en ámbar, estrellas con radio `2,6 + 0,82·√MW` y leyenda de potencia fija. Recuadro con el país completo para ubicar la carta y elegir sitios fuera de ella.
- **Índice:** tabla ordenable; la fila seleccionada se marca en rojo y "fuera del rango" aparece bajo el nombre.
- **Botones:** contorno de 1 px en placa, versalitas; el estado activo se llena de rojo (Modo exposición) o se bordea en rojo (ejemplos).
- **Avisos:** lista con rombo; los de alerta tienen borde y fondo rojos.
- **Gráficos:** Plotly local con fondo transparente, grilla `line` y rótulos `muted`.

## Do's and Don'ts

- **Do** mantener el modelo, la unidad y la partición visibles junto a las métricas.
- **Do** marcar fuera de rango, ceros y clima promedio con texto además del color.
- **Don't** usar itálica fuera de los títulos de vista y la marca.
- **Don't** agregar sombras de tarjeta, gradientes de texto ni una segunda tinta de alerta.
- **Don't** mostrar un dato ausente como cero.
