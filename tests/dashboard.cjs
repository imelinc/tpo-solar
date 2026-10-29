const fs=require('fs'),assert=require('assert'),{JSDOM}=require('jsdom');
const root=require('path').resolve(__dirname,'..');
const html=fs.readFileSync(root+'/app/index.html','utf8');
const dom=new JSDOM(html,{url:'https://local.test/index.html',runScripts:'outside-only',pretendToBeVisual:true});
const w=dom.window,errors=[],plots=new Map();
w.matchMedia=()=>({matches:true,addListener(){},removeListener(){}});
w.HTMLElement.prototype.animate=()=>({cancel(){}});
w.Plotly={react(id,traces,layout){plots.set(typeof id==='string'?id:id.id,{traces,layout});return Promise.resolve();},register(){},setPlotConfig(){},Plots:{resize(){}}};
w.console.error=(e)=>errors.push(String(e));
w.eval(fs.readFileSync(root+'/app/datos.js','utf8'));
w.eval(fs.readFileSync(root+'/app/tablero.js','utf8'));
const $=s=>w.document.querySelector(s);
const change=(id,value)=>{const el=$(id);el.value=value;el.dispatchEvent(new w.Event('change'));};
const route=name=>{w.location.hash='#'+name;w.dispatchEvent(new w.HashChangeEvent('hashchange'));};
assert.equal($('#error').hidden,true,'sin error inicial');
assert($('#resumen-matriz').textContent.includes('431'));
assert($('#resumen-n').textContent.includes('75 sin decisión'));
assert(plots.get('resumen-scatter').traces[0].y.includes('Random Forest'));
for(const view of ['resumen','datos','modelos','evaluacion','casos']){
 route(view);assert.equal(w.document.querySelectorAll('.view:not([hidden])').length,1);assert.equal($('.view:not([hidden])').id,'vista-'+view);
 assert($('#evidencia').textContent.includes('MAE'));assert($('#referencias').querySelectorAll('a').length>=3);
}
route('datos');for(const type of ['box','hist','corr','scatter']){change('#eda-tipo',type);assert(plots.get('eda-chart').traces.length);}
change('#eda-planta','station09');assert(plots.get('eda-chart').traces[0].customdata.every(p=>p==='station09'));
route('modelos');change('#modelos-territorio','argentina');assert($('#evidencia').textContent.includes('Regresión lineal múltiple'));
for(const p of ['train','validacion','test']){change('#modelos-particion',p);assert.equal($('#modelos-tabla tbody').children.length,3);}
change('#modelos-territorio','china');assert.equal($('#modelos-tabla tbody').children.length,5);
route('evaluacion');assert($('#matriz').textContent.includes('431'));assert($('#matriz').textContent.includes('43'));
for(const level of ['0.1','0.25','0.5','1'])for(const dur of ['todas','1','3','7'])for(const plant of ['todas',...w.DEFENSA.regresion.plantas_entrenamiento]){
 change('#eval-caida',level);change('#eval-duracion',dur);change('#eval-planta',plant);
 const rows=w.DEFENSA.simulaciones.filter(r=>r.caida===+level&&(dur==='todas'||r.duracion===+dur)&&(plant==='todas'||r.planta===plant));
 const expected=rows.reduce((s,r)=>s+r.tp,0);
 assert.equal($('#matriz').querySelectorAll('.matrix-cell strong')[3].textContent,expected.toLocaleString('es-AR'));
}
route('casos');change('#caso-fecha','2018-07-01');change('#caso-planta','station09');assert($('#caso-lectura').textContent.includes('Sin dato en la fecha'));
change('#caso-fecha','2018-07-10');change('#caso-planta','station08');assert($('#caso-lectura').textContent.includes('Sin decisión'));
change('#caso-planta','station04');assert($('#caso-lectura').textContent.includes('Capacidad no confiable'));
$('button[data-pais="argentina"]').click();assert($('#evidencia').textContent.includes('Argentina'));assert.equal($('#caso-parque-label').hidden,false);
change('#caso-parque','UL42FV');const series=plots.get('caso-chart').traces[0].y;assert(series.some(v=>v===0),'ceros operativos visibles');
$('#presentar').click();assert(w.document.body.classList.contains('exposicion'));$('#presentar').click();assert(!w.document.body.classList.contains('exposicion'));
assert.equal(errors.length,0,errors.join('\n'));
console.log('OK: navegación de 5 vistas, EDA, modelos, 144 combinaciones de filtros, ausencia, sensor, capacidad, Argentina, ceros y exposición.');
console.log('Alcance: DOM y datos de los gráficos; no valida render ni layout de un navegador real.');
