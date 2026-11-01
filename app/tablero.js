/* Solar / Datos. Evidencia de src/academico.py. Sin red y sin enlaces externos. */
'use strict';
const D = window.DEFENSA;
const $ = s => document.querySelector(s);
const fmt = (n, d=0) => n == null || !Number.isFinite(+n) ? '—' : (+n).toLocaleString('es-AR',{minimumFractionDigits:d,maximumFractionDigits:d});
const esc = s => String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const MESES = ['ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic'];
const MESES_LARGO = ['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre'];
const DIAS = [0,31,28,31,30,31,30,31,31,30,31,30,31];
const C = {paper:'#f5f9f4',plate:'#ffffff',plate2:'#e4efe7',line:'#cfe0d4',lineStrong:'#7fa992',ink:'#111b16',muted:'#34463c',faint:'#53665b',blue:'#1f3fbf',grid:'#2e9c6a'};
const SANS = 'Barlow, Helvetica Neue, Arial, sans-serif';
const TITULOS = {
  atlas:['Los datos de los parques','Dónde están los 56 parques, cuánto rinden y qué muestra la exploración antes de modelar.'],
  modelos:['Qué modelo estima mejor','El menor RMSE de validation (2024) elige el modelo. El test es desde 2025 y es retrospectivo: esos meses ya se exploraron.'],
  sitio:['Cuánto generaría un parque','Hacé clic en el mapa donde iría el parque. El modelo estima el factor con la ubicación, el clima y el mes; la energía sale de la potencia y las horas.'],
  serie:['Un parque real','Factor de capacidad observado contra el estimado, mes a mes. Los ceros operativos siguen en la serie.']
};
const DESCRIPCION = {
  rf:'Promedia muchos árboles. Cada uno ve una muestra y un subconjunto de variables. Dentro del rango observado responde; afuera no extrapola.',
  xgb:'Suma árboles en secuencia: cada uno corrige el error del anterior. El RMSE de validation (2024) limita la complejidad. Afuera del rango de los parques no extrapola.',
  arbol:'Parte los datos con preguntas. Cada hoja predice un promedio. Afuera del rango repite la hoja del borde.',
  lineal_multiple:'Suma ubicación, clima y mes en una recta. Enero queda como referencia del mes.',
  lineal_simple:'Una recta que usa solo la irradiación. Es la línea de base.'
};
const ZOOM = 5;
const S = {vista:'atlas',foco:null,parque:null,orden:'mw',desc:true,dibujado:{}};
const config = {responsive:true,displaylogo:false,displayModeBar:'hover',modeBarButtonsToRemove:['lasso2d','select2d','autoScale2d'],toImageButtonOptions:{format:'png',filename:'solar-datos',scale:2}};

/* Gráficos */
function eje(extra={}){return {gridcolor:C.line,linecolor:C.lineStrong,zeroline:false,tickfont:{size:12,color:C.muted,family:SANS},title:{font:{size:12,color:C.faint,family:SANS}},automargin:true,...extra};}
function layout(extra={}){return {font:{family:SANS,size:13,color:C.ink},paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'rgba(0,0,0,0)',margin:{l:8,r:12,t:10,b:34},showlegend:false,hoverlabel:{bgcolor:'#fff',bordercolor:C.ink,font:{color:C.ink,size:13,family:SANS}},...extra};}
function plot(id,traces,extra={}){
  const el=document.getElementById(id);if(!el)return;
  const done=Plotly.react(el,traces,layout(extra),config);
  const fail=()=>{el.innerHTML='<p class="empty">No se pudo dibujar el gráfico. Recargá la página para volver a intentarlo.</p>';};
  return done&&done.then?done.catch(fail):done;
}

/* Cálculo de un sitio: lee la grilla precalculada; no reimplementa el modelo */
const bisiesto = y => y%4===0 && (y%100!==0 || y%400===0);
const diasMes = (y,m) => m===2 && bisiesto(y) ? 29 : DIAS[m];
function km(lat1,lon1,lat2,lon2){const rad=Math.PI/180;const x=(lon2-lon1)*rad*Math.cos((lat1+lat2)/2*rad);const y=(lat2-lat1)*rad;return 6371*Math.hypot(x,y);}
function argminAbs(xs,v){let k=0,b=Infinity;xs.forEach((x,i)=>{const d=Math.abs(x-v);if(d<b){b=d;k=i;}});return k;}
function estimar(lat,lon,anio,mw){
  if(!(mw>0)||!Number.isFinite(lat)||!Number.isFinite(lon)||!Number.isInteger(anio))return null;
  const g=D.grilla,i=argminAbs(g.lats,lat),j=argminAbs(g.lons,lon),slat=g.lats[i],slon=g.lons[j];
  let parque=D.parques[0],distancia=Infinity;
  for(const p of D.parques){const d=km(slat,slon,p.lat,p.lon);if(d<distancia){parque=p;distancia=d;}}
  const clave=g.anios.includes(anio)?String(anio):'0';
  const tabla=g.factores[clave],base=(i*g.lons.length+j)*12;
  const meses=[],modos=[];
  let energia=0,horas=0;
  for(let mes=1;mes<=12;mes++){
    const factor=tabla[base+mes-1];
    const obs=D._obs.get(parque.i+'|'+anio+'|'+mes);
    const tip=D._tip.get(parque.i+'|'+mes);
    const modo=obs?'observado':tip?'tipico':null;
    if(factor==null||!modo)continue;
    const h=diasMes(anio,mes)*24,gwh=factor*mw*h/1000;
    energia+=gwh;horas+=h;modos.push(modo);
    meses.push({mes,factor,gwh,clima:modo,ghi:(obs||tip).ghi});
  }
  if(!meses.length)return null;
  const modo=new Set(modos).size===1?modos[0]:'mixto';
  const r=D.rango;
  const dentro=lat>=r.lat_min&&lat<=r.lat_max&&lon>=r.lon_min&&lon<=r.lon_max;
  return {horas,lat,lon,anio,potencia_mw:mw,lat_celda:slat,lon_celda:slon,distancia_celda_km:km(lat,lon,slat,slon),energia_gwh:energia,factor:energia*1000/(mw*horas),modo,dentro,distancia_km:distancia,nombre:parque.nombre,provincia:parque.provincia,central:parque.central,meses,incompleto:meses.length<12};
}

