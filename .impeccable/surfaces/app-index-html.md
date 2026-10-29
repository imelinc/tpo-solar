---
version: 1
slug: app-index-html
primary_target: app/index.html
related_targets:
  - app/estilos.css
  - app/tablero.js
---

Scope: dashboard de defensa de Ciencia de Datos, modo Operate. Principal audiencia: jurado y cuatro integrantes en aula, 12/11/2026. Recorrido confirmado: Resumen → Datos → Modelos → Evaluación → Casos. China diario y Argentina mensual, con métricas y modelos distintos.

## Direction contract

Dirección elegida por el usuario: **Laboratorio comparativo**. Referencia `seed:6a8420f350ea078c`, tipo grounded, construcción en código. Boceto de elección local: `.impeccable/mocks/decision/laboratorio.html`. Preferencias explícitas: claro, minimalista y sobrio.

THESIS: El análisis comparativo es la interfaz: el jurado ve qué se eligió, qué errores comete y qué clase respalda cada paso.

OWN-WORLD: Marco gris frío claro, hoja blanca, IBM Plex Sans local, tinta #18252d y datos #227a6c. Chrome neutro, cifras tabulares y gráficos sin adornos. Diseño canónico en DESIGN.md y .impeccable/design.json.

STORY: Primero evidencia con alcance, luego interpretación. La regresión estima una cantidad; la regla produce una alerta y se evalúa con su propia matriz.

FIRST VIEWPORT: Navegación lateral, encabezado de producto y franja persistente de modelo/unidades/métricas; comparación de RMSE a la izquierda y matriz con precision/recall a la derecha. La franja del recorrido conecta observación, regresión, residuo y revisión.

SIGNATURE: Procedencia visible: cada vista mantiene modelo, población, período y referencias de clase; filtros de evaluación recalculan matriz y métricas desde los mismos experimentos.

RISK: Demasiados metadatos pueden competir con el gráfico. Las notas largas van en detalles; incertidumbre y exclusiones de matrices quedan visibles.

## Verificación

Revisión independiente: correcciones de fuente y datos resueltas; no certifica layout. Pruebas Python y DOM, lint estático y recursos locales comprobados. Sin capturas de navegador por la restricción documentada en docs/verificacion.md. No se anuncia aprobación visual.
