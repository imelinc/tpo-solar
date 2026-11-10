"""Bot de Telegram que consulta la evidencia de la defensa (defensa_evidencia.json).

No entrena ni calcula modelos: lee lo que ya produjo `python -m src.academico`.
Necesita internet y un token de @BotFather. El tablero y el gemelo siguen funcionando sin esto.

    set TELEGRAM_TOKEN=<token>            (PowerShell: $env:TELEGRAM_TOKEN="<token>")
    python -m src.bot_telegram             # escucha y responde
    python -m src.bot_telegram --probar "/revisar"        # responde en pantalla, sin red
    python -m src.bot_telegram --chat-id   # muestra tu chat id (antes escribile algo al bot)
    python -m src.bot_telegram --avisar    # manda el ranking a TELEGRAM_CHAT_ID y termina

Comandos: /revisar, /parque <nombre o código>, /sitio <lat> <lon> [MW] [año], /modelos, /resumen, /ayuda.
Una señal no es una falla confirmada: el bot lo repite.
"""
from __future__ import annotations

import calendar
import html
import json
import math
import os
import sys
import time
import unicodedata

from src.config import DATA_PROCESSED

API = "https://api.telegram.org/bot{token}/{metodo}"
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
AYUDA = (
    "☀️ <b>Parques solares argentinos</b>\n"
    "/revisar — parques con señal, de mayor a menor energía faltante\n"
    "/parque <i>nombre o código</i> — un parque: potencia, señal y último mes\n"
    "/sitio <i>lat lon [MW] [año]</i> — energía estimada de un sitio nuevo\n"
    "/modelos — los seis modelos y cuál se eligió\n"
    "/resumen — cuántos meses y GWh quedaron marcados\n"
    "Una señal no es una falla confirmada: es un parque que conviene mirar primero."
)


def cargar(ruta=None) -> dict:
    return json.loads((ruta or DATA_PROCESSED / "defensa_evidencia.json").read_text(encoding="utf-8"))


