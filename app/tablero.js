/* Dashboard de la flota solar. Lee window.DATOS (app/datos.js, generado por app/build_dashboard.py). */
"use strict";

const D = window.DATOS;
const $ = (s) => document.querySelector(s);
const fmt = (n, d = 0) => (n == null || Number.isNaN(n)) ? "—"
  : n.toLocaleString("es-AR", { minimumFractionDigits: d, maximumFractionDigits: d });
const usd = (n) => "USD " + fmt(n);
const pct = (r) => fmt(r * 100) + "%";
const fechaLarga = (f) => new Date(f + "T12:00:00").toLocaleDateString("es-AR", { day: "numeric", month: "long", year: "numeric" });
const mesLargo = (m) => {
  const s = new Date(m + "-15T12:00:00").toLocaleDateString("es-AR", { month: "long", year: "numeric" });
  return s[0].toUpperCase() + s.slice(1);
};
const restarDias = (f, d) => { const x = new Date(f + "T12:00:00Z"); x.setUTCDate(x.getUTCDate() - d); return x.toISOString().slice(0, 10); };
const plural = (n, uno, varios) => n === 1 ? uno : varios;
const titulo = (s) => s.toLowerCase().replace(/(^|\s)(\S)/g, (m, a, b) => a + b.toUpperCase()).replace(/\b(Ii|Iii|Iv|Vi)\b/g, (m) => m.toUpperCase());

const ESTADO = {
  rojo: { txt: "Atender hoy", orden: 0 },
  amarillo: { txt: "Revisar esta semana", orden: 1 },
  gris: { txt: "Sin dato confiable", orden: 2 },
  verde: { txt: "En orden", orden: 3 },
};
const COLOR = { verde: "#129a3c", amarillo: "#f2a900", rojo: "#d03b3b", gris: "#8b979c" };
const TINTA = "#0f2a36", TENUE = "#566b74";
const FUENTE = getComputedStyle(document.body).fontFamily;
const CONFIG = { displayModeBar: false, responsive: true };
const EJE = { gridcolor: "#dfe4e2", linecolor: "#b9c3c0", zeroline: false, tickfont: { color: TENUE, size: 13 }, automargin: true };
const base = (extra = {}) => Object.assign({
  font: { family: FUENTE, size: 14, color: TINTA },
  paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
  margin: { l: 10, r: 16, t: 10, b: 10 }, showlegend: false,
  hoverlabel: { bgcolor: "#ffffff", bordercolor: "#c9d1cf", font: { color: TINTA, family: FUENTE, size: 14 } },
}, extra);
const GEO = {
  resolution: 50, projection: { type: "mercator" }, showframe: false, bgcolor: "rgba(0,0,0,0)",
  showland: true, landcolor: "#f4f6f5", showocean: true, oceancolor: "#d3e0e3",
  showcoastlines: true, coastlinecolor: "#8ea3a9", showcountries: true, countrycolor: "#aebcc0", showlakes: false,
};
// Posición del número de cada planta en el mapa: 02, 03 y 05 están a pocos km entre sí
const ROTULO = { station05: "top center", station03: "middle left", station02: "bottom right", station07: "middle left" };
// "Parque Solar Fotovoltaico Cauchari III" -> "Cauchari III": el prefijo se repite y no distingue
const nombreCorto = (s) => s.replace(/^(parque solar fotovoltaico|parque solar|pque\.? solar( fv| fotovoltaico)?|pque\.? fotov\.?|pque\.?|proyecto solar( fv)?|c\.? ?fotov\.?|p\.\s?s\.?(f\.?v\.?)?|parque)\s+/i, "") || s;
const corto = (s, n = 26) => s.length > n ? s.slice(0, n - 1).trimEnd() + "…" : s;
const lampara = (estado, extra = "") => `<span class="lampara ${estado} ${extra}" aria-hidden="true"></span>`;
const flecha = `<svg width="12" height="12" viewBox="0 0 12 12" aria-hidden="true"><path d="m4 2 4 4-4 4" stroke="currentColor" stroke-width="2" fill="none"/></svg>`;

