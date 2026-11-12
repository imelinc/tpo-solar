"""Arma gemelo/index.html y app/gemelo.html: el gemelo digital del Detector Solar con los parques y el modelo del repo.

Lee data/processed (defensa_evidencia.json y defensa_argentina.parquet), arma un bloque de datos
y lo inserta en gemelo/gemelo_base.html junto con gemelo/repo_panel.js. No entrena nada.

    python gemelo/build_gemelo.py
"""
from __future__ import annotations

import base64
import json
import re
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from src.config import DATA_PROCESSED  # noqa: E402

AQUI = Path(__file__).resolve().parent
# Igual que MISMO_SITIO de src/senales.py (no se importa para no pedir scikit-learn): una ampliación es el mismo sitio.
MISMO_SITIO = {"UL42FV": "ULL4FV"}
ESTADOS = ["normal", "sin_vecinos", "parque", "arranque", "zona"]


def datos_repo() -> dict:
    ev = json.loads((DATA_PROCESSED / "defensa_evidencia.json").read_text(encoding="utf-8"))
    d = pd.read_parquet(DATA_PROCESSED / "defensa_argentina.parquet")
    elegido = next(m for m in ev["regresion"]["comparacion"] if m["id"] == ev["regresion"]["elegido"])
    meses: dict[str, dict] = {}
    for r in d.itertuples():
        esp = None if pd.isna(r.pred_oof) else round(float(r.pred_oof), 4)
        meses.setdefault(r.central, {})[r.fecha[:7]] = [round(float(r.factor_capacidad), 4), esp, ESTADOS.index(r.estado)]
    parques = [{"central": p["central"], "nombre": p["nombre"], "prov": p["provincia"].title(), "lat": round(p["lat"], 4),
                "lon": round(p["lon"], 4), "mw": p["potencia_mw"], "m": meses.get(p["central"], {})} for p in ev["parques"]]
    ranking = {r["central"]: {k: r[k] for k in ("desde", "hasta", "meses", "rinde_modelo", "rinde_vecinos", "gwh_faltante")}
               for r in ev["senales"]["ranking"]}
    return {"parques": parques, "ranking": ranking, "mismo_sitio": MISMO_SITIO, "estados": ESTADOS,
            "modelo": ev["regresion"]["nombre"], "rmse_test": elegido["test"]["rmse"], "usd_mwh": ev["senales"]["usd_mwh"],
            "fecha_evaluacion": ev["fecha_evaluacion"], "fuente": "CAMMESA mensual y Open-Meteo, defensa_evidencia.json",
            "resumen": {k: ev["senales"]["resumen"][k] for k in ("sitios", "gwh_faltante", "usd_millones", "pct")}}


def reemplazar(html: str, viejo: str, nuevo: str) -> str:
    if html.count(viejo) != 1:
        raise SystemExit(f"El ancla aparece {html.count(viejo)} veces (se esperaba 1): {viejo[:70]!r}")
    return html.replace(viejo, nuevo)


CSS = """
#parque{max-width:250px}
#repoBody .selhd{margin-bottom:6px}
#repoBody .diag{margin:6px 0}
#repoSec canvas{width:100%;height:150px;display:block;margin-top:6px}
#repoSec .chcap{margin-top:4px}
"""

HTML_PARQUE = """<label class="site" for="parque"><span class="chip" style="padding:4px 6px">Parque real</span>
      <select id="parque"><option value="">— planta de ejemplo —</option></select></label>
    <div class="escenario-grupo"><span class="escenarios-lab">Escenario</span>
    <div id="escenarios" role="group" aria-label="Escenario"><button data-m="manual" aria-pressed="true">Manual</button><button data-m="auto" aria-pressed="false">Autónomo</button></div></div>
    <div class="clock">"""

