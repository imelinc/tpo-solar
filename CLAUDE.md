# Proyecto

TPO de Ciencia de Datos de UADE. Español argentino. El alcance autoritativo está en `docs/alineacion_materia.md`: solo técnicas respaldadas por los apuntes de Notion. Unifica este proyecto con el Detector Solar de Fran.

## Motor actual

Pregunta: ¿qué parque solar argentino conviene mirar primero? `src/academico.py` estima el factor de capacidad mensual con ubicación y clima: regresión lineal simple/múltiple, polinómica, árbol, Random Forest y XGBoost. Elige el menor RMSE de 2024. La prueba es desde 2025 y es retrospectiva. La energía es factor × potencia × horas del mes.

`src/senales.py` marca un parque con dos meses seguidos por debajo del 80 % de lo esperado y de sus vecinos de provincia. Lo esperado sale de un modelo que no vio ese parque. Una señal no es una falla confirmada. También aporta K-Means, PCA y DBSCAN.

`src/maui.py` mide el aviso con datos por hora en una planta pública de Hawái (NREL PVDAQ 2105), con una regla sin modelo: cada inversor contra sus vecinos. Argentina es el caso principal; Maui es un zoom porque CAMMESA solo publica datos mensuales.

Un sitio nuevo copia el clima del parque más cercano. Si el año no está medido, usa el promedio anterior a 2024. La pantalla lee una grilla de 0,2° calculada con el modelo elegido. Fuera del rectángulo de entrenamiento el número es un caso límite.

La app consume `defensa_evidencia.json` y `maui_evidencia.json` a través de `app/build_dashboard.py`. No debe mostrar cifras de otra versión. Cada vista identifica fuente, modelo, partición y métricas.

## Comandos

```bash
python -m unittest discover -s tests -v
python -m src.academico
python -m src.maui        # baja crudos de PVDAQ si faltan
python app/build_dashboard.py
python -m src.build_datasets
```

Los crudos van en data/raw y los procesados en data/processed, usando src/config.py. Notebook 01 descarga cuando faltan procesados. Modelado y dashboard deben ser reproducibles localmente.

## Condiciones

- La app funciona sin conexión, con recursos locales y sin APIs.
- Estado desconocido no equivale a normalidad. Capacidad no confiable excluye interpretación económica.
- Los ceros operativos se conservan en evaluación. No confundir ausente y cero.
- Toda evaluación es retrospectiva; no afirmar independencia ciega después de haber explorado el período.
- No inventar etiquetas de fallas ni una matriz de confusión. Las fallas inyectadas solo miden el tiempo de aviso: no entrenan nada (el docente dijo «fuerte no» a entrenar con datos sintéticos).
- El inversor 11 de Maui es copia exacta del 04: se cuenta una vez. No reutilizar cifras de Maui que los cuenten por separado.
- No afirmar causas ni ahorros demostrados: señal, energía faltante y plata en juego a un precio supuesto.
- No presentar la energía estimada como producción ya medida.
- Usuario autorizó commits y pushes periódicos directos a main. Verificar remoto y no forzar historia.
- Defensa 12/11/2026. Cuatro integrantes, trabajo compartido: Ignacio Melinc, Matias Young, Francisco Fabrello y Malena Garcia Moraglio.
