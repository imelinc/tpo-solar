/* Solar / Datos. Evidencia calculada por src/academico.py. Sin peticiones de red. */
'use strict';
const D = window.DEFENSA;
const $ = s => document.querySelector(s);
const fmt = (n, d=0) => n == null || !Number.isFinite(+n) ? '—' : (+n).toLocaleString('es-AR',{minimumFractionDigits:d,maximumFractionDigits:d});
const pct = (n,d=1) => n == null ? '—' : fmt(n*100,d)+'%';
const fecha = s => new Date(s+'T12:00:00').toLocaleDateString('es-AR',{day:'numeric',month:'short',year:'numeric'});
const esc = s => String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const TITULOS = {resumen:['¿Qué aprendió el modelo?','Comparar modelos, interpretar errores y poner a prueba las alertas.'],datos:['Entender los datos antes de modelar','Fuentes reales, calidad, preparación y análisis exploratorio.'],modelos:['Elegir el modelo con evidencia','Comparar error y generalización, con las herramientas de las clases.'],evaluacion:['Medir lo que detecta y lo que se escapa','Una regla de alertas, una muestra definida y una matriz de confusión.'],casos:['De la métrica al caso concreto','China y Argentina: distintas fuentes, frecuencias y límites.']};
const NOMBRES = {resumen:'Resumen',datos:'Datos',modelos:'Modelos',evaluacion:'Evaluación',casos:'Casos'};
const S={vista:'resumen',pais:'china',planta:'station09',parque:'ULL4FV',fecha:'2019-05-10'};
let keyboardAt=0;
document.addEventListener('keydown',()=>{keyboardAt=Date.now();});
const ink='#18252d',muted='#52636d',teal='#227a6c',red='#b4313b',blue='#2f70bb';
const config={responsive:true,displaylogo:false,displayModeBar:false};
const eje={gridcolor:'#edf1f3',zeroline:false,tickfont:{size:12,color:muted},automargin:true};
const layout=extra=>({font:{family:'Plex, Helvetica Neue, sans-serif',size:13,color:ink},paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'rgba(0,0,0,0)',margin:{l:40,r:14,t:15,b:40},showlegend:false,hoverlabel:{bgcolor:'#fff',font:{color:ink,size:13}},...extra});
function plot(id,traces,extra={}) { const el=document.getElementById(id); if(!el)return; return Plotly.react(el,traces,layout(extra),config).catch(()=>{el.innerHTML='<p class="empty">No se pudo dibujar el gráfico. Recargá la página para volver a intentarlo.</p>';}); }
const metricasDe=(r,p='test')=>r.comparacion.find(m=>m.id===r.elegido)[p];
function clase(key){const c=D.clases[key];return `<a href="${c.url}" target="_blank" rel="noopener">Clase ${c.clase} · ${esc(c.tema)} ↗</a>`;}
function referencia(keys){$('#referencias').innerHTML='<div class="references">'+keys.map(clase).join('')+'</div>';}
function barraEvidencia(){
 const argentino=(S.vista==='modelos'&&$('#modelos-territorio').value==='argentina')||(S.vista==='casos'&&S.pais==='argentina');
 const r=argentino?D.regresion_argentina:D.regresion,m=metricasDe(r);
 $('#evidencia').innerHTML=`<span class="model-name">${esc(r.nombre)} · Regresión</span><div class="evidence-metrics"><span>MAE <b>${fmt(m.mae,4)}</b></span><span>RMSE <b>${fmt(m.rmse,4)}</b></span><span>R² <b>${fmt(m.r2,4)}</b></span></div><span class="evidence-context">${argentino?'Argentina · FC · 2025–sep. 2026':'China · MW/MW · may.–jun. 2019'} · prueba, n = ${fmt(m.n)}</span>`;
}
function mostrar(){
 const activo=document.activeElement;
 const hash=location.hash.slice(1);S.vista=Object.hasOwn(TITULOS,hash)?hash:'resumen';
 document.querySelectorAll('.view').forEach(el=>{el.hidden=el.id!=='vista-'+S.vista;});
 document.querySelectorAll('#navegacion a').forEach(a=>{if(a.hash==='#'+S.vista)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');});
 $('#titulo').textContent=TITULOS[S.vista][0];$('#subtitulo').textContent=TITULOS[S.vista][1];
 $('#breadcrumb').textContent=NOMBRES[S.vista];
 barraEvidencia();({resumen:resumen,datos:datos,modelos:modelos,evaluacion:evaluacion,casos:casos}[S.vista])();
 const vista=document.getElementById('vista-'+S.vista);
 if(activo&&activo.matches&&activo.matches('[data-ir]')&&!vista.contains(activo))document.getElementById('contenido').focus();
 if(Date.now()-keyboardAt>500&&!matchMedia('(prefers-reduced-motion: reduce)').matches)vista.animate([{opacity:.75},{opacity:1}],{duration:160,easing:'cubic-bezier(.23,1,.32,1)'});
}
function descargar(texto,nombre,tipo){const url=URL.createObjectURL(new Blob([texto],{type:tipo}));const a=document.createElement('a');a.href=url;a.download=nombre;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
function lect(label,value,note){return `<div class="finding"><span class="finding-label">${label}</span><strong>${value}</strong><p>${note}</p></div>`;}
function resumen(){
 referencia(['ensambles','clasificacion','validacion','regresion']);
 const r=D.regresion,m=metricasDe(r),ar=metricasDe(D.regresion_argentina);
 $('#recorrido').innerHTML=[['Clima observado','Irradiancia, temperatura y viento'],[r.nombre,'Estimar potencia · Regresión'],['Residuo + boxplot','Señalar un desvío · Clase 4'],['Revisión técnica','Interpretar antes de intervenir']].map(([a,b],i)=>`<div class="flow-step"><b>${esc(a)}</b><p>${esc(b)}</p>${i<3?'<span aria-hidden="true">→</span>':''}</div>`).join('');
 const sm=sumarMatriz(D.simulaciones.filter(x=>x.caida===.5));
 $('#resumen-n').textContent=fmt(sm.n)+' días-experimento con decisión · '+fmt(D.simulaciones.filter(x=>x.caida===.5).reduce((a,r)=>a+r.sin_decision,0))+' sin decisión, excluidos. Inyecciones solo para evaluar; no son fallas operativas confirmadas.';
 $('#resumen-lecturas').innerHTML=lect('Precision · Caída del 50%',pct(sm.precision),'Proporción de alertas correctas en el benchmark.')+lect('Recall · Caída del 50%',pct(sm.recall),'Proporción de días con caída que detecta la regla.');
 $('#resumen-matriz').innerHTML=`<div></div><div class="matrix-label">Predijo normal</div><div class="matrix-label">Predijo alerta</div><div class="matrix-label">Real<br>sin caída</div><div class="matrix-cell"><strong>${fmt(sm.tn)}</strong><span>TN · Verdaderos negativos</span></div><div class="matrix-cell error-cell"><strong>${fmt(sm.fp)}</strong><span>FP · Falsos positivos</span></div><div class="matrix-label">Real<br>con caída</div><div class="matrix-cell error-cell"><strong>${fmt(sm.fn)}</strong><span>FN · Falsos negativos</span></div><div class="matrix-cell"><strong>${fmt(sm.tp)}</strong><span>TP · Verdaderos positivos</span></div>`;
 const cmp=[...r.comparacion].sort((a,b)=>a.validacion.rmse-b.validacion.rmse);
 plot('resumen-scatter',[{type:'bar',orientation:'h',y:cmp.map(x=>x.nombre),x:cmp.map(x=>x.validacion.rmse),marker:{color:cmp.map(x=>x.id===r.elegido?teal:'#c5d3da')},text:cmp.map(x=>fmt(x.validacion.rmse,4)),textposition:'outside',cliponaxis:false,hovertemplate:'%{y}<br>RMSE %{x:.4f} MW/MW<extra></extra>'}],{xaxis:{...eje,title:{text:'RMSE (MW/MW)',font:{size:12}},range:[0,Math.max(...cmp.map(x=>x.validacion.rmse))*1.3]},yaxis:{...eje,showgrid:false,autorange:'reversed'},margin:{l:140,r:25,t:12,b:40}});
 $('#resumen-alcances').innerHTML=`<div><h3>China · Observación horaria</h3><p>${D.plantas.length} plantas con sensores. Regresión de potencia y alertas al cierre del día. Una sola vuelta estacional y capacidad inconsistente en station04.</p><span class="scope-metric">${fmt(D.eda.n_horario)} <small class="caption">registros horarios</small></span></div><div><h3>Argentina · Comparación mensual</h3><p>CAMMESA y clima externo. ${esc(D.regresion_argentina.nombre)}, con MAE ${fmt(ar.mae,4)} de factor de capacidad. Comparación retrospectiva, sin etiquetas de fallas confirmadas.</p><span class="scope-metric">${fmt(D.regresion_argentina.parques)} <small class="caption">parques comparables de ${D.eda.plantas_argentina}</small></span></div>`;
}
function datos(){
 referencia(['etl','calidad','eda','features']);
 $('#arquitectura').innerHTML=[['Fuentes','PVOD · CAMMESA<br>Open-Meteo · NASA'],['Preparación','Fechas y unidades<br>Calidad y categorías'],['Modelado','Train → validación<br>Regresión comparada'],['Evaluación','MAE · RMSE · R²<br>Residuos y matriz'],['Aplicación','Gráficos locales<br>Evidencia para decidir']].map(([a,b])=>`<div><h3>${a}</h3><p>${b}</p></div>`).join('');
 $('#calidad').innerHTML=[['China',fmt(D.eda.n_horario),'registros horarios'],['Argentina',fmt(D.eda.n_mensual),'meses-parque originales'],['Duplicados',fmt(D.eda.duplicados_horario+D.eda.duplicados_mensual),'en las claves de ambas tablas'],['Ceros conservados',fmt(D.regresion_argentina.ceros_conservados),'meses operativos comparables']].map(([a,b,c])=>`<div><span class="metric-label">${a}</span><strong class="metric-number">${b}</strong><span class="metric-note">${c}</span></div>`).join('');
 $('#preparacion').innerHTML='<ul><li>Target China: potencia medida / capacidad nominal. La planta se codifica con One-Hot Encoding; hora, mes y día del año se derivan de la fecha.</li><li>Entrenar una referencia sana excluye apagones con sol y registros congelados. Los apagones se conservan al evaluar.</li><li>station04 tiene capacidad no confiable; station09 se aplica al modelo genérico, sin usarla para aprender producción sana.</li><li>Un sensor caído, un registro inválido o poca señal implican sin decisión, nunca funcionamiento normal.</li><li>Argentina excluye centroides provinciales y capacidades inválidas. Las coordenadas de localidad siguen siendo aproximadas; se muestran como tales en el caso.</li></ul>';
 renderEDA();
}
function renderEDA(){
 const tipo=$('#eda-tipo').value,p=$('#eda-planta').value,all=D.eda.nube,rows=all.filter(x=>p==='todas'||x.plant_id===p);
 $('#eda-planta').disabled=tipo==='corr';
 const names={scatter:'Irradiancia y potencia',box:'Distribución por planta',hist:'Forma de la distribución',corr:'Correlación entre variables observadas'};
 $('#eda-titulo').textContent=names[tipo];
 $('#eda-nota').textContent=tipo==='corr'?'Todas las horas de sol del dataset; sin filtro de planta.':`Muestra determinista: ${fmt(rows.length)} registros horarios con sol${p==='todas'?'':', '+p}.`;
 const rule={scatter:'Una asociación visible justifica explorar modelos; no prueba causalidad ni el error de predicción.',box:'La caja contiene el 50% central. Los puntos extremos requieren investigación; no se eliminan por ser extremos.',hist:'El histograma muestra frecuencias de potencia normalizada. La selección cambia la población observada.',corr:'La correlación mide asociación lineal, entre −1 y 1. No reemplaza la validación de un modelo.'};
 $('#eda-interpretacion').textContent=rule[tipo];
 if(!rows.length&&tipo!=='corr'){document.getElementById('eda-chart').innerHTML='<p class="empty">Sin observaciones para esta selección.</p>';return;}
 if(tipo==='scatter')plot('eda-chart',[{x:rows.map(x=>x.irradiancia),y:rows.map(x=>x.target),customdata:rows.map(x=>x.plant_id),mode:'markers',marker:{color:teal,size:5,opacity:.45},hovertemplate:'%{customdata}<br>%{x:.0f} W/m²<br>%{y:.3f} MW/MW<extra></extra>'}],{xaxis:{...eje,title:'Irradiancia medida (W/m²)'},yaxis:{...eje,title:'Potencia / capacidad (MW/MW)'}});
 if(tipo==='box')plot('eda-chart',[{type:'box',x:rows.map(x=>x.plant_id),y:rows.map(x=>x.target),marker:{color:teal,size:3},line:{color:teal,width:1.3},fillcolor:'#eaf3f5',boxpoints:'outliers',hovertemplate:'%{x}<br>%{y:.3f} MW/MW<extra></extra>'}],{xaxis:{...eje,showgrid:false},yaxis:{...eje,title:'Potencia / capacidad (MW/MW)'}});
 if(tipo==='hist')plot('eda-chart',[{type:'histogram',x:rows.map(x=>x.target),nbinsx:30,marker:{color:teal,line:{color:'#fff',width:1}},hovertemplate:'Potencia %{x:.2f}<br>%{y} observaciones<extra></extra>'}],{xaxis:{...eje,title:'Potencia / capacidad (MW/MW)'},yaxis:{...eje,title:'Frecuencia (registros)'}});
 if(tipo==='corr'){const names=['Potencia','Irradiancia','Temperatura','Clima externo'];plot('eda-chart',[{type:'heatmap',x:names,y:names,z:D.eda.correlacion,zmin:-1,zmax:1,colorscale:[[0,'#b4313b'],[.5,'#f6f8f9'],[1,teal]],texttemplate:'%{z:.2f}',textfont:{size:13},showscale:false,hovertemplate:'%{x} / %{y}<br>r = %{z:.3f}<extra></extra>'}],{xaxis:{...eje,showgrid:false},yaxis:{...eje,showgrid:false,autorange:'reversed'},margin:{l:90,r:10,t:20,b:70}});}
}
function modeloActual(){return $('#modelos-territorio').value==='argentina'?D.regresion_argentina:D.regresion;}
function modelos(){
 referencia(['arbol','ensambles','validacion','regresion']);barraEvidencia();
 const r=modeloActual(),p=$('#modelos-particion').value,isArg=r===D.regresion_argentina;
 $('#modelos-regla').textContent=isArg?'La selección utiliza el RMSE de 2024, no el resultado de prueba.':r.regla_eleccion;
 const parts=isArg?[['Entrenamiento','Hasta diciembre 2023'],['Validación','Enero–diciembre 2024'],['Prueba retrospectiva','Enero 2025–septiembre 2026']]:[['Entrenamiento',`${fecha(r.particiones.entrenamiento.desde)} → ${fecha(r.particiones.entrenamiento.hasta)}`],['Validación','Abril de 2019'],['Prueba retrospectiva','Mayo–junio de 2019']];
 $('#split').innerHTML=parts.map(([a,b])=>`<div><b>${a}</b><p>${b}</p></div>`).join('');
 const rows=[...r.comparacion].sort((a,b)=>a[p].rmse-b[p].rmse);
 plot('modelos-chart',[{type:'bar',orientation:'h',x:rows.map(x=>x[p].rmse),y:rows.map(x=>x.nombre),marker:{color:rows.map(x=>x.id===r.elegido?teal:'#c5d3da')},text:rows.map(x=>fmt(x[p].rmse,4)),textposition:'outside',cliponaxis:false,hovertemplate:'%{y}<br>RMSE %{x:.4f}<extra></extra>'}],{xaxis:{...eje,title:{text:isArg?'RMSE de factor de capacidad':'RMSE (MW/MW)',font:{size:12}},range:[0,Math.max(...rows.map(x=>x[p].rmse))*1.26]},yaxis:{...eje,showgrid:false,autorange:'reversed'},margin:{l:140,r:25,t:10,b:44}});
 const desc={rf:'Promedia árboles entrenados con muestras y variables diferentes. Captura relaciones no lineales y reduce la variabilidad de un árbol. No extrapola fuera del rango aprendido.',xgb:'Construye árboles en secuencia para corregir errores. Requiere controlar complejidad y evaluar la generalización.',arbol:'Divide los datos mediante preguntas. Cada hoja predice un promedio; la profundidad y el mínimo por hoja limitan el sobreajuste.',lineal_multiple:'Combina varias predictoras en una relación lineal. Es una referencia sencilla e interpretable; no necesita más complejidad si los datos de validación no la justifican.',lineal_simple:'Una recta usa solamente la irradiancia para estimar potencia. Es la referencia más sencilla de la comparación.'};
 $('#modelo-explicacion').innerHTML=`<p class="model-choice">${esc(r.nombre)}</p><p class="model-description">${desc[r.elegido]}</p><h3>Variables de entrada</h3><div class="feature-list">${r.features.map(f=>`<span>${esc(({irradiancia:'Irradiancia',temperatura:'Temperatura',viento:'Viento',hora:'Hora',mes:'Mes',dia_del_anio:'Día del año',om_ghi_kwh_m2_mes:'Irradiación mensual',om_temp_max_media_c:'Temperatura máxima',om_nubosidad_media_pct:'Nubosidad'})[f]||f)}</span>`).join('')}</div><p class="caption below">${isArg?'Sin ID del parque: estima una referencia de parque típico.':'150 árboles · mínimo de 5 muestras por hoja · semilla 42.'}</p>`;
 $('#modelos-unidades').textContent=`${r.unidad_target}. Métricas de ${p==='test'?'prueba retrospectiva':p==='train'?'entrenamiento':'validación'}.`;
 $('#modelos-tabla tbody').innerHTML=r.comparacion.map(row=>`<tr class="${row.id===r.elegido?'selected-model':''}"><td>${esc(row.nombre)}${row.id===r.elegido?'<span class="chosen-tag">Elegido</span>':''}</td><td class="number">${fmt(row[p].mae,4)}</td><td class="number">${fmt(row[p].rmse,4)}</td><td class="number">${fmt(row[p].r2,4)}</td><td class="number">${fmt(row[p].n)}</td></tr>`).join('');
 const met=r.comparacion.find(x=>x.id===r.elegido)[p];
 $('#modelo-detalles').innerHTML=`<p><b>MAE:</b> promedio de errores absolutos. <b>MSE:</b> ${fmt(met.mse,6)}, promedio de errores al cuadrado. <b>RMSE:</b> raíz del MSE; penaliza más los errores grandes. La selección usa RMSE de validación, no el MSE de prueba. <b>R²:</b> compara con predecir la media y puede ser negativo en datos nuevos.</p><p>${esc(r.protocolo)}</p><p>La comparación entre entrenamiento y prueba ayuda a detectar sobreajuste. Los transformadores se ajustan dentro del pipeline, con los datos de entrenamiento. Los escenarios controlados nunca participan del ajuste.</p>${!isArg?`<p>Para calibrar los residuos se usan cinco folds agrupados por mes, solo dentro de entrenamiento. No es una simulación cronológica completa. La importancia de una variable no prueba causalidad.</p><p>Importancias de ${esc(r.nombre)}: ${r.importancias.slice(0,6).map(x=>`${esc(x.variable)} (${pct(x.valor)})`).join(' · ')}.</p>`:`<p>${esc(r.limite)}</p>`}`;
}
function sumarMatriz(rows){let tn=0,fp=0,fn=0,tp=0;rows.forEach(r=>{tn+=r.tn;fp+=r.fp;fn+=r.fn;tp+=r.tp;});const n=tn+fp+fn+tp,div=(a,b)=>b?a/b:null;return{tn,fp,fn,tp,n,accuracy:div(tp+tn,n),precision:div(tp,tp+fp),recall:div(tp,tp+fn),f1:div(2*tp,2*tp+fp+fn)};}
function filasEval(level=+$('#eval-caida').value){const p=$('#eval-planta').value,d=$('#eval-duracion').value;return D.simulaciones.filter(r=>r.caida===level&&(p==='todas'||r.planta===p)&&(d==='todas'||r.duracion===+d));}
function evaluacion(){
 referencia(['eda','clasificacion','validacion','regresion']);
 const rows=filasEval(),m=sumarMatriz(rows),unknown=rows.reduce((a,r)=>a+r.sin_decision,0),count=rows.filter(r=>r.demora!=null).length;
 $('#matriz').innerHTML=`<div></div><div class="matrix-label">Predijo normal</div><div class="matrix-label">Predijo alerta</div><div class="matrix-label">Real<br>sin caída</div><div class="matrix-cell"><strong>${fmt(m.tn)}</strong><span>TN · Verdaderos negativos</span></div><div class="matrix-cell error-cell"><strong>${fmt(m.fp)}</strong><span>FP · Falsos positivos</span></div><div class="matrix-label">Real<br>con caída</div><div class="matrix-cell error-cell"><strong>${fmt(m.fn)}</strong><span>FN · Falsos negativos</span></div><div class="matrix-cell"><strong>${fmt(m.tp)}</strong><span>TP · Verdaderos positivos</span></div>`;
 $('#eval-muestra').textContent=`${fmt(m.n)} días-experimento con decisión · ${fmt(unknown)} sin decisión, excluidos · ${rows.length} episodios independientes. La misma fecha base puede repetirse en distintos experimentos.`;
 $('#eval-metricas').innerHTML=[['Precision',m.precision,'TP / (TP + FP) · ¿Cuántas alertas fueron correctas?'],['Recall',m.recall,'TP / (TP + FN) · ¿Cuántos días de caída detecta?'],['F1',m.f1,'Equilibrio entre precision y recall'],['Accuracy',m.accuracy,'(TP + TN) / total · Aciertos sobre todos los días']].map(([a,b,c])=>`<div class="metric-line"><span>${a}</span><b>${pct(b)}</b><small>${c}</small></div>`).join('');
 const levels=[.1,.25,.5,1],ms=levels.map(l=>sumarMatriz(filasEval(l)));
 plot('eval-curva',[['precision','Precision',teal],['recall','Recall',blue],['f1','F1','#859ba6']].map(([key,name,c])=>({x:levels.map(x=>pct(x,0)),y:ms.map(x=>x[key]),name,mode:'lines+markers',marker:{size:6},line:{color:c,width:2},hovertemplate:name+': %{y:.1%}<extra></extra>'})),{showlegend:true,legend:{orientation:'h',x:0,y:1.15,font:{size:12}},xaxis:{...eje,showgrid:false,title:'Caída inyectada'},yaxis:{...eje,tickformat:'.0%',range:[-.03,1.03]},margin:{l:40,r:12,t:30,b:40}});
 const prevalence=m.n?(m.tp+m.fn)/m.n:null;
 $('#evaluacion-detalles').innerHTML=`<p><b>Regla:</b> ${esc(D.regresion.detector)}</p><p>Caída seleccionada: ${$('#eval-caida').selectedOptions[0].text}. Prevalencia controlada de días con caída: ${pct(prevalence)}. Episodios con al menos una alerta: ${count} de ${rows.length}. Cada planta, caída, duración y semilla tiene identidad propia.</p><p>Los días sin decisión quedan fuera de los cuatro conteos; nunca se convierten en TN. Una demora solo existe para episodios detectados, por lo que no describe por sí sola a los episodios omitidos.</p><p>Los valores altos de precision del experimento no garantizan la misma precision en campo: la frecuencia real de fallas es desconocida. No hay etiquetas operativas para construir una matriz de confusión de la historia real.</p><p>${esc(D.regresion.protocolo)}</p>`;
}
const stateText={normal:'Sin alerta',alerta:'Con alerta',sin_dato:'Sin decisión',capacidad:'Capacidad no confiable',ausente:'Sin dato en la fecha'};
function casos(){
 referencia(['calidad','ensambles','regresion']);barraEvidencia();
 const china=S.pais==='china';
 document.querySelectorAll('[data-pais]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.pais===S.pais)));
 $('#caso-planta-label').hidden=!china;$('#caso-fecha-label').hidden=!china;$('#caso-parque-label').hidden=china;
 if(china)casoChina();else casoArgentina();
}
function casoChina(){
 const all=D.diario.filter(r=>r.plant_id===S.planta&&r.fecha<=S.fecha),actual=D.diario.find(r=>r.plant_id===S.planta&&r.fecha===S.fecha),status=actual?.estado||'ausente';
 const rows=all.slice(-90),ok=rows.filter(r=>r.decide&&r.estado!=='capacidad'),alertas=ok.filter(r=>r.alerta),mwh=alertas.reduce((a,r)=>a+(r.deficit_mwh||0),0),isGeneric=!D.regresion.plantas_entrenamiento.includes(S.planta);
 const message={normal:'No cruzó el umbral de residuos en esta fecha. Esto no confirma ausencia de fallas pequeñas.',alerta:'Un residuo bajo justifica revisar medición y operación. La señal no confirma la causa del desvío.',sin_dato:actual?.sensor_caido?'El sensor no permite decidir. Revisar el instrumento antes de interpretar el rendimiento.':'La calidad o la magnitud de la señal no permiten una decisión confiable.',capacidad:'La potencia medida excede la ficha declarada. Se excluye de la interpretación económica hasta verificar la capacidad.',ausente:'No hay observación de esta planta en la fecha de corte. No se asume funcionamiento normal.'};
 $('#caso-lectura').innerHTML=`<div><h2>${esc(S.planta)} · ${stateText[status]}</h2><p>${message[status]} ${isGeneric?'Referencia de un modelo genérico, sin historia sana propia.':''}</p></div><div><span class="case-number">${status==='capacidad'?'—':fmt(mwh)} <small class="caption">MWh</small></span><p>Déficit estimado en ${alertas.length} días con alerta<br>Últimas ${rows.length} observaciones disponibles</p></div>`;
 $('#caso-titulo').textContent='Energía observada y referencia';
 $('#caso-alcance').textContent=`${D.regresion.nombre}${isGeneric?' genérico':''} · ${rows.length?fecha(rows[0].fecha)+' → '+fecha(rows.at(-1).fecha):'Sin datos'} · ${actual?.particion||'sin partición en la fecha'}`;
 if(!rows.length){document.getElementById('caso-chart').innerHTML='<p class="empty">No hay registros hasta esta fecha.</p>';}
 else plot('caso-chart',[{x:rows.map(r=>r.fecha),y:rows.map(r=>r.real*r.capacidad),name:'Observado',mode:'lines',line:{color:teal,width:2},hovertemplate:'Observado %{y:.1f} MWh<extra></extra>'},{x:rows.map(r=>r.fecha),y:rows.map(r=>r.decide?r.esperada*r.capacidad:null),name:'Referencia',mode:'lines',line:{color:'#91a7b2',width:1.6},hovertemplate:'Referencia %{y:.1f} MWh<extra></extra>'},{x:alertas.map(r=>r.fecha),y:alertas.map(r=>r.real*r.capacidad),mode:'markers',marker:{color:red,size:6},hovertemplate:'Día con alerta<extra></extra>'}],{hovermode:'x unified',xaxis:{...eje,showgrid:false,type:'date',nticks:5,tickformat:'%d %b'},yaxis:{...eje,title:'MWh por día',rangemode:'tozero'}});
 $('#caso-lista-titulo').textContent='Flota al '+fecha(S.fecha);
 $('#caso-lista').innerHTML=D.plantas.map(p=>{const r=D.diario.find(x=>x.plant_id===p.id&&x.fecha===S.fecha),st=r?.estado||'ausente';return `<button class="plant-row" data-planta="${p.id}" aria-pressed="${p.id===S.planta}"><span class="row-name">${p.id}<br><small>${fmt(p.mw,1)} MW nominales</small></span><span class="state-label ${st}">${stateText[st]}</span></button>`;}).join('');
 $('#caso-lista').querySelectorAll('[data-planta]').forEach(b=>b.addEventListener('click',()=>{S.planta=b.dataset.planta;$('#caso-planta').value=S.planta;casos();document.querySelector(`#caso-lista [data-planta="${S.planta}"]`)?.focus();}));
 const cal=D.regresion.calibracion[S.planta]||D.regresion.calibracion_generica,per=D.regresion.por_planta[S.planta];
 const valor=status==='capacidad'
  ?'La capacidad no es confiable: no se informa déficit en MWh ni un valor en dólares.'
  :`La diferencia positiva respecto de la referencia no demuestra energía recuperable. ${esc(D.economia.nota)} Un precio de USD ${fmt(D.economia.precio,2)}/MWh daría un valor ilustrativo de USD ${fmt(mwh*D.economia.precio)} sobre los días con alerta y capacidad utilizable.`;
 $('#caso-detalles').innerHTML=`<p>PVOD · Hebei, China · 2018–2019. Se utiliza la misma regla evaluada en la matriz; no hay una política de estados distinta. Umbral de residuo de esta referencia: ${pct(cal.umbral)}.</p><p>${ok.length} días con decisión y ${rows.length-ok.length} sin interpretación utilizable en el período mostrado. ${per?`Métricas horarias de esta planta en prueba: MAE ${fmt(per.mae,4)}, RMSE ${fmt(per.rmse,4)}, R² ${fmt(per.r2,4)}, n = ${fmt(per.n)}.`:'Esta planta no forma parte del conjunto de prueba de plantas entrenadas; no se le atribuyen las métricas de una planta conocida.'}</p><p>La línea representa el modelo entrenado antes de abril; las fechas de entrenamiento se muestran retrospectivamente y dentro de muestra. Validación y prueba se identifican por fecha.</p><p>${valor}</p><p>«Sin alerta» no equivale a ausencia de falla. Una sola vuelta estacional y las mediciones limitan la interpretación.</p>`;
}
function casoArgentina(){
 const all=D.argentina.filter(r=>r.central===S.parque).sort((a,b)=>a.fecha.localeCompare(b.fecha)),rows=all,latest=all.at(-1),test=all.filter(r=>r.fecha>='2025-01-01'),alerts=test.filter(r=>r.alerta),r=D.regresion_argentina;
 $('#caso-lectura').innerHTML=`<div><h2>${esc(latest?.central_descripcion||S.parque)}</h2><p>Comparación mensual · ${esc(r.nombre)}. ${test.length} meses en prueba retrospectiva, ${alerts.length} con alerta. No hay etiquetas de fallas operativas confirmadas.</p></div><div><span class="case-number">${fmt(test.filter(x=>x.energia_gwh===0).length)}</span><p>meses observados con cero<br>Conservados en la evaluación</p></div>`;
 $('#caso-titulo').textContent='Factor de capacidad observado y referencia';$('#caso-alcance').textContent=`CAMMESA + Open-Meteo · ${esc(latest?.provincia||'')} · Modelo de parque típico · FC adimensional`;
 const flags=rows.filter(x=>x.alerta);
 plot('caso-chart',[{x:rows.map(x=>x.fecha),y:rows.map(x=>x.factor_capacidad),mode:'lines',name:'Observado',line:{color:teal,width:2},hovertemplate:'Observado %{y:.1%}<extra></extra>'},{x:rows.map(x=>x.fecha),y:rows.map(x=>x.pred),mode:'lines',name:'Referencia típica',line:{color:'#91a7b2',width:1.6},hovertemplate:'Parque típico %{y:.1%}<extra></extra>'},{x:flags.map(x=>x.fecha),y:flags.map(x=>x.factor_capacidad),mode:'markers',marker:{size:6,color:red},hovertemplate:'Mes con alerta<extra></extra>'}],{hovermode:'x unified',xaxis:{...eje,showgrid:false,type:'date',nticks:5,tickformat:'%Y'},yaxis:{...eje,title:'Factor de capacidad',tickformat:'.0%',rangemode:'tozero'},shapes:[{type:'rect',xref:'x',yref:'paper',x0:'2025-01-01',x1:rows.at(-1)?.fecha,y0:0,y1:1,fillcolor:'#f2f7f8',line:{width:0},layer:'below'}]});
 $('#caso-lista-titulo').textContent='Parques para explorar';
 const selected=['ULL4FV','UL42FV','CHEPFV','VMR2FV','TAMBFV'];
 const ids=selected.filter(c=>D.argentina.some(x=>x.central===c));
 $('#caso-lista').innerHTML=ids.map(c=>{const ar=D.argentina.filter(x=>x.central===c&&x.fecha>='2025-01-01'),n=ar.filter(x=>x.alerta).length,zeros=ar.filter(x=>x.energia_gwh===0).length;return `<button class="plant-row" data-parque="${c}" aria-pressed="${c===S.parque}"><span>${c}<br><small>${zeros} meses con cero</small></span><span>${n} <small>con alerta</small></span></button>`;}).join('')+'<p class="caption below">Los conteos corresponden a los meses de prueba desde enero de 2025.</p>';
 $('#caso-lista').querySelectorAll('[data-parque]').forEach(b=>b.addEventListener('click',()=>{S.parque=b.dataset.parque;$('#caso-parque').value=S.parque;casos();document.querySelector(`#caso-lista [data-parque="${S.parque}"]`)?.focus();}));
 $('#caso-detalles').innerHTML=`<p>${esc(r.protocolo)} ${esc(r.limite)}</p><p>La curva de referencia muestra un parque típico. La alerta usa además la normalización por el nivel histórico propio del parque y su umbral de boxplot. La normalización se aprende con fechas de entrenamiento.</p><p>Fuente de coordenada del parque: ${esc(latest?.coord_source)}. Las coordenadas de localidad son aproximadas. La capacidad puede proceder de un mes cercano: verificar cambios de habilitación antes de atribuir el desvío a una falla.</p><p>La región argentina incluye ${r.parques} parques comparables de ${D.eda.plantas_argentina} en la fuente original. Se conservaron ${r.ceros_conservados} ceros operativos; no son datos ausentes.</p><p>No se informa precision, recall ni matriz de confusión sobre este historial porque no hay etiquetas independientes de fallas.</p>`;
}
function iniciar(){
 if(!D||!window.Plotly)throw new Error('Faltan los archivos locales de datos o gráficos. Conservá la carpeta app completa y recargá la página.');
 const opt=(values,all)=>`${all?'<option value="todas">Todas las plantas</option>':''}${values.map(v=>`<option value="${esc(v)}">${esc(v)}</option>`).join('')}`;
 $('#eda-planta').innerHTML=opt(D.plantas.map(x=>x.id),true);
 $('#eval-planta').innerHTML=opt(D.regresion.plantas_entrenamiento,true);
 $('#caso-planta').innerHTML=opt(D.plantas.map(x=>x.id));$('#caso-planta').value=S.planta;
 const parques=[...new Set(D.argentina.map(x=>x.central))].sort();$('#caso-parque').innerHTML=opt(parques);$('#caso-parque').value=S.parque;
 const dates=D.diario.map(x=>x.fecha).sort();$('#caso-fecha').min=dates[0];$('#caso-fecha').max=dates.at(-1);$('#caso-fecha').value=S.fecha;
 for(const id of ['eda-tipo','eda-planta'])$('#'+id).addEventListener('change',renderEDA);
 for(const id of ['modelos-territorio','modelos-particion'])$('#'+id).addEventListener('change',modelos);
 for(const id of ['eval-caida','eval-duracion','eval-planta'])$('#'+id).addEventListener('change',evaluacion);
 $('#caso-planta').addEventListener('change',e=>{S.planta=e.target.value;casos();});
 $('#caso-parque').addEventListener('change',e=>{S.parque=e.target.value;casos();});
 $('#caso-fecha').addEventListener('change',e=>{if(!e.target.value)return;S.fecha=e.target.value;casos();});
 document.querySelectorAll('[data-pais]').forEach(b=>b.addEventListener('click',()=>{S.pais=b.dataset.pais;casos();}));
 document.querySelectorAll('[data-ir]').forEach(b=>b.addEventListener('click',()=>{location.hash=b.dataset.ir;}));
 $('#presentar').addEventListener('click',()=>{const active=document.body.classList.toggle('exposicion');$('#presentar').setAttribute('aria-pressed',String(active));$('#presentar').textContent=active?'Vista estándar':'Modo exposición';document.querySelectorAll('.view:not([hidden]) .js-plotly-plot').forEach(el=>Plotly.Plots.resize(el));});
 $('#descargar-datos').addEventListener('click',()=>descargar(JSON.stringify(D,null,2),'solar-evidencia.json','application/json'));
 $('#descargar-metricas').addEventListener('click',()=>{const r=modeloActual(),p=$('#modelos-particion').value;const csv='Modelo,Particion,MAE,RMSE,R2,N\n'+r.comparacion.map(x=>[x.nombre,p,x[p].mae,x[p].rmse,x[p].r2,x[p].n].join(',')).join('\n');descargar(csv,'solar-metricas.csv','text/csv;charset=utf-8');});
 window.addEventListener('hashchange',mostrar);
 Plotly.register({moduleType:'locale',name:'es',dictionary:{},format:{days:['domingo','lunes','martes','miércoles','jueves','viernes','sábado'],shortDays:['dom','lun','mar','mié','jue','vie','sáb'],months:['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre'],shortMonths:['ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic'],date:'%d/%m/%Y',decimal:',',thousands:'.'}});Plotly.setPlotConfig({locale:'es'});
 mostrar();
}
try{iniciar();}catch(error){const box=$('#error');box.hidden=false;box.textContent=error.message;console.error(error);}