// ------------------------------------------------------------------ estado de la página
const FECHAS = Object.keys(D.flota.tablero).sort();
const S = {
  fecha: FECHAS.includes("2019-05-10") ? "2019-05-10" : FECHAS.at(-1),
  planta: "station09", dias: 90,
  mes: D.argentina.meses.at(-1), parque: "ULL4FV",
  costo: D.negocio.costo, precio: D.negocio.precio, tasa: D.negocio.tasa * 100,
};
const tablero = () => D.flota.tablero[S.fecha];
const filaDe = (p) => tablero().find((r) => r.p === p);

function perdidaEnAlertas(p, desde, hasta) {
  const d = D.flota.plantas[p];
  let mwh = 0, dias = 0;
  d.fecha.forEach((f, i) => { if (f > desde && f <= hasta && d.alerta[i]) { mwh += d.perdida[i] || 0; dias++; } });
  return { mwh, dias };
}

// ------------------------------------------------------------------ navegación
const VISTAS = { flota: vistaFlota, planta: vistaPlanta, argentina: vistaArgentina, negocio: vistaNegocio };
function mostrar() {
  const v = location.hash.slice(1);
  const vista = v in VISTAS ? v : "flota";
  document.querySelectorAll(".vista").forEach((s) => { s.hidden = s.id !== "v-" + vista; });
  document.querySelectorAll(".vistas a").forEach((a) => {
    if (a.hash === "#" + vista) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current");
  });
  $("#control-dia").hidden = !["flota", "planta"].includes(vista);
  if (vista !== mostrar.ultima) window.scrollTo(0, 0);
  mostrar.ultima = vista;
  VISTAS[vista]();
}
function irAPlanta(p) { S.planta = p; location.hash = "#planta"; }

