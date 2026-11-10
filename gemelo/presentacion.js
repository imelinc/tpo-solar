// =============================== Modo presentación guiado ===============================
// Seis pasos con «Siguiente» (flechas, PageDown/PageUp del control del proyector, Esc para salir).
// Cada paso arma su propia escena desde cero, así «Anterior» siempre funciona. Una línea en vivo cuenta qué pasa
// y la simulación se frena sola en el momento clave. Las cifras salen de REPO (defensa_evidencia.json).
const PRES = { on: false, i: 0, timer: null, paso: {} };
const G_B = 1;   // grupo B: el de la demo manual

function presFoco(...els) {
  document.querySelectorAll(".foco").forEach(e => e.classList.remove("foco"));
  els.filter(Boolean).forEach(e => e.classList.add("foco"));
  const lat = els.find(e => e && e.closest && e.closest("aside")); if (lat) lat.scrollIntoView({ block: "start", behavior: "smooth" });
}
function presDia() { return DEMOS[0].start.slice(0, 10); }           // un día despejado del sitio
function presEscena(hora, sched, speed, play) {
  if (MODO !== "manual") setModo("manual");
  document.querySelectorAll(".demos button").forEach(b => b.setAttribute("aria-pressed", "false"));
  jump(fromLocal(presDia() + "T" + hora), sched.map(e => ({ ...e, at: fromLocal(presDia() + "T" + e.at) })), null, true);
  setSpeed(speed); setPlaying(play); select(G_B);
}
function presCifrasParque() {
  const s = REPO.ranking.TOC3FV;
  return s ? { rinde: Math.round(s.rinde_modelo * 100), gwh: nf(s.gwh_faltante, 0), usd: nf(s.gwh_faltante * REPO.usd_mwh / 1000, 1) } : null;
}
const presCard = a => document.getElementById("cards").children[a];
const presSec = id => document.getElementById(id).closest(".sec");

