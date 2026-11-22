"""Pruebas de viviani.calculo (sin interfaz)."""

import math
import time
import unittest

import numpy as np

from perimetro_viviani import RAZON_REFERENCIA, suma_de_riemann
from viviani.calculo import (
    MAX_BARRAS,
    CalculoCancelado,
    calcular,
)


class PruebasCoincidencia(unittest.TestCase):
    def test_coincide_con_el_programa_original(self):
        # 1, 7, 120, 121: alrededor del límite de barras; 1_234_567: más de un bloque
        for n in (1, 7, 120, 121, 1000, 1_234_567):
            with self.subTest(n=n):
                esperado = suma_de_riemann(7.5, n, "punto_medio")
                obtenido = calcular(7.5, n).perimetro
                self.assertLess(abs(obtenido - esperado) / esperado, 1e-12)

    def test_area_de_las_barras_es_el_perimetro(self):
        for n in (1, 10, 120, 121, 1000, 1_234_567):
            with self.subTest(n=n):
                r = calcular(5.0, n)
                area = float(np.sum(r.barras_ancho * r.barras_altura))
                self.assertAlmostEqual(area / r.perimetro, 1.0, places=12)

    def test_cantidad_de_barras_y_agrupacion(self):
        chico = calcular(1.0, 10)
        self.assertFalse(chico.agrupado)
        self.assertEqual(len(chico.barras_altura), 10)
        self.assertEqual(len(chico.puntos_t), 10)
        grande = calcular(1.0, 1000)
        self.assertTrue(grande.agrupado)
        self.assertEqual(len(grande.barras_altura), MAX_BARRAS)
        self.assertIsNone(grande.puntos_t)

    def test_barras_cubren_todo_el_intervalo(self):
        r = calcular(1.0, 1001)
        fin = r.barras_inicio + r.barras_ancho
        self.assertAlmostEqual(float(fin[-1]), 2 * math.pi, places=9)
        # Cada barra empieza donde termina la anterior
        np.testing.assert_allclose(r.barras_inicio[1:], fin[:-1], atol=1e-9)

    def test_errores_contra_la_referencia(self):
        r = calcular(2.0, 100)
        self.assertAlmostEqual(r.referencia, 2 * RAZON_REFERENCIA)
        self.assertAlmostEqual(r.error_absoluto, abs(r.perimetro - r.referencia))
        self.assertAlmostEqual(r.error_relativo, r.error_absoluto / r.referencia * 100)


class PruebasValidacion(unittest.TestCase):
    def test_datos_invalidos(self):
        casos = [
            (0, 10),
            (-1, 10),
            (math.nan, 10),
            (math.inf, 10),
            (1.0, 0),
            (1.0, 2.5),
            (1.0, True),
            (1.0, 10_000_001),
            (1e308, 10),
        ]
        for radio, n in casos:
            with self.subTest(radio=radio, n=n):
                with self.assertRaises(ValueError):
                    calcular(radio, n)

    def test_radio_enorme_dice_demasiado_grande(self):
        with self.assertRaisesRegex(ValueError, "demasiado grande"):
            calcular(1e308, 10)


class PruebasProgresoYCancelacion(unittest.TestCase):
    def test_cancelacion(self):
        with self.assertRaises(CalculoCancelado):
            calcular(1.0, 3_000_000, cancelado=lambda: True)

    def test_cancelacion_a_mitad(self):
        llamadas = []

        def cancelar_en_el_segundo_bloque():
            llamadas.append(1)
            return len(llamadas) >= 2

        with self.assertRaises(CalculoCancelado):
            calcular(1.0, 3_000_000, cancelado=cancelar_en_el_segundo_bloque)

    def test_progreso_llega_a_100(self):
        avances = []
        calcular(1.0, 2_500_000, progreso=avances.append)
        self.assertEqual(avances[-1], 100)
        self.assertEqual(avances, sorted(avances))
        self.assertGreater(len(avances), 1)

    def test_progreso_con_n_pequeno(self):
        avances = []
        calcular(1.0, 5, progreso=avances.append)
        self.assertEqual(avances, [100])


class PruebasRendimiento(unittest.TestCase):
    def test_diez_millones_termina(self):
        inicio = time.perf_counter()
        r = calcular(5.0, 10_000_000)
        segundos = time.perf_counter() - inicio
        print(f"\n  n = 10 000 000: {segundos:.2f} s")
        self.assertLess(r.error_relativo, 1e-10)
        self.assertLess(segundos, 20)


if __name__ == "__main__":
    unittest.main()