// ------------------------------------------------------------------ 1. flota hoy
function vistaFlota() {
  const t = tablero();
  const orden = [...t].sort((a, b) => ESTADO[a.estado].orden - ESTADO[b.estado].orden || (b.usd ?? -1) - (a.usd ?? -1));
  const rojos = orden.filter((r) => r.estado === "rojo"), amarillos = orden.filter((r) => r.estado === "amarillo");
  const desde = restarDias(S.fecha, 30);
  const mes = Object.keys(D.flota.plantas).reduce((a, p) => a + perdidaEnAlertas(p, desde, S.fecha).mwh, 0);
  const lineaMes = `En los 30 días previos la flota perdió <b>${fmt(mes)} MWh</b> (${usd(mes * D.negocio.precio)}) en días con alerta.`;

  let h;
  if (rojos.length) {
    const r = rojos[0], n = rojos.length;
    const extra = amarillos.length ? ` Además, ${amarillos.length} ${plural(amarillos.length, "planta para revisar", "plantas para revisar")} esta semana.` : "";
    h = `${lampara("rojo")}<div><h1>${n} ${plural(n, "planta necesita", "plantas necesitan")} un técnico hoy</h1>
      <p><b>${r.p}</b> rinde ${pct(r.rend)} de lo normal.${extra} ${lineaMes}</p></div>
      <div class="cifra"><strong>${usd(r.usd)}</strong><span>pierde ${r.p} por día</span></div>`;
  } else if (amarillos.length) {
    h = `${lampara("amarillo")}<div><h1>Nadie necesita un técnico hoy</h1>
      <p>${amarillos.length} ${plural(amarillos.length, "planta para revisar", "plantas para revisar")} esta semana: <b>${amarillos.map((r) => r.p).join(", ")}</b>. ${lineaMes}</p></div>
      <div class="cifra"><strong>${usd(mes * D.negocio.precio)}</strong><span>perdidos en 30 días</span></div>`;
  } else {
    h = `${lampara("verde")}<div><h1>Toda la flota rinde como se espera</h1><p>${lineaMes}</p></div>
      <div class="cifra"><strong>${usd(mes * D.negocio.precio)}</strong><span>perdidos en 30 días</span></div>`;
  }
  $("#flota-franja").innerHTML = h;

  // lista por prioridad: los problemas con fila propia, las plantas en orden como fichas
  const grupos = ["rojo", "amarillo", "gris", "verde"].map((e) => [e, orden.filter((r) => r.estado === e)]).filter(([, rs]) => rs.length);
  $("#flota-lista").innerHTML = `<h2>Plantas por prioridad <em>${fechaLarga(S.fecha)}</em></h2>` + grupos.map(([e, rs]) => {
    const cab = `<p class="grupo-titulo">${lampara(e)} ${ESTADO[e].txt} <b>${rs.length}</b></p>`;
    if (e === "verde") {
      return `<div class="grupo">${cab}<div class="chips">${rs.map((r) =>
        `<button class="chip" data-p="${r.p}" title="Rinde ${pct(r.rend)} de lo normal">${r.p}</button>`).join("")}</div></div>`;
    }
    return `<div class="grupo">${cab}${rs.map((r) => {
      const tipica = D.flota.plantas[r.p].modelo !== "propio" ? " Se compara con una planta típica." : "";
      const que = e === "gris"
        ? `Capacidad declarada no confiable<small>Mide más potencia de la que dice su ficha técnica: hay que corregirla antes de evaluarla.</small>`
        : `Rinde ${pct(r.rend)} de lo normal${r.alerta !== "—" ? " · " + r.alerta.toLowerCase() : ""}<small>${r.accion}.${tipica}</small>`;
      const sello = r.baja ? ` <span class="sello">Baja confianza</span>` : "";
      return `<button class="fila" data-p="${r.p}">${lampara(e)}<span class="nombre">${r.p}${sello}</span>
        <span class="que">${que}</span>
        <span class="plata">${r.usd == null ? "—" : usd(r.usd)}<small>${r.usd == null ? "" : "por día"}</small></span>
        <span class="ir">Ver planta ${flecha}</span></button>`;
    }).join("")}</div>`;
  }).join("");

  const lista = $("#flota-lista");
  lista.querySelectorAll("[data-p]").forEach((b) => {
    b.addEventListener("click", () => irAPlanta(b.dataset.p));
    b.addEventListener("mouseenter", () => enfocar(b.dataset.p));
    b.addEventListener("focus", () => enfocar(b.dataset.p));
    b.addEventListener("mouseleave", () => enfocar(null));
    b.addEventListener("blur", () => enfocar(null));
  });

  // mapa: las plantas con problema se dibujan arriba
  const pts = [...orden].reverse();
  Plotly.react("flota-mapa", [{
    type: "scattergeo", lon: pts.map((r) => D.flota.plantas[r.p].lon), lat: pts.map((r) => D.flota.plantas[r.p].lat),
    text: pts.map((r) => r.p.replace("station", "")), mode: "markers+text",
    textposition: pts.map((r) => ROTULO[r.p] || "middle right"),
    textfont: { size: 13, color: TINTA, family: FUENTE },
    marker: { size: 20, color: pts.map((r) => COLOR[r.estado]), line: { width: 3, color: "#ffffff" }, opacity: 1 },
    customdata: pts.map((r) => [r.p, ESTADO[r.estado].txt]),
    hovertemplate: "<b>%{customdata[0]}</b><br>%{customdata[1]}<extra></extra>",
  }], base({ geo: { ...GEO, scope: "asia", lonaxis: { range: [112.9, 118.3] }, lataxis: { range: [36.1, 40.0] } } }), CONFIG);
  const mapa = $("#flota-mapa");
  mapa.removeAllListeners?.("plotly_click");
  mapa.on("plotly_click", (ev) => irAPlanta(ev.points[0].customdata[0]));
  mapa._orden = pts.map((r) => r.p);
}

function enfocar(p) {
  const lista = $("#flota-lista"), mapa = $("#flota-mapa");
  lista.classList.toggle("atenuado", !!p);
  lista.querySelectorAll("[data-p]").forEach((b) => b.classList.toggle("foco", b.dataset.p === p));
  if (mapa._orden) Plotly.restyle(mapa, { "marker.opacity": [mapa._orden.map((q) => (!p || q === p) ? 1 : 0.25)] });
}