const PASOS = [
  {
    t: "Un parque real que rinde menos",
    entrar() {
      if (!PARQUE || PARQUE.central !== "TOC3FV") elegirParque("TOC3FV");
      presEscena("09:00", [], 600, false);
      presFoco(document.getElementById("repoSec"));
    },
    texto() {
      const c = presCifrasParque();
      return `<b>Tocota III</b> (San Juan, 60 MW), con datos reales de CAMMESA. En el gráfico de la derecha, la <b>línea negra</b> es lo que generó cada mes y la <b>azul punteada</b> lo que debería haber generado según su clima.` +
        (c ? ` Rinde <b>${c.rinde} %</b> de lo esperado: faltan <b>${c.gwh} GWh</b>, unos <b>US$ ${c.usd} M</b> a un precio supuesto.` : "") +
        ` El problema: con datos <b>mensuales</b> nos enteramos meses después.`;
    },
  },
  {
    t: "Una copia de la planta, hora por hora",
    entrar() { presEscena("09:00", [], 600, true); presFoco(document.getElementById("stage"), document.getElementById("cards")); },
    texto: () => `Esto es un <b>gemelo digital</b>: una planta simulada con el sol y el clima reales de San Juan. Tiene <b>cuatro grupos</b> de paneles (A, B, C y D). ` +
      `Cada tarjeta de abajo muestra cuánto genera ahora y cuánto debería. La barra compara cada grupo con los otros tres: todos ven el mismo cielo, ` +
      `así que si uno rinde menos, <b>el problema es el equipo, no el clima</b>.`,
  },
  {
    t: "Rompemos un equipo",
    entrar() { this.parado = false; presEscena("09:00", [{ g: G_B, tipo: "inversor", at: "10:00" }], 600, true); presFoco(presCard(G_B)); },
    texto: () => `A las <b>10:00</b> se apaga el inversor del <b>grupo B</b>. El detector no sabe nada: solo mira cuánto genera cada grupo y lo compara con sus vecinos.`,
    vivo() {
      const f = S.fault[G_B], al = S.alert[G_B];
      if (al && !al.res) {
        if (!this.parado) { this.parado = true; setPlaying(false); presFoco(presCard(G_B), presSec("feed")); }
        return { estado: `✓ El detector avisó solo, <b>${fmtDur(al.det || 0)}</b> después de la falla.`,
          extra: `<div class="pres-comp"><div><span>Gemelo · datos por hora</span><b>${fmtDur(al.det || 0)}</b></div>` +
            `<div><span>Modelo mensual del repo</span><b>2 meses</b><small>pide dos meses seguidos por debajo del 80 %</small></div></div>` };
      }
      if (f && S.t >= f.at) return { estado: `${fmtHora(S.t)} · El grupo B dejó de generar. El detector todavía no lo sabe: espera ver una hora de sol completa.` };
      return { estado: `${fmtHora(S.t)} · Todo normal: los cuatro grupos generan parecido.` };
    },
  },
  {
    t: "Qué avisa el sistema",
    entrar() {
      if (!S.alert[G_B] || S.alert[G_B].res) {      // si se llega con «Anterior» o salteando, rearmar la falla ya detectada
        presEscena("09:00", [{ g: G_B, tipo: "inversor", at: "10:00" }], 600, false);
        for (let k = 0; k < 48 && !S.alert[G_B]; k++) avanzar(S.t + H / 4);
        drawDay(); drawHist(); updateSide(); renderFeed();
      }
      setPlaying(false); presFoco(presSec("feed"), document.getElementById("sPill").closest(".sec"));
    },
    texto: () => `La alerta dice <b>qué grupo</b> falla, <b>cuánto rinde</b> frente a sus vecinos y <b>cuánta plata</b> se pierde por día. ` +
      `La causa que propone es una <b>hipótesis</b>: se entrenó con fallas simuladas. Ahora mandamos al técnico.`,
    accion: () => (S.alert[G_B] && !S.alert[G_B].res) || S.fault[G_B] ? { txt: "Mandar técnico", fn: () => { inyectar(G_B, "arreglar"); updateSide(); setPlaying(true); } } : null,
    vivo: () => (S.fault[G_B] || (S.alert[G_B] && !S.alert[G_B].res)) ? { estado: "Grupo B en falla: esperando al técnico." } : { estado: "✓ Reparado: el grupo B vuelve a generar como sus vecinos." },
  },
  {
    t: "Sin nadie mirando: avisa al técnico",
    entrar() { this.lento = false; setModo("auto"); presFoco(document.getElementById("stage"), presSec("feed")); },
    texto: () => `Ahora nadie toca nada. El gemelo <b>rompe algo por su cuenta</b>, el detector manda el aviso al <b>celular del técnico</b> por Telegram con un botón «Reparado», ` +
      `y cuando el técnico lo toca, <b>el sistema lo registra solo</b>.`,
    vivo() {
      const a = abiertas()[0], al = a != null ? S.alert[a] : null, tg = PUEDE_TG && TG.tok && TG.chat;
      const hechas = S.alerts.filter(x => x.g != null && x.fix && x.res).length;
      if (al && !al.res) {
        if (!this.lento) { this.lento = true; setSpeed(600); }
        return tg && al.tgEnviado != null
          ? { estado: `📱 Aviso enviado al celular: <b>grupo ${GRUPOS[a].id}</b>. Esperando que el técnico toque «Reparado» en Telegram…` }
          : { estado: `Detectado: <b>grupo ${GRUPOS[a].id}</b>. Telegram no está conectado: tocá «Simular técnico».`, accion: { txt: "Simular técnico", fn: () => inyectar(a, "arreglar") } };
      }
      this.lento = false;
      if (a != null) return { estado: `${fmtHora(S.t)} · Se rompió el <b>grupo ${GRUPOS[a].id}</b>. El detector todavía no lo sabe.` };
      return { estado: hechas ? `✓ El técnico confirmó la reparación${tg ? " desde Telegram" : ""} y el sistema lo registró (${hechas} ${hechas === 1 ? "vez" : "veces"}). Sigue vigilando.` : `${fmtHora(S.t)} · Planta funcionando. En cualquier momento algo se rompe…` };
    },
  },
  {
    t: "Lo que nos llevamos",
    entrar() { setPlaying(false); presFoco(); },
    texto() {
      const r = REPO.resumen;
      return `<div class="pres-comp"><div><span>Parques con señal (mensual)</span><b>${Object.keys(REPO.ranking).length}</b></div>` +
        `<div><span>Energía que falta</span><b>${nf(r.gwh_faltante, 0)} GWh</b><small>${nf(r.pct, 1)} % de lo generado</small></div>` +
        `<div><span>Plata en juego</span><b>US$ ${nf(r.usd_millones, 1)} M</b><small>a ${REPO.usd_mwh} US$/MWh, precio supuesto</small></div>` +
        `<div><span>Aviso con datos por hora</span><b>≈ 1 h</b><small>en vez de meses</small></div></div>` +
        `El modelo mensual dice <b>a qué parque mirar primero</b>; el gemelo muestra <b>cómo se avisaría en horas</b> si hubiera datos por hora. ` +
        `Límites: las fallas del gemelo son simuladas y en Argentina no hay datos públicos por hora. Una señal no es una falla confirmada.`;
    },
  },
];