/* Datos derivados */
const NOMBRES = {lineal_simple:'Simple linear regression',lineal_multiple:'Multiple linear regression',arbol:'Decision tree',rf:'Random Forest',xgb:'XGBoost'};
const ingles = t => String(t).replace(/Prueba retrospectiva/g,'Test retrospectivo').replace(/Entrenamiento/g,'Train').replace(/entrenamiento/g,'train').replace(/Validación/g,'Validation').replace(/validación/g,'validation').replace(/Prueba/g,'Test').replace(/prueba/g,'test');
function preparar(){
  D.regresion.comparacion.forEach(m=>{m.nombre=NOMBRES[m.id]||m.nombre;});
  D.regresion.nombre=NOMBRES[D.regresion.elegido]||D.regresion.nombre;
  D._obs=new Map(D.clima.map(r=>[r.i+'|'+r.anio+'|'+r.mes,r]));
  D._tip=new Map(D.tipico.map(r=>[r.i+'|'+r.mes,r]));
  D._idx=new Map(D.parques.map(p=>[p.central,p]));
  const por=new Map();
  for(const r of D.serie){if(!por.has(r.central))por.set(r.central,[]);por.get(r.central).push(r);}
  for(const rows of por.values())rows.sort((a,b)=>a.fecha.localeCompare(b.fecha));
  D._serie=por;
  D._stats=new Map([...por].map(([id,rows])=>{
    const prueba=rows.filter(r=>r.particion==='prueba');
    const media=rows.reduce((s,r)=>s+r.factor_capacidad,0)/rows.length;
    const mae=prueba.length?prueba.reduce((s,r)=>s+Math.abs(r.factor_capacidad-r.pred),0)/prueba.length:null;
    return [id,{n:rows.length,media,mae,ceros:rows.filter(r=>r.factor_capacidad===0).length,desde:rows[0].fecha,hasta:rows.at(-1).fecha}];
  }));
  // Fila de exploración: cada mes-parque con su clima
  D._eda=D.serie.map(r=>{const p=D._idx.get(r.central);const c=D._obs.get(p.i+'|'+(+r.fecha.slice(0,4))+'|'+(+r.fecha.slice(5,7)));return c?{factor:r.factor_capacidad,ghi:c.ghi,temp:c.temp,nub:c.nub,lat:p.lat,lon:p.lon,mes:+r.fecha.slice(5,7)}:null;}).filter(Boolean);
  // Campo típico anual de la grilla: promedio de los doce meses
  const g=D.grilla,t=g.factores['0'];
  D._campo=[];
  for(let i=0;i<g.lats.length;i++)for(let j=0;j<g.lons.length;j++){
    let s=0,n=0;for(let m=0;m<12;m++){const v=t[(i*g.lons.length+j)*12+m];if(v!=null){s+=v;n++;}}
    if(n)D._campo.push({lat:g.lats[i],lon:g.lons[j],f:s/n});
  }
}
function titulo(s){
  const chico=new Set(['de','del','la','las','el','los','y']);
  return String(s).toLowerCase().split(/\s+/).map((w,k)=>{
    if(/^(i|ii|iii|iv|v|vi|fv|s\.?a\.?|sa)$/i.test(w))return w.toUpperCase();
    if(k>0&&chico.has(w))return w;
    return w.charAt(0).toUpperCase()+w.slice(1);
  }).join(' ').replace(/^P\.?\s?S\.?\s?F?\.?V?\.?\s/i,'P.S. ').replace(/^Pque\b/,'Parque');
}
const provincia = s => titulo(s||'');
function dms(v,pos,neg){const a=Math.abs(v),g=Math.floor(a),m=Math.round((a-g)*60);return `${g}° ${String(m).padStart(2,'0')}′ ${v<0?neg:pos}`;}
const coords = (lat,lon) => `${dms(lat,'N','S')} · ${dms(lon,'E','O')}`;
const dentroRango = p => p.lat>=D.rango.lat_min&&p.lat<=D.rango.lat_max&&p.lon>=D.rango.lon_min&&p.lon<=D.rango.lon_max;

