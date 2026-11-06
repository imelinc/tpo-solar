"""Figuras y pantallas de respaldo, sin JavaScript ni red."""
import sys, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
import pandas as pd

DEST = ROOT / "docs" / "respaldo"
DEST.mkdir(parents=True, exist_ok=True)
for viejo in ["matriz.png", "deteccion.png", "station09.png", "eda.png"]:
    (DEST / viejo).unlink(missing_ok=True)
D = json.loads((ROOT / "data/processed/defensa_evidencia.json").read_text())
font_manager.fontManager.addfont(str(ROOT / "app/fonts/plex-regular.ttf"))
plt.rcParams.update({"font.family": "IBM Plex Sans", "font.size": 12, "axes.spines.top": False,
                    "axes.spines.right": False, "axes.spines.left": False, "axes.spines.bottom": False,
                    "axes.labelcolor": "#52636d", "text.color": "#18252d", "xtick.color": "#52636d",
                    "ytick.color": "#52636d", "figure.facecolor": "white", "axes.facecolor": "white"})
color = "#227a6c"

def save(name):
    plt.tight_layout(pad=2)
    plt.savefig(DEST / f"{name}.png", dpi=140, bbox_inches="tight")
    plt.close()

R = D["regresion"]
rows = R["comparacion"]
fig, ax = plt.subplots(figsize=(10, 5.2))
ax.barh([r["nombre"] for r in rows], [r["validacion"]["rmse"] for r in rows],
        color=[color if r["id"] == R["elegido"] else "#c5d3da" for r in rows], height=0.55)
ax.set(title="RMSE de validación · 2024", xlabel="Factor de capacidad")
ax.invert_yaxis(); ax.grid(axis="x", alpha=.15); save("modelos")
elegido = next(r for r in rows if r["id"] == R["elegido"])
S = D["senales"]
parque = S["ranking"][0]["central"]
serie = [r for r in D["serie"] if r["central"] == parque]
fig, ax = plt.subplots(figsize=(10, 5.2))
x = pd.to_datetime([r["fecha"] for r in serie])
ax.plot(x, [r["factor_capacidad"] for r in serie], color=color, label="Observado", lw=1.6)
ax.plot(x, [r["pred_oof"] for r in serie], color="#91a7b2", label="Esperado", lw=1.2)
ax.set(title=f"{serie[-1]['nombre']} · factor de capacidad", ylabel="Factor de capacidad")
ax.legend(frameon=False); ax.grid(axis="y", alpha=.15); save("serie")
demo = D["presets"][0]["resultado"]
fig, ax = plt.subplots(figsize=(10, 5.2))
ax.bar([m["mes"] for m in demo["meses"]], [m["gwh"] for m in demo["meses"]], color=color)
ax.set(title=f"Sitio nuevo, 2023 · {demo['potencia_mw']:.0f} MW", xlabel="Mes", ylabel="GWh")
ax.grid(axis="y", alpha=.15); save("sitio")

filas = S["ranking"][:6]
fig, ax = plt.subplots(figsize=(10, 5.2))
ax.barh([r["nombre"][:34] for r in filas], [r["gwh_faltante"] for r in filas], color=color, height=0.55)
ax.set(title="Parques a revisar · energía faltante desde 2025", xlabel="GWh")
ax.invert_yaxis(); ax.grid(axis="x", alpha=.15); save("senales")

def es(n, d=3):
    s = f"{n:,.{d}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")

t = elegido["test"]
R0 = S["resumen"]
slides = [
    ("Qué parque solar mirar primero", "Argentina · generación mensual",
     f"<img src='senales.png' alt='Parques a revisar'><p>{R0['sitios']} sitios con señal desde 2025, {es(R0['gwh_faltante'], 0)} GWh faltantes, unos USD {es(R0['usd_millones'], 1)} millones a USD {S['usd_mwh']}/MWh. Una señal no es una falla confirmada.</p><p>Ignacio Melinc · Matias Young · Francisco Fabrello · Malena Garcia Moraglio</p>"),
    ("Elegir con 2024", "La prueba queda aparte",
     f"<img src='modelos.png' alt='RMSE de validación'><p>{R['nombre']}. Prueba desde 2025: RMSE {es(t['rmse'])}, MAE {es(t['mae'])}, R² {es(t['r2'])}. Parque no visto en el entrenamiento: RMSE {es(R['cv_parques']['rmse'])}.</p>"),
    ("El parque con más energía faltante", serie[-1]["nombre"],
     "<img src='serie.png' alt='Factor observado y esperado'>"),
    ("Un sitio nuevo", "10 MW junto a un parque existente, clima de 2023",
     f"<img src='sitio.png' alt='Energía mensual estimada'><p>{es(demo['energia_gwh'], 2)} GWh en el año. A {es(demo['distancia_km'], 0)} km del clima copiado. Fuera del rectángulo de parques, el número es un caso límite.</p>"),
]
html = """<!doctype html><html lang="es-AR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>TPO Ciencia de Datos · Respaldo</title><style>@font-face{font-family:Plex;src:url('../../app/fonts/plex-regular.ttf')}*{box-sizing:border-box}body{margin:0;font:20px/1.55 Plex,Arial,sans-serif;color:#18252d;background:#f4f6f7}nav{padding:18px 5%;font-size:15px}section{min-height:100vh;padding:40px 6%;background:white;border-bottom:1px solid #e3eaed}h1{font-size:36px;font-weight:400;margin:0 0 9px}h2{font-size:19px;font-weight:400;color:#52636d;margin:0 0 24px}p{max-width:85ch;color:#52636d}img{max-width:100%;max-height:62vh}footer{font-size:13px;color:#52636d;margin-top:25px}@media(max-width:700px){section{padding:28px 20px}h1{font-size:28px}body{font-size:17px}}@media print{nav{display:none}section{min-height:0;height:100vh}}</style><nav>TPO Ciencia de Datos · Argentina · Defensa 12/11/2026</nav>"""
for title, subtitle, body in slides:
    html += f"<section><h1>{title}</h1><h2>{subtitle}</h2>{body}<footer>Fuente: src/academico.py y src/senales.py · Evaluación retrospectiva</footer></section>"
html += "</html>"
(DEST / "index.html").write_text(html)
print("Respaldo:", DEST / "index.html")