HTML_SECCION = """<div class="sec" id="repoSec">
      <h3>Parque real · modelo del repo</h3>
      <div id="repoBody"></div>
      <canvas class="ch" id="chRepo" hidden aria-label="Factor de capacidad mensual: observado, esperado por el modelo y simulado por el gemelo"></canvas>
      <div class="chcap" id="repoCap" hidden><span><i style="background:var(--ink)"></i>Observado (CAMMESA)</span><span><i style="background:var(--sel)"></i>Esperado (modelo)</span><span><i style="background:var(--muted)"></i>Gemelo sano</span></div>
      <p class="note" id="repoFuente" style="border:0;padding-top:6px"></p>
    </div>
    <div class="sec">
      <h3>Alertas</h3>"""


MARCA = ('<div class="brand"><svg class="brand-mark" viewBox="0 0 32 32" aria-hidden="true"><rect x=".75" y=".75" width="30.5" height="30.5"/>'
         '<path class="ticks" d="M8 .75v4M16 .75v6M24 .75v4M.75 8h4M.75 16h6M.75 24h4"/><circle cx="17" cy="15" r="6.5"/></svg>'
         '<div class="bn"><b>TPO<i>/</i>Gemelo solar</b><span id="subt">—</span></div></div>')
PRES_HTML = ('<div class="pres" id="pres" hidden aria-live="polite"><div class="pres-cab"><span class="pres-n"></span><span class="pres-t"></span></div>'
             '<div class="pres-x"></div><div class="pres-e"></div><p class="pres-v"></p>'
             '<div class="pres-b"><button class="btn pres-prev">← Anterior</button><button class="btn pres-a" hidden></button>'
             '<button class="btn primary pres-next">Siguiente →</button></div></div>')
NAV_TABLERO = ('<nav class="tablero-nav" aria-label="Vistas del tablero"><a href="__TABLERO__#revisar">Parques</a><a href="__TABLERO__#sitio">Sitio nuevo</a>'
               '<a href="__TABLERO__#modelos">Modelos</a><a href="__TABLERO__#atlas">Datos</a><a aria-current="page">Gemelo</a><a href="__PRESENTACION__">Presentación</a></nav>')
REDUCED = "@media (prefers-reduced-motion: reduce){.toast,.lbl .dot.bad{animation:none}}"
MARCA_CONTROLES = "// =============================== controles ==============================="


def estilo() -> str:
    css = (AQUI / "estilo_tpo.css").read_text(encoding="utf-8")
    for f in (RAIZ / "app" / "fonts").glob("barlow*.woff2"):
        css = css.replace(f"__B64_{f.stem}__", base64.b64encode(f.read_bytes()).decode())
    if "__B64_" in css:
        raise SystemExit("Falta una fuente de app/fonts para estilo_tpo.css")
    return css


def reemplazar_bloque(html: str, desde: str, hasta: str, nuevo: str) -> str:
    patron = re.compile(re.escape(desde) + ".*?(?=" + re.escape(hasta) + ")", re.S)
    if len(patron.findall(html)) != 1:
        raise SystemExit(f"No se encontró un único bloque entre {desde[:40]!r} y {hasta[:40]!r}")
    return patron.sub(lambda _: nuevo, html, count=1)


