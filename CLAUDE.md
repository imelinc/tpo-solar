# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Class project (TPO, ciencia de datos): predict the energy a solar plant should generate given weather, and flag when it underperforms. Documentation, comments and notebooks are in Spanish; keep that when editing them.

Notebooks 01 to 05 and the dashboard are complete. `docs/plan_modelado.md` holds the hypothesis and results; `docs/guion_defensa.md` is the 15-minute defense script.

## Commands

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt        # versions are pinned on purpose; don't bump casually
nbstripout --install                   # strips notebook outputs on commit (run once per clone)
python tests/test_features.py          # minimal asserts over src/ (pytest also works)
python app/build_dashboard.py          # regenerates app/datos.js and app/geo.js
open app/index.html                    # dashboard: static page, no server
```

There is no linter or CI. `tests/test_features.py` is the only check; keep it passing and extend it when `src/` logic changes.

Notebooks run either locally or in Colab. Their first cell clones `https://github.com/imelinc/tpo-solar.git` and installs `requirements.txt` when running under `google.colab`. That means Colab runs the code on GitHub `main`, not your local working tree: changes must be pushed to be seen there.

## Architecture

The project is a pipeline wired through the filesystem, not through a library API:

1. `notebooks/01_descarga.ipynb` downloads raw sources into `data/raw/` (gitignored, ~50 MB limit per file) and writes cleaned, joined parquet files to `data/processed/`.
2. `02_eda` explores `data/processed/`. `03_modelos` compares expected-generation models on months not seen in training and saves the chosen model to `models/` (`.pkl`, gitignored, ~43 MB).
3. `04_deteccion` computes the residual (real − expected), applies the detectors and, at the end, writes the small tables the dashboard needs: `data/processed/app_diario.parquet`, `app_horario.parquet` and `app_argentina.parquet` (committed). `05_negocio` turns alerts into MWh and USD.
4. `app/build_dashboard.py` reads those tables through `src/` and writes `app/datos.js` (data) and `app/geo.js` (Plotly topojson). `app/index.html` + `app/tablero.js` render them with the vendored `app/vendor/plotly-2.35.2.min.js`. The page opens with a double click (`file://`), so it must never fetch anything.

Shared code lives in `src/` and is imported by the notebooks and the dashboard builder. `src/config.py` defines the canonical paths (`DATA_RAW`, `DATA_PROCESSED`, `MODELS`) relative to the repo root; use these rather than hardcoding paths. `src/features.py` holds reusable feature functions; `agregar_features_tiempo` must stay in any feature pipeline (the team treats time as always-present). `src/deteccion.py` has `diario_flota`, `serie_planta` and `semaforo_flota`, which read the precalculated tables when `models/*.pkl` is missing (`precalculado=True`). `src/negocio.py` holds prices and assumptions; `app/tablero.js` repeats its two cleaning formulas and warns in the console if they drift.

Notebooks import `src` by appending the repo root to `sys.path` in their setup cell; `app/build_dashboard.py` does the same. Keep that pattern when adding new entry points.

Design context for the dashboard lives in `PRODUCT.md` (audience, constraints) and `DESIGN.md` (visual system).

## Hard constraints

- **The dashboard must work offline.** Nothing in `app/` calls live APIs (CAMMESA, Open-Meteo, etc.) or loads from a CDN; anything it shows comes from `data/processed/` via `app/datos.js`. The defense is planned without internet, on a classroom projector.
- Raw data is never committed. Anything that produces `data/processed/` or `models/` should be reproducible from `01_descarga` and the notebooks. After changing the model or the detector, rerun 03 → 04, then `python app/build_dashboard.py`, and commit the regenerated tables and `app/datos.js`.
- Notebooks are committed with outputs stripped (`nbstripout`). Don't commit notebook outputs.
- The headline model error is 6.04% (blind evaluation). 5.04% is not blind and appears only as a note.
- Team process (from README): one notebook per stage with one owner; work on a branch and merge to `main` through a reviewed PR.
