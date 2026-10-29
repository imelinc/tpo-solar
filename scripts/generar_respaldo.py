"""Exporta figuras estáticas y una presentación de respaldo sin JavaScript ni red."""
import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from src.academico import metricas_confusion

DEST=ROOT/'docs/respaldo';DEST.mkdir(parents=True,exist_ok=True)
D=json.loads((ROOT/'data/processed/defensa_evidencia.json').read_text())
font_manager.fontManager.addfont(str(ROOT/'app/fonts/plex-regular.ttf'))
plt.rcParams.update({'font.family':'IBM Plex Sans','font.size':12,'axes.spines.top':False,'axes.spines.right':False,
                     'axes.spines.left':False,'axes.spines.bottom':False,'axes.labelcolor':'#52636d',
                     'text.color':'#18252d','xtick.color':'#52636d','ytick.color':'#52636d','figure.facecolor':'white',
                     'axes.facecolor':'white','axes.titlepad':17})
color='#227a6c'
def save(name):
 plt.tight_layout(pad=2)
 plt.savefig(DEST/(name+'.png'),dpi=150,bbox_inches='tight')
 plt.close()

R=D['regresion'];rows=R['comparacion'];fig,ax=plt.subplots(figsize=(10,5.4))
ax.barh([r['nombre'] for r in rows],[r['validacion']['rmse'] for r in rows],color=[color if r['id']==R['elegido'] else '#c5d3da' for r in rows],height=.55)
ax.set(title='Comparar modelos antes de elegir',xlabel='RMSE de validación (MW/MW) · China, abril de 2019')
ax.invert_yaxis();ax.grid(axis='x',alpha=.15);ax.set_axisbelow(True);save('modelos')
levels=[.1,.25,.5,1];mats=[]
for level in levels:
 sims=[r for r in D['simulaciones'] if r['caida']==level]
 mats.append(metricas_confusion(**{k:sum(r[k] for r in sims) for k in ['tn','fp','fn','tp']}))
m=mats[2];fig,ax=plt.subplots(figsize=(9,5.4));z=[[m['tn'],m['fp']],[m['fn'],m['tp']]]
ax.imshow([[.7,.15],[.15,.7]],cmap='Greens',vmin=0,vmax=1)
for i in range(2):
 for j in range(2):ax.text(j,i,f"{z[i][j]:,}".replace(',','.')+'\n'+[['TN','FP'],['FN','TP']][i][j],ha='center',va='center',fontsize=28,color='#18252d')
