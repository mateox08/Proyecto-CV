"""Pruebas de la validación de R y n (docs/DISENO.md, sección 4.3)."""

import unittest

from viviani.validacion import validar_radio, validar_subintervalos

MSG_R_VACIO = "Escriba el radio R."
MSG_R_FINITO = "R debe ser un número finito."
MSG_R_NUMERO = "Escriba un número, por ejemplo 5 o 7.5."
MSG_R_POSITIVO = "R debe ser mayor que cero."

MSG_N_VACIO = "Escriba el número de subintervalos n."
MSG_N_FINITO = "n debe ser un número finito."
MSG_N_MILES = "Escriba n sin puntos ni comas, por ejemplo 1000."
MSG_N_ENTERO = "n debe ser un número entero, sin decimales."
MSG_N_DIGITOS = "Escriba solo dígitos, por ejemplo 1000."
MSG_N_POSITIVO = "n debe ser mayor que cero."
MSG_N_MAXIMO = "n no debe superar 10 000 000."


class PruebasRadio(unittest.TestCase):
    def comprobar_valido(self, texto, esperado):
        valor, mensaje = validar_radio(texto)
        self.assertEqual(mensaje, "", texto)
        self.assertAlmostEqual(valor, esperado)

    def comprobar_error(self, texto, mensaje_esperado):
        valor, mensaje = validar_radio(texto)
        self.assertIsNone(valor, texto)
        self.assertEqual(mensaje, mensaje_esperado, texto)

    def test_validos(self):
        self.comprobar_valido("5", 5.0)
        self.comprobar_valido("  5  ", 5.0)
        self.comprobar_valido("7,5", 7.5)
        self.comprobar_valido("7.5", 7.5)
        self.comprobar_valido("+7", 7.0)
        self.comprobar_valido(".5", 0.5)
        self.comprobar_valido("5.", 5.0)
        self.comprobar_valido("1e2", 100.0)
        self.comprobar_valido("1,5e1", 15.0)

    def test_radio_enorme_es_valido(self):
        # El desbordamiento lo detecta el cálculo, no la validación.
        valor, mensaje = validar_radio("1e300")
        self.assertEqual(mensaje, "")
        self.assertEqual(valor, 1e300)

    def test_vacio(self):
        self.comprobar_error("", MSG_R_VACIO)
        self.comprobar_error("   ", MSG_R_VACIO)

    def test_no_finito(self):
        for texto in ("nan", "NaN", "NAN", "inf", "Inf", "-inf", "+INF", "infinity"):
            self.comprobar_error(texto, MSG_R_FINITO)
        self.comprobar_error("-Infinity", MSG_R_FINITO)
        self.comprobar_error("1e999", MSG_R_FINITO)

    def test_no_numerico(self):
        for texto in ("abc", "1,2,3", "1.2.3", "7 5", "5cm", "--5", "1_0", "0x10"):
            self.comprobar_error(texto, MSG_R_NUMERO)

    def test_digitos_unicode_se_rechazan(self):
        # Decisión documentada en validacion.py: solo dígitos ASCII.
        self.comprobar_error("１２", MSG_R_NUMERO)

    def test_cero_y_negativos(self):
        self.comprobar_error("0", MSG_R_POSITIVO)
        self.comprobar_error("0,0", MSG_R_POSITIVO)
        self.comprobar_error("-1", MSG_R_POSITIVO)
        self.comprobar_error("-0.5", MSG_R_POSITIVO)


class PruebasSubintervalos(unittest.TestCase):
    def comprobar_valido(self, texto, esperado):
        valor, mensaje = validar_subintervalos(texto)
        self.assertEqual(mensaje, "", texto)
        self.assertEqual(valor, esperado)

    def comprobar_error(self, texto, mensaje_esperado):
        valor, mensaje = validar_subintervalos(texto)
        self.assertIsNone(valor, texto)
        self.assertEqual(mensaje, mensaje_esperado, texto)

    def test_validos(self):
        self.comprobar_valido("1", 1)
        self.comprobar_valido("10", 10)
        self.comprobar_valido("  1000  ", 1000)
        self.comprobar_valido("+7", 7)
        self.comprobar_valido("10 000", 10000)
        self.comprobar_valido("10 000", 10000)
        self.comprobar_valido("10000000", 10_000_000)

    def test_vacio(self):
        self.comprobar_error("", MSG_N_VACIO)
        self.comprobar_error("  ", MSG_N_VACIO)

    def test_no_finito(self):
        for texto in ("nan", "NaN", "inf", "-inf", "Infinity"):
            self.comprobar_error(texto, MSG_N_FINITO)

    def test_separador_de_miles(self):
        for texto in ("1.000", "10,000", "1.000.000", "999,999"):
            self.comprobar_error(texto, MSG_N_MILES)

    def test_decimales_y_cientifica(self):
        for texto in ("10.5", "10,5", "2,5", "1,2,3", "1e6", "2.5e3", "1E6"):
            self.comprobar_error(texto, MSG_N_ENTERO)

    def test_no_son_digitos(self):
        for texto in ("abc", "5cm", "--5", "1_0", "０１", "x.5"):
            self.comprobar_error(texto, MSG_N_DIGITOS)

    def test_cero_y_negativos(self):
        self.comprobar_error("0", MSG_N_POSITIVO)
        self.comprobar_error("-5", MSG_N_POSITIVO)
        self.comprobar_error("-99999999999999999999999", MSG_N_POSITIVO)

    def test_demasiado_grande(self):
        self.comprobar_error("10000001", MSG_N_MAXIMO)
        self.comprobar_error("9" * 5000, MSG_N_MAXIMO)


if __name__ == "__main__":
    unittest.main()