def construir() -> Path:
    html = (AQUI / "gemelo_base.html").read_text(encoding="utf-8")
    js = (AQUI / "repo_panel.js").read_text(encoding="utf-8")
    js = js.replace("__REPO_JSON__", json.dumps(datos_repo(), ensure_ascii=False, separators=(",", ":")))
    esc = (AQUI / "escenarios.js").read_text(encoding="utf-8")
    esc += "\n" + (AQUI / "presentacion.js").read_text(encoding="utf-8")
    tg = (AQUI / "telegram_bidireccional.js").read_text(encoding="utf-8")

    # --- parques reales y modelo del repo ---
    html = reemplazar(html, "<title>Gemelo Solar DKASC</title>", "<title>Gemelo Solar · TPO Ciencia de Datos</title>")
    html = reemplazar(html, REDUCED, REDUCED + CSS)
    html = reemplazar(html, '<div class="clock">', HTML_PARQUE)
    html = reemplazar(html, "<small>Si la planta fuera de 1 MW, hoy estaría perdiendo</small>",
                      '<small id="fMWlab">Si la planta fuera de 1 MW, hoy estaría perdiendo</small>')
    html = reemplazar(html, '<div class="sec">\n      <h3>Alertas</h3>', HTML_SECCION)
    html = reemplazar(html, "ESCALA_MW = 1000 / KWP_TOTAL;", "ESCALA_BASE = 1000 / KWP_TOTAL;\nlet ESCALA_MW = ESCALA_BASE, PARQUE = null;")
    html = reemplazar(html, "en una planta de 1 MW)", "${MWTXT(false)})")
    html = reemplazar(html, "${usd(al.loss * ESCALA_MW)} en 1 MW)", "${usd(al.loss * ESCALA_MW)} ${MWTXT(true)})")
    html = reemplazar(html, '  select(inicial ? 3 : S.sel);\n}\ndocument.getElementById("sitio").addEventListener("change", e => cambiarSitio(e.target.value, false));',
                      '  select(inicial ? 3 : S.sel); renderRepo();\n}\n'
                      'document.getElementById("sitio").addEventListener("change", e => { elegirParque(""); cambiarSitio(e.target.value, false); });')
    html = reemplazar(html, 'cambiarSitio("alice", true); setSpeed(3600);', "iniciarRepo(); iniciarEscenarios(); iniciarPresentacion(); " + 'cambiarSitio("alice", true); setSpeed(3600);')
    html = reemplazar(html, "window.__gemelo = { S,", "window.__gemelo = { elegirParque, setModo, S,")
    # El árbol que diagnostica la causa se entrenó con fallas simuladas: el repo no lo valida (el docente dijo «fuerte no»).
    if html.count("Causa probable:") < 2:
        raise SystemExit("No se encontró el texto «Causa probable:» donde se esperaba")
    html = html.replace("Causa probable:", "Hipótesis (árbol entrenado con fallas simuladas, no validada):")

    # Mismo criterio que el repo: la señal mensual pide dos meses seguidos (no «15 días»).
    html = reemplazar(html, "Una revisión mensual tarda ~15 días.", "Con datos mensuales, la señal del repo pide dos meses seguidos.")
    html = reemplazar(html, "<b>Diagnóstico: ${al.dx.causa}</b>", "<b>Hipótesis (no validada): ${al.dx.causa}</b>")

    # --- estilo del tablero ---
    html = reemplazar(html, '<html lang="es">', '<html lang="es" data-theme="light">')
    html = re.sub(r'<link rel="(?:preconnect|stylesheet)" href="https://fonts\.g[^>]*>\n?', "", html)
    html = reemplazar(html, '<div class="brand"><b>Gemelo Solar</b><span id="subt">—</span></div>', MARCA + NAV_TABLERO)
    html = reemplazar(html, REDUCED + CSS, REDUCED + CSS + "\n" + estilo())

    # --- escenarios manual y autónomo, Telegram en los dos sentidos ---
    html = reemplazar(html, '<button class="btn" id="tgBtn" hidden>Telegram</button>',
                      '<button class="btn" id="presBtn" aria-pressed="false">Presentar</button>'
                      '<button class="btn" id="grillaBtn" aria-pressed="true">Grilla</button><button class="btn" id="tgBtn" hidden>Telegram</button>')
    html = reemplazar(html, '<div class="toasts" id="toasts" aria-live="polite"></div>',
                      PRES_HTML + '\n    <div class="toasts" id="toasts" aria-live="polite"></div>')
    html = reemplazar(html, '<span class="rl">vs. vecinos —</span>', '<span class="rl">— de sus vecinos</span>')
    html = reemplazar(html, 'c.querySelector(".rl").textContent = `vs. vecinos ${Math.round(rel * 100)} %`;',
                      'c.querySelector(".rl").textContent = `rinde ${Math.round(rel * 100)} % de sus vecinos`;')
    html = reemplazar(html, '<div class="toasts" id="toasts" aria-live="polite"></div>',
                      '<div class="modo-banner" id="modoBanner" hidden></div>\n    <div class="toasts" id="toasts" aria-live="polite"></div>')
    html = reemplazar(html, '<div class="r"><button class="btn" id="tgTest">Probar</button>',
                      '<small id="tgEstado" data-ok="1"></small>\n      <div class="r"><button class="btn" id="tgBorrar">Olvidar</button><button class="btn" id="tgTest">Probar</button>')
    html = reemplazar(html, "Creá un bot con @BotFather, mandale un mensaje y pegá acá el token y tu chat id.",
                      "Pegá el código que te dio @BotFather y tocá Guardar. Antes mandale cualquier mensaje al bot desde Telegram: así te encuentra.")
    html = reemplazar(html, '<input id="tgChat" placeholder="Chat id (número)" autocomplete="off">',
                      '<input id="tgChat" type="hidden">')
    html = reemplazar(html, '<input id="tgTok" placeholder="Token del bot" autocomplete="off">',
                      '<input id="tgTok" type="password" placeholder="Token del bot" autocomplete="off">')
    html = reemplazar(html, "Se guardan solo en este navegador.",
                      "Se guardan solo en este navegador (no van al repo ni a la web). El gemelo avisa y escucha al técnico: no abras a la vez el bot de Python con el mismo token.")
    html = reemplazar_bloque(html, "// =============================== Telegram (solo versión descargada)",
                             "// =============================== paso horario", tg + "\n")
    html = reemplazar_bloque(html, "// Telegram (solo en el archivo descargado", "window.__gemelo = {", "")
    html = reemplazar(html, MARCA_CONTROLES, js + "\n" + esc + "\n" + MARCA_CONTROLES)
    html = reemplazar(html, "function processSchedule() { for (const e of S.schedule) if (!e.done && S.t >= e.at) { e.done = true; inyectar(e.g, e.tipo, e.at); } }",
                      "function processSchedule() { for (const e of S.schedule) if (!e.done && S.t >= e.at) { e.done = true; inyectar(e.g, e.tipo, e.at); } autoTick(); }")
    html = reemplazar(html, 'function renderFeed() {\n  const el = document.getElementById("feed");',
                      'function renderFeed() {\n  renderEscenario();\n  const el = document.getElementById("feed");')
    html = reemplazar(html, 'al.res && al.resTxt ? al.resTxt + "." : al.body;', 'al.res && al.resTxt ? al.resTxt + "." : al.body + pendTxt(al);')
    html = reemplazar(html, 'b.textContent = al.fleet ? "Limpiar toda la planta" : "Mandar técnico";',
                      'b.textContent = al.fleet ? "Limpiar toda la planta" : (MODO === "auto" ? "Simular aviso del técnico" : "Mandar técnico");')
    if html.count("__TABLERO__") != 4:
        raise SystemExit("El menú del tablero no quedó armado")
    destino = AQUI / "index.html"
    destino.write_text(html.replace("__TABLERO__", "../app/index.html").replace("__PRESENTACION__", "../app/presentacion.html"), encoding="utf-8")
    seccion = RAIZ / "app" / "gemelo.html"            # la sección «Gemelo» del tablero publicado
    seccion.write_text(html.replace("__TABLERO__", "index.html").replace("__PRESENTACION__", "presentacion.html"), encoding="utf-8")
    return destino


if __name__ == "__main__":
    d = construir()
    print(f"Escrito {d} ({d.stat().st_size / 1e6:.2f} MB) y app/gemelo.html (sección del tablero)")
