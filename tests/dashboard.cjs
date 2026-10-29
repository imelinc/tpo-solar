const fs=require('fs'),assert=require('assert'),{JSDOM}=require('jsdom');
const root=require('path').resolve(__dirname,'..');
const html=fs.readFileSync(root+'/app/index.html','utf8');
const js=fs.readFileSync(root+'/app/tablero.js','utf8');
assert(!html.toLowerCase().includes('notion'),'el html no enlaza Notion');
assert(!js.toLowerCase().includes('notion'),'el tablero no enlaza Notion');
assert(!html.includes('Clase '), 'la página no cita clases');
assert(!html.includes('China') && !js.includes('China'), 'la pantalla es solo Argentina');
const dom=new JSDOM(html,{url:'https://local.test/index.html',runScripts:'outside-only',pretendToBeVisual:true});
const w=dom.window,errors=[],plots=new Map();
w.matchMedia=()=>({matches:true,addListener(){},removeListener(){}});
w.HTMLElement.prototype.animate=()=>({cancel(){}});
w.Plotly={react(id,traces,layout){plots.set(typeof id==='string'?id:id.id,{traces,layout});return Promise.resolve();},register(){},setPlotConfig(){},Plots:{resize(){}}};
w.console.error=(e)=>errors.push(String(e));
w.eval(fs.readFileSync(root+'/app/datos.js','utf8'));
w.eval(js);
const $=s=>w.document.querySelector(s);
const set=(id,value)=>{const el=$(id);el.value=value;el.dispatchEvent(new w.Event('input',{bubbles:true}));};
const route=name=>{w.location.hash='#'+name;w.dispatchEvent(new w.HashChangeEvent('hashchange'));};
assert.equal($('#error').hidden,true,'sin error inicial');
assert.equal($('.view:not([hidden])').id,'vista-modelos');
assert.equal(w.document.body.dataset.pais,'argentina');
assert(plots.get('modelos-chart').traces[0].y.some(y=>String(y).includes('Random Forest')));
assert.equal($('#modelos-tabla tbody').children.length,5);
assert($('#evidencia').textContent.includes('MAE'));
for(const view of ['modelos','sitio','serie']){
 route(view);assert.equal(w.document.querySelectorAll('.view:not([hidden])').length,1);assert.equal($('.view:not([hidden])').id,'vista-'+view);
 assert($('#evidencia').textContent.includes('MAE'));
}
const cerca=(a,b)=>Math.abs(a-b)<1e-4;
for(const p of w.DEFENSA.presets){
 const r=p.resultado;
 set('#sitio-lat',r.lat);set('#sitio-lon',r.lon);set('#sitio-anio',r.anio);set('#sitio-mw',r.potencia_mw);
 assert.equal($('#sitio-aviso').dataset.modo,r.modo,p.nombre);
 assert.equal($('#sitio-aviso').dataset.dentro,String(r.dentro),p.nombre);
 assert(cerca(+$('#sitio-aviso').dataset.energia,r.energia_gwh),p.nombre+' '+$('#sitio-aviso').dataset.energia+' vs '+r.energia_gwh);
}
route('serie');
const cero=w.DEFENSA.serie.find(r=>r.factor_capacidad===0);
$('#serie-parque').value=cero.central;$('#serie-parque').dispatchEvent(new w.Event('change'));
assert(plots.get('serie-chart').traces[0].y.some(v=>v===0),'ceros operativos visibles');
$('#navegacion a[href="#sitio"]').focus();route('sitio');
assert.equal(w.document.activeElement.getAttribute('href'),'#sitio');
$('#presentar').click();assert(w.document.body.classList.contains('exposicion'));$('#presentar').click();assert(!w.document.body.classList.contains('exposicion'));
assert.equal(errors.length,0,errors.join('\n'));
console.log('OK: modelos, sitio y serie. Los presets coinciden con la grilla. Hay ceros en la serie.');
console.log('Alcance: DOM y datos de los gráficos; no valida render ni layout de un navegador real.');
