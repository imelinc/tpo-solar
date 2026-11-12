# Gemelo digital + bot de Telegram unificados con el repo

Para entender cómo se hicieron las cuentas y qué mostrar el 12/11. Todo lo de esta página es local: nada está commiteado.

## Qué se agregó

| Archivo | Qué es |
|---|---|
| `gemelo/gemelo_base.html` | El gemelo 3D original del Detector Solar (Fran), sin tocar. |
| `gemelo/repo_panel.js` | El código nuevo: selector de parque real, panel del modelo y gráfico. |
| `gemelo/estilo_tpo.css` | El estilo del tablero (papel milimetrado, Barlow, tinta y azul, sin rojo). Las fuentes van embebidas. |
| `gemelo/escenarios.js` | Escenarios Manual y Autónomo. |
| `gemelo/telegram_bidireccional.js` | Telegram en los dos sentidos: el gemelo avisa y escucha al técnico. |
| `gemelo/build_gemelo.py` | Une todo y los datos del repo → `gemelo/index.html`. |
| `gemelo/index.html` | El gemelo unificado para abrir suelto con doble clic (sin red, salvo Telegram). |
| `app/gemelo.html` | El mismo gemelo como sección **Gemelo** del tablero: es lo que se sube a Netlify junto con `app/`. |
| `src/bot_telegram.py` | Bot que consulta `defensa_evidencia.json`. |
| `tests/test_bot.py` | Seis pruebas, entre ellas que `/sitio` da igual que el tablero. |

```bash
python gemelo/build_gemelo.py                       # regenera gemelo/index.html si cambia la evidencia
python -m src.bot_telegram --probar "/revisar"      # el bot sin red, para ensayar
$env:TELEGRAM_TOKEN="<token>"; python -m src.bot_telegram    # el bot de verdad (PowerShell)
```

El token va solo en la variable de entorno. No lo pegues en el código ni en git. Para que el gemelo mande alertas por Telegram hay que abrir `gemelo/index.html` con doble clic (no por http) y cargar token y chat id en el botón «Telegram».

## Los dos escenarios (selector «Escenario» arriba)

**Manual** (el de siempre): quien presenta da la señal de falla con las demos o con los botones del panel derecho (apagar inversor, soltar un string, polvo, sombra) y manda al técnico con «Mandar técnico».

**Autónomo**: el gemelo rompe un grupo **por su cuenta** (inversor del B, string del D, inversor del C, string del A, en ese orden). El detector lo encuentra y le manda al bot un mensaje con el botón **«🔧 Reparado · Grupo B»**. Cuando el técnico toca el botón (o escribe `/reparado B`), el gemelo da la falla por resuelta, responde «✅ Grupo B reparado» con el tiempo transcurrido, y unas horas simuladas después rompe otra cosa. El cartel de arriba cuenta fallas detectadas, reparadas y esperando al técnico.

Comandos del técnico en Telegram: el botón del aviso, `/reparado [grupo]` (sin letra sirve si hay una sola falla abierta), `/estado` y `/ayuda`. El gemelo solo escucha al chat configurado.

### Que el bot quede cargado para todos los dispositivos (recomendado)

El token se guarda **una sola vez en Netlify** como variable secreta y sirve en cualquier celu o compu. El gemelo lo detecta solo: el botón dice «Telegram ✓» y no pide nada. El token nunca llega al navegador (lo usa la función `netlify/functions/telegram.mjs`, que solo deja mandar mensajes al chat configurado).

1. En Netlify: **Site configuration → Environment variables → Add a variable**:
   - `TELEGRAM_TOKEN` = el código de @BotFather
   - `TELEGRAM_CHAT_ID` = el chat que recibe los avisos (el del celular del técnico, por ejemplo `1624865224`, o el de un grupo con el profe)
