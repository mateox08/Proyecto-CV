"""Pruebas automáticas. Ejecutar con:  python -m unittest -v"""

import math
import unittest

from perimetro_viviani import RAZON_REFERENCIA, suma_de_riemann


class PruebasSumaDeRiemann(unittest.TestCase):
    def test_valor_de_control(self):
        # Con n grande, L/R debe acercarse a 7,6404
        self.assertAlmostEqual(suma_de_riemann(1, 1000) , RAZON_REFERENCIA, places=9)

    def test_proporcional_al_radio(self):
        # Si R se duplica, el perímetro se duplica
        self.assertAlmostEqual(
            suma_de_riemann(10, 200), 2 * suma_de_riemann(5, 200), places=9
        )

    def test_el_error_disminuye_al_aumentar_n(self):
        error_4 = abs(suma_de_riemann(1, 4) - RAZON_REFERENCIA)
        error_10 = abs(suma_de_riemann(1, 10) - RAZON_REFERENCIA)
        self.assertLess(error_10, error_4)

    def test_izquierda_y_derecha_coinciden(self):
        # f(0) = f(2*pi), por eso ambas sumas tienen el mismo valor
        self.assertAlmostEqual(
            suma_de_riemann(3, 25, "izquierda"),
            suma_de_riemann(3, 25, "derecha"),
            places=9,
        )

    def test_un_subintervalo(self):
        # Con n = 1 y punto medio: f(pi) * 2*pi = R*sqrt(2) * 2*pi
        self.assertAlmostEqual(
            suma_de_riemann(1, 1), math.sqrt(2) * 2 * math.pi, places=9
        )


class PruebasValidacion(unittest.TestCase):
    def test_radio_no_positivo(self):
        for radio in (0, -3, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                suma_de_riemann(radio, 10)

    def test_n_invalido(self):
        for n in (0, -5, 2.5, True, 10**9):
            with self.assertRaises(ValueError):
                suma_de_riemann(1, n)

    def test_metodo_invalido(self):
        with self.assertRaises(ValueError):
            suma_de_riemann(1, 10, "trapecio")


if __name__ == "__main__":
    unittest.main()
