# Arquitectura

Clases 2 y 4: del archivo mensual al dashboard, sin red en la defensa.

```mermaid
flowchart LR
    CAM[CAMMESA mensual] --> PREP[Coordenadas, potencia y ceros]
    OM[Open-Meteo mensual] --> PREP
    PREP --> SPLIT[Train hasta 2023 / validación 2024 / prueba desde 2025]
    SPLIT --> REG[Cinco regresores]
    REG --> MET[MAE, RMSE y R²]
    REG --> GRID[Grilla de 0,2° con el modelo elegido]
    MET --> JSON[defensa_evidencia.json]
    GRID --> JSON
    JSON --> APP[app/index.html]
```

## Contrato

1. `python -m src.academico` entrena, arma la grilla y escribe la evidencia.
2. `python app/build_dashboard.py` copia esa evidencia a `app/datos.js`. No vuelve a entrenar.
3. `app/index.html` muestra Atlas (carta y exploración), Modelos, Sitio y Parque. La consulta de un sitio lee la grilla.

El identificador del parque no es una entrada del modelo. La energía en GWh se calcula en la página a partir del factor, la potencia y las horas del mes.
