---
name: Solar / Datos · Informe sobre papel milimetrado
description: Hoja de informe de laboratorio sobre papel milimetrado, corregida con birome; la tinta dice qué es dato, qué es estimación y qué es alerta.
colors:
  paper: "#f5f9f4"
  white: "#ffffff"
  tint: "#e9f2eb"
  grid: "#2e9c6a"
  ink: "#111b16"
  ink-2: "#34463c"
  ink-3: "#53665b"
  rule: "#cfe0d4"
  rule-strong: "#7fa992"
  blue: "#1f3fbf"
  red: "#cf1f19"
typography:
  display:
    fontFamily: "Barlow Condensed (local)"
    fontSize: "clamp(40px, 4.4vw, 64px)"
    fontWeight: 700
    lineHeight: 0.98
  title:
    fontFamily: "Barlow Condensed"
    fontSize: "25px"
    fontWeight: 700
    lineHeight: 1.1
  body:
    fontFamily: "Barlow (local)"
    fontSize: "16px"
    lineHeight: 1.5
  label:
    fontFamily: "Barlow Condensed"
    fontSize: "13px–14px"
    fontWeight: 500
    letterSpacing: ".08em"
    textTransform: uppercase
  figure:
    fontFamily: "Barlow Condensed"
    fontSize: "28px–34px"
    fontWeight: 700
rounded:
  none: "0"
spacing:
  gap: "20px"
  plate: "14px 20px 18px"
  page: "24px 28px"
---

# Design System: Solar / Datos · Informe sobre papel milimetrado

## Overview

**North Star: "La hoja corregida".** El dashboard es la hoja de un informe de laboratorio sobre papel milimetrado, de las que se entregan en la facultad: cajetín de plano arriba, figuras con marco y una tinta distinta para cada cosa. Aula con luces prendidas, proyector y computadora: por eso es claro. Rediseño total del 01/11/2026 que reemplaza la carta estelar oscura (seed 2ab30e04, candidato 4 de la lista propia).

## Colors

- **Papel** (`paper`) con grilla verde (`grid`) de 16 px y líneas mayores cada 80 px. El botón **Grilla** la muestra u oculta y el estado se recuerda. Las figuras (`white`) tapan la grilla para que los gráficos se lean limpios.
- **Tinta** (`ink`) es lo observado: texto, marcos, estrellas de la carta, línea observada. **Azul birome** (`blue`) es lo que estima el modelo: campo de factor en la carta, línea punteada, punto de prueba, barras de energía, la cifra de energía. **Rojo corrección** (`red`) es lo que marca el docente: parque seleccionado, retículo, caso límite, ceros operativos, modelo elegido, avisos de alerta. No se usa como decoración.
- Ningún estado depende solo del color: observado y estimado también difieren en la forma de línea (llena y punteada), validación y prueba en aro y punto, y toda alerta lleva texto.

## Typography

- **Barlow Condensed 700** para títulos de vista, de figura, cifras y rótulos del cajetín; **Barlow** para cuerpo, tablas y campos. Cifras tabulares siempre. Sin itálica en ningún texto.
- Rótulos en versalitas de 13–14 px con espaciado de .08em, cortos: nunca frases largas en mayúscula.
- Modo exposición agranda cuerpo, títulos, rótulos y la carta para el proyector.

## Layout

Barra superior fija: marca, cuatro vistas como celdas (la activa en tinta llena), Grilla y Modo exposición. Debajo, el **cajetín**: título de la vista con su bajada a la izquierda y una grilla de celdas rotuladas a la derecha con el modelo elegido, RMSE, MAE y R² de prueba, RMSE de parque nuevo y el alcance (factor de capacidad mensual, prueba retrospectiva desde 2025).

- **Atlas:** carta a la altura de la pantalla (600 × 887) e índice ordenable; cuatro figuras de exploración y la ficha de calidad.
- **Modelos:** partición temporal con ancho proporcional a los meses, RMSE por modelo, ficha del modelo con importancias, observado contra estimado, validación por parque y tabla.
- **Sitio:** formulario y ejemplos; carta con retículo y línea al parque que presta el clima; la energía como resultado de un cálculo, con avisos y barras mensuales.
- **Parque:** encabezado con coordenadas, serie con la prueba sombreada, residuos y la grilla de series de todos los parques.

A 1180 px las grillas pasan a una columna y el cajetín se apila; a 860 px la navegación ocupa su propia fila y las celdas pasan a dos columnas.

## Elevation & Depth

Plano y sin sombras. Las figuras son rectángulos blancos de 1 px de tinta sin radio; el cajetín y la barra superior llevan 2 px. Sin gradientes decorativos: el único degradado es la rampa de la leyenda del campo de factor.

## Components

- **Carta (SVG propio):** contornos de Natural Earth 1:50m locales, graticula verde de 2°, campo de factor típico estimado en celdas de 0,2° recortado a la Argentina (azul), rectángulo de entrenamiento punteado en azul, puntos de relevamiento negros con radio `2,6 + 0,82·√MW` y anillo desde 50 MW. Recuadro con el país completo para elegir sitios fuera de la carta.
- **Índice:** tabla ordenable; la fila seleccionada se marca en rojo y "fuera del rango" aparece bajo el nombre.
- **Botones:** contorno de 1 px en tinta, versalitas; el estado activo se llena de tinta (vistas) o de azul (Grilla, Modo exposición). Los ejemplos y las series elegidas se marcan en rojo.
- **Energía de un sitio:** cifra en azul con doble subrayado de total contable; en caso límite pasa a rojo y tachada.
- **Avisos:** lista con cuadrado; los de alerta tienen borde y fondo rojos.
- **Gráficos:** Plotly local con fondo transparente, grilla `rule` y rótulos en Barlow.

## Do's and Don'ts

- **Do** mantener el modelo, la unidad y la partición visibles junto a las métricas.
- **Do** marcar fuera de rango, ceros y clima promedio con texto además del color.
- **Do** conservar un solo significado por tinta: negro dato, azul estimación, rojo alerta.
- **Don't** usar itálica, sombras de tarjeta, gradientes de texto ni una segunda tinta de alerta.
- **Don't** mostrar un dato ausente como cero.
