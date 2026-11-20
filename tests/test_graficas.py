"""Pruebas básicas de las dos gráficas (sin abrir ventanas)."""

import tempfile
import unittest
from pathlib import Path

from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication

from viviani.calculo import calcular
from viviani.graficas import GraficaCurva3D, GraficaRiemann
from viviani.tema import paleta

APP = QApplication.instance() or QApplication([])


class PruebasGraficas(unittest.TestCase):
    def test_exportar_3d_crea_png(self):
        grafica = GraficaCurva3D(paleta(), reducir_movimiento=True)
        grafica.mostrar(7.5)
        self.assertEqual(grafica.nombre_sugerido(), "viviani_3d_R7-5cm.png")
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = str(Path(carpeta) / "curva.png")
            grafica.exportar(ruta)
            self.assertGreaterEqual(QImage(ruta).width(), 2000)

    def test_riemann_muestra_y_salta_la_animacion(self):
        grafica = GraficaRiemann(paleta())
        grafica.resize(500, 400)
        grafica.mostrar_resultado(calcular(5.0, 1000))
        self.assertTrue(grafica.esta_animando())
        grafica.saltar_animacion()
        self.assertFalse(grafica.esta_animando())


if __name__ == "__main__":
    unittest.main()
