# Notebooks

Estos cuadernos arman y exploran los archivos. La defensa no los proyecta.

El recorrido de la exposición es `src/academico.py`, `src/senales.py` y `app/index.html`. El protocolo está en `docs/plan_modelado.md`.

| Notebook | Qué hace |
|---|---|
| `01_descarga` | Descarga y arma los procesados si faltan. Controla duplicados, faltantes, fuentes de coordenadas y las reglas de calidad. |
| `02_eda` | Histograma, boxplot por mes, dispersión con la irradiación, matriz de correlación, cobertura por provincia y ceros. |
| `03_modelos` | Lee la evidencia (o reentrena con `REENTRENAR = True`): cinco modelos por partición, importancias, observado contra estimado, residuos y validación por parque. |
| `04_sitio` | Energía de un sitio nuevo con la misma función que usa el dashboard, la cuenta mes a mes y el caso límite de Ushuaia. |
| `05_casos` | Un parque real contra su estimación, ranking de parques por error en la prueba y conclusiones. |

| `06_senales` | Parques a revisar: lo esperado con un modelo que no vio el parque, ranking, sensibilidad, K-Means, PCA y DBSCAN. |
| `07_maui` | Análisis aparte, no se usa en la defensa. Planta por hora: calidad de los datos, mapa de calor, tiempo de aviso y otras plantas. |

No se guardan salidas en los notebooks versionados.

## Correr en vivo

Desde la carpeta del proyecto, sin red (los procesados ya están en `data/processed`):

```bash
.venv/bin/jupyter lab notebooks
```

Abrir `02_eda`, `03_modelos` o `06_senales` y correr todo. Tardan segundos. JupyterLab no está en `requirements.txt`: se instala aparte con `.venv/bin/python -m pip install jupyterlab`. VS Code con el intérprete `.venv` también sirve.

Si la carpeta del proyecto se mueve, los scripts del `.venv` quedan apuntando a la ruta vieja: recrearlo o usar `.venv/bin/python -m jupyter lab`.

En Colab, la primera celda clona el repositorio público e instala `requirements.txt`; los procesados vienen en el repositorio. Si Colab pide reiniciar la sesión después de instalar, se reinicia y se vuelve a correr todo.

- [02 · Análisis exploratorio](https://colab.research.google.com/github/imelinc/tpo-solar/blob/main/notebooks/02_eda.ipynb)
- [03 · Modelos](https://colab.research.google.com/github/imelinc/tpo-solar/blob/main/notebooks/03_modelos.ipynb)
- [04 · Sitio nuevo](https://colab.research.google.com/github/imelinc/tpo-solar/blob/main/notebooks/04_sitio.ipynb)
- [06 · Señales](https://colab.research.google.com/github/imelinc/tpo-solar/blob/main/notebooks/06_senales.ipynb)