/* La carta: SVG propio, sin mosaicos ni red */
const MARCOS = {
  carta:{lon0:-71.8,lon1:-57.4,lat0:-21.5,lat1:-39.8,w:600},
  pais:{lon0:-74.2,lon1:-53.2,lat0:-21.2,lat1:-55.4,w:150}
};
function proyeccion(m){
  const k=m.k||Math.cos((m.lat0+m.lat1)/2*Math.PI/180);
  const s=m.w/((m.lon1-m.lon0)*k),h=(m.lat0-m.lat1)*s;
  return {w:m.w,h,k,s,x:lon=>(lon-m.lon0)*k*s,y:lat=>(m.lat0-lat)*s,lon:x=>m.lon0+x/(k*s),lat:y=>m.lat0-y/s};
}
const trazo = (P,anillos) => anillos.map(a=>{let s='';for(let i=0;i<a.length;i+=2)s+=(i?'L':'M')+P.x(a[i]).toFixed(1)+','+P.y(a[i+1]).toFixed(1);return s+'Z';}).join('');
function contornos(P){
  let out='';
  for(const [pais,anillos] of Object.entries(window.CONTORNOS||{})){
    const d=trazo(P,anillos);
    out+=pais==='ARG'?`<path d="${d}" fill="${C.plate2}" stroke="${C.ink}" stroke-width="1.3" stroke-linejoin="round"/>`:`<path d="${d}" fill="none" stroke="${C.lineStrong}" stroke-width="1" stroke-linejoin="round"/>`;
  }
  return out;
}
const CAMPO = [0.20,0.34];
const radio = mw => 2.6+Math.sqrt(Math.max(mw,0))*0.82;
function graticula(m){
  const span=m.lon1-m.lon0,paso=span>8?2:span>3?1:.5,lats=[],lons=[];
  for(let v=Math.ceil(m.lat1/paso)*paso;v<=m.lat0+1e-9;v+=paso)lats.push(+v.toFixed(2));
  for(let v=Math.ceil(m.lon0/paso)*paso;v<=m.lon1+1e-9;v+=paso)lons.push(+v.toFixed(2));
  return {paso,lats,lons};
}
// Marco de la carta centrado en un parque; conserva la proporción 600 × 887
function marcoZoom(p){
  const c=MARCOS.carta,dl=(c.lon1-c.lon0)/ZOOM,dt=(c.lat0-c.lat1)/ZOOM;
  const lon0=Math.min(Math.max(p.lon-dl/2,c.lon0),c.lon1-dl),lat0=Math.min(Math.max(p.lat+dt/2,c.lat1+dt),c.lat0);
  return {lon0,lon1:lon0+dl,lat0,lat1:lat0-dt,w:c.w,k:proyeccion(c).k};
}
function dibujarCarta(svg,m,opts={}){
  const P=proyeccion(m),grande=m.w>300,lineas=graticula(m);
  svg.setAttribute('viewBox',`0 0 ${P.w.toFixed(0)} ${P.h.toFixed(0)}`);
  svg._P=P;
  let s=`<defs><clipPath id="clip-${svg.id}"><rect width="${P.w}" height="${P.h}"/></clipPath></defs>`;
  s+=`<rect width="${P.w}" height="${P.h}" fill="#fff"/>`;
  s+=`<g clip-path="url(#clip-${svg.id})">`;
  if(grande){
    for(const lat of lineas.lats)s+=`<line x1="0" x2="${P.w}" y1="${P.y(lat)}" y2="${P.y(lat)}" stroke="${C.grid}" stroke-opacity=".35" stroke-width=".7"/>`;
    for(const lon of lineas.lons)s+=`<line y1="0" y2="${P.h}" x1="${P.x(lon)}" x2="${P.x(lon)}" stroke="${C.grid}" stroke-opacity=".35" stroke-width=".7"/>`;
  }
  s+=contornos(P);
  if(grande&&opts.campo){
    const g=D.grilla,cw=g.paso*P.k*P.s,ch=g.paso*P.s;
    s+=`<clipPath id="tierra-${svg.id}"><path d="${trazo(P,(window.CONTORNOS||{}).ARG||[])}"/></clipPath><g clip-path="url(#tierra-${svg.id})">`;
    for(const c of D._campo){const a=Math.max(0,Math.min(1,(c.f-CAMPO[0])/(CAMPO[1]-CAMPO[0])));s+=`<rect x="${(P.x(c.lon)-cw/2).toFixed(1)}" y="${(P.y(c.lat)-ch/2).toFixed(1)}" width="${(cw+.3).toFixed(1)}" height="${(ch+.3).toFixed(1)}" fill="${C.blue}" fill-opacity="${(0.03+Math.pow(a,1.5)*0.42).toFixed(3)}"><title>Factor típico estimado ${fmt(c.f,3)}</title></rect>`;}
    s+='</g>';
  }
  const r=D.rango;
  if(opts.restringir&&grande){const x0=P.x(r.lon_min),x1=P.x(r.lon_max),y0=P.y(r.lat_max),y1=P.y(r.lat_min);s+=`<path d="M0,0H${P.w}V${P.h}H0Z M${x0.toFixed(1)},${y0.toFixed(1)}V${y1.toFixed(1)}H${x1.toFixed(1)}V${y0.toFixed(1)}Z" fill="#fff" fill-opacity=".62" fill-rule="evenodd" pointer-events="none"/>`;}
  s+=`<rect x="${P.x(r.lon_min)}" y="${P.y(r.lat_max)}" width="${P.x(r.lon_max)-P.x(r.lon_min)}" height="${P.y(r.lat_min)-P.y(r.lat_max)}" fill="none" stroke="${C.blue}" stroke-width="${grande?1.4:.9}" stroke-dasharray="7 4"/>`;
  if(grande)s+=`<text x="${P.x(r.lon_min)+4}" y="${P.y(r.lat_min)+16}" fill="${C.blue}">RANGO DEL TRAIN SET</text>`;
  if(!grande){const c=opts.marco||MARCOS.carta;s+=`<rect x="${P.x(c.lon0)}" y="${P.y(c.lat0)}" width="${P.x(c.lon1)-P.x(c.lon0)}" height="${P.y(c.lat1)-P.y(c.lat0)}" fill="none" stroke="${C.ink}" stroke-width="1"/>`;}
  const q=opts.consulta;
  if(q&&grande){const g=D.grilla,cw=g.paso*P.k*P.s,ch=g.paso*P.s;s+=`<rect x="${(P.x(q.lon_celda)-cw/2).toFixed(1)}" y="${(P.y(q.lat_celda)-ch/2).toFixed(1)}" width="${cw.toFixed(1)}" height="${ch.toFixed(1)}" fill="${C.ink}" fill-opacity=".14" stroke="${C.ink}" stroke-width="1.4"/>`;}
  // Línea al parque que presta el clima
  if(q){const p=D._idx.get(q.central);if(p)s+=`<line x1="${P.x(q.lon)}" y1="${P.y(q.lat)}" x2="${P.x(p.lon)}" y2="${P.y(p.lat)}" stroke="${C.ink}" stroke-width="${grande?1.4:1}" stroke-dasharray="3 4"/>`;}
  // Estrellas: diámetro por potencia en escala fija
  const parques=[...D.parques].sort((a,b)=>b.potencia_mw-a.potencia_mw);
  for(const p of parques){
    const rr=grande?radio(p.potencia_mw):Math.max(1.3,radio(p.potencia_mw)/3.2),sel=p.central===opts.seleccion;
    if(grande&&p.potencia_mw>=50)s+=`<circle cx="${P.x(p.lon)}" cy="${P.y(p.lat)}" r="${(rr+4).toFixed(1)}" fill="none" stroke="${C.ink}" stroke-width=".8" pointer-events="none"/>`;
    s+=`<circle class="${grande?'estrella':''}" data-central="${esc(p.central)}" cx="${P.x(p.lon).toFixed(1)}" cy="${P.y(p.lat).toFixed(1)}" r="${rr.toFixed(1)}" fill="${C.ink}" stroke="#fff" stroke-width="${grande?1.2:.4}"><title>${esc(titulo(p.nombre))} · ${esc(provincia(p.provincia))} · ${fmt(p.potencia_mw,1)} MW</title></circle>`;
    if(sel&&grande)s+=`<circle cx="${P.x(p.lon)}" cy="${P.y(p.lat)}" r="${rr+7}" fill="none" stroke="${C.ink}" stroke-width="2.4"/><text class="nombre sel" x="${P.x(p.lon)+rr+11}" y="${P.y(p.lat)+5}">${esc(titulo(p.nombre))}</text>`;
  }
  if(grande&&opts.rotulos){
    const ya=new Set([opts.seleccion]);
    const visibles=opts.zoom?parques.filter(p=>p.lon>=m.lon0&&p.lon<=m.lon1&&p.lat<=m.lat0&&p.lat>=m.lat1):parques.slice(0,4);
    for(const p of visibles){if(ya.has(p.central))continue;s+=`<text class="nombre" x="${P.x(p.lon)+radio(p.potencia_mw)+5}" y="${P.y(p.lat)+4}">${esc(titulo(p.nombre).replace(/^(Parque Solar( Fotovoltaico)?|P\.S\.( F\.V\.)?)\s+/i,''))}</text>`;}
  }
  // Retículo del sitio consultado
  if(q){
    const x=P.x(q.lon),y=P.y(q.lat),R=grande?13:5,col=C.ink;
    s+=`<g pointer-events="none"><circle cx="${x}" cy="${y}" r="${R}" fill="none" stroke="${col}" stroke-width="${grande?1.8:1.2}"/><circle cx="${x}" cy="${y}" r="${grande?2.6:1.4}" fill="${col}"/>`+
      `<line x1="${x-R*1.8}" x2="${x-R*.55}" y1="${y}" y2="${y}" stroke="${col}" stroke-width="1.4"/><line x1="${x+R*.55}" x2="${x+R*1.8}" y1="${y}" y2="${y}" stroke="${col}" stroke-width="1.4"/>`+
      `<line y1="${y-R*1.8}" y2="${y-R*.55}" x1="${x}" x2="${x}" stroke="${col}" stroke-width="1.4"/><line y1="${y+R*.55}" y2="${y+R*1.8}" x1="${x}" x2="${x}" stroke="${col}" stroke-width="1.4"/></g>`;
  }
  s+='</g>';
  if(grande){
    for(const lat of lineas.lats)s+=`<text x="4" y="${P.y(lat)-4}">${fmt(Math.abs(lat),lineas.paso<1?1:0)}° S</text>`;
    for(const lon of lineas.lons)if(lineas.paso!==2||Math.abs(lon/2)%2===1)s+=`<text x="${P.x(lon)+4}" y="${P.h-6}">${fmt(Math.abs(lon),lineas.paso<1?1:0)}° O</text>`;
  }
  s+=`<rect x=".5" y=".5" width="${P.w-1}" height="${P.h-1}" fill="none" stroke="${C.ink}" stroke-width="1.2"/>`;
  svg.innerHTML=s;
}
function leyendaCarta(){
  const est=[5,20,50,100].map(mw=>{const r=radio(mw);return `<svg width="${2*r+4}" height="${2*r+4}" aria-hidden="true"><circle cx="${r+2}" cy="${r+2}" r="${r}" fill="${C.ink}"/></svg><span>${mw}</span>`;}).join('');
  $('#atlas-leyenda').innerHTML=`<div class="grp"><span class="ttl">Potencia (MW)</span>${est}</div>`+
    `<div class="grp"><span class="ttl">Factor típico estimado</span><span>${fmt(CAMPO[0],2)}</span><span class="ramp" aria-hidden="true"></span><span>${fmt(CAMPO[1],2)}</span></div>`+
    `<div class="grp"><svg width="28" height="12" aria-hidden="true"><rect x="1" y="1" width="26" height="10" fill="none" stroke="${C.blue}" stroke-dasharray="5 3"/></svg><span>Rango de parques del train set</span></div>`;
}
function puntoCarta(svg,ev){
  const P=svg._P;if(!P)return null;
  const pt=svg.createSVGPoint();pt.x=ev.clientX;pt.y=ev.clientY;
  const m=svg.getScreenCTM();if(!m)return null;
  const p=pt.matrixTransform(m.inverse());
  return {lat:+P.lat(p.y).toFixed(2),lon:+P.lon(p.x).toFixed(2)};
}

