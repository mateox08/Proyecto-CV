"""Pruebas del formato de números y del contraste de la paleta."""

import unittest

from viviani import formato, tema


class PruebasFormato(unittest.TestCase):
    def test_punto_decimal(self):
        self.assertEqual(formato.formatear_decimal(38.2016729), "38.201673")

    def test_cientifico(self):
        self.assertEqual(formato.formatear_cientifico(3.049e-4), "3.049 × 10⁻⁴")
        self.assertEqual(formato.formatear_cientifico(0), "0")
        self.assertEqual(formato.formatear_cientifico(0.05), "0.05000")
        # 9.9996e-5 redondea a 1.000e-4 (no debe salir '10.000 × 10⁻⁵')
        self.assertEqual(formato.formatear_cientifico(9.9996e-5), "1.000 × 10⁻⁴")

    def test_radio(self):
        self.assertEqual(formato.formatear_radio(5.0), "5")
        self.assertEqual(formato.formatear_radio(7.5), "7.5")


class PruebasContraste(unittest.TestCase):
    """Contraste WCAG AA: 4,5 a 1 para el texto sobre su fondo."""

    PARES = [
        ("texto", "fondo"), ("texto", "superficie"), ("texto_sec", "superficie"),
        ("etiqueta", "superficie"), ("texto_sobre_acento", "acento"),
        ("error", "superficie"), ("error", "fondo_error"),
    ]  # fmt: skip

    def test_contraste_del_texto(self):
        colores = tema.paleta()
        for frente, fondo in self.PARES:
            with self.subTest(par=(frente, fondo)):
                razon = tema.razon_de_contraste(colores[frente], colores[fondo])
                self.assertGreaterEqual(razon, 4.5)


if __name__ == "__main__":
    unittest.main()
