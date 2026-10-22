# TPO Ciencia de Datos — Detector de bajo rendimiento solar

Predecimos cuánta energía debería generar una planta solar según el clima y detectamos cuándo rinde de menos.

## Estructura

```
data/raw/          datos descargados, sin tocar (NO van en git)
data/processed/    parquet limpios y unidos (los leen modelos y app)
notebooks/         un notebook por etapa (01 descarga → 04 detección)
src/               funciones reutilizables (config, features)
models/            modelo entrenado (.pkl)
app/               dashboard en Streamlit
```

## Cómo correrlo

**Local**
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
nbstripout --install          # borra salidas de notebooks al commitear
streamlit run app/app.py
```

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
