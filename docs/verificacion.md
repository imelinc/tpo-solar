# Verificación de la versión de defensa

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

## Límites que siguen abiertos

La herramienta de navegador bloqueó una apertura `file://` por política. No se intentó eludir el rechazo por otro navegador, servidor o renderizador. Por eso no se dispone de capturas automatizadas finales a 1440, 768 y 390 px. El usuario sí confirmó visualmente la aplicación en su navegador. Siguen sin comprobarse la legibilidad en el proyector del aula y el comportamiento de cada viewport mediante capturas. Las pruebas de DOM y el código responsive no bastan para afirmar que esa verificación pasó.

Se verificó la instalación tanto en el entorno existente como en uno nuevo desde una copia versionada, con los procesados incluidos. No se descargaron todas las fuentes de nuevo ni se probó Colab. La entrega permite ejecutar los modelos con datos locales, pero el acceso futuro a fuentes externas requiere una comprobación adicional.

Confirmar con el docente la aceptación de cuatro integrantes frente a los 5–6 de la consigna. Los casos reales no cuentan con etiquetas independientes ni se verificaron sus causas en campo. La evaluación sigue siendo retrospectiva.
