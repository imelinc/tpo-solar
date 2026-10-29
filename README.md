# Solar / Datos · TPO Ciencia de Datos

Estimación de generación solar y análisis de desvíos con técnicas de las clases de Ciencia de Datos de UADE, segundo cuatrimestre 2026.

**Defensa:** 12/11/2026. **Integrantes:** Ignacio Melinc, Matias Young, Francisco Fabrello y Malena Garcia Moraglio. Trabajo compartido en todas las etapas.

## Recorrido

Resumen → Datos → Modelos → Evaluación → Casos. China tiene observaciones horarias y análisis diario; Argentina, comparación mensual. Se distingue regresión (MAE, RMSE, R²) de la regla de alertas (matriz de confusión, accuracy, precision, recall, F1).

[Alcance curricular y clases de Notion](docs/alineacion_materia.md) · [Protocolo](docs/plan_modelado.md) · [Guion](docs/guion_defensa.md).

## Ejecutar

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m src.academico
python app/build_dashboard.py
```

Abrir `app/index.html` en un navegador. La aplicación usa datos, biblioteca y tipografía locales. No consulta APIs durante la defensa.

Los notebooks 01–05 siguen extracción, EDA, modelos, evaluación y casos. Sus salidas están vacías en Git; ejecutarlos antes de la defensa. La celda inicial admite Colab y también ejecución local desde la raíz o `notebooks/`.

## Pruebas de interfaz (opcionales, Node 22)

```bash
npm ci
npm run test:dashboard
```

Estas pruebas verifican DOM, navegación, matrices y datos enviados a Plotly; no sustituyen una prueba visual en navegador. La aplicación se abre sin Node.

## Fuentes y reproducción desde cero

Los procesados están incluidos. Para volver a descargar las fuentes:

```bash
python -m src.build_datasets
```

Por defecto los crudos se guardan en `data/raw/` y los procesados en `data/processed/`. Para probar en carpetas temporales, definir `TPO_DIR` y `TPO_RAW`. Las descargas requieren internet y se reutilizan por caché. Las fuentes y unidades están en `data/processed/diccionario_de_datos.md`.

## Estructura

- `src/academico.py`: entrenamiento, selección, calibración, evaluación y evidencia.
- `data/processed/defensa_*`: tablas y resultados de la defensa.
- `notebooks/`: explicación ejecutable por etapas.
- `app/`: aplicación estática para la exposición.
- `tests/`: matrices, decisiones inválidas e identidades de simulación.
- `docs/`: respaldo curricular, metodología y guion.

La evaluación es retrospectiva: los períodos ya se exploraron anteriormente. Las caídas controladas sirven solo para evaluar, nunca para entrenar. Una alerta no confirma la causa física de un desvío. El equipo informó cuatro integrantes; queda confirmar la aceptación del docente porque la consigna escrita indica cinco o seis.

[Diagrama de arquitectura](docs/arquitectura.md).

## Respaldo de exposición

Abrir `docs/respaldo/index.html`: presentación de ocho pantallas con seis figuras PNG, sin JavaScript ni red. Se regenera con `python scripts/generar_respaldo.py`. El guion asigna bloques de exposición a los cuatro integrantes, manteniendo trabajo compartido.

[Verificación realizada y pendientes](docs/verificacion.md).
