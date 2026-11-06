# Verificación de la versión de defensa

## Unificación con el Detector Solar — 05/11/2026

- `python -m unittest discover -s tests -v` pasa 17 pruebas. Se suman las reglas de señal, el caso sin vecinos, los ceros, la zona, el arranque, la regla horaria y la detección de copias.
- `node tests/dashboard.cjs` recorre las cuatro vistas.
- Sumar la polinómica no cambió XGBoost ni la grilla: las métricas y los factores de 2023 son idénticos a la versión anterior.
- Render real: las cuatro vistas se revisaron en el navegador integrado a 1440 × 900 y a 375 × 812, sin errores de consola y sin scroll horizontal de la página. Todos los recursos se sirven localmente.
- Los notebooks 02 a 07 se ejecutaron completos, sin guardar salidas.
- La carpeta original del Detector Solar dejó de estar disponible en Descargas durante el trabajo. Las cifras de esta versión se recalcularon desde los crudos públicos y no dependen de ella.

## Rediseño del dashboard y revisión del TP — 29/10/2026

- `python -m unittest discover -s tests -v` pasa 10 pruebas.
- `node tests/dashboard.cjs` recorre Datos, Modelos, Sitio y Parque: una estrella por parque en la carta, índice completo, los cuatro gráficos de exploración, cinco modelos en tabla, los cinco presets coinciden con la grilla (energía, modo de clima y rango), ceros marcados en la serie y una serie chica por parque. Plotly se reemplaza por un stub: verifica los datos enviados, no el render.
- Render real: la app se sirvió con `python -m http.server` y se recorrieron las cuatro vistas en el navegador integrado a 1440 × 900 y a 375 × 812. Sin errores de consola y sin scroll horizontal en móvil. Se probó el preset de Ushuaia: el total sale tachado y el aviso de caso límite aparece.
- El detector de diseño de Impeccable no marca problemas de calidad reales. Los avisos de contraste toman un fondo blanco que no existe (el texto gris sobre el azul noche da 5,6:1). Las rayas son la leyenda de los meses con clima promedio.
- Los cinco notebooks se reescribieron para Argentina y se ejecutaron completos con nbclient y el intérprete del proyecto, sin errores. No se guardan salidas.
- `src/build_datasets.py` arma solo el dataset argentino. Se retiraron la descarga de PVOD (China), NASA POWER y los archivos `dataset_A_*` y `pvod_plantas_metadata.csv`. Se rearmó desde cero en una carpeta temporal, con descargas nuevas: 5.036 filas y las mismas columnas; todos los valores coinciden con la versión del repo salvo la precipitación de 523 meses, que Open-Meteo revisó después del 22/10. La precipitación no entra al modelo.
- El dashboard ya no tiene franja de bandera ni selector de país. Los contornos de los países son Natural Earth 1:50m, locales en `app/geo-argentina.js`. La tipografía es Barlow y Barlow Condensed (OFL), locales en `app/fonts/`. El diseño es un informe sobre papel milimetrado: tinta negra para lo observado y para marcar alertas y ceros, azul para lo estimado. Sin rojo.

## Recorte a Argentina — 29/10/2026

El modelo elegido por validación es XGBoost: RMSE 0,0499 en 2024; en la prueba retrospectiva desde 2025, MAE 0,0425, RMSE 0,0664 y R² 0,487 sobre 1.105 meses-parque. RMSE de parque nuevo (cinco grupos por parque): 0,0592. La consulta de un sitio lee la grilla de 0,2°.

## Límites que siguen abiertos

- No hay prueba en el proyector del aula. El fondo es oscuro; usar «Modo exposición» y revisar el brillo antes de la defensa.
- Las señales y los casos reales no cuentan con etiquetas independientes y sus causas no se verificaron en campo. La evaluación es retrospectiva.
- Confirmar con el docente la aceptación de cuatro integrantes frente a los 5–6 de la consigna.
