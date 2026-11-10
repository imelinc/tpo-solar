// =============================== Unificación con el repo: parques reales y modelo XGBoost ===============================
// Este bloque lo inserta gemelo/build_gemelo.py dentro del gemelo. REPO sale de data/processed (no se escribe a mano).
const REPO = __REPO_JSON__;
const SITIOS_ARG = ["sanjuan", "jujuy", "cordoba", "caba"];
const fcTxt = v => (v == null || !isFinite(v) ? "—" : nf(v, 2));
const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const kmGeo = (la1, lo1, la2, lo2) => { const r = Math.PI / 180, x = (lo2 - lo1) * r * Math.cos((la1 + la2) / 2 * r), y = (la2 - la1) * r; return 6371 * Math.hypot(x, y); };
const MWTXT = corto => PARQUE ? `en ${PARQUE.nombre.trim()} (${nf(PARQUE.mw, 0)} MW)` : (corto ? "en 1 MW" : "en una planta de 1 MW");
const senalDe = p => REPO.ranking[p.central] || REPO.ranking[REPO.mismo_sitio[p.central]] || null;

// Factor de capacidad de la planta del gemelo, sana y limpia, mes por mes con el clima del sitio base.
const FC_CACHE = {};
function fcGemelo() {
  if (FC_CACHE[SITEKEY]) return FC_CACHE[SITEKEY];
  const acc = {};
  for (let i = 0; i < N; i++) {
    const t = T0 + i * H - H / 2, p = localParts(t), k = p.y + "-" + String(p.mo + 1).padStart(2, "0"), o = acc[k] || (acc[k] = { e: 0, h: 0 });
    GRUPOS.forEach((g, a) => (o.e += idealKW(a, t))); o.h++;
  }
  const r = {}; for (const k in acc) r[k] = acc[k].e / (KWP_TOTAL * acc[k].h);
  return (FC_CACHE[SITEKEY] = r);
}
function anioParaComparar(p) {
  const n = {}; for (const k in p.m) if (p.m[k][0] != null) n[k.slice(0, 4)] = (n[k.slice(0, 4)] || 0) + 1;
  if ((n["2023"] || 0) >= 3) return "2023";
  const ys = Object.keys(n).sort((a, b) => n[b] - n[a] || b - a); return ys[0] || null;
}
function repoTxt() {
  if (!PARQUE) return "";
  const s = senalDe(PARQUE), k = isoLocal(S.t).slice(0, 7), m = PARQUE.m[k], esp = m && m[1] != null ? m[1] : null;
  return `\n📍 Parque de referencia: <b>${esc(PARQUE.nombre.trim())}</b> (${esc(PARQUE.prov)}, ${nf(PARQUE.mw, 0)} MW)` +
    (esp != null ? `\nEl modelo del repo (${REPO.modelo}) espera un factor de capacidad de ${fcTxt(esp)} para ${k}.` : "") +
    (s ? `\n⚠️ En los datos reales de CAMMESA este parque ya tiene una señal: rinde ${Math.round(s.rinde_modelo * 100)} % de lo esperado desde ${s.desde.slice(0, 7)}.` : "");
}
function elegirParque(c) {
  const lab = document.getElementById("fMWlab"), sel = document.getElementById("parque");
  if (sel && sel.value !== (c || "")) sel.value = c || "";
  if (!c) { PARQUE = null; ESCALA_MW = ESCALA_BASE; lab.textContent = "Si la planta fuera de 1 MW, hoy estaría perdiendo"; renderRepo(); return; }
  const p = REPO.parques.find(x => x.central === c); if (!p) return;
  let best = null; SITIOS_ARG.forEach(k => { const d = kmGeo(p.lat, p.lon, SITIOS[k].lat, SITIOS[k].lon); if (!best || d < best.d) best = { k, d }; });
  PARQUE = p; PARQUE.base = best; ESCALA_MW = p.mw * 1000 / KWP_TOTAL;
  lab.textContent = `Si la planta fuera ${p.nombre.trim()} (${nf(p.mw, 0)} MW), hoy estaría perdiendo`;
  if (SITEKEY !== best.k) cambiarSitio(best.k, false); else renderRepo();
}
function renderRepo() {
  const body = document.getElementById("repoBody"), cv = document.getElementById("chRepo");
  if (!body) return;
  const ctx = cv.getContext("2d"), dpr = window.devicePixelRatio || 1, W = cv.clientWidth || 340, Hh = 150;
  cv.width = W * dpr; cv.height = Hh * dpr; ctx.setTransform(dpr, 0, 0, dpr, 0, 0); ctx.clearRect(0, 0, W, Hh);
  if (!PARQUE) { cv.hidden = true; document.getElementById("repoCap").hidden = true; body.innerHTML = `<p class="diag">Elegí un <b>parque real</b> arriba: el gemelo toma su potencia y su clima más cercano, y lo compara con lo que el modelo del repo esperaba y con lo que CAMMESA midió.</p>`; return; }
  const p = PARQUE, s = senalDe(p), yr = anioParaComparar(p), gem = fcGemelo(), base = SITIOS[p.base.k].nm.split(" · ")[0];
  const filas = []; for (let mes = 1; mes <= 12; mes++) {
    const k = yr ? `${yr}-${String(mes).padStart(2, "0")}` : null, m = k && p.m[k];
    filas.push({ mes, obs: m ? m[0] : null, esp: m ? m[1] : null, gem: k && yr === "2023" ? gem[k] ?? null : (gem["2023-" + String(mes).padStart(2, "0")] ?? null) });
  }
  const mae = ks => { const v = filas.filter(f => f.obs != null && f.esp != null && f.gem != null).map(f => Math.abs(f[ks] - f.obs)); return v.length ? v.reduce((a, b) => a + b, 0) / v.length : null; };
  const maeM = mae("esp"), maeG = mae("gem");
  const ult = Object.keys(p.m).sort().pop(), um = p.m[ult], rinde = um && um[0] != null && um[1] ? um[0] / um[1] : null;
  const ESTADO = { normal: "normal", parque: "rinde menos que el modelo y que sus vecinos", zona: "toda la zona rinde menos", arranque: "arranque (primeros meses)", sin_vecinos: "sin vecinos: no se sabe" };
  const usdM = s ? s.gwh_faltante * REPO.usd_mwh / 1000 : null;
  body.innerHTML =
    `<div class="selhd"><span class="nm">${esc(p.nombre.trim())}</span><span class="pill ${s ? "bad" : "ok"}">${s ? "Señal" : "Sin señal"}</span></div>` +
    `<p class="diag">${esc(p.prov)} · ${nf(p.mw, 0)} MW. Clima del gemelo: ${esc(base)}, a ${Math.round(p.base.d)} km.</p>` +
    (s ? `<p class="diag"><b>Señal del repo:</b> rinde ${Math.round(s.rinde_modelo * 100)} % de lo esperado y ${Math.round(s.rinde_vecinos * 100)} % de sus vecinos desde ${s.desde.slice(0, 7)} (${s.meses} meses). Faltan ${nf(s.gwh_faltante, 0)} GWh, unos US$ ${nf(usdM, 1)} millones a ${REPO.usd_mwh} US$/MWh. Una señal no es una falla confirmada.</p>`
       : `<p class="diag">Sin dos meses seguidos por debajo del 80 % del modelo y de los vecinos.</p>`) +
    (um ? `<p class="diag">Último mes (${ult}): observado ${fcTxt(um[0])}, esperado ${fcTxt(um[1])}${rinde != null ? ` (rinde ${Math.round(rinde * 100)} %)` : ""}. Estado: ${ESTADO[REPO.estados[um[2]]] || "—"}.</p>` : "") +
    (yr ? `<p class="diag">Año comparado: <b>${yr}</b>. Error medio contra lo observado: modelo ${fcTxt(maeM)} · gemelo ${fcTxt(maeG)} (factor de capacidad).</p>` : `<p class="diag">Este parque no tiene meses con datos.</p>`);
  cv.hidden = !yr; document.getElementById("repoCap").hidden = !yr;
  if (!yr) return;
  const series = [["obs", css("--ink"), []], ["esp", css("--sel"), [2, 3]], ["gem", css("--muted"), [6, 4]]];
  const vals = filas.flatMap(f => [f.obs, f.esp, f.gem]).filter(v => v != null), top = Math.max(0.4, Math.ceil(Math.max(...vals) * 20) / 20);
  const L = 30, R = 6, T = 8, B = 18, x = m => L + (m - 1) / 11 * (W - L - R), y = v => T + (1 - v / top) * (Hh - T - B);
  ctx.font = "10px " + css("--mono"); ctx.fillStyle = css("--muted"); ctx.strokeStyle = css("--line"); ctx.lineWidth = 1; ctx.textAlign = "right";
  for (let v = 0; v <= top + 1e-9; v += 0.1) { ctx.beginPath(); ctx.moveTo(L, y(v)); ctx.lineTo(W - R, y(v)); ctx.stroke(); ctx.fillText(nf(v, 1), L - 4, y(v) + 3); }
  ctx.textAlign = "center"; ["E", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"].forEach((l, i) => ctx.fillText(l, x(i + 1), Hh - 5));
  series.forEach(([k, col, dash]) => {
    ctx.strokeStyle = col; ctx.fillStyle = col; ctx.lineWidth = 2; ctx.setLineDash(dash); ctx.beginPath(); let abierto = false;
    filas.forEach(f => { const v = f[k]; if (v == null) { abierto = false; return; } if (!abierto) { ctx.moveTo(x(f.mes), y(v)); abierto = true; } else ctx.lineTo(x(f.mes), y(v)); });
    ctx.stroke(); ctx.setLineDash([]); filas.forEach(f => { if (f[k] != null) { ctx.beginPath(); ctx.arc(x(f.mes), y(f[k]), 2.2, 0, 7); ctx.fill(); } });
  });
}
function iniciarRepo() {
  const sel = document.getElementById("parque"), con = REPO.parques.filter(p => senalDe(p)), sin = REPO.parques.filter(p => !senalDe(p));
  const op = (p, mark) => `<option value="${esc(p.central)}">${mark}${esc(p.nombre.trim())} · ${esc(p.prov)} · ${nf(p.mw, 0)} MW</option>`;
  sel.innerHTML = `<option value="">— planta de ejemplo —</option>` +
    `<optgroup label="Con señal en el repo (a revisar)">${con.map(p => op(p, "⚠ ")).join("")}</optgroup>` +
    `<optgroup label="Sin señal">${sin.map(p => op(p, "")).join("")}</optgroup>`;
  sel.addEventListener("change", e => elegirParque(e.target.value));
  document.getElementById("repoFuente").textContent = `Fuente: ${REPO.fuente}. Modelo: ${REPO.modelo} (RMSE ${nf(REPO.rmse_test, 3)} en la prueba desde 2025). Evaluación del ${REPO.fecha_evaluacion}.`;
}
