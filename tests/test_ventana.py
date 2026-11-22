"""Prueba de humo de la ventana completa (sin abrirla en pantalla ni sonar)."""

import unittest

from PySide6.QtCore import QEvent, QEventLoop, QTimer
from PySide6.QtWidgets import QApplication

from viviani.calculo import calcular
from viviani.graficas import GraficaCurva3D, GraficaRiemann
from viviani.sonido import Sonidos
from viviani.tema import paleta
from viviani.ui.ventana import VentanaPrincipal, paso_de_n

APP = QApplication.instance() or QApplication([])


class PruebasVentana(unittest.TestCase):
    def setUp(self):
        self.sonidos = Sonidos(reproductor=lambda _datos: None)
        self.ventana = VentanaPrincipal(
            GraficaCurva3D(paleta(), reducir_movimiento=True),
            GraficaRiemann(paleta()),
            self.sonidos,
            calcular,
        )
        self.addCleanup(self.cerrar_ventana)

    def cerrar_ventana(self):
        # Se destruye de verdad: si la ventana sigue viva cuando Python
        # termina, Qt puede fallar al cerrar el proceso (ver app.main).
        self.ventana.close()
        self.ventana.deleteLater()
        QApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    def esperar_resultado(self):
        bucle = QEventLoop()
        self.ventana._calculo.terminado.connect(bucle.quit)
        QTimer.singleShot(5000, bucle.quit)  # por si algo falla, no se cuelga
        bucle.exec()

    def test_calcula_y_muestra_el_resultado(self):
        self.ventana.bloque_n.escribir("10")
        self.ventana.calcular_ahora()
        self.esperar_resultado()
        self.ventana.panel_resultado.saltar_animacion()
        texto = self.ventana.panel_resultado.etiqueta_perimetro.text()
        self.assertIn("38.201", texto)
        self.assertEqual(round(self.ventana.panel_resultado.medidor.cifras), 5)
        self.assertIn("0.628319", self.ventana.formula.accessibleName())

    def test_dato_invalido_muestra_el_mensaje(self):
        self.ventana.bloque_r.escribir("-3")
        self.ventana.calcular_ahora()
        self.assertEqual(
            self.ventana.bloque_r.mensaje.text(), "R debe ser mayor que cero."
        )

    def test_flechas_multiplican_n(self):
        self.assertEqual(paso_de_n(100, 1), "1000")
        self.assertEqual(paso_de_n(5, -1), "1")


if __name__ == "__main__":
    unittest.main()