2. Publicar **con la CLI** desde la raíz del repo (arrastrar la carpeta `app/` no sube la función):
   ```bash
   npx netlify-cli login
   npx netlify-cli link        # elegir el sitio tpo-ciencia-de-datos
   npx netlify-cli deploy --prod
   ```
   `netlify.toml` ya dice que se publica `app/` con la función.
3. Abrir la sección Gemelo: tiene que decir **«Telegram ✓»** sin cargar nada.

Si se publica arrastrando `app/` como siempre, el gemelo sigue funcionando igual que antes: hay que pegar el token en cada navegador.

### Cómo dejarlo andando en un solo navegador (sin la función)

1. Mandarle un mensaje cualquiera al bot desde el celular (así el gemelo detecta tu chat).
2. Abrir `gemelo/index.html` (doble clic o la página publicada) → botón **Telegram** → pegar **solo el token** → **Guardar**. El chat se completa solo. Queda guardado en ese navegador; con **Olvidar** se borra.
3. Con **Probar** tiene que llegarte el mensaje y decir «Escuchando al técnico ✓».
4. Elegir **Autónomo** y mirar el celular.

Ojo: mientras el gemelo escucha, **no corras `python -m src.bot_telegram` con el mismo token** (Telegram da error 409). Para usar los dos, usen bots distintos. Para la defensa conviene un hotspot del celular y, como respaldo sin red, el botón **«Simular aviso del técnico»**, que hace lo mismo desde la pantalla.

## Cómo se hicieron las cuentas

### 1. El repo: «cuánto debería generar este parque»

1. **Dato**: energía mensual de cada parque (CAMMESA) y clima mensual de su ubicación (Open-Meteo). 56 parques, 3.610 meses.
2. **Target, factor de capacidad (FC)** = energía del mes ÷ (potencia × horas del mes). Saca el tamaño del parque: queda lo que depende del lugar y del clima. Ejemplo: 10 MW × 720 h con FC 0,30 → 2,16 GWh.
3. **Entradas del modelo**: irradiación del mes, latitud, longitud, temperatura máxima, nubosidad y mes.
4. **Particiones** (por fecha, no al azar): entrena hasta 2023, valida 2024 (ahí se elige), prueba desde 2025. Se compararon seis modelos y ganó XGBoost por menor RMSE de 2024 (RMSE de prueba 0,066, R² 0,49). Random Forest queda prácticamente igual.
5. **«Esperado» de cada parque** (`pred_oof`): un modelo entrenado hasta 2023 **sin ese parque**. Así lo esperado no «sabe» cuánto generó el parque que estamos juzgando.

### 2. El repo: «cuál conviene mirar primero» (`src/senales.py`)

- `rinde_modelo` = FC observado ÷ FC esperado.
- `rinde_vecinos` = `rinde_modelo` ÷ la mediana de `rinde_modelo` de su provincia ese mes (mín. 3 vecinos). Si toda la zona rinde menos, es clima o zona, no el parque.
- **Señal** = ambos por debajo de 0,8 durante **dos meses seguidos**. Los primeros 6 meses de un parque (o tras ampliar potencia) son «arranque» y no cuentan.
- **Energía faltante** = (esperado − observado) × potencia × horas. **Plata** = GWh × 1.000 × 60 US$/MWh (precio supuesto, ajustable).
- Resultado: 109 meses marcados en 14 sitios, 200 GWh faltantes (3,3 % de lo generado), unos US$ 12 millones. Tocota III, Ullum 4 y Sierras del Ullum concentran el 87 %.
- Un modelo mensual **no ve caídas chicas**: ante una caída inyectada del 10 % detecta 1 %, del 30 % detecta 61 %, del 50 % detecta 83 %. Esto es lo que justifica el gemelo.

### 3. El gemelo: «qué pasaría con datos por hora» (`gemelo_base.html`)

