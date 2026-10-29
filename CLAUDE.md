# Proyecto

TPO de Ciencia de Datos de UADE. Español argentino. El alcance autoritativo está en `docs/alineacion_materia.md`: solo técnicas respaldadas por los apuntes de Notion. El usuario pidió retirar completamente las referencias a otras técnicas.

## Motor actual

`src/academico.py` usa regresión lineal simple/múltiple, árbol de regresión, Random Forest y XGBoost. Selección por validación. Regla de alertas con boxplot de residuos. Clasificación y regresión tienen métricas distintas. Se entrena solo con datos observados; las inyecciones son únicamente pruebas controladas.

La app consume `defensa_evidencia.json` a través de `app/build_dashboard.py`. No debe mostrar cifras calculadas por otra versión. Cada vista identifica fuente, modelo, partición, métricas y clase de respaldo.

## Comandos

```bash
python -m unittest discover -s tests -v
python -m src.academico
python app/build_dashboard.py
python -m src.build_datasets
```

Los crudos van en data/raw y los procesados en data/processed, usando src/config.py. Notebook 01 descarga cuando faltan procesados. Modelado y dashboard deben ser reproducibles localmente.

## Condiciones

- La app funciona sin conexión, con recursos locales y sin APIs.
- Estado desconocido no equivale a normalidad. Capacidad no confiable excluye interpretación económica.
- Los ceros operativos se conservan en evaluación. No confundir ausente y cero.
- Toda evaluación es retrospectiva; no afirmar independencia ciega después de haber explorado el período.
- No inventar etiquetas de fallas reales ni una matriz de confusión para Argentina.
- No presentar déficit estimado como recuperación o ahorro demostrado.
- Usuario autorizó commits y pushes periódicos directos a main. Verificar remoto y no forzar historia.
- Defensa 12/11/2026. Cuatro integrantes, trabajo compartido: Ignacio Melinc, Matias Young, Francisco Fabrello y Malena Garcia Moraglio.