/* Encabezado y navegación */
function barraEvidencia(){
  const r=D.regresion,m=r.comparacion.find(x=>x.id===r.elegido).test,cv=r.cv_parques;
  const celda=(k,v,c='')=>`<div class="celda ${c}"><span>${k}</span><b>${v}</b></div>`;
  $('#evidencia').innerHTML=celda('Modelo elegido',esc(r.nombre),'modelo')+celda('RMSE test',fmt(m.rmse,4))+celda('MAE test',fmt(m.mae,4))+celda('R² test',fmt(m.r2,3))+celda('RMSE new park',fmt(cv.rmse,4))+celda('Alcance','Factor de capacidad mensual · test retrospectivo desde 2025','alcance');
}
function mostrar(){
  const enfocado=document.activeElement;
  const pedido=(location.hash||'#atlas').slice(1);
  const cambio=S.vista!==pedido&&S._iniciado;
  S.vista=Object.hasOwn(TITULOS,pedido)?pedido:'atlas';S._iniciado=true;
  if(cambio)window.scrollTo(0,0);
  document.querySelectorAll('.view').forEach(el=>{el.hidden=el.id!=='vista-'+S.vista;});
  document.querySelectorAll('#navegacion a').forEach(a=>{if(a.hash==='#'+S.vista)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');});
  $('#titulo').textContent=TITULOS[S.vista][0];
  $('#subtitulo').textContent=TITULOS[S.vista][1];
  barraEvidencia();
  ({atlas,modelos,sitio,serie}[S.vista])();
  const vista=$('#vista-'+S.vista);vista.classList.remove('entra');void vista.offsetWidth;vista.classList.add('entra');
  requestAnimationFrame(()=>requestAnimationFrame(()=>document.querySelectorAll('.view:not([hidden]) .js-plotly-plot').forEach(el=>Plotly.Plots.resize(el))));
  if(enfocado?.matches?.('#navegacion a') && enfocado.hash==='#'+S.vista)enfocado.focus();
}

/* Datos (#atlas): carta, índice, exploración */
function dibujarAtlas(){
  const p=S.zoom&&D._idx.get(S.zoom),marco=p?marcoZoom(p):MARCOS.carta;
  dibujarCarta($('#atlas-carta'),marco,{campo:true,rotulos:true,seleccion:S.parque,zoom:!!p});
  dibujarCarta($('#atlas-inset'),MARCOS.pais,{marco:p?marco:null});
  $('#atlas-reset').hidden=!p;
  $('#atlas-meta').textContent=p?`acercado ${ZOOM}× · ${titulo(p.nombre)}`:'graticula de 2°';
}
function atlas(){
  dibujarAtlas();
  leyendaCarta();
  indice();
  eda();
}
function indice(){
  const filas=D.parques.map(p=>({p,st:D._stats.get(p.central)})).filter(x=>x.st);
  const k=S.orden,dir=S.desc?-1:1;
  const val={nombre:x=>titulo(x.p.nombre),provincia:x=>x.p.provincia,mw:x=>x.p.potencia_mw,factor:x=>x.st.media,rango:x=>dentroRango(x.p)?0:1};
  filas.sort((a,b)=>{const va=val[k](a),vb=val[k](b);return (typeof va==='string'?va.localeCompare(vb,'es'):va-vb)*dir;});
  $('#indice tbody').innerHTML=filas.map(({p,st})=>`<tr data-central="${esc(p.central)}" tabindex="0" aria-selected="${p.central===S.parque}"><td>${esc(titulo(p.nombre))}</td><td>${esc(provincia(p.provincia))}</td><td class="number">${fmt(p.potencia_mw,1)}</td><td class="number">${fmt(st.media,3)}</td><td class="rango">${dentroRango(p)?'dentro':'<b>fuera</b>'}</td></tr>`).join('');
  document.querySelectorAll('#indice th button').forEach(b=>{if(b.dataset.orden===k)b.setAttribute('aria-sort',S.desc?'descending':'ascending');else b.removeAttribute('aria-sort');});
  const fuera=D.parques.filter(p=>!dentroRango(p)).length;
  $('#indice-meta').textContent=`${D.parques.length} parques`;
  $('#indice-nota').textContent=`${fuera} parques quedan fuera del rectángulo del train set: entraron después de 2023. Clic en una fila marca el parque y acerca la carta; clic en una estrella lo marca; doble clic abre su serie.`;
}
function seleccionarParque(id,abrir,acercar){
  S.parque=id;
  if(abrir){location.hash='#serie';return;}
  if(acercar)S.zoom=id;
  dibujarAtlas();
  document.querySelectorAll('#indice tbody tr').forEach(tr=>tr.setAttribute('aria-selected',String(tr.dataset.central===id)));
  document.querySelector(`#indice tr[data-central="${CSS.escape(id)}"]`)?.scrollIntoView({block:'nearest'});
}
function pearson(a,b){const n=a.length,ma=a.reduce((s,v)=>s+v,0)/n,mb=b.reduce((s,v)=>s+v,0)/n;let sab=0,sa=0,sb=0;for(let i=0;i<n;i++){const x=a[i]-ma,y=b[i]-mb;sab+=x*y;sa+=x*x;sb+=y*y;}return sab/Math.sqrt(sa*sb);}
function eda(){
  if(S.dibujado.eda)return;S.dibujado.eda=true;
  const prov=new Map();
  for(const r of D.serie){const k=provincia(r.provincia);if(!prov.has(k))prov.set(k,{suma:0,n:0,parques:new Set()});const v=prov.get(k);v.suma+=r.factor_capacidad;v.n++;v.parques.add(r.central);}
  const filas=[...prov].map(([k,v])=>({k,media:v.suma/v.n,n:v.n,parques:v.parques.size})).sort((a,b)=>b.media-a.media);
  $('#eda-prov-meta').textContent=`factor medio · ${filas.length} provincias`;
  plot('eda-prov',[{type:'bar',orientation:'h',x:filas.map(r=>r.media),y:filas.map(r=>`${r.k} (${r.parques})`),marker:{color:C.ink},text:filas.map(r=>fmt(r.media,3)),textposition:'outside',cliponaxis:false,textfont:{size:12,color:C.ink,family:SANS},customdata:filas.map(r=>[r.parques,r.n]),hovertemplate:'%{y}<br>factor medio %{x:.3f}<br>%{customdata[1]} meses-parque<extra></extra>'}],
    {xaxis:eje({title:{text:'Factor de capacidad medio (entre paréntesis, cantidad de parques)'},tickformat:'.2f',range:[0,Math.max(...filas.map(r=>r.media))*1.18]}),yaxis:eje({autorange:'reversed',tickfont:{size:12,color:C.ink,family:SANS}}),margin:{l:8,r:40,t:6,b:46},bargap:.3});
  const f=D._eda.map(r=>r.factor);
  plot('eda-mes',MESES.map((m,k)=>({type:'box',name:m,y:D._eda.filter(r=>r.mes===k+1).map(r=>r.factor),marker:{color:C.ink,size:3,opacity:.5},line:{color:k>=4&&k<=7?C.muted:C.blue,width:1.4},fillcolor:'rgba(31,63,191,.09)',boxpoints:'outliers',hoverinfo:'y'})),
    {yaxis:eje({title:{text:'Factor de capacidad'},tickformat:'.2f'}),xaxis:eje()});
  const g=D._eda.map(r=>r.ghi),rr=pearson(g,f);
  $('#eda-r').textContent=`correlación ${fmt(rr,2)}`;
  plot('eda-disp',[{type:'scattergl',mode:'markers',x:g,y:f,marker:{color:C.ink,size:4,opacity:.35},hovertemplate:'%{x:.0f} kWh/m² · factor %{y:.3f}<extra></extra>'}],
    {xaxis:eje({title:{text:'Irradiación del mes (kWh/m²)'}}),yaxis:eje({title:{text:'Factor de capacidad'},tickformat:'.2f'})});
  const vars=[['factor','factor'],['ghi','irradiación'],['temp','temp. máx.'],['nub','nubosidad'],['lat','latitud'],['lon','longitud']];
  const cols=vars.map(([k])=>D._eda.map(r=>r[k]));
  const z=cols.map(a=>cols.map(b=>pearson(a,b)));
  plot('eda-corr',[{type:'heatmap',z,x:vars.map(v=>v[1]),y:vars.map(v=>v[1]),zmin:-1,zmax:1,colorscale:[[0,'#a9c4b4'],[.5,C.plate],[1,'#8da2ee']],showscale:false,text:z.map(r=>r.map(v=>fmt(v,2))),texttemplate:'%{text}',textfont:{size:12,color:C.ink},hovertemplate:'%{y} y %{x}: %{text}<extra></extra>',xgap:2,ygap:2}],
    {xaxis:eje({showgrid:false,side:'bottom'}),yaxis:eje({showgrid:false,autorange:'reversed'}),margin:{l:8,r:8,t:6,b:30}});
}
/* Modelos */
function modelos(){
  const r=D.regresion,el=r.comparacion.find(m=>m.id===r.elegido);
  const n=[el.train.n,el.validacion.n,el.test.n];
  $('#split').style.gridTemplateColumns=n.map(v=>v+'fr').join(' ');
  $('#split').innerHTML=`<div><b>Train</b><p>Hasta 2023 · ${fmt(n[0],0)} meses con generación</p></div><div><b>Validation</b><p>2024 · ${fmt(n[1],0)} · elige</p></div><div><b>Test</b><p>Desde 2025 · ${fmt(n[2],0)} · retrospectivo</p></div>`;
  $('#modelos-unidades').textContent=r.unidad_target;
  $('#modelos-tabla tbody').innerHTML=r.comparacion.map(m=>`<tr class="${m.id===r.elegido?'selected-model':''}"><td>${esc(m.nombre)}${m.id===r.elegido?'<span class="chosen-tag">elegido</span>':''}</td><td class="number">${fmt(m.train.rmse,4)}</td><td class="number">${fmt(m.validacion.rmse,4)}</td><td class="number">${fmt(m.test.rmse,4)}</td><td class="number">${fmt(m.test.mae,4)}</td><td class="number">${fmt(m.test.r2,3)}</td><td class="number">${fmt(m.test.n,0)}</td></tr>`).join('');
  $('#modelo-detalles').textContent=`${ingles(r.protocolo)} Si dos modelos empatan, queda el más simple. Se conservaron ${fmt(r.ceros_conservados,0)} ceros operativos.`;
  $('#porque-titulo').textContent=`Por qué ${el.nombre}`;
  const por=f=>[...r.comparacion].sort((x,y)=>f(x)-f(y))[0];
  const seg=[...r.comparacion].filter(m=>m.id!==el.id).sort((a,b)=>a.validacion.rmse-b.validacion.rmse)[0];
  const resto=r.comparacion.filter(m=>m.id!==el.id&&m.id!==seg.id).map(m=>m.validacion.rmse);
  const mejorTest=por(m=>m.test.rmse),mejorMae=por(m=>m.test.mae);
  const prueba=mejorTest.id===el.id?`En el test desde 2025, también tiene el menor RMSE (${fmt(el.test.rmse,4)}).`
    :`En el test desde 2025, ${mejorTest.nombre} queda apenas mejor en RMSE (${fmt(mejorTest.test.rmse,4)} contra ${fmt(el.test.rmse,4)}): prácticamente un empate.`+(mejorMae.id===el.id?` ${el.nombre} tiene el menor MAE (${fmt(el.test.mae,4)}).`:'');
  $('#modelo-porque').innerHTML=[
    `La regla se fijó antes de mirar el test: gana el menor RMSE de validation en 2024. ${el.nombre} tuvo ${fmt(el.validacion.rmse,4)} y ${seg.nombre}, ${fmt(seg.validacion.rmse,4)}. Los demás quedaron entre ${fmt(Math.min(...resto),4)} y ${fmt(Math.max(...resto),4)}.`,
    DESCRIPCION[el.id],
    `${prueba} Con R² de ${fmt(el.test.r2,3)} explica ${fmt(el.test.r2*100,0)} % de la variación mensual, y el test es retrospectivo: no equivale a un período nunca visto.`
  ].map(t=>`<p>${esc(t)}</p>`).join('');
}

/* Sitio */
function valoresSitio(){return {lat:parseFloat($('#sitio-lat').value),lon:parseFloat($('#sitio-lon').value),anio:parseInt($('#sitio-anio').value,10),mw:parseFloat($('#sitio-mw').value)};}
function avisos(r){
  const L=[],rg=D.rango;
  if(!r.dentro)L.push(['alerta',`Caso límite: el punto queda fuera del rango de los parques del train set (latitud ${fmt(rg.lat_min,1)} a ${fmt(rg.lat_max,1)}, longitud ${fmt(rg.lon_min,1)} a ${fmt(rg.lon_max,1)}). El modelo no extrapola: el número no vale como estimación.`]);
  if(r.distancia_km>D.umbral_km)L.push(['alerta',`El parque que presta el clima está a ${fmt(r.distancia_km,0)} km de la celda: más de ${D.umbral_km} km, la copia es débil.`]);
  if(r.distancia_celda_km>1)L.push(['',`Se usa la celda de ${fmt(D.grilla.paso,1)}° más cercana, a ${fmt(r.distancia_celda_km,0)} km del punto pedido.`]);
  if(r.modo==='tipico')L.push(['',`${r.anio} no tiene clima medido: se usa el promedio mensual anterior a 2024. No es un pronóstico del clima de ese año.`]);
  if(r.modo==='mixto')L.push(['',`Parte de ${r.anio} tiene clima medido y el resto usa el promedio mensual anterior a 2024.`]);
  if(r.incompleto)L.push(['alerta','Faltan meses con clima. El total cubre solo los meses disponibles.']);
  return L;
}
function sitio(){
  const v=valoresSitio(),r=estimar(v.lat,v.lon,v.anio,v.mw);
  const aviso=$('#sitio-aviso'),lectura=$('#sitio-lectura');
  $('#sitio-donde').textContent=Number.isFinite(v.lat)&&Number.isFinite(v.lon)?coords(v.lat,v.lon):'—';
  if(!r){
    aviso.dataset.modo='';aviso.dataset.dentro='';aviso.textContent='Elegí un año y una potencia mayor que cero.';
    lectura.innerHTML='';$('#sitio-avisos').innerHTML='';$('#sitio-clima-nota').textContent='';
    dibujarCarta($('#sitio-carta'),MARCOS.carta,{campo:true,restringir:true});dibujarCarta($('#sitio-inset'),MARCOS.pais,{});
    plot('sitio-chart',[],{});plot('sitio-clima',[],{});return;
  }
  aviso.dataset.modo=r.modo;aviso.dataset.dentro=String(r.dentro);aviso.dataset.energia=String(r.energia_gwh);
  const clima=r.modo==='observado'?`Con el clima medido en ${r.anio}`:r.modo==='tipico'?'Con el clima promedio anterior a 2024':`Con clima medido y promedio de ${r.anio}`;
  const st=D._stats.get(r.central);
  aviso.textContent=`Cuenta: ${fmt(r.potencia_mw,1)} MW × ${fmt(r.horas,0)} horas${r.incompleto?' de los meses con clima':' del año'} × factor ${fmt(r.factor*100,1)} % = ${fmt(r.energia_gwh,2)} GWh. El factor es la parte de la potencia máxima que el parque entrega en promedio; el modelo lo estima con la ubicación, el clima y el mes. Si trabajara a plena potencia todas las horas daría ${fmt(r.potencia_mw*r.horas/1000,0)} GWh.`;
  lectura.className='site-reading'+(r.dentro?'':' limite');
  lectura.innerHTML=`<h2>${r.incompleto?'Energía de los meses con clima':`Un parque de ${fmt(r.potencia_mw,1)} MW generaría`}</h2><div class="energy"><strong>${fmt(r.energia_gwh,2)} GWh</strong><span>${r.incompleto?'':`en ${r.anio} · `}factor anual ${fmt(r.factor*100,1)} %</span></div><p>${esc(clima)}, copiado de ${esc(titulo(r.nombre))} (${esc(provincia(r.provincia))}), el parque real más cercano, a ${fmt(r.distancia_km,0)} km. Ese parque tuvo un factor medio de ${fmt(st.media*100,1)} %.</p>`;
  $('#sitio-avisos').innerHTML=avisos(r).map(([c,t])=>`<li class="${c}">${esc(t)}</li>`).join('');
  $('#sitio-clima-nota').textContent=`Además del sol, el modelo usa la temperatura máxima y la nubosidad de ${titulo(r.nombre)}, más la latitud, la longitud y el mes.`;
  dibujarCarta($('#sitio-carta'),MARCOS.carta,{campo:true,consulta:r,restringir:true});
  dibujarCarta($('#sitio-inset'),MARCOS.pais,{consulta:r});
  const trama=r.meses.map(m=>m.clima==='observado'?'':'/');
  plot('sitio-chart',[{type:'bar',x:r.meses.map(m=>MESES[m.mes-1]),y:r.meses.map(m=>m.gwh),customdata:r.meses.map(m=>[m.factor,m.clima==='observado'?'clima medido':'clima promedio']),
    marker:{color:r.dentro?C.blue:C.faint,pattern:{shape:trama,fgcolor:r.dentro?C.blue:C.faint,bgcolor:'#fff',fgopacity:1,size:7,solidity:.45}},hovertemplate:'%{x}: %{y:.2f} GWh<br>factor %{customdata[0]:.3f} · %{customdata[1]}<extra></extra>'}],
    {yaxis:eje({title:{text:'GWh'}}),xaxis:eje(),bargap:.25});
  plot('sitio-clima',[{type:'bar',x:r.meses.map(m=>MESES[m.mes-1]),y:r.meses.map(m=>m.ghi),marker:{color:C.ink,line:{color:C.ink,width:1},pattern:{shape:trama,fgcolor:C.ink,bgcolor:'#fff',fgopacity:1,size:7,solidity:.45}},hovertemplate:'%{x}: %{y:.0f} kWh/m²<extra></extra>'}],
    {yaxis:eje({title:{text:'kWh/m²'}}),xaxis:eje(),bargap:.25});
}
function leyendaSitio(){
  $('#sitio-leyenda').innerHTML=`<div class="grp"><svg width="24" height="24" aria-hidden="true"><circle cx="12" cy="12" r="7" fill="none" stroke="${C.ink}" stroke-width="1.8"/><path d="M1 12h6M17 12h6M12 1v6M12 17v6" stroke="${C.ink}" stroke-width="1.4"/></svg><span>Sitio elegido</span></div>`+
    `<div class="grp"><svg width="22" height="14" aria-hidden="true"><rect x="1" y="1" width="20" height="12" fill="${C.ink}" fill-opacity=".14" stroke="${C.ink}" stroke-width="1.4"/></svg><span>Celda de 0,2° del cálculo</span></div>`+
    `<div class="grp"><svg width="12" height="12" aria-hidden="true"><circle cx="6" cy="6" r="4.5" fill="${C.ink}"/></svg><span>Parque real</span></div>`+
    `<div class="grp"><span class="ttl">Factor típico estimado</span><span>${fmt(CAMPO[0],2)}</span><span class="ramp" aria-hidden="true"></span><span>${fmt(CAMPO[1],2)}</span></div>`+
    `<div class="grp"><svg width="28" height="12" aria-hidden="true"><rect x="1" y="1" width="26" height="10" fill="none" stroke="${C.blue}" stroke-dasharray="5 3"/></svg><span>Rango de parques del train set</span></div>`;
}
const LIMITES={lat:[-56,-21],lon:[-74,-53]};
function fijarSitio(pt){
  if(!pt)return;
  const aviso=$('#sitio-rechazo');
  if(!dentroRango(pt)){
    const rg=D.rango;
    aviso.textContent=`Ese punto queda fuera del rango de los parques del train set (latitud ${fmt(rg.lat_min,1)} a ${fmt(rg.lat_max,1)}, longitud ${fmt(rg.lon_min,1)} a ${fmt(rg.lon_max,1)}). El modelo no extrapola, así que ahí no se estima. Elegí un punto dentro del recuadro punteado.`;
    aviso.hidden=false;return;
  }
  aviso.hidden=true;
  $('#sitio-lat').value=Math.min(LIMITES.lat[1],Math.max(LIMITES.lat[0],pt.lat));
  $('#sitio-lon').value=Math.min(LIMITES.lon[1],Math.max(LIMITES.lon[0],pt.lon));
  sitio();
}
/* Parque */
function serie(){
  const id=S.parque;$('#serie-parque').value=id;
  const rows=D._serie.get(id)||[];
  if(!rows.length){$('#serie-lectura').innerHTML='<p class="empty">Ese parque no tiene meses comparables.</p>';return;}
  const p=D._idx.get(id),st=D._stats.get(id),ultimo=rows.at(-1);
  $('#serie-lectura').innerHTML=`<div><h2>${esc(titulo(ultimo.nombre))}</h2><p class="coords">${esc(provincia(ultimo.provincia))} · ${coords(p.lat,p.lon)}${dentroRango(p)?'':' · fuera del rango del train set'}</p></div>`+
    `<dl><div><dt>Potencia</dt><dd>${fmt(ultimo.potencia_mw,1)} MW</dd></div><div><dt>Meses</dt><dd>${fmt(st.n,0)}</dd></div><div><dt>Factor medio</dt><dd>${fmt(st.media,3)}</dd></div><div><dt>MAE en test</dt><dd>${fmt(st.mae,3)}</dd></div><div><dt>Meses en cero</dt><dd>${fmt(st.ceros,0)}</dd></div></dl>`;
  const prueba=rows.filter(r=>r.particion==='prueba');
  $('#serie-alcance').textContent=`${rows[0].fecha.slice(0,7)} a ${ultimo.fecha.slice(0,7)} · ${prueba.length} meses en test`;
  const corte=prueba[0],x=rows.map(r=>r.fecha),ceros=rows.filter(r=>r.factor_capacidad===0);
  const fondo=corte?[{type:'rect',xref:'x',x0:corte.fecha,x1:ultimo.fecha,yref:'paper',y0:0,y1:1,fillcolor:'rgba(31,63,191,.07)',line:{width:0}}]:[];
  plot('serie-chart',[
    {type:'scatter',mode:'lines+markers',name:'Observado',x,y:rows.map(r=>r.factor_capacidad),line:{color:C.ink,width:2},marker:{size:4,color:C.ink},hovertemplate:'%{x|%b %Y}<br>observado %{y:.3f}<extra></extra>'},
    {type:'scatter',mode:'lines',name:'Estimado',x,y:rows.map(r=>r.pred),line:{color:C.blue,width:2.4,dash:'dot'},hovertemplate:'%{x|%b %Y}<br>estimado %{y:.3f}<extra></extra>'},
    {type:'scatter',mode:'markers',name:'Cero',x:ceros.map(r=>r.fecha),y:ceros.map(()=>0),marker:{symbol:'circle-open',size:16,line:{width:2.6},color:C.ink},hovertemplate:'%{x|%b %Y}: cero operativo<extra></extra>'}
  ],{yaxis:eje({title:{text:'Factor de capacidad'},tickformat:'.2f',rangemode:'tozero'}),xaxis:eje(),shapes:fondo,
     annotations:corte?[{x:corte.fecha,xanchor:'left',yref:'paper',y:1,yanchor:'top',text:'test',showarrow:false,font:{color:C.blue,size:12},xshift:6}]:[]});
  plot('serie-residuo',[{type:'bar',x,y:rows.map(r=>r.factor_capacidad-r.pred),marker:{color:rows.map(r=>r.factor_capacidad-r.pred<0?C.lineStrong:C.ink),opacity:.9},hovertemplate:'%{x|%b %Y}<br>observado − estimado: %{y:.3f}<extra></extra>'}],
    {yaxis:eje({title:{text:'Residuo'},tickformat:'.2f',zeroline:true,zerolinecolor:C.faint}),xaxis:eje(),shapes:fondo,bargap:.1});
  multiples();
}
function multiples(){
  const box=$('#multiples');
  if(!box.dataset.listo){
    const ids=[...D._serie.keys()].sort((a,b)=>{const pa=D._idx.get(a),pb=D._idx.get(b);return pa.provincia.localeCompare(pb.provincia,'es')||titulo(pa.nombre).localeCompare(titulo(pb.nombre),'es');});
    const W=170,H=38,t0=Date.parse('2018-01-01'),t1=Date.parse('2026-10-01');
    box.innerHTML=ids.map(id=>{
      const rows=D._serie.get(id).filter(r=>r.fecha>='2018'),p=D._idx.get(id);
      const X=f=>((Date.parse(f)-t0)/(t1-t0)*W).toFixed(1),Y=v=>(H-2-v/.42*(H-4)).toFixed(1);
      const lin=k=>rows.map((r,i)=>(i?'L':'M')+X(r.fecha)+','+Y(r[k])).join('');
      return `<button type="button" data-central="${esc(id)}" aria-pressed="false"><b>${esc(titulo(p.nombre))}</b><small>${esc(provincia(p.provincia))} · ${fmt(p.potencia_mw,0)} MW</small><svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" aria-hidden="true"><path d="${lin('pred')}" fill="none" stroke="${C.blue}" stroke-width="1.2" stroke-dasharray="2 2" vector-effect="non-scaling-stroke"/><path d="${lin('factor_capacidad')}" fill="none" stroke="${C.ink}" stroke-width="1.2" vector-effect="non-scaling-stroke"/></svg></button>`;
    }).join('');
    box.dataset.listo='1';
  }
  box.querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.central===S.parque)));
}

