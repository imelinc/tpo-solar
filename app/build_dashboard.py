"""Empaqueta evidencia calculada y recursos locales para la defensa sin conexión.

python -m src.academico recalcula. Este comando solo empaqueta; no altera cifras.
"""
import json
import sys
from pathlib import Path

APP = Path(__file__).resolve().parent
sys.path.insert(0, str(APP.parent))
from src.config import DATA_PROCESSED


def main():
    ruta = DATA_PROCESSED / 'defensa_evidencia.json'
    datos = json.loads(ruta.read_text())
    # Un artefacto incompleto no reemplaza una aplicación que ya funciona.
    for key in ['regresion', 'regresion_argentina', 'simulaciones', 'diario', 'argentina', 'clases']:
        if not datos.get(key):
            raise ValueError(f'Falta evidencia: {key}. Ejecutar python -m src.academico')
    if len({r['id'] for r in datos['simulaciones']}) != len(datos['simulaciones']):
        raise ValueError('Simulaciones con identidad duplicada')
    for r in datos['diario']:
        if not r['decide'] and r['estado'] == 'normal':
            raise ValueError('Un día sin decisión no puede mostrarse normal')
    (APP / 'datos.js').write_text('window.DEFENSA = ' + json.dumps(datos, ensure_ascii=False, allow_nan=False, separators=(',', ':')) + ';\n')
    print(f'Empaquetado: {len(datos["simulaciones"])} simulaciones; {len(datos["diario"])} días-planta; {len(datos["argentina"])} meses-parque.')
    print(f'datos.js: {(APP / "datos.js").stat().st_size/1e6:.2f} MB. No requiere red.')


if __name__ == '__main__':
    main()