// ------------------------------------------------------------------ 2. una planta
function vistaPlanta() {
  const p = S.planta, d = D.flota.plantas[p], hoy = filaDe(p);
  $("#planta-chips").innerHTML = Object.keys(D.flota.plantas).sort().map((q) =>
    `<button class="chip" data-p="${q}" aria-pressed="${q === p}">${lampara(filaDe(q)?.estado ?? "gris")}${q}</button>`).join("");
  $("#planta-chips").querySelectorAll("[data-p]").forEach((b) => b.addEventListener("click", () => { S.planta = b.dataset.p; vistaPlanta(); }));
  $("#planta-periodo").querySelectorAll("button").forEach((b) => b.setAttribute("aria-pressed", String(+b.dataset.dias === S.dias)));

  const desde = restarDias(S.fecha, S.dias);
  const idx = d.fecha.map((f, i) => i).filter((i) => d.fecha[i] > desde && d.fecha[i] <= S.fecha);
  const periodo = { 30: "en el último mes", 90: "en los últimos 3 meses", 400: "en todo el período" }[S.dias];
  let real = 0, esp = 0;
  idx.forEach((i) => { if (d.decide[i]) { real += d.real[i]; esp += d.esperada[i]; } });
  const { mwh, dias } = perdidaEnAlertas(p, desde, S.fecha);
  const sensor = idx.filter((i) => d.sensor[i]).length, baja = idx.filter((i) => d.baja[i]).length;
  const estado = hoy?.estado ?? "gris";
  const tipica = d.modelo !== "propio" ? " Como no tiene historia sana propia, se compara con una planta típica." : "";
  const hoyTxt = hoy ? ` Al ${fechaLarga(S.fecha)}: <b>${ESTADO[estado].txt.toLowerCase()}</b>.` : "";

  $("#planta-rango").textContent = idx.length ? `${fechaLarga(d.fecha[idx[0]])} al ${fechaLarga(d.fecha[idx.at(-1)])}` : "";
  if (estado === "gris") {
    $("#planta-franja").innerHTML = `${lampara("gris")}<div><h1>${p}: capacidad declarada no confiable</h1>
      <p>Mide más potencia de la que dice su ficha técnica, así que su rendimiento no se puede juzgar hasta corregirla. La energía de abajo se muestra solo como referencia.</p></div><div></div>`;
  } else if (!esp) {
    $("#planta-franja").innerHTML = `${lampara(estado)}<div><h1>${p}: sin días para juzgar ${periodo}</h1>
      <p>En este período no hubo días con datos suficientes (sensor caído o días muy nublados).${hoyTxt}</p></div><div></div>`;
  } else {
    $("#planta-franja").innerHTML = `${lampara(estado)}<div><h1>${p} generó ${pct(real / esp)} de lo que debía ${periodo}</h1>
      <p>${dias ? `Perdió <b>${fmt(mwh)} MWh</b> en ${dias} ${plural(dias, "día", "días")} con alerta.` : "No tuvo días con alerta."}${hoyTxt}${tipica}${sensor ? ` ${sensor} ${plural(sensor, "día quedó", "días quedaron")} sin decisión por el sensor caído.` : ""}</p></div>
      <div class="cifra"><strong>${usd(mwh * D.negocio.precio)}</strong><span>perdidos en días con alerta</span></div>`;
  }
  $("#planta-aviso").innerHTML = baja ? `<div class="aviso"><span class="sello">Baja confianza</span><div>
    <strong>De enero a marzo las alertas de ${p} son de baja confianza.</strong>
    Esta planta rinde menos todos los inviernos (sombra o nieve) y el modelo, con un solo año de datos, no lo aprende. Los avisos se muestran, pero no implican una falla.</div></div>` : "";

  const x = idx.map((i) => d.fecha[i]);
  const tam = S.dias <= 30 ? 13 : S.dias <= 90 ? 9 : 6;
  const carril = (nombre, cond, color, abierto = false) => {
    const xs = idx.filter(cond).map((i) => d.fecha[i]);
    return { type: "scatter", mode: "markers", x: xs, y: xs.map(() => nombre), yaxis: "y2", hoverinfo: "skip",
      marker: { symbol: abierto ? "square-open" : "square", size: tam, color, line: { width: abierto ? 2 : 0, color } } };
  };
  Plotly.react("planta-grafico", [
    { type: "bar", x, y: idx.map((i) => d.real[i]), marker: { color: "#1f6f86" }, name: "Generó",
      hovertemplate: "Generó %{y:,.0f} MWh<extra></extra>" },
    { type: "bar", x, y: idx.map((i) => d.perdida[i] > 0 ? d.perdida[i] : null), marker: { color: "#e2735f" }, name: "Dejó de generar",
      hovertemplate: "Dejó de generar %{y:,.0f} MWh<extra></extra>" },
    { type: "scatter", mode: "lines", x, y: idx.map((i) => d.decide[i] ? d.esperada[i] : null), line: { color: TINTA, width: 2, shape: "hvh" },
      name: "Debía generar", hovertemplate: "Debía generar %{y:,.0f} MWh<extra></extra>" },
    carril("Alerta del detector", (i) => d.alerta[i], "#d03b3b"),
    carril("Falla grave", (i) => d.grave[i], "#8f1f1f"),
    carril("Baja confianza", (i) => d.baja[i] && (d.alerta[i] || d.grave[i]), "#c98a00", true),
    carril("Sin decisión (sensor)", (i) => d.sensor[i], "#8b979c"),
  ], base({
    barmode: "stack", bargap: 0.12, hovermode: "x unified",
    margin: { l: 10, r: 16, t: 6, b: 10 },
    xaxis: { ...EJE, anchor: "y2", type: "date", tickformat: "%d %b", hoverformat: "%d de %B de %Y", showgrid: false },
    yaxis: { ...EJE, domain: [0.3, 1], title: { text: "MWh por día", font: { color: TENUE, size: 13 } }, rangemode: "tozero" },
    yaxis2: { ...EJE, domain: [0, 0.22], type: "category", showgrid: true, fixedrange: true, range: [-0.5, 3.5],
      categoryorder: "array", categoryarray: ["Sin decisión (sensor)", "Baja confianza", "Falla grave", "Alerta del detector"] },
  }), CONFIG);
}

