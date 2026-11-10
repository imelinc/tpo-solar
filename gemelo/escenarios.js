// =============================== Escenarios: manual y autónomo ===============================
// Manual: quien presenta rompe un grupo con los botones y manda al técnico desde la pantalla.
// Autónomo: el gemelo rompe un grupo solo, el detector avisa al bot de Telegram y el técnico confirma «Reparado» desde el bot;
//           al llegar la confirmación el sistema da la falla por resuelta y, un rato después, rompe otra cosa.
// Las fallas son simuladas: sirven para medir el tiempo de aviso, no prueban nada sobre parques reales.
let MODO = "manual";
const AUTO_PLAN = [{ g: 1, tipo: "inversor" }, { g: 3, tipo: "string" }, { g: 2, tipo: "inversor" }, { g: 0, tipo: "string" }];
const AUTO = { idx: 0, next: null };
const pendTxt = al => (al.tgEnviado != null && !al.res ? ` · Avisado por Telegram a las ${fmtHora(al.tgEnviado)}: esperando al técnico.` : "");

function proximaFalla(t) {
  let c = t + 3 * H; const h = localParts(c).h;
  if (h < 8 || h >= 15) c = fromLocal(isoLocal(c) + "T09:00") + (h >= 15 ? 24 * H : 0);
  return c;
}
function autoTick() {
  if (MODO !== "auto" || S.silent) return;
  if (S.fault.some(f => f) || S.alert.some(x => x && !x.res)) return;       // todavía hay algo sin reparar
  if (AUTO.next == null) { AUTO.next = proximaFalla(S.t); return; }
  if (S.t >= AUTO.next) { const p = AUTO_PLAN[AUTO.idx++ % AUTO_PLAN.length]; AUTO.next = null; select(p.g); inyectar(p.g, p.tipo, S.t); }
}
function repararDesdeTelegram(a) {
  const al = S.alert[a];
  if (!(S.fault[a] || (al && !al.res))) return false;
  const desde = al ? al.t : S.t;
  inyectar(a, "arreglar");
  if (al) al.resTxt = "Reparado: el técnico lo confirmó por Telegram";
  tgEnviar(`✅ <b>Grupo ${GRUPOS[a].id} reparado</b>. El gemelo ya lo ve normal.\nTiempo desde la alerta hasta tu aviso: ${fmtDur(S.t - desde)} (tiempo simulado).`);
  updateSide(); renderFeed();
  return true;
}
function renderEscenario() {
  const bn = document.getElementById("modoBanner"); if (!bn) return;
  bn.hidden = MODO !== "auto"; if (MODO !== "auto") return;
  const dets = S.alerts.filter(x => x.g != null && x.fix), rep = dets.filter(x => x.res).length, esp = dets.length - rep;
  const tg = PUEDE_TG && TG.tok && TG.chat ? "Telegram conectado" : "Sin Telegram: usá «Simular aviso del técnico»";
  bn.innerHTML = `<b>Escenario autónomo</b> falla sola → avisa al bot → el técnico confirma · Fallas detectadas ${dets.length} · reparadas ${rep} · esperando al técnico ${esp} · ${tg}`;
}
function iniciarAuto() {
  AUTO.idx = 0; AUTO.next = null;
  document.querySelectorAll(".demos button").forEach(b => b.setAttribute("aria-pressed", "false"));
  jump(fromLocal(DEMOS[0].start.slice(0, 10) + "T07:00"), [], "<b>Autónomo</b>El gemelo va a romper un grupo por su cuenta. El detector avisa al bot de Telegram y, cuando el técnico toca «Reparado» en el bot, el sistema lo registra y sigue.", true);
  setSpeed(3600); select(1); setPlaying(true);
}
function setModo(m) {
  MODO = m; document.body.dataset.modo = m;
  document.querySelectorAll("#escenarios button").forEach(b => b.setAttribute("aria-pressed", String(b.dataset.m === m)));
  const fix = document.querySelector("#acts button.fix");
  if (fix) fix.lastChild.textContent = m === "auto" ? "Simular aviso del técnico (sin Telegram)" : "Mandar técnico (repara y limpia)";
  if (m === "auto") iniciarAuto(); else runDemo(0);
  renderEscenario(); renderFeed();
}
function iniciarEscenarios() {
  document.getElementById("escenarios").addEventListener("click", e => { const b = e.target.closest("button"); if (b && b.dataset.m !== MODO) setModo(b.dataset.m); });
  try { if (localStorage.getItem("gemeloSinGrilla") === "1") document.body.classList.add("sin-grilla"); } catch (e) {}
  const g = document.getElementById("grillaBtn");
  g.setAttribute("aria-pressed", String(!document.body.classList.contains("sin-grilla")));
  g.addEventListener("click", () => { const sin = document.body.classList.toggle("sin-grilla"); g.setAttribute("aria-pressed", String(!sin)); try { localStorage.setItem("gemeloSinGrilla", sin ? "1" : "0"); } catch (e) {} });
  if (!PUEDE_TG) return;
  const b = document.getElementById("tgBtn"), pop = document.getElementById("tgpop"); b.hidden = false; b.textContent = TG.tok ? "Telegram ✓" : "Telegram";
  document.getElementById("tgTok").value = TG.tok || ""; document.getElementById("tgChat").value = TG.chat || ""; document.getElementById("tgOn").checked = TG.on !== false;
  b.addEventListener("click", () => (pop.hidden = !pop.hidden));
  // Con solo el token alcanza: el chat se detecta con el último mensaje que le escribieron al bot.
  const leer = async () => {
    TG.tok = document.getElementById("tgTok").value.trim(); TG.chat = document.getElementById("tgChat").value.trim(); TG.on = document.getElementById("tgOn").checked;
    if (TG.tok && TG.chat) {       // un chat viejo o inventado no sirve: si Telegram no lo conoce, se busca de nuevo
      try { const r = await tgLlamar("getChat", { chat_id: TG.chat }); if (!r.ok && /chat not found/i.test(r.description || "")) { TG.chat = ""; document.getElementById("tgChat").value = ""; } } catch (e) {}
    }
    if (TG.tok && !TG.chat) {
      tgEstado("Buscando tu chat…", true);
      try {
        const r = await tgLlamar("getUpdates", { timeout: 0 });
        if (!r.ok) { tgEstado("Telegram respondió: " + (r.description || "token inválido"), false); return false; }
        const c = (r.result || []).map(u => (u.message || (u.callback_query || {}).message || {}).chat).filter(Boolean).pop();
        if (!c) { tgEstado("Mandale cualquier mensaje al bot desde Telegram y volvé a tocar el botón.", false); return false; }
        TG.chat = String(c.id); document.getElementById("tgChat").value = TG.chat;
      } catch (e) { tgEstado("Sin conexión con Telegram", false); return false; }
    }
    return !!(TG.tok && TG.chat);
  };
  document.getElementById("tgSave").addEventListener("click", async () => {
    if (!(await leer())) return;
    try { localStorage.setItem("gemeloTG", JSON.stringify({ tok: TG.tok, chat: TG.chat, on: TG.on })); } catch (e) {}
    b.textContent = TG.tok ? "Telegram ✓" : "Telegram"; pop.hidden = true; tgIniciar(); renderEscenario();
  });
  document.getElementById("tgBorrar").addEventListener("click", () => {
    clearInterval(tgTimer); TG.tok = TG.chat = ""; document.getElementById("tgTok").value = ""; document.getElementById("tgChat").value = "";
    try { localStorage.removeItem("gemeloTG"); } catch (e) {}
    b.textContent = "Telegram"; tgEstado("Datos borrados de este navegador.", true); renderEscenario();
  });
  document.getElementById("tgTest").addEventListener("click", async () => {
    if (!(await leer())) return;
    telegram({ sev: "info", title: "Prueba de conexión", body: "Las alertas del gemelo van a llegar acá. Para probar el aviso al técnico, elegí el escenario Autónomo." }, true); tgIniciar();
  });
  tgIniciar();
}
