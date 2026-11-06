"""Empaqueta la evidencia argentina. No reentrena ni cambia cifras.

python -m src.academico recalcula. Después: python app/build_dashboard.py
"""
import json
import sys
from pathlib import Path

APP = Path(__file__).resolve().parent
sys.path.insert(0, str(APP.parent))
from src.config import DATA_PROCESSED


def main():
    ruta = DATA_PROCESSED / "defensa_evidencia.json"
    datos = json.loads(ruta.read_text())
    for key in ["regresion", "senales", "grilla", "serie", "parques", "clima", "tipico", "presets", "rango"]:
        if not datos.get(key):
            raise ValueError(f"Falta evidencia: {key}. Ejecutar python -m src.academico")
    if datos.get("pais") != "Argentina":
        raise ValueError("La evidencia no es la de Argentina")
    if len(datos["regresion"]["comparacion"]) != 6:
        raise ValueError("La comparación tiene que incluir los seis modelos")
    (APP / "datos.js").write_text("window.DEFENSA = " + json.dumps(datos, ensure_ascii=False, allow_nan=False, separators=(",", ":")) + ";\n")
    print(f"Empaquetado: {datos['regresion']['nombre']}; {len(datos['serie'])} meses-parque; {len(datos['parques'])} parques.")
    print(f"datos.js: {(APP / 'datos.js').stat().st_size / 1e6:.2f} MB. No requiere red.")


if __name__ == "__main__":
    main()
