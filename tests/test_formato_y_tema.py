"""Pruebas del formato de números y del contraste de la paleta."""

import unittest

from viviani import formato, tema


class PruebasFormato(unittest.TestCase):
    def test_coma_decimal(self):
        self.assertEqual(formato.formatear_decimal(38.201673), "38,201673")

    def test_entero_con_miles(self):
        self.assertEqual(formato.formatear_entero(10_000_000), "10 000 000")
        self.assertEqual(formato.formatear_entero(100), "100")

    def test_cientifico(self):
        self.assertEqual(formato.formatear_cientifico(3.049e-4), "3,049 × 10⁻⁴")
        self.assertEqual(formato.formatear_cientifico(1.5e12), "1,500 × 10¹²")
        self.assertEqual(formato.formatear_cientifico(0), "0")
        # Exponente entre -2 y 3: se escribe normal, con 4 cifras
        self.assertEqual(formato.formatear_cientifico(0.05), "0,05000")
        self.assertEqual(formato.formatear_cientifico(12.3456), "12,35")

    def test_cientifico_redondeo_de_mantisa(self):
        # 9,9996e-5 redondea a 1,000e-4 (no debe salir '10,000 × 10⁻⁵')
        self.assertEqual(formato.formatear_cientifico(9.9996e-5), "1,000 × 10⁻⁴")

    def test_medida_y_radio(self):
        self.assertEqual(formato.formatear_medida(38.20167296), "38,201673")
        self.assertEqual(formato.formatear_medida(7.640395578e9), "7,640396 × 10⁹")
        self.assertEqual(formato.formatear_radio(5.0), "5")
        self.assertEqual(formato.formatear_radio(7.5), "7,5")

    def test_nombre_metodo(self):
        self.assertEqual(formato.nombre_metodo("punto_medio"), "punto medio")


class PruebasContraste(unittest.TestCase):
    """Contraste WCAG AA: 4,5:1 para texto y 3:1 para elementos gráficos."""

    TEXTO = [
        ("texto", "fondo"), ("texto", "superficie"), ("texto", "fondo_aviso"),
        ("texto_sec", "fondo"), ("texto_sec", "superficie"),
        ("texto_sec", "superficie_deshab"), ("texto_deshab", "superficie_deshab"),
        ("texto_sobre_acento", "acento"), ("texto_sobre_acento", "acento_hover"),
        ("acento", "superficie"), ("acento", "fondo"),
        ("error", "superficie"), ("error", "fondo"), ("error", "fondo_error"),
        ("exito", "superficie"), ("exito", "fondo"),
        ("aviso", "superficie"), ("aviso", "fondo_aviso"),
        ("tooltip_texto", "tooltip_fondo"),
    ]  # fmt: skip
    GRAFICOS = [
        ("borde", "superficie"), ("foco", "superficie"), ("foco", "fondo"),
        ("serie_azul", "superficie"), ("serie_naranja", "superficie"),
        ("serie_verde", "superficie"), ("serie_morado", "superficie"),
        ("punto_doble", "superficie"),
    ]  # fmt: skip

    def test_contraste_en_ambos_modos(self):
        for oscuro in (False, True):
            colores = tema.paleta(oscuro)
            for pares, minimo in ((self.TEXTO, 4.5), (self.GRAFICOS, 3.0)):
                for frente, fondo in pares:
                    razon = tema.razon_de_contraste(colores[frente], colores[fondo])
                    with self.subTest(modo=colores["modo"], par=(frente, fondo)):
                        self.assertGreaterEqual(razon, minimo)

    def test_blanco_sobre_negro(self):
        self.assertAlmostEqual(tema.razon_de_contraste("#FFFFFF", "#000000"), 21.0)


if __name__ == "__main__":
    unittest.main()
