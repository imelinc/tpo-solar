"""Comprobaciones de decisiones, etiquetas y reproducibilidad de la defensa.

Ejecutar: python -m unittest discover -s tests -v
"""
import unittest
import json
from pathlib import Path
import numpy as np
import pandas as pd
from src.academico import (agregar_alertas, crear_modelo, evaluar_simulaciones,
                           metricas_confusion, metricas_regresion, umbral_boxplot)


class EvaluacionAcademica(unittest.TestCase):
    def test_matriz_con_errores_conocidos(self):
        m = metricas_confusion(tn=66, fp=6, fn=12, tp=30)
        self.assertEqual(m['n'], 114)
        self.assertAlmostEqual(m['precision'], 30 / 36)
        self.assertAlmostEqual(m['recall'], 30 / 42)
        self.assertAlmostEqual(m['accuracy'], 96 / 114)
        self.assertAlmostEqual(m['f1'], 60 / 78)

    def test_sin_positivos_no_inventa_precision(self):
        m = metricas_confusion(5, 0, 0, 0)
        self.assertIsNone(m['precision'])
        self.assertIsNone(m['recall'])
        self.assertIsNone(m['f1'])
        self.assertEqual(m['accuracy'], 1)

    def test_regresion_conserva_unidades_y_r2_negativo(self):
        m = metricas_regresion([0, 1, 2], [3, 3, 3])
        self.assertEqual(m['mae'], 2)
        self.assertAlmostEqual(m['rmse'], np.sqrt(14 / 3))
        self.assertLess(m['r2'], 0)

    def test_sensor_invalido_no_puede_ser_normal(self):
        e = pd.DataFrame({'plant_id': ['s', 's', 'station04'], 'decide': [False, True, True],
                          'residuo': [np.nan, -0.7, 0.2], 'esperada': 5., 'real': 2., 'capacidad': 10.})
        x = agregar_alertas(e, {}, {'umbral': -0.2})
        self.assertEqual(x.estado.tolist(), ['sin_dato', 'alerta', 'capacidad'])
        self.assertFalse(x.alerta.iloc[0])
        self.assertTrue(np.isnan(x.deficit_mwh.iloc[0]))
        self.assertTrue(np.isnan(x.deficit_mwh.iloc[2]))

    def test_boxplot_tolera_un_extremo_sin_ajustarse_a_el(self):
        r = pd.Series(list(np.linspace(-.04, .04, 100)) + [-.9])
        p = umbral_boxplot(r)
        self.assertLess(-.9, p['umbral'])
        self.assertLess(p['umbral'], r.quantile(.25))
        with self.assertRaises(ValueError):
            umbral_boxplot(pd.Series([.1, .2]))

    def test_simulaciones_independientes_y_dias_sin_decision(self):
        base = pd.DataFrame({'plant_id': 's', 'fecha': pd.date_range('2019-05-01', periods=25).strftime('%Y-%m-%d'),
                             'decide': True, 'real': 5., 'esperada': 5., 'residuo': 0., 'capacidad': 1.})
        base.loc[3, 'decide'] = False
        original = base.copy(deep=True)
        sims = evaluar_simulaciones(base, {}, {'umbral': -.2})
        self.assertEqual(len(sims), 4 * 3 * 5)
        self.assertEqual(len({r['id'] for r in sims}), len(sims))
        for r in sims:
            self.assertEqual(r['n'], 24)
            self.assertEqual(r['sin_decision'], 1)
            self.assertEqual(r['n'], r['tp'] + r['tn'] + r['fp'] + r['fn'])
            if r['caida'] == 1 and r['tp']:
                self.assertEqual(r['fn'], 0)
        self.assertEqual(sims, evaluar_simulaciones(base, {}, {'umbral': -.2}))
        pd.testing.assert_frame_equal(base, original)

    def test_cobertura_diaria_benchmark_igual_a_aplicacion(self):
        # Contrato con la evidencia real: no dejar desaparecer horas inválidas.
        ruta = Path(__file__).resolve().parents[1] / 'data/processed/defensa_evidencia.json'
        evidencia = json.loads(ruta.read_text())
        for planta in evidencia['regresion']['plantas_entrenamiento']:
            dias = [r for r in evidencia['diario'] if r['plant_id'] == planta and r['fecha'] >= '2019-05-01']
            esperados = sum(r['decide'] for r in dias)
            excluidos = sum(not r['decide'] for r in dias)
            for sim in evidencia['simulaciones']:
                if sim['planta'] == planta:
                    self.assertEqual(sim['n'], esperados, sim['id'])
                    self.assertEqual(sim['sin_decision'], excluidos, sim['id'])
        parcial = next(r for r in evidencia['diario'] if r['plant_id'] == 'station01' and r['fecha'] == '2019-06-10')
        self.assertFalse(parcial['decide'])
        self.assertEqual(parcial['estado'], 'sin_dato')

    def test_modelo_fuera_del_alcance_rechazado(self):
        with self.assertRaises(ValueError):
            crear_modelo('no_permitido')


if __name__ == '__main__':
    unittest.main()
