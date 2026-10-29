---
version: 1
slug: app-index-html
primary_target: app/index.html
related_targets:
  - app/estilos.css
  - app/tablero.js
---

Scope: dashboard de defensa de Ciencia de Datos, modo Operate. Principal audiencia: jurado y cuatro integrantes en aula, 12/11/2026. Recorrido: Modelos → Alertas → Caso, pensado para 5–7 minutos. China horario y Argentina mensual se distinguen por fondo y bandera. La página no muestra enlaces a los apuntes.

## Direction contract

Dirección elegida por el usuario: **Laboratorio comparativo**. Referencia `seed:6a8420f350ea078c`, tipo grounded, construcción en código. Boceto de elección local: `.impeccable/mocks/decision/laboratorio.html`. Preferencias explícitas: claro, minimalista y sobrio.

THESIS: El gráfico compara y el país se reconoce al instante. El jurado ve qué modelo se eligió, con qué error, y qué detecta la regla.

OWN-WORLD: Hoja blanca sobre un marco que cambia con el país: cálido con franja roja y oro en China, celeste con franja de la bandera en Argentina. IBM Plex Sans local, cifras tabulares y series en verde petróleo y azul. Diseño canónico en DESIGN.md.

STORY: Primero la comparación de modelos, después la matriz de China, al final un caso. Argentina no tiene matriz.

FIRST VIEWPORT: Selector grande con banderas, franja de modelo y métricas, gráfico de RMSE de validación contra prueba.

SIGNATURE: El fondo y la bandera dicen el país. Clic en una barra o en la curva recalcula la lectura. Los filtros de alertas salen de los mismos experimentos.

RISK: Demasiados metadatos pueden competir con el gráfico. Las notas largas van en detalles; incertidumbre y exclusiones de matrices quedan visibles.

## Verificación

Revisión independiente: correcciones de fuente y datos resueltas; no certifica layout. Pruebas Python y DOM, lint estático y recursos locales comprobados. Sin capturas de navegador por la restricción documentada en docs/verificacion.md. No se anuncia aprobación visual.
