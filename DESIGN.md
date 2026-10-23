# Design

Sistema visual del dashboard (`app/index.html`, `app/tablero.js`). Mundo: el tablero de una sala de despacho
eléctrico, traducido a decisiones para alguien no técnico y legible proyectado en un aula con luz.

## Principios

- **Cada vista abre con una franja de decisión**: una frase que dice qué pasa y qué hacer, y a la derecha la cifra que la respalda. Debajo, la evidencia (mapa, lista, gráfico).
- **Lenguaje de negocio**: "rinde 44% de lo normal", "lo que dejó de generar". Los términos técnicos quedan en notas.
- **Énfasis, no arcoíris**: solo lo que necesita atención lleva color de estado; el resto va en gris petróleo.
- **Nada se esconde**: baja confianza, capacidad no confiable y sensor caído se muestran como sellos o filas propias.

## Color (fondo claro: proyector en aula con luz)

| Rol | Valor |
|---|---|
| Suelo de la página | `#e4e8e6` |
| Panel / panel secundario | `#f8f9f8` / `#eef1f0` |
| Juntas (bordes 1px) | `#c9d1cf` |
| Tinta (azul petróleo) / secundaria / tenue | `#0f2a36` / `#34505c` / `#566b74` |
| Franja de decisión | fondo `#0f2a36`, texto `#f3f6f5`, secundario `#b5c7cd` |
| Acento (foco, links) | `#0b6d80` |
| Estado: en orden / revisar / atender / sin dato | `#129a3c` / `#f2a900` / `#d03b3b` / `#8b979c` |
| Serie "generó" / "dejó de generar" | `#1f6f86` / `#e2735f` |
| Elementos sin problema en gráficos | `#a9b8bc` / `#7d9199` |

El estado nunca va solo en color: siempre con texto ("Atender hoy", "Revisar esta semana", "En orden", "Sin dato confiable").

## Tipografía

Una sola familia del sistema (`system-ui`), base 17px. Titular de franja 1.95rem/700, cifra de franja 2.6rem/700,
rótulos de panel 0.74rem en versalitas con tracking 0.12em, cifras de tablas y lecturas con `tabular-nums`.

## Componentes

- **Lámpara**: círculo de 16px con brillo radial y anillo del mismo color al 22%; 34px en la franja.
- **Sello**: borde 1.5px, mayúsculas 0.72rem; variantes `supuesto` (ámbar oscuro) y `medido` (acento).
- **Fila de planta**: botón blanco con borde de junta; al pasar el mouse se oscurece el borde y el resto de la lista se atenúa al 45% (y el mapa al 25%).
- **Fichas (chips)**: píldoras para plantas en orden y para elegir planta; la elegida va en tinta.
- **Segmentos**: control de período con la opción activa en tinta.
- **Paneles**: radio 10px, borde de junta, sin sombra; la franja es el único elemento con sombra suave.

## Gráficos (Plotly.js, sin barra de herramientas)

- Barras apiladas "generó" + "dejó de generar" y línea escalonada "debía generar"; filas de avisos debajo como carriles.
- Grilla `#dfe4e2`, ejes `#b9c3c0`, etiquetas en tinta tenue; tooltip blanco con borde de junta.
- Mapas con el topojson de Plotly precargado en `app/geo.js` (tierra `#f4f6f5`, mar `#d3e0e3`).
- Fechas y números en formato es-AR (locale registrado en `tablero.js`).

## Movimiento

Solo cambios de estado: 150 ms ease-out en bordes, fondos y opacidad. Se desactiva con `prefers-reduced-motion`.
