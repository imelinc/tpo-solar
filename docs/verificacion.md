# Verificación de la versión de defensa

## Recorte a Argentina — 29/10/2026

`python -m unittest discover -s tests -v` pasa 10 pruebas. `node tests/dashboard.cjs` confirma que los cinco modelos, los presets y los ceros de la serie coinciden con la evidencia. En el navegador se recorrió Modelos, Sitio (2023, 2028 y Ushuaia) y Serie, en escritorio y a 390 px de ancho. El modelo elegido por validación es XGBoost. La consulta de un sitio lee la grilla de 0,2°.

Fecha: 29/10/2026.

## Hecho con evidencia

- El usuario confirmó que el dashboard final «se ve bien» al abrirlo en su navegador. No conoce la resolución del proyector.
- Se comprobó una copia limpia de `git archive` en un entorno virtual nuevo: instalación completa, ocho pruebas, reentrenamiento y empaquetado correctos, sin modelos locales. La evidencia resultante coincide dentro de una tolerancia numérica de 1e-10.
- Se leyeron las doce clases de Ciencia de Datos devueltas por su base en Notion, y los criterios del docente. La tabla curricular está en `alineacion_materia.md`.
- Se ejecutaron los cinco notebooks con Jupyter/nbclient y el intérprete del proyecto. Después de corregir cobertura diaria se repitieron 03, 04 y 05. No se guardan salidas en los notebooks versionados.
- El entrenamiento y la elección de China se recalcularon: Random Forest, MAE 0,0311537, RMSE 0,0473253 y R² 0,9656053 en 4.944 observaciones de prueba, target MW/MW nominal.
- Argentina seleccionó regresión lineal múltiple por validación: MAE 0,0491646, RMSE 0,0704831 y R² 0,4211503 en 1.105 meses-parque de prueba, target factor de capacidad.
- Ocho pruebas Python verifican fórmulas, estados sin decisión, identidades de simulación y equivalencia de cobertura diaria entre benchmark y aplicación.
- Prueba DOM de las cinco vistas, tipos de EDA, tablas de modelos, 144 combinaciones de filtros, casos de ausencia/sensor/capacidad, ceros argentinos y modo exposición. Plotly se reemplaza por un stub en esta prueba: verifica las series enviadas, no su render.
- El benchmark contiene 480 episodios con identidad única. Por nivel de caída hay 5.145 días-experimento con decisión y 75 excluidos.
- Una revisión independiente de fuente y datos detectó tres problemas; tras corregirlos calificó los tres como resueltos. Su dictamen no certifica el resultado visual.
- Los recursos referenciados de scripts, CSS y fuentes están presentes localmente. No hay scripts ni hojas remotos en el HTML.
- `node --check` y `git diff --check` correctos. `pip check` sin dependencias rotas.
- Lint de diseño sobre tres archivos: cero fallos y cero advertencias. El detector mecánico adicional señaló texto de 11 px; se elevó el mínimo a 12 px. Esto no sustituye inspección visual.
- Se generaron seis figuras PNG desde la evidencia y se inspeccionaron las seis imágenes. Hay una presentación de respaldo local de ocho pantallas en `respaldo/index.html`.

## Revisión de cierre del 29/10/2026

`main` local y `origin/main` coincidían en `c1557c9` antes de esta pasada. Se midieron anchos de texto con la fuente local contra las cajas de 390 px: el título de Datos más «Descargar evidencia JSON» no entra en el panel, y la barra superior queda a unos 16 px del borde. El modo exposición dejaba en 12 px rótulos de matriz, contexto y pasos que el cuerpo ya había agrandado. Esas correcciones están en CSS. El rastro decía «Evaluacion». station04 mostraba un valor ilustrativo de USD 0 pese a la capacidad no confiable. El detalle de modelos ahora incluye el MSE de la partición visible. El respaldo escribe los decimales como la aplicación y agrega las métricas de prueba de Argentina.

La herramienta de navegador volvió a rechazar `file://`. No se abrió otro navegador, servidor ni renderizador. No hay capturas nuevas a 1440, 768 ni 390 px. La comparación de anchos no reemplaza esa inspección. Los ticks de Plotly siguen en 12 px: agrandarlos sin ver el gráfico podía cortar las etiquetas.

## Límites que siguen abiertos

No hay capturas automatizadas a 1440, 768 y 390 px ni prueba del proyector del aula. El usuario confirmó antes que el dashboard se ve bien en su navegador; esta pasada no repitió esa mirada. Las pruebas de DOM y las medidas de texto no alcanzan para afirmar que cada viewport quedó verificado.

Se verificó la instalación tanto en el entorno existente como en uno nuevo desde una copia versionada, con los procesados incluidos. No se descargaron todas las fuentes de nuevo ni se probó Colab. La entrega permite ejecutar los modelos con datos locales, pero el acceso futuro a fuentes externas requiere una comprobación adicional.

Confirmar con el docente la aceptación de cuatro integrantes frente a los 5–6 de la consigna. Los casos reales no cuentan con etiquetas independientes ni se verificaron sus causas en campo. La evaluación sigue siendo retrospectiva.