// ------------------------------------------------------------------ 3. argentina
function filasMes() {
  return Object.entries(D.argentina.parques).flatMap(([c, q]) => {
    const i = q.fecha.indexOf(S.mes);
    if (i < 0 || q.fc[i] == null || q.fc_esp[i] == null) return [];
    const estado = q.alerta[i] ? "rojo" : q.bajo_p10[i] ? "amarillo" : "verde";
    return [{ c, nombre: nombreCorto(titulo(q.nombre)), provincia: q.provincia, lat: q.lat, lon: q.lon, fc: q.fc[i], ratio: q.fc[i] / q.fc_esp[i], estado }];
  });
}

function vistaArgentina() {
  const sel = $("#mes");
  if (!sel.options.length) {
    sel.innerHTML = [...D.argentina.meses].reverse().map((m) => `<option value="${m}">${mesLargo(m)}</option>`).join("");
    sel.addEventListener("change", () => { S.mes = sel.value; vistaArgentina(); });
    const mover = (k) => { const i = D.argentina.meses.indexOf(S.mes) + k; if (D.argentina.meses[i]) { S.mes = D.argentina.meses[i]; vistaArgentina(); } };
    $("#mes-ant").addEventListener("click", () => mover(-1));
    $("#mes-sig").addEventListener("click", () => mover(1));
  }
  sel.value = S.mes;
  const im = D.argentina.meses.indexOf(S.mes);
  $("#mes-ant").disabled = im === 0; $("#mes-sig").disabled = im === D.argentina.meses.length - 1;

  const filas = filasMes();
  const alertas = filas.filter((f) => f.estado === "rojo"), bajos = filas.filter((f) => f.estado === "amarillo");
  const peor = [...(alertas.length ? alertas : filas)].sort((a, b) => a.ratio - b.ratio)[0];
  const h1 = alertas.length
    ? `En ${mesLargo(S.mes).toLowerCase()}, ${alertas.length} de ${filas.length} parques rinden por debajo de lo esperado`
    : `En ${mesLargo(S.mes).toLowerCase()}, ningún parque tiene alerta`;
  $("#arg-franja").innerHTML = `${lampara(alertas.length ? "rojo" : "verde")}<div><h1>${h1}</h1>
    <p>${bajos.length ? `Otros ${bajos.length} están por debajo de su rango habitual. ` : ""}${peor ? `El que más se aleja: <b>${peor.nombre}</b> (${peor.provincia}), que generó ${pct(peor.ratio)} de lo esperado para el sol que tuvo.` : ""}</p></div>
    <div class="cifra"><strong>${alertas.length + bajos.length}</strong><span>parques para revisar</span></div>`;

  const capas = [["verde", 8, 0.7, "#7d9199"], ["amarillo", 13, 1, COLOR.amarillo], ["rojo", 14, 1, COLOR.rojo]].map(([e, size, op, color]) => {
    const fs = filas.filter((f) => f.estado === e);
    return { type: "scattergeo", lon: fs.map((f) => f.lon), lat: fs.map((f) => f.lat), mode: "markers",
      marker: { size, color, opacity: op, line: { width: e === "verde" ? 0 : 2, color: "#ffffff" } },
      customdata: fs.map((f) => [f.c, f.nombre, f.provincia, f.ratio * 100]),
      hovertemplate: "<b>%{customdata[1]}</b><br>%{customdata[2]}<br>Generó %{customdata[3]:.0f}% de lo esperado<extra></extra>" };
  });
  Plotly.react("arg-mapa", capas, base({ geo: { ...GEO, scope: "south america", lonaxis: { range: [-73.5, -53] }, lataxis: { range: [-55.5, -21.5] } } }), CONFIG);

  const rk = [...filas].sort((a, b) => a.fc - b.fc);
  const alto = Math.max(320, rk.length * 21 + 50);
  $("#arg-ranking").style.height = alto + "px";
  Plotly.react("arg-ranking", [{
    type: "bar", orientation: "h", x: rk.map((f) => f.fc), y: rk.map((f) => f.c),
    marker: { color: rk.map((f) => f.estado === "verde" ? "#a9b8bc" : COLOR[f.estado]) },
    customdata: rk.map((f) => [f.c, f.nombre, f.provincia, f.ratio * 100]),
    hovertemplate: "<b>%{customdata[1]}</b> · %{customdata[2]}<br>Factor de capacidad %{x:.1%}<br>Generó %{customdata[3]:.0f}% de lo esperado<extra></extra>",
  }], base({
    bargap: 0.25, margin: { l: 10, r: 16, t: 4, b: 10 },
    xaxis: { ...EJE, tickformat: ".0%", side: "top" },
    yaxis: { ...EJE, tickfont: { size: 12, color: TENUE }, showgrid: false, tickvals: rk.map((f) => f.c), ticktext: rk.map((f) => corto(nombreCorto(f.nombre))) },
  }), CONFIG);

  for (const id of ["arg-mapa", "arg-ranking"]) {
    const el = document.getElementById(id);
    el.removeAllListeners?.("plotly_click");
    el.on("plotly_click", (ev) => { S.parque = ev.points[0].customdata[0]; historiaParque(); });
  }
  historiaParque();
}

