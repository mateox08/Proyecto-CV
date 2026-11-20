"""Pruebas básicas de las dos gráficas (sin abrir ventanas)."""

import unittest

from PySide6.QtWidgets import QApplication

from viviani.calculo import calcular
from viviani.graficas import GraficaCurva3D, GraficaRiemann
from viviani.tema import paleta

APP = QApplication.instance() or QApplication([])


class PruebasGraficas(unittest.TestCase):
    def test_curva_3d_cambia_de_radio(self):
        grafica = GraficaCurva3D(paleta(), reducir_movimiento=True)
        grafica.mostrar(7.5)
        self.assertIn("7.5 centímetros", grafica.descripcion_accesible())

    def test_riemann_muestra_y_salta_la_animacion(self):
        grafica = GraficaRiemann(paleta())
        grafica.resize(500, 400)
        grafica.mostrar_resultado(calcular(5.0, 1000))
        self.assertTrue(grafica.esta_animando())
        grafica.saltar_animacion()
        self.assertFalse(grafica.esta_animando())


if __name__ == "__main__":
    unittest.main()
