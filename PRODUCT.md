# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Delegado por el equipo ("elegí la mejor manera para que sea profesional y entendible"). Elección: página HTML estática
(`app/index.html`) con los datos precalculados en un archivo JS que genera un script de Python a partir de `src/` y
`data/processed/`. Gráficos con Plotly.js copiado del paquete de Python ya instalado. Reemplaza al dashboard de Streamlit.

## Users

Dos audiencias, con el mismo peso:
- **Gerente de operaciones de una flota solar (no técnico).** Lo abre a la mañana para decidir a qué planta mandar un técnico hoy, cuánta plata se está perdiendo y cada cuánto limpiar.
- **Jurado de la defensa del TPO (UADE, Ciencia de Datos).** Lo ve proyectado en el aula durante una demo de unos 2 minutos y medio, dentro de una presentación de 15 minutos. Tiene que entenderse sin explicación técnica.

## Product Purpose

Comparar lo que cada planta genera con lo que debería generar según el clima (con la planta limpia), avisar cuándo rinde de menos y traducir esa pérdida a energía y plata. Éxito: en pocos segundos se entiende qué planta está mal, cuánto cuesta y qué hacer.

## Positioning

No compara una planta contra su propio mes anterior: la compara contra un modelo físico + ML del clima y contra sus vecinas. Por eso encuentra plantas que rinden mal siempre (station09), que una revisión mensual no ve.

## Operating Context

- Se proyecta en un aula, a distancia, con la luz que haya.
- La defensa se planea sin internet: todo lo que se muestra sale de `data/processed/`.
- Período de datos de la flota: 1/7/2018 a 13/6/2019 (PVOD, 10 plantas en Hebei, China). Argentina: comparación mensual de parques de CAMMESA, 2011 a 2026.

## Capabilities and Constraints

- Semáforo por planta: verde, amarillo (revisar esta semana), rojo (visita técnica hoy) y gris (capacidad no confiable: station04). Sale de `semaforo_flota`.
- Detalle diario por planta: energía real vs. esperada con la planta limpia, alertas, días sin decisión por sensor caído, días de baja confianza (station06 enero a marzo).
- Argentina es **comparación mensual entre parques, no detección en tiempo real**; esto tiene que estar explícito.
- Calculadora de limpieza: T* y ahorro anual por MW con costo, precio y tasa de ensuciamiento.
- Límites honestos: detecta pérdidas ≥ 50% el mismo día y casos crónicos; 25% en el límite; no detecta caídas de 10% día a día.
- Número principal del modelo: 6,04% de error de energía diaria (evaluación ciega). 5,04% solo como nota.
- Todo el texto en español (Argentina).

## Evidence on Hand

- Datos reales: `data/processed/app_diario.parquet`, `app_horario.parquet`, `app_argentina.parquet`, `pvod_plantas_metadata.csv`.
- Casos: station09 (bajo rendimiento crónico: 4.724 MWh y unos USD 202 mil en días con alerta), ULL4FV (alerta en 11 de 12 meses de 2025).
- Supuestos explícitos: precio USD 42,84/MWh de RenovAr Ronda 2 (ilustrativo para plantas chinas), costo de limpieza USD 800/MW, revisión manual cada 30 días, línea base de limpieza una vez por año. No inventar clientes, cotizaciones ni ingresos reales.

## Product Principles

1. Primero la decisión, después el dato: cada pantalla abre diciendo qué pasa y qué hacer.
2. Plata y energía en palabras de negocio; los términos técnicos (residuo, índice relativo, percentil) quedan en ayudas o se traducen.
3. Honestidad sobre los límites: supuestos y baja confianza siempre a la vista, nunca escondidos.
4. Se entiende desde el fondo del aula.

## Accessibility & Inclusion

Proyector: contraste alto y letra grande. El estado nunca se comunica solo con color (siempre con texto o ícono).