function iniciar(){
  if(!D||!window.Plotly)throw new Error('Faltan los archivos locales de datos o gráficos. Conservá la carpeta app completa y recargá la página.');
  preparar();
  S.parque=D.ejemplo_parque;
  const base=D.presets[0];
  $('#sitio-lat').value=base.lat.toFixed(4);$('#sitio-lon').value=base.lon.toFixed(4);$('#sitio-anio').value=base.anio;$('#sitio-mw').value=base.potencia_mw;
  const parques=[...D._serie.keys()].map(id=>[id,titulo(D._idx.get(id).nombre),provincia(D._idx.get(id).provincia)]).sort((a,b)=>a[1].localeCompare(b[1],'es'));
  $('#serie-parque').innerHTML=parques.map(([id,n,pv])=>`<option value="${esc(id)}">${esc(n)} · ${esc(pv)}</option>`).join('');
  $('#serie-parque').value=S.parque;
  $('#indice thead').addEventListener('click',e=>{const b=e.target.closest('[data-orden]');if(!b)return;S.desc=S.orden===b.dataset.orden?!S.desc:b.dataset.orden!=='nombre'&&b.dataset.orden!=='provincia';S.orden=b.dataset.orden;indice();});
  $('#indice tbody').addEventListener('click',e=>{const tr=e.target.closest('tr[data-central]');if(tr)seleccionarParque(tr.dataset.central,false,true);});
  $('#indice tbody').addEventListener('dblclick',e=>{const tr=e.target.closest('tr[data-central]');if(tr)seleccionarParque(tr.dataset.central,true);});
  $('#indice tbody').addEventListener('keydown',e=>{const tr=e.target.closest('tr[data-central]');if(!tr)return;if(e.key==='Enter')seleccionarParque(tr.dataset.central,true);if(e.key===' '){e.preventDefault();seleccionarParque(tr.dataset.central);}});
  $('#atlas-carta').addEventListener('click',e=>{const c=e.target.closest('[data-central]');if(c)seleccionarParque(c.dataset.central);});
  $('#atlas-carta').addEventListener('dblclick',e=>{const c=e.target.closest('[data-central]');if(c)seleccionarParque(c.dataset.central,true);});
  $('#sitio-carta').addEventListener('click',e=>fijarSitio(puntoCarta($('#sitio-carta'),e)));
  $('#sitio-carta').addEventListener('mousemove',e=>{const pt=puntoCarta($('#sitio-carta'),e);$('#sitio-carta').classList.toggle('fuera',!!pt&&!dentroRango(pt));});
  $('#sitio-carta').addEventListener('mouseleave',()=>$('#sitio-carta').classList.remove('fuera'));
  $('#atlas-reset').addEventListener('click',()=>{S.zoom=null;dibujarAtlas();});
  $('#sitio-form').addEventListener('input',sitio);
  $('#sitio-carta').addEventListener('keydown',e=>{const d={ArrowUp:[1,0],ArrowDown:[-1,0],ArrowLeft:[0,-1],ArrowRight:[0,1]}[e.key];if(!d)return;e.preventDefault();const v=valoresSitio(),p=D.grilla.paso;fijarSitio({lat:+(v.lat+d[0]*p).toFixed(2),lon:+(v.lon+d[1]*p).toFixed(2)});});
  leyendaSitio();
  $('#serie-parque').addEventListener('change',()=>{S.parque=$('#serie-parque').value;serie();});
  $('#multiples').addEventListener('click',e=>{const b=e.target.closest('[data-central]');if(!b)return;S.parque=b.dataset.central;serie();$('#serie-lectura').scrollIntoView({block:'start',behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});});
  const grilla=on=>{document.body.classList.toggle('sin-grilla',!on);$('#grilla').setAttribute('aria-pressed',String(on));try{localStorage.setItem('grilla',on?'1':'0');}catch{}};
  try{if(localStorage.getItem('grilla')==='0')grilla(false);}catch{}
  $('#grilla').addEventListener('click',()=>grilla($('#grilla').getAttribute('aria-pressed')!=='true'));
  $('#presentar').addEventListener('click',()=>{const on=document.body.classList.toggle('exposicion');$('#presentar').setAttribute('aria-pressed',String(on));$('#presentar').textContent=on?'Vista estándar':'Modo exposición';document.querySelectorAll('.js-plotly-plot').forEach(el=>Plotly.Plots.resize(el));});
  window.addEventListener('hashchange',mostrar);
  Plotly.register({moduleType:'locale',name:'es',dictionary:{},format:{days:['domingo','lunes','martes','miércoles','jueves','viernes','sábado'],shortDays:['dom','lun','mar','mié','jue','vie','sáb'],months:MESES_LARGO,shortMonths:MESES,date:'%d/%m/%Y',decimal:',',thousands:'.'}});
  Plotly.setPlotConfig({locale:'es'});
  mostrar();
}
try{iniciar();}catch(error){const box=$('#error');box.hidden=false;box.textContent=error.message;console.error(error);}