function historiaParque() {
  const q = D.argentina.parques[S.parque];
  if (!q) return;
  const ult = q.alerta.slice(-12).reduce((a, b) => a + b, 0);
  $("#arg-historia-titulo").innerHTML = `<p class="grupo-titulo" style="text-transform:none;letter-spacing:0;font-size:1.05rem">
    <b style="color:${TINTA};font-size:1.15rem">${nombreCorto(titulo(q.nombre))}</b>&nbsp;· ${q.provincia} · alerta en ${ult} de sus últimos 12 meses con dato</p>`;
  const al = q.fecha.map((f, i) => i).filter((i) => q.alerta[i]);
  Plotly.react("arg-historia", [
    { type: "scatter", mode: "lines", x: q.fecha, y: q.fc_esp, name: "Esperado para el sol que tuvo", line: { color: "#9aabb0", width: 2.5 },
      hovertemplate: "Esperado %{y:.1%}<extra></extra>" },
    { type: "scatter", mode: "lines+markers", x: q.fecha, y: q.fc, name: "Real", line: { color: TINTA, width: 2 }, marker: { size: 4 },
      hovertemplate: "Real %{y:.1%}<extra></extra>" },
    { type: "scatter", mode: "markers", x: al.map((i) => q.fecha[i]), y: al.map((i) => q.fc[i]), name: "Mes con alerta",
      marker: { color: COLOR.rojo, size: 10, line: { width: 2, color: "#fff" } }, hoverinfo: "skip" },
  ], base({
    showlegend: true, legend: { orientation: "h", y: 1.12, x: 0, font: { size: 13, color: TENUE } }, hovermode: "x unified",
    margin: { l: 10, r: 16, t: 30, b: 10 },
    xaxis: { ...EJE, type: "date", hoverformat: "%B %Y", showgrid: false },
    yaxis: { ...EJE, tickformat: ".0%", title: { text: "factor de capacidad", font: { color: TENUE, size: 13 } }, rangemode: "tozero" },
  }), CONFIG);
}