- **Planta simulada** de 4 grupos de paneles (46 kWp). Cada hora calcula la potencia con un **modelo físico** (sol, ángulo de los paneles, temperatura) y el clima real de 2023 del sitio.
- **El detector** compara cada grupo contra la **mediana de sus vecinos a la misma hora** (todos ven el mismo cielo) y avisa si: rinde < 35 % (equipo caído), < 90 % durante 3 horas de sol (pérdida parcial) o se va quedando atrás día a día (CUSUM, suciedad).
- Las fallas **las inyectás vos** con los botones. El detector nunca las ve, solo mide cuánto tarda en avisar: horas contra los meses del modelo mensual.
- **Lo nuevo**: elegís un parque real. Toma su potencia (la plata se escala a sus MW), copia el clima del sitio base más cercano (de San Juan, Jujuy, Córdoba, CABA) y dibuja tres líneas por mes: lo que CAMMESA midió, lo que esperaba el modelo del repo y lo que simula el gemelo sano. Si el parque tiene señal, la muestra con su energía faltante.

## Qué mostrar en la presentación: botón «Presentar»

En el gemelo, el botón **Presentar** (arriba a la derecha) arma la demo en 6 pasos. Se avanza con **Siguiente**, las flechas o el control remoto del proyector (PageDown/PageUp), y se sale con **Esc**. Cada paso explica qué hay en pantalla, resalta en azul la parte de la que se habla y tiene una línea en vivo que cuenta lo que pasa.

| Paso | Qué se ve | Qué decir |
|---|---|---|
| 1. Un parque real que rinde menos | Tocota III y su gráfico: observado (negro) contra esperado (azul) | Rinde 54 %, faltan 99 GWh, pero con datos mensuales nos enteramos tarde |
| 2. Una copia de la planta | El gemelo funcionando normal | Cuatro grupos con el mismo cielo: si uno rinde menos, es el equipo |
| 3. Rompemos un equipo | A las 10:00 se apaga el inversor B; la simulación se frena sola al detectarlo | «1 h contra 2 meses» |
| 4. Qué avisa el sistema | La alerta resaltada; botón «Mandar técnico» | Qué grupo, cuánto rinde, cuánta plata; la causa es una hipótesis |
| 5. Sin nadie mirando | Escenario autónomo: falla sola, aviso al celular, el técnico toca «Reparado» | El sistema registra solo la reparación |
| 6. Lo que nos llevamos | 14 parques, 201 GWh, US$ 12 M, aviso en ≈ 1 h | Límites: fallas simuladas, sin datos por hora en Argentina |

Si Telegram no está conectado, el paso 5 muestra el botón **«Simular técnico»** y la demo sigue igual.

## Lo que NO hay que decir (alineado con `CLAUDE.md`)

- **Las fallas son simuladas.** Sirven para medir el tiempo de aviso, no prueban que el detector funcione en parques reales. No hay etiquetas de fallas reales.
- **El «diagnóstico de la causa» del gemelo** viene de un árbol entrenado con fallas simuladas, algo que el docente descartó. Por eso en el gemelo unificado se muestra como «Hipótesis (… no validada)». Si no hace falta, no lo muestren.
- **El gemelo no es una validación del modelo.** El «error medio» que muestra el panel compara el gemelo con CAMMESA solo como orden de magnitud: usa el clima de otro sitio y una planta genérica. En parques con señal puede salir «mejor» que el modelo simplemente porque el parque rinde poco.
- **Una señal no es una falla confirmada.** La plata es a un precio supuesto, no un ahorro.
- **El año 2023 es el único del gemelo** (clima por hora). Para parques que arrancaron después, el panel compara con el año que más meses tenga.
- Para Argentina no hay datos por hora públicos. El gemelo avisa en horas porque la simulación genera datos por hora.

## Pendientes y decisiones

- `docs/alineacion_materia.md:37` dice que Telegram y el asistente quedaron fuera por riesgo técnico y dependencia de red. Conviene hablarlo con el equipo: si entra, sería como demo opcional, con captura de respaldo.
- Hay que decidir si el gemelo va a Netlify. Desde http/https el botón de Telegram no aparece: hay que abrir el archivo local.
- Pasos de git (rama, commit, push): sin hacer.
