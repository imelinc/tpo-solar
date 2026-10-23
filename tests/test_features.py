"""Tests mínimos de src/. Correr con: python tests/test_features.py (o pytest si lo tienen)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))
from src.fallas import inyectar_caida_abrupta, inyectar_soiling  # noqa: E402
from src.features import (agregar_features_solares, agregar_features_tiempo,  # noqa: E402
                          filtro_rendimiento_argentina, limpiar_pvod, marcar_valores_congelados)


def test_tiempo():
    df = agregar_features_tiempo(pd.DataFrame({"timestamp": ["2019-01-01 06:00", "2019-07-01 18:00"]}))
    assert df["hora"].tolist() == [6, 18] and df["mes"].tolist() == [1, 7]
    assert np.isclose(df["hora_sin"].iloc[0], 1) and np.isclose(df["hora_sin"].iloc[1], -1)


def test_congelados():
    s = pd.Series([0, 0, 0, 5.0, 5.0, 5.0, 2.0, 3.0, 3.0])
    assert marcar_valores_congelados(s).tolist() == [False] * 3 + [True] * 3 + [False] * 3


def test_limpiar_pvod_marca_congelado_nocturno():
    df = pd.DataFrame({"plant_id": "s", "pvod_power": [4.0, 4.0, 4.0, 1.0], "is_daylight": [1, 0, 0, 1],
                       "plant_capacity_mw": 10.0})
    out = limpiar_pvod(df)
    assert out["dato_congelado"].tolist() == [True, True, True, False]
    assert out["pvod_power"].tolist() == [4.0, 0.0, 0.0, 1.0]


def test_solares_mediodia_vs_noche():
    # Una planta en Hebei (38° N, 115° E, inclinación 33°): 04:00 UTC ~ mediodía solar, 16:00 UTC noche.
    df = pd.DataFrame({"timestamp_utc": pd.to_datetime(["2019-01-15 04:00", "2019-01-15 16:00"]),
                       "plant_lat": 38.0, "plant_lon": 115.0, "plant_array_tilt_deg": 33.0,
                       "om_shortwave_radiation": [500.0, 0.0], "om_diffuse_radiation": [100.0, 0.0],
                       "om_temperature_2m": [0.0, -5.0], "om_wind_speed_10m_ms": [2.0, 2.0]})
    out = agregar_features_solares(df)
    assert out["sol_zenit_deg"].iloc[0] < 70 < out["sol_zenit_deg"].iloc[1]
    # En invierno el panel inclinado al sur recibe más que el plano horizontal.
    assert out["om_poa"].iloc[0] > 500 and out["om_poa"].iloc[1] == 0
    assert out["om_temp_celda"].iloc[0] > 0


def test_filtro_argentina():
    df = pd.DataFrame({"fecha": ["2023-01-01", "2023-01-01", "2020-01-01", "2023-01-01", "2023-01-01"],
                       "central": ["A", "B", "CUM2FV", "CUM2FV", "C"],
                       "coord_source": ["osm_parque", "osm_centroide_provincia", "osm_parque", "osm_parque",
                                        "osm_parque"],
                       "potencia_mw": [10, 10, 10, 10, 10], "energia_mwh": [100, 100, 100, 100, 0],
                       "factor_capacidad": [0.2, 0.2, 0.2, 0.2, 0.0]})
    assert filtro_rendimiento_argentina(df).tolist() == [True, False, False, True, False]


def test_fallas():
    idx = pd.date_range("2019-01-01", periods=10 * 24, freq="h")
    p = pd.Series(1.0, index=idx)
    pa, la = inyectar_caida_abrupta(p, "2019-01-03", dias=2, fraccion=0.5)
    assert la.sum() == 0.5 * 48 and pa.min() == 0.5 and pa.iloc[0] == 1.0
    ps, ls = inyectar_soiling(p, "2019-01-02", dias=5, tasa_diaria=0.01)
    assert ls.iloc[0] == 0 and np.isclose(ls.max(), 0.01 * (5 - 1 / 24)) and ls.iloc[-1] == 0
    assert (ps <= p).all()


if __name__ == "__main__":
    for nombre, f in list(globals().items()):
        if nombre.startswith("test_"):
            f()
            print("ok", nombre)