// ------------------------------------------------------------------ 4. limpieza y plata
// Mismas fórmulas que src/negocio.py (t_optimo_limpieza, costo_anual_limpieza, ahorro_anual_limpieza)
const N = D.negocio;
const tOptimo = (c, p, r) => Math.sqrt(2 * c / (p * N.e_mw * r));
const costoAnual = (t, c, p, r) => 365 * (c / t + p * N.e_mw * r * t / 2);
const ahorroAnual = (c, p, r) => costoAnual(N.t_base, c, p, r) - costoAnual(tOptimo(c, p, r), c, p, r);
{
  const t = tOptimo(N.costo, N.precio, N.tasa), a = ahorroAnual(N.costo, N.precio, N.tasa);
  if (Math.abs(t - N.control.t) > 1e-6 || Math.abs(a - N.control.ahorro) > 1e-3) console.warn("La calculadora no coincide con src/negocio.py", { t, a, control: N.control });
}

function vistaNegocio() {
  const ids = { costo: "costo", precio: "precio", tasa: "tasa" };
  for (const k in ids) {
    const el = document.getElementById(ids[k]);
    if (!el.dataset.listo) { el.value = S[k]; el.addEventListener("input", () => { S[k] = +el.value; vistaNegocio(); }); el.dataset.listo = "1"; }
  }
  const c = S.costo, p = S.precio, r = S.tasa / 100;
  $("#costo-v").textContent = usd(c);
  $("#precio-v").textContent = `USD ${fmt(p, 2)}`;
  $("#tasa-v").textContent = `${fmt(S.tasa, 3)}%`;
  const medida = Math.abs(S.tasa - N.tasa * 100) < 0.0005;
  $("#tasa-nota").innerHTML = medida
    ? `<span class="sello medido">Medido</span> En los datos: la energía cae 0,049% por cada día sin lluvia.`
    : `<span class="sello supuesto">Escenario</span> El valor medido en los datos es 0,049% por día.`;

  const T = tOptimo(c, p, r), ahorro = ahorroAnual(c, p, r);
  $("#l-t").textContent = `${fmt(T)} días`;
  $("#l-ahorro").textContent = usd(ahorro);
  $("#l-costo").textContent = usd(costoAnual(T, c, p, r));
  $("#neg-franja").innerHTML = T >= N.t_base
    ? `${lampara("verde")}<div><h1>Con estos supuestos, alcanza con limpiar una vez por año</h1>
       <p>La suciedad cuesta menos que la limpieza: el intervalo óptimo sería de ${fmt(T)} días.</p></div><div></div>`
    : `${lampara("amarillo")}<div><h1>Conviene limpiar cada ${fmt(T)} días</h1>
       <p>Unas ${fmt(365 / T, 1)} limpiezas por año, además de las lluvias. Frente a limpiar una vez por año, se ahorran <b>${usd(ahorro)} por MW al año</b>.</p></div>
       <div class="cifra"><strong>${usd(ahorro)}</strong><span>ahorro por MW al año</span></div>`;

  const ts = Array.from({ length: 356 }, (_, i) => i + 10);
  const cs = ts.map((t) => costoAnual(t, c, p, r));
  const techo = Math.max(costoAnual(N.t_base, c, p, r), costoAnual(T, c, p, r)) * 1.5;
  Plotly.react("neg-curva", [
    { type: "scatter", mode: "lines", x: ts, y: cs, line: { color: TINTA, width: 2.5 },
      hovertemplate: "Limpiar cada %{x} días: USD %{y:,.0f} por MW al año<extra></extra>" },
    { type: "scatter", mode: "markers+text", x: [Math.min(T, 365)], y: [costoAnual(Math.min(T, 365), c, p, r)], text: [`Óptimo: cada ${fmt(T)} días`],
      textposition: "bottom center", textfont: { size: 14, color: TINTA }, marker: { size: 13, color: COLOR.amarillo, line: { width: 3, color: "#fff" } }, hoverinfo: "skip" },
    { type: "scatter", mode: "markers+text", x: [N.t_base], y: [costoAnual(N.t_base, c, p, r)], text: ["Una vez por año"],
      textposition: "top left", textfont: { size: 13, color: TENUE }, marker: { size: 10, color: "#8b979c" }, hoverinfo: "skip" },
  ], base({
    margin: { l: 10, r: 20, t: 10, b: 10 },
    xaxis: { ...EJE, range: [10, 372], title: { text: "días entre limpiezas", font: { color: TENUE, size: 13 } } },
    yaxis: { ...EJE, range: [0, techo], tickprefix: "USD ", title: { text: "costo por MW al año", font: { color: TENUE, size: 13 } } },
  }), CONFIG);

  // caso station09: pérdida en días con alerta, al precio elegido
  const s9 = D.flota.plantas.station09;
  let mwh = 0, dias = 0, real = 0, esp = 0;
  const porMes = {};
  s9.fecha.forEach((f, i) => {
    if (s9.decide[i]) { real += s9.real[i]; esp += s9.esperada[i]; }
    if (s9.alerta[i]) { mwh += s9.perdida[i] || 0; dias++; porMes[f.slice(0, 7)] = (porMes[f.slice(0, 7)] || 0) + (s9.perdida[i] || 0); }
  });
  const flota = Object.keys(D.flota.plantas).reduce((a, q) => a + perdidaEnAlertas(q, "0000", "9999").mwh, 0);
  $("#caso-titulo").textContent = `station09 perdió ${fmt(mwh)} MWh en ${dias} días con alerta: ${usd(mwh * p)}`;
  $("#caso-texto").innerHTML = `Durante el año generó ${pct(real / esp)} de lo que debía. Es el ${pct(mwh / flota)} de toda la energía perdida en días con alerta de la flota (${fmt(flota)} MWh).`;
  const meses = Object.keys(porMes).sort();
  Plotly.react("caso-grafico", [{
    type: "bar", x: meses.map((m) => m + "-15"), y: meses.map((m) => porMes[m] * p), marker: { color: "#e2735f" },
    hovertemplate: "%{x|%B %Y}: USD %{y:,.0f}<extra></extra>",
  }], base({
    bargap: 0.2, margin: { l: 10, r: 10, t: 10, b: 10 },
    xaxis: { ...EJE, type: "date", tickformat: "%b %Y", showgrid: false },
    yaxis: { ...EJE, tickprefix: "USD ", title: { text: "perdido por mes", font: { color: TENUE, size: 13 } } },
  }), CONFIG);
}

// ------------------------------------------------------------------ arranque
Plotly.register({
  moduleType: "locale", name: "es", dictionary: {},
  format: {
    days: ["domingo", "lunes", "martes", "miércoles", "jueves", "viernes", "sábado"],
    shortDays: ["dom", "lun", "mar", "mié", "jue", "vie", "sáb"],
    months: ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"],
    shortMonths: ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"],
    date: "%d/%m/%Y", decimal: ",", thousands: ".",
  },
});
Plotly.setPlotConfig({ locale: "es" });
const fechaInput = $("#fecha");
fechaInput.min = FECHAS[0]; fechaInput.max = FECHAS.at(-1); fechaInput.value = S.fecha;
fechaInput.addEventListener("change", () => {
  const f = fechaInput.value;
  S.fecha = FECHAS.includes(f) ? f : (FECHAS.filter((x) => x <= f).at(-1) ?? FECHAS[0]);
  fechaInput.value = S.fecha;
  mostrar();
});
$("#planta-periodo").querySelectorAll("button").forEach((b) => b.addEventListener("click", () => { S.dias = +b.dataset.dias; vistaPlanta(); }));
window.addEventListener("hashchange", mostrar);
mostrar();
