"""Pruebas de las gráficas (sin abrir ventanas: QT_QPA_PLATFORM=offscreen)."""

import tempfile
import time
import unittest
from dataclasses import replace
from pathlib import Path

from PySide6.QtCore import QEvent, QEventLoop, Qt, QTimer
from PySide6.QtGui import QImage, QKeyEvent
from PySide6.QtWidgets import QApplication

from viviani.calculo import calcular, datos_convergencia
from viviani.graficas import GraficaConvergencia, GraficaCurva3D, GraficaRiemann
from viviani.tema import paleta

app = QApplication.instance() or QApplication([])
DATOS = datos_convergencia()


def esperar_senal(senal, tope_ms):
    """Corre el bucle de eventos hasta la señal o hasta el tope. Devuelve segundos."""
    bucle = QEventLoop()
    senal.connect(bucle.quit)
    QTimer.singleShot(tope_ms, bucle.quit)
    inicio = time.perf_counter()
    bucle.exec()
    return time.perf_counter() - inicio


def hacer_graficas(oscuro):
    colores = paleta(oscuro)
    convergencia = GraficaConvergencia(colores)
    convergencia.establecer_datos(DATOS)
    return GraficaCurva3D(colores), GraficaRiemann(colores), convergencia


class PruebasExportacion(unittest.TestCase):
    def setUp(self):
        carpeta = tempfile.TemporaryDirectory()
        self.addCleanup(carpeta.cleanup)
        self.carpeta = Path(carpeta.name)

    def test_exportar_crea_png_ancho(self):
        for oscuro in (False, True):
            curva, riemann, conv = hacer_graficas(oscuro)
            for n in (10, 1000):
                resultado = calcular(5.0, n)
                curva.mostrar(5.0)
                riemann.mostrar_resultado(resultado, animar=False)
                conv.marcar_actual(resultado, animar=False)
                for nombre, grafica in (("c", curva), ("r", riemann), ("v", conv)):
                    with self.subTest(grafica=nombre, n=n, oscuro=oscuro):
                        ruta = self.carpeta / f"{nombre}_{n}_{oscuro}.png"
                        grafica.exportar(str(ruta))
                        imagen = QImage(str(ruta))
                        self.assertGreaterEqual(imagen.width(), 1000)
                        # Fondo blanco aunque la pantalla esté en modo oscuro
                        self.assertEqual(imagen.pixelColor(2, 2).name(), "#ffffff")

    def test_exportar_no_altera_la_pantalla(self):
        _, riemann, _ = hacer_graficas(True)
        riemann.mostrar_resultado(calcular(5.0, 10), animar=False)
        figura, tamano = riemann.figure, riemann.figure.get_size_inches().copy()
        riemann.exportar(str(self.carpeta / "r.png"))
        self.assertIs(riemann.figure, figura)
        self.assertEqual(list(riemann.figure.get_size_inches()), list(tamano))
        self.assertEqual(riemann.figure.get_facecolor()[:3] != (1, 1, 1), True)

    def test_exportar_estados_previos(self):
        # Antes del primer cálculo también se puede exportar
        _, riemann, conv = hacer_graficas(False)
        riemann.mostrar_funcion(5.0)
        riemann.exportar(str(self.carpeta / "r.png"))
        conv.exportar(str(self.carpeta / "v.png"))
        self.assertTrue((self.carpeta / "r.png").exists())
        self.assertTrue((self.carpeta / "v.png").exists())


class PruebasTextos(unittest.TestCase):
    def test_nombres_sugeridos(self):
        curva, riemann, conv = hacer_graficas(False)
        resultado = calcular(5.0, 10)
        curva.mostrar(5.0)
        riemann.mostrar_resultado(resultado, animar=False)
        conv.marcar_actual(resultado, animar=False)
        self.assertEqual(curva.nombre_sugerido(), "viviani_3d_R5cm.png")
        self.assertEqual(riemann.nombre_sugerido(), "riemann_R5cm_n10_punto_medio.png")
        self.assertEqual(conv.nombre_sugerido(), "convergencia_n10_punto_medio.png")

    def test_nombre_con_coma_decimal(self):
        _, riemann, _ = hacer_graficas(False)
        riemann.mostrar_resultado(calcular(7.5, 10), animar=False)
        self.assertEqual(
            riemann.nombre_sugerido(), "riemann_R7-5cm_n10_punto_medio.png"
        )

    def test_descripciones_accesibles(self):
        curva, riemann, conv = hacer_graficas(False)
        resultado = calcular(5.0, 10)
        curva.mostrar(5.0)
        riemann.mostrar_resultado(resultado, animar=False)
        conv.marcar_actual(resultado, animar=False)
        self.assertEqual(
            curva.descripcion_accesible(),
            "Gráfica 3D de la Ventana de Viviani sobre una esfera de radio 5 "
            "centímetros. Punto doble en (5, 0, 0).",
        )
        self.assertEqual(
            riemann.descripcion_accesible(),
            "Suma de Riemann con 10 rectángulos, método punto medio. "
            "Suma igual a 38,201673 centímetros.",
        )
        self.assertTrue(
            conv.descripcion_accesible().startswith(
                "Convergencia: con n = 10 y punto medio, el error relativo es "
            )
        )
        self.assertTrue(conv.descripcion_accesible().endswith("por ciento."))
        self.assertEqual(riemann.accessibleName(), riemann.descripcion_accesible())


class PruebasRuido(unittest.TestCase):
    def test_error_de_ruido_se_describe_sin_numero(self):
        conv = hacer_graficas(False)[2]
        ruido = replace(calcular(5.0, 1000), error_relativo=0.0)
        conv.marcar_actual(ruido, animar=False)
        self.assertIn("menor que el límite de precisión", conv.descripcion_accesible())


