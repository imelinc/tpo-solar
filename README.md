# TPO Ciencia de Datos

Qué parque solar argentino conviene mirar primero: cuánto debería generar cada uno según su clima, cuáles rinden menos y cuánta plata está en juego. Ciencia de Datos de UADE, segundo cuatrimestre 2026.

**Defensa:** 12/11/2026. **Integrantes:** Ignacio Melinc, Matias Young, Francisco Fabrello y Malena Garcia Moraglio. Trabajo compartido en todas las etapas.

## Recorrido

Parques → Sitio nuevo → Modelos → Datos. El target es el factor de capacidad. La energía sale de multiplicar por la potencia y por las horas de cada mes. Las métricas son MAE, RMSE y R².

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

Publicada en https://tpo-ciencia-de-datos.netlify.app (subida a mano a Netlify: al cambiar la app hay que volver a subirla). También se puede abrir `app/index.html` en un navegador. La aplicación usa datos, biblioteca y tipografía locales. No consulta APIs durante la defensa.

Los notebooks construyen y revisan los archivos. La defensa usa el comando de arriba y `app/index.html`. Ver `notebooks/LEEME.md`.

## Pruebas de interfaz (opcionales, Node 22)

```bash
npm ci
npm run test:dashboard
```

Estas pruebas verifican DOM, navegación y que la consulta de un sitio coincida con la grilla. No sustituyen una prueba visual en navegador. La aplicación se abre sin Node.

## Fuentes y reproducción desde cero

Los procesados están incluidos. Para volver a descargar las fuentes:

```bash
python -m src.build_datasets
```

Por defecto los crudos se guardan en `data/raw/` y los procesados en `data/processed/`. Para probar en carpetas temporales, definir `TPO_DIR` y `TPO_RAW`. Las descargas requieren internet y se reutilizan por caché. Las fuentes y unidades están en `data/processed/diccionario_de_datos.md`.

## Estructura

- `src/academico.py`: entrenamiento, selección, grilla de consulta y evidencia.
- `src/senales.py`: parques a revisar, K-Means, PCA y DBSCAN.
- `src/maui.py`: análisis aparte por hora en plantas públicas de NREL. La app, el informe y la presentación no lo usan.
- `data/processed/defensa_*`: resultados de la defensa.
- `app/`: Parques, Sitio nuevo, Modelos y Datos, sin red.
- `tests/`: métricas, señales, regla horaria y la consulta de un sitio.
- `docs/`: alcance, protocolo y guion.

La evaluación es retrospectiva. Un año futuro usa el clima promedio, no un pronóstico meteorológico. Fuera del rectángulo de parques el resultado es un caso límite. El equipo informó cuatro integrantes; la consigna escrita pide cinco o seis.

[Diagrama de arquitectura](docs/arquitectura.md).

## Respaldo de exposición

Abrir `docs/respaldo/index.html`: pantallas estáticas sin JavaScript ni red. Se regenera con `python scripts/generar_respaldo.py`. El guion está en `docs/guion_presentacion_10min.md`.

[Verificación realizada y pendientes](docs/verificacion.md).
