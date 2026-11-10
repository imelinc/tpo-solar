import unittest

from src import bot_telegram as bot


class BotTelegram(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ev = bot.cargar()

    def test_sitio_coincide_con_el_preset_del_tablero(self):
        p = self.ev["presets"][0]["resultado"]
        r = bot.consultar_sitio(self.ev, p["lat"], p["lon"], p["anio"], p["potencia_mw"])
        self.assertAlmostEqual(r["energia_gwh"], p["energia_gwh"], places=6)
        self.assertAlmostEqual(r["factor"], p["factor"], places=6)

    def test_revisar_lista_el_ranking_y_aclara_que_no_es_falla(self):
        t = bot.responder("/revisar", self.ev)
        self.assertIn(self.ev["senales"]["ranking"][0]["nombre"].strip(), t)
        self.assertIn("no es una falla confirmada", t)

    def test_parque_por_codigo_y_por_nombre(self):
        self.assertIn("TOC3FV", bot.responder("/parque toc3fv", self.ev))
        self.assertIn("Señal", bot.responder("/parque tocota", self.ev))
        self.assertIn("No encontré", bot.responder("/parque zzzz", self.ev))

    def test_sitio_fuera_de_argentina_y_mal_formado(self):
        self.assertIn("fuera de Argentina", bot.responder("/sitio 40 10", self.ev))
        self.assertIn("Usá /sitio", bot.responder("/sitio hola", self.ev))
        self.assertIn("caso límite", bot.responder("/sitio -40 -70 10 2025", self.ev))

    def test_modelos_marca_el_elegido(self):
        t = bot.responder("/modelos", self.ev)
        self.assertIn("✅ XGBoost", t)

    def test_texto_libre_y_comando_desconocido(self):
        self.assertIn("/ayuda", bot.responder("hola", self.ev))
        self.assertIn("No conozco", bot.responder("/xyz", self.ev))


if __name__ == "__main__":
    unittest.main()
