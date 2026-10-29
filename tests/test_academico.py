"""Decisiones de la defensa argentina.

Ejecutar: python -m unittest discover -s tests -v
"""
import unittest
import numpy as np
import pandas as pd
from src.academico import consultar, crear_modelo, metricas_regresion, preparar
from src.config import DATA_PROCESSED


def _grilla():
    # 2×2 celdas. La primera vale 0,2 en 2023 y 0,3 en el clima típico.
    n = 2 * 2 * 12
    return {"paso": 0.2, "lats": [-30.0, -29.8], "lons": [-68.0, -67.8], "anios": [2023, 2026],
            "factores": {"2023": [0.2] * 12 + [0.1] * (n - 12), "2026": [0.25] * 6 + [0.3] * 6 + [0.1] * (n - 12),
                         "0": [0.3] * n}}


def _mundo():
    parques = [{"i": 0, "central": "A", "nombre": "Parque A", "provincia": "San Juan",
                "lat": -30.0, "lon": -68.0, "potencia_mw": 10}]
    clima = [{"i": 0, "anio": 2023, "mes": m, "ghi": 100, "temp": 20, "nub": 10} for m in range(1, 13)]
    clima += [{"i": 0, "anio": 2026, "mes": m, "ghi": 90, "temp": 20, "nub": 10} for m in range(1, 7)]
    tipico = [{"i": 0, "mes": m, "ghi": 80, "temp": 18, "nub": 12} for m in range(1, 13)]
    rango = {"lat_min": -31.0, "lat_max": -29.0, "lon_min": -69.0, "lon_max": -67.0}
    return parques, clima, tipico, rango


class EvaluacionAcademica(unittest.TestCase):
    def test_regresion_conserva_unidades_y_r2_negativo(self):
        m = metricas_regresion([0, 1, 2], [3, 3, 3])
        self.assertEqual(m["mae"], 2)
        self.assertAlmostEqual(m["rmse"], np.sqrt(14 / 3))
        self.assertLess(m["r2"], 0)

    def test_modelo_fuera_del_alcance_rechazado(self):
        with self.assertRaises(ValueError):
            crear_modelo("no_permitido")

    def test_anio_futuro_repite_el_clima_tipico(self):
        g, mundo = _grilla(), _mundo()
        a = consultar(g, *mundo, -30, -68, 2027, 10)
        b = consultar(g, *mundo, -30, -68, 2029, 10)
        self.assertEqual(a["modo"], "tipico")
        self.assertEqual(b["modo"], "tipico")
        self.assertAlmostEqual(a["energia_gwh"], b["energia_gwh"])
        self.assertAlmostEqual(a["energia_gwh"], 0.3 * 10 * 365 * 24 / 1000)

    def test_bisiesto_solo_cambia_las_horas(self):
        g, mundo = _grilla(), _mundo()
        comun = consultar(g, *mundo, -30, -68, 2027, 10)
        bisiesto = consultar(g, *mundo, -30, -68, 2028, 10)
        self.assertGreater(bisiesto["energia_gwh"], comun["energia_gwh"])
        self.assertAlmostEqual(bisiesto["energia_gwh"] - comun["energia_gwh"], 0.3 * 10 * 24 / 1000)

    def test_la_potencia_escala_la_energia(self):
        g, mundo = _grilla(), _mundo()
        simple = consultar(g, *mundo, -30, -68, 2023, 10)
        doble = consultar(g, *mundo, -30, -68, 2023, 20)
        self.assertAlmostEqual(doble["energia_gwh"], simple["energia_gwh"] * 2)
        self.assertEqual(simple["modo"], "observado")
        self.assertTrue(simple["dentro"])

    def test_2026_mezcla_meses_medidos_y_promedio(self):
        r = consultar(_grilla(), *_mundo(), -30, -68, 2026, 10)
        self.assertEqual(r["modo"], "mixto")

    def test_ushuaia_queda_fuera_del_rango(self):
        r = consultar(_grilla(), *_mundo(), -54.8, -68.3, 2023, 10)
        self.assertFalse(r["dentro"])
        self.assertGreater(r["distancia_celda_km"], 100)

    def test_potencia_cero_rechazada(self):
        with self.assertRaises(ValueError):
            consultar(_grilla(), *_mundo(), -30, -68, 2023, 0)

    def test_prepara_conserva_ceros_y_descarta_coordenada_provincial(self):
        filas = [
            self._fila("A", "2023-01-01", 10, 0.2, "osm_parque"),
            self._fila("A", "2023-02-01", 0, 0.0, "osm_parque"),
            self._fila("A", "2022-12-01", 0, 0.0, "osm_parque"),
            self._fila("B", "2023-01-01", 5, 0.2, "osm_centroide_provincia"),
            self._fila("CUM2FV", "2019-01-01", 8, 0.2, "osm_parque"),
            self._fila("CUM2FV", "2023-06-01", 8, 0.2, "osm_parque"),
            self._fila("D", "2023-01-01", 8, 0.8, "osm_parque"),
        ]
        d = preparar(pd.DataFrame(filas))
        self.assertEqual(sorted(d["central"].unique()), ["A", "CUM2FV"])
        self.assertTrue((d["energia_mwh"] == 0).any())
        self.assertFalse((d["central"].eq("A") & d["fecha"].eq("2022-12-01")).any())
        self.assertTrue((d["central"].eq("CUM2FV") & d["fecha"].eq("2023-06-01")).any())
        self.assertFalse((d["central"].eq("CUM2FV") & d["fecha"].eq("2019-01-01")).any())

    def test_datos_reales_excluyen_centroide_y_conservan_ceros(self):
        ruta = DATA_PROCESSED / "dataset_B_argentina_mensual.parquet"
        if not ruta.exists():
            self.skipTest("sin dataset argentino")
        d = preparar(pd.read_parquet(ruta))
        self.assertNotIn("osm_centroide_provincia", set(d["coord_source"]))
        self.assertGreater(int(d["energia_mwh"].eq(0).sum()), 0)
        self.assertGreater(d["central"].nunique(), 10)
        self.assertTrue(d["lat"].between(-45, -20).all())

    @staticmethod
    def _fila(central, fecha, energia, factor, coord):
        return {"central": central, "fecha": fecha, "energia_mwh": energia, "factor_capacidad": factor,
                "potencia_mw": 10, "coord_source": coord, "lat": -31.5, "lon": -68.5,
                "om_ghi_kwh_m2_mes": 180, "om_temp_max_media_c": 25, "om_nubosidad_media_pct": 20,
                "central_descripcion": central, "provincia": "San Juan", "energia_gwh": energia / 1000}


if __name__ == "__main__":
    unittest.main()
