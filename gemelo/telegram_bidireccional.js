// =============================== Telegram: avisa y escucha al técnico (solo versión descargada) ===============================
// Reemplaza al bloque original, que solo mandaba mensajes. Acá el gemelo manda la alerta con un botón «Reparado»
// y lee la respuesta del técnico (botón o /reparado B) para dar la falla por resuelta.
// Telegram permite leer sus respuestas desde el navegador (Access-Control-Allow-Origin: *), así que no hace falta servidor.
// Usa getUpdates: no correr al mismo tiempo `python -m src.bot_telegram` con el mismo token (Telegram da error 409).
// Telegram permite leer sus respuestas desde cualquier página (CORS abierto), también la publicada.
// El token y el chat id se cargan desde el botón «Telegram» y quedan solo en el localStorage de ese navegador: no van en el repo.
const PUEDE_TG = true;
const TG = (() => { try { return JSON.parse(localStorage.getItem("gemeloTG") || "{}"); } catch (e) { return {}; } })();
let tgOffset = null, tgTimer = null;
function tgEstado(t, ok) { const el = document.getElementById("tgEstado"); if (el) { el.textContent = t; el.dataset.ok = ok ? "1" : "0"; } TG.ult = { t, ok }; }
// Modo «servidor»: si Netlify tiene el token guardado (función netlify/functions/telegram.mjs), el gemelo
// habla con Telegram a través de ella y no hace falta cargar nada en ningún dispositivo.
// Modo «navegador»: el de siempre, con el token pegado en este navegador.
const TG_SERVIDOR = "/.netlify/functions/telegram";
let TG_MODO = "navegador";
async function tgDetectarServidor() {
  if (location.protocol === "file:") return null;
  try {
    const r = await fetch(TG_SERVIDOR, { method: "GET", cache: "no-store" });
    if (!r.ok || !(r.headers.get("content-type") || "").includes("json")) return null;
    const j = await r.json(); return j && j.configurado && j.chat ? String(j.chat) : null;
  } catch (e) { return null; }
}
function tgLlamar(metodo, p) {
  if (TG_MODO === "servidor")
    return fetch(TG_SERVIDOR, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ metodo, params: p }) }).then(r => r.json());
  return fetch(`https://api.telegram.org/bot${TG.tok}/${metodo}`, { method: "POST", body: new URLSearchParams(p) }).then(r => r.json());
}
function tgEnviar(texto, extra = {}) {
  if (!PUEDE_TG || !TG.tok || !TG.chat) return Promise.resolve(null);
  return tgLlamar("sendMessage", { chat_id: TG.chat, text: texto, parse_mode: "HTML", ...extra })
    .then(r => { tgEstado(r.ok ? "Mensaje enviado ✓" : "Telegram respondió: " + (r.description || "error"), r.ok); return r; })
    .catch(() => { tgEstado("No se pudo conectar con Telegram (¿hay internet?)", false); return null; });
}
function telegram(al, forzar) {
  if (!PUEDE_TG || !TG.tok || !TG.chat || (!forzar && (!TG.on || !(al.sev === "bad" || al.sev === "warn")))) return;
  const pedir = !forzar && al.g != null && al.fix, L = pedir ? GRUPOS[al.g].id : "";
  const txt = `☀️ <b>Gemelo Solar</b> · ${SITE.nm.split(" · ")[0]}${repoTxt()}\n🚨 <b>${al.title}</b>\n${al.body}` +
    (al.dx ? `\nHipótesis (árbol entrenado con fallas simuladas, no validada): <b>${al.dx.causa}</b> (${Math.round(al.dx.p * 100)} %)` : "") +
    (al.det != null ? `\nDetectado ${fmtDur(al.det)} después de la falla.` : "") + (al.loss != null ? `\nSe pierden ${usd(al.loss)} por día.` : "") +
    (pedir ? `\n\n🔧 Cuando lo repares, tocá el botón o escribí /reparado ${L}.` : "");
  const extra = pedir ? { reply_markup: JSON.stringify({ inline_keyboard: [[{ text: `🔧 Reparado · Grupo ${L}`, callback_data: `fix:${al.g}` }]] }) } : {};
  if (pedir) al.tgEnviado = S.t;
  tgEnviar(txt, extra);
}
function tgIniciar() {
  clearInterval(tgTimer); tgOffset = null;
  if (PUEDE_TG && TG.tok && TG.chat) { tgPoll(); tgTimer = setInterval(tgPoll, 2500); }
}
async function tgPoll() {
  if (!TG.tok || !TG.chat) return;
  try {
    if (tgOffset == null) {      // la primera vez se descartan los mensajes viejos
      const r = await tgLlamar("getUpdates", { offset: -1, timeout: 0 });
      if (!r.ok) { tgEstado("Telegram respondió: " + (r.description || "error"), false); return; }
      const u = r.result || []; tgOffset = u.length ? u[u.length - 1].update_id + 1 : 0; tgEstado("Escuchando al técnico ✓", true); return;
    }
    const r = await tgLlamar("getUpdates", { offset: tgOffset, timeout: 0, allowed_updates: JSON.stringify(["message", "callback_query"]) });
    if (!r.ok) { tgEstado("Telegram respondió: " + (r.description || "error"), false); return; }
    for (const u of r.result) { tgOffset = u.update_id + 1; tgUpdate(u); }
  } catch (e) { tgEstado("Sin conexión con Telegram", false); }
}
function abiertas() { return GRUPOS.map((g, a) => a).filter(a => S.fault[a] || (S.alert[a] && !S.alert[a].res)); }
function tgUpdate(u) {
  const cq = u.callback_query, m = u.message, chat = String(cq ? cq.message && cq.message.chat && cq.message.chat.id : m && m.chat && m.chat.id);
  if (chat !== String(TG.chat)) return;           // solo escucha al chat configurado
  if (cq) {
    const k = /^fix:([0-3])$/.exec(cq.data || ""); if (!k) return;
    const ok = repararDesdeTelegram(+k[1]);
    tgLlamar("answerCallbackQuery", { callback_query_id: cq.id, text: ok ? "Reparado ✓" : "Ese grupo no tenía alertas abiertas" }).catch(() => {});
    return;
  }
  const t = ((m && m.text) || "").trim().toLowerCase(); if (!t) return;
  const letra = (/\b([abcd])\b/.exec(t.replace(/^\/\w+(@\w+)?/, "")) || [])[1];
  if (/^\/(reparado|listo)\b|^(reparado|listo)\b/.test(t)) {
    let a = letra ? "abcd".indexOf(letra) : -1;
    if (a < 0) { const ab = abiertas(); if (ab.length === 1) a = ab[0]; else if (!ab.length) { tgEnviar("No hay alertas abiertas. 👍"); return; } else { tgEnviar("Hay más de un grupo con problemas: escribí /reparado " + ab.map(x => GRUPOS[x].id).join(", /reparado ") + "."); return; } }
    if (!repararDesdeTelegram(a)) tgEnviar(`El grupo ${GRUPOS[a].id} no tiene alertas abiertas.`);
  } else if (/^\/estado\b/.test(t)) {
    tgEnviar(`📊 <b>Estado de la planta</b> · ${fmtFecha(S.t)} ${fmtHora(S.t)}\n` + GRUPOS.map((g, a) => `Grupo ${g.id}: ${estado(a).t} (${Math.round(S.ema[a] * 100)} % vs. vecinos)`).join("\n"));
  } else {      // /start, /ayuda y cualquier otro texto ("hola"): explicar qué se puede hacer
    tgEnviar("☀️ <b>Gemelo Solar</b>\nTe aviso cuando el detector encuentra una falla.\n/estado — cómo está cada grupo\n/reparado B — avisar que ya reparaste el grupo B (o tocá el botón del aviso)\n\nSi no ves avisos, elegí el escenario Autónomo en el gemelo.");
  }
}