def _norm(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")


def _n(v: float, d: int = 1) -> str:
    return f"{v:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _e(s) -> str:
    return html.escape(str(s))


def _km(lat1, lon1, lat2, lon2) -> float:
    x = math.radians(lon2 - lon1) * math.cos(math.radians((lat1 + lat2) / 2))
    return 6371.0 * math.hypot(x, math.radians(lat2 - lat1))


def cmd_revisar(ev: dict, n: int = 5) -> str:
    s = ev["senales"]
    filas = []
    for i, r in enumerate(s["ranking"][:n], 1):
        usd = r["gwh_faltante"] * s["usd_mwh"] / 1000
        filas.append(f"{i}. <b>{_e(r['nombre'].strip())}</b> ({_e(r['provincia'].title())})\n"
                     f"   rinde {round(r['rinde_modelo'] * 100)} % del modelo y {round(r['rinde_vecinos'] * 100)} % de sus vecinos "
                     f"desde {r['desde'][:7]} ({r['meses']} meses). Faltan {_n(r['gwh_faltante'], 0)} GWh ≈ US$ {_n(usd)} M a {s['usd_mwh']} US$/MWh.")
    return (f"🔎 <b>Parques a revisar primero</b> ({len(s['ranking'])} con señal)\n" + "\n".join(filas) +
            "\n\nUna señal no es una falla confirmada. La plata es a un precio supuesto.")


def buscar_parque(ev: dict, texto: str) -> list[dict]:
    q = _norm(texto.strip())
    exacto = [p for p in ev["parques"] if _norm(p["central"]) == q]
    return exacto or [p for p in ev["parques"] if q and (q in _norm(p["nombre"]) or q in _norm(p["central"]))]


def _ultimo_mes(central: str):
    import pandas as pd
    d = pd.read_parquet(DATA_PROCESSED / "defensa_argentina.parquet", columns=["central", "fecha", "factor_capacidad", "pred_oof", "estado"])
    d = d[d["central"].eq(central)].sort_values("fecha")
    return None if d.empty else d.iloc[-1]


def cmd_parque(ev: dict, texto: str, ultimo=_ultimo_mes) -> str:
    if not texto.strip():
        return "Usá /parque seguido de un nombre o código. Ejemplo: /parque tocota"
    hallados = buscar_parque(ev, texto)
    if not hallados:
        return f"No encontré ningún parque con «{_e(texto)}». Probá con una parte del nombre o el código (ej. TOC3FV)."
    if len(hallados) > 1:
        lista = "\n".join(f"• {_e(p['nombre'].strip())} — {p['central']}" for p in hallados[:8])
        return "Encontré varios, escribí el código:\n" + lista
    p = hallados[0]
    sitio = {"UL42FV": "ULL4FV"}.get(p["central"], p["central"])
    r = next((x for x in ev["senales"]["ranking"] if x["central"] == sitio), None)
    out = [f"☀️ <b>{_e(p['nombre'].strip())}</b> ({p['central']})",
           f"{_e(p['provincia'].title())} · {_n(p['potencia_mw'], 0)} MW · lat {_n(p['lat'], 2)}, lon {_n(p['lon'], 2)}"]
    if r:
        usd = r["gwh_faltante"] * ev["senales"]["usd_mwh"] / 1000
        out.append(f"⚠️ <b>Señal</b>: rinde {round(r['rinde_modelo'] * 100)} % del modelo y {round(r['rinde_vecinos'] * 100)} % de sus vecinos "
                   f"desde {r['desde'][:7]} ({r['meses']} meses). Faltan {_n(r['gwh_faltante'], 0)} GWh ≈ US$ {_n(usd)} M a un precio supuesto.")
    else:
        out.append("Sin señal: no estuvo dos meses seguidos por debajo del 80 % del modelo y de sus vecinos.")
    try:
        u = ultimo(p["central"])
    except Exception:  # sin pandas o sin el parquet: el resto de la respuesta sirve igual
        u = None
    if u is not None:
        esp = f", esperado {_n(u['pred_oof'], 2)}" if u["pred_oof"] == u["pred_oof"] else ""
        out.append(f"Último mes ({u['fecha'][:7]}): factor de capacidad observado {_n(u['factor_capacidad'], 2)}{esp}. Estado: {u['estado']}.")
    out.append("Una señal no es una falla confirmada.")
    return "\n".join(out)


def consultar_sitio(ev: dict, lat: float, lon: float, anio: int, mw: float) -> dict:
    """Misma cuenta que src.academico.consultar, sin numpy: celda más cercana de la grilla, factor × MW × horas."""
    g = ev["grilla"]
    if mw <= 0:
        raise ValueError("La potencia tiene que ser mayor que cero")
    i = min(range(len(g["lats"])), key=lambda k: abs(g["lats"][k] - lat))
    j = min(range(len(g["lons"])), key=lambda k: abs(g["lons"][k] - lon))
    clave = str(anio) if anio in g["anios"] else "0"
    base = (i * len(g["lons"]) + j) * 12
    energia = horas = 0.0
    meses = []
    for mes in range(1, 13):
        f = g["factores"][clave][base + mes - 1]
        if f is None:
            continue
        h = calendar.monthrange(anio, mes)[1] * 24
        gwh = f * mw * h / 1000
        energia += gwh
        horas += h
        meses.append((mes, f, gwh))
    if not meses:
        raise ValueError("Ese sitio no tiene clima de referencia")
    r = ev["rango"]
    cercano = min(ev["parques"], key=lambda p: _km(g["lats"][i], g["lons"][j], p["lat"], p["lon"]))
    return {"energia_gwh": energia, "factor": energia * 1000 / (mw * horas), "meses": meses, "tipico": clave == "0",
            "dentro": r["lat_min"] <= lat <= r["lat_max"] and r["lon_min"] <= lon <= r["lon_max"],
            "parque_cercano": cercano, "km_cercano": _km(lat, lon, cercano["lat"], cercano["lon"])}


def cmd_sitio(ev: dict, texto: str) -> str:
    uso = "Usá /sitio <i>lat lon [MW] [año]</i>. Ejemplo: /sitio -28.12 -67.27 10 2025"
    try:
        v = [float(x.replace(",", ".")) for x in texto.split()]
        lat, lon = v[0], v[1]
        mw = v[2] if len(v) > 2 else 10.0
        anio = int(v[3]) if len(v) > 3 else 2025
        if not (-56 <= lat <= -21 and -74 <= lon <= -53):
            return "Esas coordenadas quedan fuera de Argentina. " + uso
        r = consultar_sitio(ev, lat, lon, anio, mw)
    except (ValueError, IndexError) as exc:
        return (str(exc) + "\n" if str(exc) and "convert" not in str(exc) and "list index" not in str(exc) else "") + uso
    mejor = max(r["meses"], key=lambda m: m[1])
    peor = min(r["meses"], key=lambda m: m[1])
    p = r["parque_cercano"]
    out = [f"📍 <b>Sitio nuevo</b> ({_n(lat, 2)}, {_n(lon, 2)}) · {_n(mw, 0)} MW · {anio}",
           f"Energía estimada: <b>{_n(r['energia_gwh'])} GWh</b> al año (factor de capacidad {_n(r['factor'], 2)}).",
           f"Mejor mes: {MESES[mejor[0] - 1]} ({_n(mejor[1], 2)}). Peor: {MESES[peor[0] - 1]} ({_n(peor[1], 2)}).",
           f"Clima copiado del parque más cercano: {_e(p['nombre'].strip())}, a {round(r['km_cercano'])} km."]
    if r["tipico"]:
        out.append(f"El año {anio} no está medido: usa el clima típico anterior a 2024.")
    if not r["dentro"]:
        out.append("⚠️ Está fuera del rectángulo de parques con que se entrenó: tomalo como caso límite.")
    out.append("Es una estimación retrospectiva, no producción medida.")
    return "\n".join(out)


def cmd_modelos(ev: dict) -> str:
    r = ev["regresion"]
    filas = sorted(r["comparacion"], key=lambda m: m["validacion"]["rmse"])
    cuerpo = "\n".join(f"{'✅' if m['id'] == r['elegido'] else '•'} {_e(m['nombre'])}: RMSE 2024 {_n(m['validacion']['rmse'], 3)}"
                       f" · prueba {_n(m['test']['rmse'], 3)} · R² {_n(m['test']['r2'], 2)}" for m in filas)
    return (f"📊 <b>Modelos</b> (elegido por menor RMSE de validación 2024)\n{cuerpo}\n"
            f"Prueba desde 2025, retrospectiva. Para un parque que el modelo no vio, RMSE {_n(r['cv_parques']['rmse'], 3)}.")


def cmd_resumen(ev: dict) -> str:
    s = ev["senales"]["resumen"]
    return (f"📌 <b>Resumen de señales</b> ({s['desde'][:7]} a {s['hasta'][:7]})\n"
            f"{s['marcados']} meses de parque marcados en {s['sitios']} sitios, de {s['meses']} meses evaluados.\n"
            f"Energía faltante: {_n(s['gwh_faltante'], 0)} GWh ({_n(s['pct'])} % de lo generado) ≈ US$ {_n(s['usd_millones'])} M a "
            f"{ev['senales']['usd_mwh']} US$/MWh.\nSeñal, no falla confirmada; la plata es a un precio supuesto.")


def responder(texto: str, ev: dict) -> str:
    partes = (texto or "").strip().split(maxsplit=1)
    if not partes or not partes[0].startswith("/"):
        return "Escribí /ayuda para ver qué puedo consultar."
    cmd, resto = partes[0].split("@")[0].lower(), (partes[1] if len(partes) > 1 else "")
    if cmd in ("/start", "/ayuda", "/help"):
        return AYUDA
    if cmd == "/revisar":
        return cmd_revisar(ev)
    if cmd == "/parque":
        return cmd_parque(ev, resto)
    if cmd == "/sitio":
        return cmd_sitio(ev, resto)
    if cmd == "/modelos":
        return cmd_modelos(ev)
    if cmd == "/resumen":
        return cmd_resumen(ev)
    return "No conozco ese comando. Escribí /ayuda."


def llamar(token: str, metodo: str, **params) -> dict:
    import requests
    r = requests.post(API.format(token=token, metodo=metodo), data=params, timeout=40)
    r.raise_for_status()
    return r.json()


def enviar(token: str, chat: str | int, texto: str) -> None:
    llamar(token, "sendMessage", chat_id=chat, text=texto, parse_mode="HTML", disable_web_page_preview="true")


def escuchar(token: str, ev: dict) -> None:
    print("Bot escuchando. Ctrl+C para cortar.")
    offset = 0
    while True:
        try:
            for u in llamar(token, "getUpdates", offset=offset, timeout=30).get("result", []):
                offset = u["update_id"] + 1
                m = u.get("message") or {}
                if m.get("text"):
                    enviar(token, m["chat"]["id"], responder(m["text"], ev))
        except Exception as exc:  # la red se cae: reintentar sin matar el bot
            print("Error de red, reintento en 5 s:", type(exc).__name__)
            time.sleep(5)


def main(argv: list[str]) -> int:
    ev = cargar()
    if "--probar" in argv:
        i = argv.index("--probar")
        print(html.unescape(responder(argv[i + 1] if i + 1 < len(argv) else "/ayuda", ev)))
        return 0
    token = os.environ.get("TELEGRAM_TOKEN", "")
    if not token:
        print("Falta la variable de entorno TELEGRAM_TOKEN (el token de @BotFather). No lo pegues en el código ni en git.")
        return 1
    if "--chat-id" in argv:
        # Antes hay que escribirle un mensaje al bot desde el celular.
        vistos = {}
        for u in llamar(token, "getUpdates", timeout=0).get("result", []):
            c = (u.get("message") or (u.get("callback_query") or {}).get("message") or {}).get("chat")
            if c:
                vistos[c["id"]] = c.get("title") or c.get("first_name") or c.get("username") or "?"
        if not vistos:
            print("No hay mensajes todavía: escribile algo al bot desde Telegram y volvé a correr esto.")
            return 1
        for cid, nombre in vistos.items():
            print(f"chat id {cid}  ({nombre})")
        return 0
    if "--avisar" in argv:
        chat = os.environ.get("TELEGRAM_CHAT_ID", "")
        if not chat:
            print("Falta TELEGRAM_CHAT_ID (el número de tu chat).")
            return 1
        enviar(token, chat, cmd_revisar(ev))
        print("Aviso enviado.")
        return 0
    escuchar(token, ev)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
