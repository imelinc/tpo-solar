# TPO Ciencia de Datos — Detector de bajo rendimiento solar

Predecimos cuánta energía debería generar una planta solar según el clima y detectamos cuándo rinde de menos.

## Estructura

```
data/raw/          datos descargados, sin tocar (NO van en git)
data/processed/    parquet limpios y unidos (los leen modelos y app)
notebooks/         un notebook por etapa (01 descarga → 04 detección)
src/               funciones reutilizables (config, features)
models/            modelo entrenado (.pkl)
app/               dashboard (página HTML que se abre sin servidor)
```

## Cómo correrlo

**Local**
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
nbstripout --install          # borra salidas de notebooks al commitear
open app/index.html           # dashboard
```

### Dashboard

Doble clic en `app/index.html` (o arrastrarlo al navegador). No necesita servidor, Python ni internet: los datos van
precalculados en `app/datos.js` y los mapas en `app/geo.js`. Vistas: flota hoy (semáforo), una planta, Argentina
(comparación mensual) y limpieza y plata (calculadora).

Si cambian el modelo o el detector, regenerarlo así: correr `03_modelos` → `04_deteccion` (dejan `data/processed/app_*.parquet`) y después

```bash
python app/build_dashboard.py
```

Commitear `app/datos.js` junto con las tablas. Plotly.js (`app/vendor/`) se copió del paquete `plotly` de `requirements.txt`.

**Colab:** abrir el notebook desde GitHub (Archivo → Abrir notebook → GitHub). La primera celda clona el repo e instala todo. Para guardar: Archivo → Guardar una copia en GitHub.

## Reglas del equipo
- Un notebook por etapa y un dueño por notebook. No editar el mismo notebook a la vez.
- Cada uno trabaja en su rama y se junta a `main` con un pull request revisado por otro.
- Borrar salidas antes de commitear notebooks.
- Datos crudos: carpeta compartida de Drive (o release del repo); el notebook 01 los descarga.
- Archivos > 50 MB no van en git. El `.pkl` sí, si es chico; las versiones están fijas en `requirements.txt` para que abra igual en todas las compus.
- El dashboard nunca llama APIs en vivo: el día de la defensa tiene que andar sin internet.

## Roles
| Rol | Responsable |
|---|---|
| Negocio y storytelling | |
| Ingeniería de datos | |
| Análisis exploratorio | |
| Modelado | |
| Detección y validación | |
| App y visualización | |