ax.set(xticks=[0,1],xticklabels=['Predijo normal','Predijo alerta'],yticks=[0,1],yticklabels=['Sin caída inyectada','Con caída inyectada'],title='Matriz de confusión · Caída controlada del 50%')
ax.tick_params(length=0);fig.text(.5,.01,f"{m['n']:,} días-experimento con decisión. Los días sin decisión se excluyen. Clase 9.".replace(',','.'),ha='center',fontsize=10);save('matriz')
fig,ax=plt.subplots(figsize=(10,5.4))
for key,label,c in [('precision','Precision',color),('recall','Recall','#2f70bb'),('f1','F1','#859ba6')]:ax.plot([10,25,50,100],[r[key] for r in mats],marker='o',label=label,color=c)
ax.set(title='El tamaño de la caída cambia la utilidad',xlabel='Caída inyectada (%)',ylabel='Métrica',ylim=(0,1.05),xticks=[10,25,50,100]);ax.grid(axis='y',alpha=.15);ax.legend(frameon=False);save('deteccion')
s9=[r for r in D['diario'] if r['plant_id']=='station09'];fig,ax=plt.subplots(figsize=(10,5.4))
import pandas as pd
x=pd.to_datetime([r['fecha'] for r in s9])
ax.plot(x,[r['real']*r['capacidad'] for r in s9],color=color,label='Observado',lw=1.5)
ax.plot(x,[r['esperada']*r['capacidad'] if r['decide'] else float('nan') for r in s9],color='#91a7b2',label='Referencia genérica',lw=1.2)
ax.set(title='station09 · Un desvío para investigar',ylabel='Energía diaria (MWh)');ax.legend(frameon=False);ax.grid(axis='y',alpha=.15);save('station09')
arg=[r for r in D['argentina'] if r['central']=='ULL4FV'];fig,ax=plt.subplots(figsize=(10,5.4));x=pd.to_datetime([r['fecha'] for r in arg])
ax.plot(x,[r['factor_capacidad'] for r in arg],color=color,label='Observado',lw=1.6)
ax.plot(x,[r['pred'] for r in arg],color='#91a7b2',label='Parque típico',lw=1.2)
ax.set(title='Argentina · ULL4FV, comparación mensual',ylabel='Factor de capacidad');ax.legend(frameon=False);ax.grid(axis='y',alpha=.15);save('argentina')
# EDA observado, para evitar depender de Plotly o de internet en la exposición.
fig,ax=plt.subplots(figsize=(10,5.4));a=D['eda']['nube'];ax.scatter([r['irradiancia'] for r in a],[r['target'] for r in a],s=12,alpha=.35,color=color)
ax.set(title='Datos reales · Irradiancia y potencia',xlabel='Irradiancia medida (W/m²)',ylabel='Potencia / capacidad (MW/MW)');ax.grid(alpha=.12);save('eda')
chosen=next(r for r in rows if r['id']==R['elegido'])['test']
slides=[('Una pregunta de negocio','¿Podemos estimar la producción solar según el clima y señalar qué plantas conviene revisar?','<p>Fuentes reales. Referencia estimada. Evaluación retrospectiva. Ninguna alerta confirma por sí sola una causa física.</p><p>Ignacio Melinc · Matias Young · Francisco Fabrello · Malena Garcia Moraglio</p>'),
('De las fuentes a la aplicación','Pipeline ETL y CRISP-DM · Clases 2 y 4','<ol><li>PVOD / CAMMESA / Open-Meteo</li><li>Preparar fechas, unidades y calidad</li><li>Comparar modelos con train, validación y prueba</li><li>Evaluar regresión y regla de residuos</li><li>Dashboard local: evidencia para decidir</li></ol>'),
('Entender los datos','EDA · Clase 4','<img src="eda.png" alt="Dispersión de irradiancia y potencia"><p>La asociación justifica explorar modelos. No prueba causalidad.</p>'),
('Elegir el modelo','Regresión y ensambles · Clases 6, 7, 11 y 12','<img src="modelos.png" alt="Comparación de RMSE de validación">'+f"<p>Prueba retrospectiva de {R['nombre']}: MAE {chosen['mae']:.4f}, RMSE {chosen['rmse']:.4f}, R² {chosen['r2']:.4f}; n = {chosen['n']}. Target en MW/MW.</p>"),
('Leer los errores','Matriz de confusión · Clase 9','<img src="matriz.png" alt="Matriz de confusión de caída controlada del 50%">'+f"<p>Precision {m['precision']:.1%} · Recall {m['recall']:.1%}. Las caídas son pruebas, nunca entrenamiento.</p>"),
('Mostrar el límite','Accuracy no alcanza · Clase 9','<img src="deteccion.png" alt="Precision recall y F1 según la magnitud de caída"><p>La frecuencia de fallas la fija el benchmark; no se interpreta como precisión operativa garantizada.</p>'),
('Aplicar e interpretar','Casos con distinta frecuencia','<div class="pair"><img src="station09.png" alt="Energía observada y referencia de station09"><img src="argentina.png" alt="Factor de capacidad de ULL4FV"></div><p>China: diario con sensor. Argentina: mensual con clima externo y otro modelo. Sin etiquetas independientes de fallas reales.</p>'),
('Decidir con evidencia','Conclusión y próximo paso','<p>La utilidad depende del error del modelo y la calidad de los datos. La regla encuentra caídas grandes en el experimento; las pérdidas pequeñas siguen siendo difíciles.</p><p>Más años y registros de mantenimiento permitirían comprobar causas y evaluar valor recuperable.</p><p>Sin decisión no significa funcionamiento normal. Déficit estimado no significa ahorro demostrado.</p>')]
html='''<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Solar / Datos · Respaldo de defensa</title><style>@font-face{font-family:Plex;src:url('../../app/fonts/plex-regular.ttf')}*{box-sizing:border-box}body{margin:0;font:20px/1.55 Plex,Arial,sans-serif;color:#18252d;background:#f4f6f7}nav{padding:18px 5%;font-size:15px}a{color:#227a6c}section{min-height:100vh;padding:40px 6%;background:white;border-bottom:1px solid #e3eaed;break-after:page}h1{font-size:36px;font-weight:400;margin:0 0 9px}h2{font-size:19px;font-weight:400;color:#52636d;margin:0 0 24px}p{max-width:85ch;color:#52636d}img{max-width:100%;max-height:62vh;object-fit:contain}ol{line-height:2.3}.pair{display:flex;gap:24px}.pair img{width:48%}footer{font-size:13px;color:#52636d;margin-top:25px}@media(max-width:700px){section{padding:28px 20px}h1{font-size:28px}.pair{display:block}.pair img{width:100%}body{font-size:17px}}@media print{nav{display:none}section{min-height:0;height:100vh;padding:20px}img{max-height:65vh}}</style><nav>Solar / Datos · Defensa 12/11/2026 · Respaldo local sin JavaScript</nav>'''
for title,subtitle,body in slides:
 html+=f'<section><h1>{title}</h1><h2>{subtitle}</h2>{body}<footer>Fuente: evidencia generada por src/academico.py · Evaluación retrospectiva · UADE, Ciencia de Datos</footer></section>'
html+='</html>'
(DEST/'index.html').write_text(html)
print('Respaldo:',DEST/'index.html')
