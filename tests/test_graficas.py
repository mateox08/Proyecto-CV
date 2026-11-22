"""Pruebas básicas de las dos gráficas y de la ventana (sin abrir ventanas)."""

import math
import unittest

import numpy as np
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QApplication

from viviani.calculo import calcular
from viviani.graficas import GraficaCurva3D, GraficaRiemann
from viviani.graficas.barrido import DURACION_BARRIDO_MS, inicios_escalonados
from viviani.graficas.curva3d import punto, velocidad
from viviani.tema import paleta

APP = QApplication.instance() or QApplication([])


class PruebasGeometria(unittest.TestCase):
    def test_la_curva_esta_en_la_esfera_y_el_cilindro(self):
        x, y, z = punto(np.linspace(0, 2 * math.pi, 50))
        np.testing.assert_allclose(x**2 + y**2 + z**2, 1, atol=1e-12)
        np.testing.assert_allclose((x - 0.5) ** 2 + y**2, 0.25, atol=1e-12)

    def test_rapidez_es_f_sobre_r(self):
        t = np.linspace(0, 2 * math.pi, 50)
        rapidez = np.linalg.norm(velocidad(t), axis=0)
        np.testing.assert_allclose(rapidez, np.sqrt(1 + np.cos(t) ** 2), atol=1e-12)

    def test_barrido_termina_a_tiempo(self):
        inicios = inicios_escalonados(120)
        self.assertEqual(inicios[0], 0)
        self.assertLess(inicios[-1], DURACION_BARRIDO_MS)
        self.assertEqual(len(inicios_escalonados(1)), 1)


class PruebasGraficas(unittest.TestCase):
    def test_curva_3d_cambia_de_radio_y_dibuja(self):
        grafica = GraficaCurva3D(paleta(), reducir_movimiento=True)
        grafica.resize(600, 600)
        grafica.mostrar(7.5)
        self.assertIn("7.5 centímetros", grafica.descripcion_accesible())
        grafica.barrer(calcular(7.5, 10).puntos_t)
        grafica.resaltar(1.0)
        grafica.establecer_capa("cilindro", False)
        self.assertFalse(grafica.grab().isNull())

    def test_riemann_muestra_y_salta_la_animacion(self):
        grafica = GraficaRiemann(paleta())
        grafica.resize(500, 400)
        grafica.mostrar_resultado(calcular(5.0, 1000))
        self.assertTrue(grafica.esta_animando())
        grafica.saltar_animacion()
        self.assertFalse(grafica.esta_animando())

    def test_riemann_avisa_el_t_bajo_el_mouse(self):
        grafica = GraficaRiemann(paleta())
        grafica.resize(500, 300)
        grafica.mostrar_resultado(calcular(5.0, 4), animar=False)
        avisos = []
        grafica.t_resaltado.connect(avisos.append)
        centro = QPointF(grafica.width() / 2, 150)
        movimiento = QMouseEvent(
            QMouseEvent.Type.MouseMove, centro, centro,
            Qt.MouseButton.NoButton, Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
        )  # fmt: skip
        grafica.mouseMoveEvent(movimiento)
        # Con n = 4, el centro de la gráfica cae en la 2.ª o 3.ª barra
        self.assertIn(round(avisos[-1] / (math.pi / 4)), (3, 5))
        self.assertFalse(grafica.grab().isNull())


if __name__ == "__main__":
    unittest.main()