function presRender() {
  const p = PASOS[PRES.i], v = p.vivo ? p.vivo.call(PRES.paso) : null, acc = (v && v.accion) || (p.accion && p.accion());
  const box = document.getElementById("pres");
  box.querySelector(".pres-n").textContent = `Paso ${PRES.i + 1} de ${PASOS.length}`;
  box.querySelector(".pres-t").textContent = p.t;
  const txt = p.texto.call(PRES.paso); if (box.querySelector(".pres-x").dataset.k !== txt) { box.querySelector(".pres-x").innerHTML = txt; box.querySelector(".pres-x").dataset.k = txt; }
  const est = box.querySelector(".pres-v"), extra = box.querySelector(".pres-e");
  est.hidden = !v; if (v && est.dataset.k !== v.estado) { est.innerHTML = v.estado; est.dataset.k = v.estado; }
  const ex = (v && v.extra) || ""; if (extra.dataset.k !== ex) { extra.innerHTML = ex; extra.dataset.k = ex; }
  const b = box.querySelector(".pres-a"); b.hidden = !acc; if (acc) { b.textContent = acc.txt; b.onclick = () => { acc.fn(); presRender(); }; }
  box.querySelector(".pres-prev").disabled = PRES.i === 0;
  box.querySelector(".pres-next").textContent = PRES.i === PASOS.length - 1 ? "Terminar" : "Siguiente →";
}
function presIr(i) {
  if (i < 0) return; if (i >= PASOS.length) { presSalir(); return; }
  PRES.i = i; PRES.paso = PASOS[i]; PASOS[i].entrar.call(PRES.paso); presRender();
}
function presEntrar() {
  PRES.on = true; document.body.classList.add("presentando"); document.getElementById("pres").hidden = false;
  document.getElementById("presBtn").textContent = "Salir (Esc)"; document.getElementById("presBtn").setAttribute("aria-pressed", "true");
  clearInterval(PRES.timer); PRES.timer = setInterval(() => PRES.on && presRender(), 250);
  presIr(0);
}
function presSalir() {
  PRES.on = false; clearInterval(PRES.timer); document.body.classList.remove("presentando"); document.getElementById("pres").hidden = true; presFoco();
  document.getElementById("presBtn").textContent = "Presentar"; document.getElementById("presBtn").setAttribute("aria-pressed", "false");
}
function iniciarPresentacion() {
  document.getElementById("presBtn").addEventListener("click", () => (PRES.on ? presSalir() : presEntrar()));
  document.querySelector("#pres .pres-next").addEventListener("click", () => presIr(PRES.i + 1));
  document.querySelector("#pres .pres-prev").addEventListener("click", () => presIr(PRES.i - 1));
  document.addEventListener("keydown", e => {
    if (!PRES.on || /INPUT|SELECT|TEXTAREA/.test(document.activeElement.tagName)) return;
    if (e.key === "ArrowRight" || e.key === "PageDown") { e.preventDefault(); presIr(PRES.i + 1); }
    else if (e.key === "ArrowLeft" || e.key === "PageUp") { e.preventDefault(); presIr(PRES.i - 1); }
    else if (e.key === "Escape") { e.preventDefault(); presSalir(); }
  });
}
