/* Solar / Datos. Evidencia de src/academico.py. Sin red y sin enlaces externos. */
'use strict';
const D = window.DEFENSA;
const $ = s => document.querySelector(s);
const fmt = (n, d=0) => n == null || !Number.isFinite(+n) ? '—' : (+n).toLocaleString('es-AR',{minimumFractionDigits:d,maximumFractionDigits:d});
const esc = s => String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const MESES = ['ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic'];
const DIAS = [0,31,28,31,30,31,30,31,31,30,31,30,31];
const TITULOS = {
  modelos:['Qué modelo estima mejor','El menor RMSE de validación elige el modelo. La prueba es 2025 en adelante, ya explorada.'],
  sitio:['Cuánto generaría un parque','Un lugar, un año y una potencia. El clima sale del parque más cercano y el cálculo cae en la celda de 0,2° más próxima.'],
  serie:['Un parque real','Factor de capacidad observado contra el estimado. Los ceros operativos siguen en la serie.']
};
const NOMBRES = {modelos:'Modelos',sitio:'Sitio',serie:'Serie'};
const DESCRIPCION = {
  rf:'Promedia muchos árboles. Cada uno ve una muestra y un subconjunto de variables. Dentro del rango observado responde; afuera no extrapola.',
  xgb:'Suma árboles en secuencia para corregir el error del anterior. La validación frena la complejidad.',
  arbol:'Parte los datos con preguntas. Cada hoja predice un promedio. Afuera del rango repite la hoja del borde.',
  lineal_multiple:'Suma ubicación, clima y mes en una recta. Enero queda como referencia del mes.',
  lineal_simple:'Una recta que usa solo la irradiación. El lugar entra al elegir de qué parque se copia el clima.'
};
const S = {vista:'modelos',foco:null,parque:null};
document.addEventListener('keydown',()=>{S.teclado=Date.now();});
const config = {responsive:true,displaylogo:false,displayModeBar:'hover',scrollZoom:true,modeBarButtonsToRemove:['lasso2d','select2d'],toImageButtonOptions:{format:'png',filename:'solar-datos',scale:2}};
function tema(){const s=getComputedStyle(document.body);const v=n=>s.getPropertyValue(n).trim();return {ink:v('--text')||'#18252d',muted:v('--muted')||'#52636d',grid:v('--rule')||'#edf1f3',teal:'#227a6c',blue:'#2f70bb',ref:'#91a7b2'};}
function eje(extra={}){const t=tema();return {gridcolor:t.grid,zeroline:false,tickfont:{size:13,color:t.muted,family:'Plex, Helvetica Neue, sans-serif'},automargin:true,...extra};}
function layout(extra={}){const t=tema();return {font:{family:'Plex, Helvetica Neue, sans-serif',size:14,color:t.ink},paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'rgba(0,0,0,0)',margin:{l:8,r:16,t:12,b:36},hoverlabel:{bgcolor:'#fff',bordercolor:t.grid,font:{color:t.ink,size:13,family:'Plex, Helvetica Neue, sans-serif'}},...extra};}
function plot(id,traces,extra={}){const el=document.getElementById(id);if(!el)return;if(extra.height)el.style.height=extra.height+'px';const done=Plotly.react(el,traces,layout(extra),config);const fail=()=>{el.innerHTML='<p class="empty">No se pudo dibujar el gráfico. Recargá la página para volver a intentarlo.</p>';};return done&&done.then?done.catch(fail):done;}
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
    meses.push({mes,factor,gwh,clima:modo});
  }
  if(!meses.length)return null;
  const modo=new Set(modos).size===1?modos[0]:'mixto';
  const rango=D.rango;
  const dentro=lat>=rango.lat_min&&lat<=rango.lat_max&&lon>=rango.lon_min&&lon<=rango.lon_max;
  return {lat,lon,anio,potencia_mw:mw,lat_celda:slat,lon_celda:slon,distancia_celda_km:km(lat,lon,slat,slon),energia_gwh:energia,factor:energia*1000/(mw*horas),modo,dentro,distancia_km:distancia,nombre:parque.nombre,provincia:parque.provincia,central:parque.central,meses,incompleto:meses.length<12};
}
function texto(r){
  const partes=[],rango=D.rango;
  if(!r.dentro)partes.push(`El punto queda fuera de los parques del entrenamiento: latitud ${fmt(rango.lat_min,2)} a ${fmt(rango.lat_max,2)}, longitud ${fmt(rango.lon_min,2)} a ${fmt(rango.lon_max,2)}.`);
  if(r.distancia_celda_km>1)partes.push(`Se usa la celda de ${fmt(D.grilla.paso,1)}°, a ${fmt(r.distancia_celda_km,0)} km del punto pedido.`);
  const de=`${r.nombre} (${r.provincia}), a ${fmt(r.distancia_km,0)} km de la celda`;
  if(r.modo==='observado')partes.push(`El clima medido en ${r.anio} sale de ${de}.`);
  else if(r.modo==='tipico')partes.push(`Para ${r.anio} se usa el promedio mensual de entrenamiento de ${de}. En el mismo lugar, otro año sin mediciones usa ese mismo clima.`);
  else partes.push(`Parte de ${r.anio} tiene clima medido y el resto usa el promedio de ${de}.`);
  if(r.distancia_km>D.umbral_km)partes.push(`Esa distancia supera ${D.umbral_km} km: el clima copiado es una aproximación débil.`);
  if(r.incompleto)partes.push('Faltan meses con clima. El total cubre solo los meses disponibles.');
  partes.push(`Energía = factor de capacidad × ${fmt(r.potencia_mw,1)} MW × horas del mes.`);
  return partes.join(' ');
}
function indiceClima(){
  D._obs=new Map(D.clima.map(r=>[r.i+'|'+r.anio+'|'+r.mes,r]));
  D._tip=new Map(D.tipico.map(r=>[r.i+'|'+r.mes,r]));
}
function filaFoco(){const r=D.regresion;if(!r.comparacion.some(m=>m.id===S.foco))S.foco=r.elegido;return r.comparacion.find(m=>m.id===S.foco);}
function barraEvidencia(){
  const r=D.regresion,m=r.comparacion.find(x=>x.id===r.elegido).test,cv=r.cv_parques;
  $('#evidencia').innerHTML=`<span class="model-name">${esc(r.nombre)}</span><span class="evidence-metrics"><span>RMSE prueba<b>${fmt(m.rmse,3)}</b></span><span>MAE<b>${fmt(m.mae,3)}</b></span><span>R²<b>${fmt(m.r2,3)}</b></span><span>RMSE parque nuevo<b>${fmt(cv.rmse,3)}</b></span></span>`;
}
function mostrar(){
  const enfocado=document.activeElement;
  const pedido=(location.hash||'#modelos').slice(1);
  S.vista=Object.hasOwn(TITULOS,pedido)?pedido:'modelos';
  document.querySelectorAll('.view').forEach(el=>{el.hidden=el.id!=='vista-'+S.vista;});
  document.querySelectorAll('#navegacion a').forEach(a=>{if(a.hash==='#'+S.vista)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');});
  $('#titulo').textContent=TITULOS[S.vista][0];
  $('#subtitulo').textContent=TITULOS[S.vista][1];
  $('#breadcrumb').textContent=NOMBRES[S.vista];
  barraEvidencia();
  ({modelos,sitio,serie}[S.vista])();
  if(enfocado?.matches?.('#navegacion a') && enfocado.hash==='#'+S.vista)enfocado.focus();
}
function modelos(){
  const r=D.regresion,foco=filaFoco(),t=tema();
  $('#split').innerHTML=`<div><b>Entrenamiento</b><p>Hasta 2023 · meses con generación</p></div><div><b>Validación</b><p>2024 · elige el modelo</p></div><div><b>Prueba</b><p>Desde 2025 · retrospectiva</p></div>`;
  plot('modelos-chart',[
    {type:'bar',orientation:'h',name:'Validación',y:r.comparacion.map(m=>m.nombre),x:r.comparacion.map(m=>m.validacion.rmse),marker:{color:r.comparacion.map(m=>m.id===r.elegido?t.teal:'#c5d3da')}},
    {type:'bar',orientation:'h',name:'Prueba',y:r.comparacion.map(m=>m.nombre),x:r.comparacion.map(m=>m.test.rmse),marker:{color:r.comparacion.map(m=>m.id===r.elegido?t.blue:'#d5dee3')}}
  ],{barmode:'group',height:460,xaxis:eje({title:'RMSE · factor de capacidad'}),yaxis:eje({autorange:'reversed'}),legend:{orientation:'h',y:1.12},margin:{l:160,r:16,t:28,b:48}});
  const p=foco.test;
  $('#modelo-foco-titulo').textContent=foco.nombre+(foco.id===r.elegido?' · elegido':'');
  $('#modelo-cifras').innerHTML=[['RMSE',p.rmse,3],['MAE',p.mae,3],['R²',p.r2,3]].map(([n,v,d])=>`<div><span>${n} prueba</span><strong>${fmt(v,d)}</strong></div>`).join('');
  $('#modelo-porque').textContent=DESCRIPCION[foco.id];
  $('#modelo-entradas').innerHTML=(foco.id===r.elegido?r.entradas:['La tabla de abajo compara los cinco con las mismas particiones.']).map(x=>`<span>${esc(x)}</span>`).join('');
  $('#modelo-detalles').textContent=`${r.protocolo} ${r.cv_parques.nota} RMSE de parque nuevo: ${fmt(r.cv_parques.rmse,3)}. MAE ${fmt(r.cv_parques.mae,3)}. Unidad: ${r.unidad_target}. MSE de prueba: ${fmt(p.mse,4)}. n = ${fmt(p.n,0)}. Se conservaron ${fmt(r.ceros_conservados,0)} ceros operativos.`;
  $('#modelos-unidades').textContent=r.unidad_target;
  $('#modelos-tabla tbody').innerHTML=r.comparacion.map(m=>`<tr data-modelo="${esc(m.id)}" class="${m.id===S.foco?'selected-model':''}" tabindex="0"><td>${esc(m.nombre)}${m.id===r.elegido?' <span class="chosen-tag">elegido</span>':''}</td><td class="number">${fmt(m.validacion.rmse,4)}</td><td class="number">${fmt(m.test.rmse,4)}</td><td class="number">${fmt(m.test.mae,4)}</td><td class="number">${fmt(m.test.r2,3)}</td><td class="number">${fmt(m.test.n,0)}</td></tr>`).join('');
}
function valoresSitio(){
  return {lat:parseFloat($('#sitio-lat').value),lon:parseFloat($('#sitio-lon').value),anio:parseInt($('#sitio-anio').value,10),mw:parseFloat($('#sitio-mw').value)};
}
function sitio(){
  const v=valoresSitio(),r=estimar(v.lat,v.lon,v.anio,v.mw),t=tema();
  const aviso=$('#sitio-aviso'),lectura=$('#sitio-lectura');
  if(!r){aviso.dataset.modo='';aviso.dataset.dentro='';aviso.textContent='Completá latitud, longitud, año y una potencia mayor que cero.';lectura.innerHTML='';plot('sitio-chart',[],{});plot('sitio-mapa',[],{});return;}
  aviso.dataset.modo=r.modo;aviso.dataset.dentro=String(r.dentro);aviso.dataset.energia=String(r.energia_gwh);
  aviso.textContent=texto(r);
  const titulo=r.incompleto?'Energía de los meses con clima':'Energía del año';
  lectura.innerHTML=`<div><h2>${esc(titulo)}</h2><p>${esc(r.nombre)} · ${esc(r.provincia)}</p></div><div class="case-number">${fmt(r.energia_gwh,2)} GWh<br><small>${fmt(r.factor*100,1)}% factor</small></div>`;
  plot('sitio-chart',[{type:'bar',x:r.meses.map(m=>MESES[m.mes-1]),y:r.meses.map(m=>m.gwh),marker:{color:r.meses.map(m=>m.clima==='observado'?t.teal:'#9bb8c4')},hovertemplate:'%{x}: %{y:.2f} GWh<extra></extra>'}],{height:420,yaxis:eje({title:'GWh'}),xaxis:eje()});
  plot('sitio-mapa',[
    {type:'scatter',mode:'markers',name:'Parques',x:D.parques.map(p=>p.lon),y:D.parques.map(p=>p.lat),text:D.parques.map(p=>p.nombre),marker:{size:8,color:t.teal},hovertemplate:'%{text}<extra></extra>'},
    {type:'scatter',mode:'markers',name:'Consulta',x:[r.lon],y:[r.lat],marker:{size:14,color:r.dentro?t.blue:'#b4313b',symbol:'diamond'},hovertemplate:'Consulta<extra></extra>'}
  ],{height:420,xaxis:eje({title:'Longitud'}),yaxis:eje({title:'Latitud',scaleanchor:'x'}),showlegend:false});
}
function serie(){
  const id=$('#serie-parque').value||S.parque,rows=D.serie.filter(r=>r.central===id).sort((a,b)=>a.fecha.localeCompare(b.fecha)),t=tema();
  S.parque=id;
  if(!rows.length){$('#serie-lectura').innerHTML='';return;}
  const ultimo=rows.at(-1),ceros=rows.filter(r=>r.factor_capacidad===0).length,prueba=rows.filter(r=>r.particion==='prueba');
  const etiquetaCeros=ceros===1?'1 mes en cero':`${fmt(ceros,0)} meses en cero`;
  $('#serie-lectura').innerHTML=`<div><h2>${esc(ultimo.nombre)}</h2><p>${esc(ultimo.provincia)} · ${fmt(ultimo.potencia_mw,1)} MW</p></div><div class="case-number">${etiquetaCeros}</div>`;
  $('#serie-alcance').textContent=`${rows[0].fecha.slice(0,7)} a ${ultimo.fecha.slice(0,7)}. ${prueba.length} meses en la prueba.`;
  const corte=rows.find(r=>r.particion==='prueba');
  plot('serie-chart',[
    {type:'scatter',mode:'lines+markers',name:'Observado',x:rows.map(r=>r.fecha),y:rows.map(r=>r.factor_capacidad),line:{color:t.teal,width:2},marker:{size:6}},
    {type:'scatter',mode:'lines',name:'Estimado',x:rows.map(r=>r.fecha),y:rows.map(r=>r.pred),line:{color:'#91a7b2',width:2,dash:'dash'}}
  ],{height:460,yaxis:eje({title:'Factor de capacidad'}),xaxis:eje(),shapes:corte?[{type:'rect',xref:'x',x0:corte.fecha,x1:ultimo.fecha,yref:'paper',y0:0,y1:1,fillcolor:'rgba(47,112,187,.08)',line:{width:0}}]:[],showlegend:false});
  $('#serie-detalles').textContent=`${D.regresion.protocolo} ${D.regresion.parques} parques comparables. Se conservaron ${fmt(D.regresion.ceros_conservados,0)} ceros operativos. Una coordenada de localidad es aproximada.`;
}
function cargarPreset(p){
  $('#sitio-lat').value=p.lat.toFixed(4);
  $('#sitio-lon').value=p.lon.toFixed(4);
  $('#sitio-anio').value=p.anio;
  $('#sitio-mw').value=p.potencia_mw;
  sitio();
}
function iniciar(){
  if(!D||!window.Plotly)throw new Error('Faltan los archivos locales de datos o gráficos. Conservá la carpeta app completa y recargá la página.');
  indiceClima();
  S.parque=D.ejemplo_parque;
  S.foco=D.regresion.elegido;
  const base=D.presets[0];
  $('#sitio-lat').value=base.lat.toFixed(4);
  $('#sitio-lon').value=base.lon.toFixed(4);
  $('#sitio-anio').value=base.anio;
  $('#sitio-mw').value=base.potencia_mw;
  $('#sitio-presets').innerHTML=D.presets.filter(p=>p.nombre!=='Sitio nuevo, 20 MW').map(p=>`<button type="button" class="quiet-button" data-preset="${esc(p.nombre)}">${esc(p.nombre)}</button>`).join('');
  const parques=[...new Map(D.serie.map(r=>[r.central,r.nombre])).entries()].sort((a,b)=>a[1].localeCompare(b[1],'es'));
  $('#serie-parque').innerHTML=parques.map(([id,nombre])=>`<option value="${esc(id)}">${esc(nombre)}</option>`).join('');
  $('#serie-parque').value=S.parque;
  $('#modelos-tabla').addEventListener('click',e=>{const tr=e.target.closest('tr[data-modelo]');if(!tr)return;S.foco=tr.dataset.modelo;modelos();});
  $('#modelos-tabla').addEventListener('keydown',e=>{if(e.key!=='Enter')return;const tr=e.target.closest('tr[data-modelo]');if(!tr)return;S.foco=tr.dataset.modelo;modelos();});
  $('#sitio-form').addEventListener('input',sitio);
  $('#sitio-presets').addEventListener('click',e=>{const b=e.target.closest('[data-preset]');if(!b)return;cargarPreset(D.presets.find(p=>p.nombre===b.dataset.preset));});
  $('#serie-parque').addEventListener('change',serie);
  $('#presentar').addEventListener('click',()=>{const active=document.body.classList.toggle('exposicion');$('#presentar').setAttribute('aria-pressed',String(active));$('#presentar').textContent=active?'Vista estándar':'Modo exposición';document.querySelectorAll('.js-plotly-plot').forEach(el=>Plotly.Plots.resize(el));});
  window.addEventListener('hashchange',mostrar);
  Plotly.register({moduleType:'locale',name:'es',dictionary:{},format:{days:['domingo','lunes','martes','miércoles','jueves','viernes','sábado'],shortDays:['dom','lun','mar','mié','jue','vie','sáb'],months:['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre'],shortMonths:MESES,date:'%d/%m/%Y',decimal:',',thousands:'.'}});
  Plotly.setPlotConfig({locale:'es'});
  mostrar();
}
try{iniciar();}catch(error){const box=$('#error');box.hidden=false;box.textContent=error.message;console.error(error);}