class PruebasTema(unittest.TestCase):
    def test_cambio_de_tema_en_caliente(self):
        for grafica in hacer_graficas(False):
            for oscuro in (True, False, True):
                colores = paleta(oscuro)
                grafica.aplicar_tema(colores)
                grafica.grab()
                fondo = grafica.figure.get_facecolor()
                self.assertEqual(fondo, _a_rgba(colores["superficie"]))


def _a_rgba(hexadecimal):
    h = hexadecimal.lstrip("#")
    return tuple(int(h[i : i + 2], 16) / 255 for i in (0, 2, 4)) + (1.0,)


class PruebasCurva3D(unittest.TestCase):
    def test_vista_y_limites(self):
        curva = hacer_graficas(False)[0]
        self.assertEqual(curva.focusPolicy(), Qt.StrongFocus)
        curva.restablecer_vista()
        eje = curva._eje()
        self.assertEqual((eje.elev, eje.azim), (22, 35))
        curva.rotar(10, 100)
        self.assertEqual(eje.elev, 90)
        curva.rotar(-5, -500)
        self.assertEqual(eje.elev, -90)
        self.assertAlmostEqual(eje.azim, 40)
        curva.restablecer_vista()
        self.assertEqual((eje.elev, eje.azim), (22, 35))

    def test_flechas_rotan_10_grados(self):
        curva = hacer_graficas(False)[0]
        eje = curva._eje()
        for tecla, esperado in (
            (Qt.Key_Right, (22, 45)),
            (Qt.Key_Left, (22, 35)),
            (Qt.Key_Up, (32, 35)),
            (Qt.Key_Down, (22, 35)),
        ):
            evento = QKeyEvent(QEvent.KeyPress, tecla, Qt.NoModifier)
            app.sendEvent(curva, evento)
            self.assertEqual((eje.elev, eje.azim), esperado)

    def test_mostrar_conserva_la_vista(self):
        curva = hacer_graficas(False)[0]
        curva.rotar(20, 5)
        curva.mostrar(7.5)
        self.assertEqual((curva._eje().elev, curva._eje().azim), (27, 55))
        self.assertIn("7,5", curva.descripcion_accesible())


class PruebasAnimacion(unittest.TestCase):
    def test_riemann_termina_en_menos_de_2_s_y_avisa(self):
        _, riemann, _ = hacer_graficas(False)
        avisos = []
        riemann.animacion_terminada.connect(lambda: avisos.append(1))
        riemann.mostrar_resultado(calcular(5.0, 10))
        self.assertTrue(riemann.esta_animando())
        segundos = esperar_senal(riemann.animacion_terminada, 3000)
        print(f"\n  animación Riemann: {segundos:.3f} s")
        self.assertLessEqual(segundos, 2.0)
        self.assertGreater(segundos, 1.0)
        self.assertFalse(riemann.esta_animando())
        self.assertEqual(avisos, [1])

    def test_riemann_agrupado_con_reducir_movimiento(self):
        _, riemann, _ = hacer_graficas(True)
        riemann.mostrar_resultado(calcular(5.0, 1000), reducir_movimiento=True)
        segundos = esperar_senal(riemann.animacion_terminada, 3000)
        self.assertLess(segundos, 0.6)
        self.assertFalse(riemann.esta_animando())

    def test_convergencia_fundido(self):
        _, _, conv = hacer_graficas(False)
        conv.marcar_actual(calcular(5.0, 10))
        self.assertTrue(conv.esta_animando())
        segundos = esperar_senal(conv.animacion_terminada, 3000)
        print(f"\n  fundido de convergencia: {segundos:.3f} s")
        self.assertLessEqual(segundos, 0.6)
        self.assertFalse(conv.esta_animando())

    def test_saltar_termina_de_inmediato(self):
        _, riemann, conv = hacer_graficas(False)
        for grafica, iniciar in (
            (riemann, lambda: riemann.mostrar_resultado(calcular(5.0, 50))),
            (conv, lambda: conv.marcar_actual(calcular(5.0, 50))),
        ):
            avisos = []
            grafica.animacion_terminada.connect(lambda a=avisos: a.append(1))
            iniciar()
            self.assertTrue(grafica.esta_animando())
            grafica.saltar_animacion()
            self.assertFalse(grafica.esta_animando())
            self.assertEqual(avisos, [1])
            grafica.saltar_animacion()  # sin animación: no hace nada
            self.assertEqual(avisos, [1])

    def test_sin_animar_el_estado_final_es_inmediato(self):
        _, riemann, conv = hacer_graficas(False)
        riemann.mostrar_resultado(calcular(5.0, 10), animar=False)
        conv.marcar_actual(calcular(5.0, 10), animar=False)
        self.assertFalse(riemann.esta_animando())
        self.assertFalse(conv.esta_animando())

    def test_un_resultado_nuevo_reemplaza_la_animacion(self):
        _, riemann, _ = hacer_graficas(False)
        avisos = []
        riemann.animacion_terminada.connect(lambda: avisos.append(1))
        riemann.mostrar_resultado(calcular(5.0, 10))
        riemann.mostrar_resultado(calcular(5.0, 20))
        self.assertTrue(riemann.esta_animando())
        esperar_senal(riemann.animacion_terminada, 3000)
        self.assertEqual(avisos, [1])  # solo termina la segunda
        self.assertIn("20 rectángulos", riemann.descripcion_accesible())


if __name__ == "__main__":
    unittest.main()
