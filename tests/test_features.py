"""Tests mínimos de src/. Correr con: python tests/test_features.py (o pytest si lo tienen)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))
from src.fallas import inyectar_caida_abrupta, inyectar_soiling  # noqa: E402
from src.deteccion import (ajustar_h_cusum, alarmas_cusum, alarmas_umbral, calibrar,  # noqa: E402
                           indice_relativo, residuo_diario, semaforo)
from src.features import (agregar_dias_desde_lluvia, agregar_features_solares, agregar_features_tiempo,  # noqa: E402
                          features_escenario, filtro_rendimiento_argentina, limpiar_pvod,
                          marcar_valores_congelados)
from src.modelos import ModeloPotencia, metricas  # noqa: E402
from src.negocio import ahorro_anual_limpieza, t_optimo_limpieza  # noqa: E402


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
                       "plant_array_azimuth": "south",
                       "om_shortwave_radiation": [500.0, 0.0], "om_diffuse_radiation": [100.0, 0.0],
                       "om_temperature_2m": [0.0, -5.0], "om_wind_speed_10m_ms": [2.0, 2.0]})
    out = agregar_features_solares(df)
    assert out["sol_zenit_deg"].iloc[0] < 70 < out["sol_zenit_deg"].iloc[1]
    # En invierno el panel inclinado al sur recibe más que el plano horizontal.
    assert out["om_poa"].iloc[0] > 500 and out["om_poa"].iloc[1] == 0
    assert out["om_temp_celda"].iloc[0] > 0


def _planta_hebei(tilt, azimut):
    return pd.DataFrame({"timestamp_utc": pd.to_datetime(["2019-01-15 04:00"]), "plant_lat": 38.0, "plant_lon": 115.0,
                         "plant_array_tilt_deg": tilt, "plant_array_azimuth": azimut,
                         "om_shortwave_radiation": 500.0, "om_diffuse_radiation": 100.0, "om_temperature_2m": 0.0,
                         "om_wind_speed_10m_ms": 2.0, "pvod_lmd_totalirrad": 800.0, "pvod_lmd_diffuseirrad": 100.0,
                         "pvod_lmd_temperature": 0.0, "pvod_lmd_windspeed": 2.0})


def test_escenarios_irradiancia():
    sur, plano, norte = _planta_hebei(33.0, "south"), _planta_hebei(0.0, "south"), _planta_hebei(33.0, "north")
    # LMD: el sensor ya mide en el plano del panel -> se usa tal cual, sin importar la geometría.
    for df in (sur, plano, norte):
        assert features_escenario(df, "lmd")["poa"].iloc[0] == 800.0
    # Open-Meteo: horizontal -> pvlib lo pasa al plano usando inclinación y azimut de la planta.
    om = {k: features_escenario(v, "om")["poa"].iloc[0] for k, v in [("sur", sur), ("plano", plano), ("norte", norte)]}
    assert abs(om["plano"] - 500) < 1  # inclinación 0 = horizontal
    assert om["sur"] > om["plano"] > om["norte"]  # en enero, mirar al sur suma y mirar al norte resta
    try:
        features_escenario(_planta_hebei(33.0, "sur-ish"), "om")
        raise AssertionError("debía fallar con azimut desconocido")
    except ValueError:
        pass


def test_modelo_fisico_y_metricas():
    d = pd.DataFrame({"plant_id": ["a"] * 4 + ["b"] * 4, "date_local": ["d1", "d1", "d2", "d2"] * 2,
                      "poa": [200.0, 800.0, 400.0, 600.0] * 2, "temp_celda": 25.0, "plant_capacity_mw": 10.0})
    d["pvod_power_norm"] = d["poa"] / 1000 * np.where(d["plant_id"] == "a", 0.8, 0.5)
    m = ModeloPotencia("fisico", "lmd").fit(d)
    assert np.isclose(m.k_["a"], 0.8) and np.isclose(m.k_["b"], 0.5)
    met = metricas(d, m.predict(d))
    assert met["MAE"] < 1e-9 and abs(met["error_energia_diaria_pct"]) < 1e-9
    # Error de energía diaria: predecir 10% de menos todos los días da 10% de error y +10% de sesgo
    met = metricas(d, d["pvod_power_norm"] * 0.9)
    assert np.isclose(met["error_energia_diaria_pct"], 10) and np.isclose(met["sesgo_energia_pct"], 10)


def test_detectores():
    sano = pd.Series(np.random.default_rng(0).normal(0, 0.03, 200))
    p = calibrar(sano)
    assert 0.02 < p["sigma"] < 0.04 and p["umbral"] < -0.06
    r = pd.Series([0.0] * 10 + [-0.5] + [0.0] * 5 + [-0.04] * 15 + [np.nan, 0.0])
    u, c = alarmas_umbral(r, p), alarmas_cusum(r, p)
    assert u.iloc[10] and u.sum() == 1          # la caída abrupta la ve el umbral...
    assert c.iloc[25:31].all() and not c.iloc[:10].any()  # ...la pérdida chica sostenida, el CUSUM
    assert not c.iloc[15]  # y la alarma de la caída abrupta se apaga en pocos días
    # Ruido autocorrelado: la regla h = 4σ da muchas falsas alarmas; ajustar h las lleva al objetivo
    rng = np.random.default_rng(1)
    ar = pd.Series(np.convolve(rng.normal(0, 0.03, 600), np.ones(5) / 5 ** 0.5, mode="same"))
    p0 = {"a": calibrar(ar)}
    p1, f = ajustar_h_cusum({"a": ar}, p0, tasa_max=1 / 30)
    assert alarmas_cusum(ar, p1["a"]).mean() <= 1 / 30 and f > 4


def test_dias_desde_lluvia():
    # 2 horas por día; lluvia de 6 mm repartida el día 3 y de 2 mm (no limpia) el día 5
    dias = [f"2019-01-0{i}" for i in range(1, 7) for _ in range(2)]
    lluvia = [0, 0, 0, 0, 3, 3, 0, 0, 1, 1, 0, 0]
    df = pd.DataFrame({"plant_id": "s", "date_local": dias, "om_precipitacion_mm": lluvia})
    out = agregar_dias_desde_lluvia(df).drop_duplicates("date_local")["dias_desde_lluvia"].tolist()
    assert out == [60, 60, 0, 1, 2, 3]  # antes de la primera lluvia: tope


def test_hibrido_y_limpia():
    rng = np.random.default_rng(0)
    n = 400
    d = pd.DataFrame({"plant_id": rng.choice(["a", "b"], n), "date_local": "d", "poa": rng.uniform(100, 1000, n),
                      "temp_celda": rng.uniform(10, 50, n), "kt": 1.0, "frac_difusa": 0.2, "sol_zenit_deg": 40.0,
                      "sol_azimut_deg": 180.0, "hora_sin": 0.0, "hora_cos": 1.0, "doy_sin": 0.0, "doy_cos": 1.0,
                      "dias_desde_lluvia": rng.integers(0, 40, n).astype(float), "plant_capacity_mw": 1.0})
    # La suciedad resta 0,5% por día sin lluvia
    d["pvod_power_norm"] = 0.8 * d["poa"] / 1000 * (1 - 0.005 * d["dias_desde_lluvia"])
    m = ModeloPotencia("hibrido", "lmd").fit(d)
    assert metricas(d, m.predict(d))["R2"] > 0.95
    assert (m.predict(d, limpia=True) >= m.predict(d) - 1e-9).mean() > 0.95  # limpia = espera más


def test_indice_relativo_vecinas():
    dias = [f"2019-01-{i:02d}" for i in range(1, 11)]
    filas = []
    for p, factor in [("a", 1.0), ("b", 1.0), ("c", 1.0)]:
        for i, f in enumerate(dias):
            nube = 0.7 if i == 4 else 1.0  # día 5: el modelo se equivoca igual en todas (error común)
            real = 5 * nube * (0.4 if (p == "c" and i >= 7) else 1.0)  # c pierde 60% desde el día 8
            filas.append({"plant_id": p, "date_local": f, "e_real": real, "e_esp": 5.0, "residuo_rel": 0.0})
    e = pd.DataFrame(filas)
    out = indice_relativo(e, {"a": ["b", "c"], "b": ["a", "c"], "c": ["a", "b"]}).set_index(["plant_id", "date_local"])
    assert np.isclose(out.loc[("a", dias[4]), "indice_rel"], 1.0)   # el error común se cancela
    assert out.loc[("c", dias[8]), "indice_rel"] < 0.5               # la falla propia no


def test_residuo_sensor_caido():
    d = pd.DataFrame({"plant_id": "s", "date_local": ["d1", "d1", "d2", "d2"], "pvod_power_norm": 0.5,
                      "plant_capacity_mw": 1.0, "poa": [800.0, 800, 10, 10], "om_poa": [700.0, 700, 700, 700]})
    e = residuo_diario(d, [0.5] * 4)
    assert e["falla_sensor"].tolist() == [False, True] and e["residuo_rel"].isna().tolist() == [False, True]


def test_t_optimo_y_semaforo():
    t = t_optimo_limpieza(800, 40, 5, 0.002)
    assert np.isclose(t, np.sqrt(2 * 800 / (40 * 5 * 0.002)))
    e = pd.DataFrame({"plant_id": ["a"] * 3 + ["b"] * 3 + ["c"] * 3, "date_local": ["2019-01-01", "2019-01-02", "2019-01-03"] * 3,
                      "indice_rel": [1, 1, 1, 1, 0.9, 0.9, 1, 1, 0.3], "alerta": [False] * 8 + [True],
                      "tipo_alerta": [""] * 8 + ["Falla grave"], "falla_sensor": False,
                      "perdida_mwh": [0, 0, 0, 0, 1, 1, 0, 0, 10], "modelo": "propio"})
    s = semaforo(e, "2019-01-03", precio_usd_mwh=50).set_index("plant_id")
    assert s["estado"].tolist() == ["verde", "amarillo", "rojo"]
    assert np.isclose(s.loc["c", "perdida_usd_dia"], 10 / 3 * 50)
    # Capacidad no confiable: gris aunque rinda raro, sin USD; baja confianza se informa sin borrar la alerta
    e["baja_confianza"] = e["plant_id"] == "c"
    s = semaforo(e, "2019-01-03", precio_usd_mwh=50, no_confiables=["b"]).set_index("plant_id")
    assert s["estado"].tolist() == ["verde", "gris", "rojo"] and np.isnan(s.loc["b", "perdida_usd_dia"])
    assert s.loc["c", "baja_confianza"] and "baja confianza" in s.loc["c", "accion"]
    assert ahorro_anual_limpieza(800, 40, 5, 0.002) > 0 and ahorro_anual_limpieza(800, 40, 5, 0) == 0


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
