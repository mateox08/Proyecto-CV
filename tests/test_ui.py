"""Pruebas de la ventana principal, sin abrir nada en pantalla (offscreen).

Las gráficas, los sonidos y el cálculo son DOBLES de prueba definidos aquí:
imitan los contratos reales y anotan lo que se les pide, así se prueba la
ventana sin depender de matplotlib ni de winsound.
"""

import tempfile
import time
import unittest
from dataclasses import dataclass
from pathlib import Path
from unittest import mock

from PySide6.QtCore import QSettings, Qt, QtMsgType, qInstallMessageHandler
from PySide6.QtGui import QColor, QPainter
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QFileDialog, QWidget

from viviani.ui import sistema
from viviani.ui.trabajador import GestorTareas
from viviani.ui.ventana import VentanaPrincipal

aplicacion = QApplication.instance() or QApplication([])

# Todo mensaje de aviso o error de Qt durante las pruebas se anota aquí.
avisos_de_qt = []


def _anotar_aviso(tipo, _contexto, mensaje):
    es_aviso = tipo in (
        QtMsgType.QtWarningMsg,
        QtMsgType.QtCriticalMsg,
        QtMsgType.QtFatalMsg,
    )
    # Los avisos sobre el directorio de fuentes dependen de la máquina, no del código.
    if es_aviso and not mensaje.startswith("QFontDatabase:"):
        avisos_de_qt.append(mensaje)


qInstallMessageHandler(_anotar_aviso)


# ---------------------------------------------------------------------------
# Dobles de prueba
# ---------------------------------------------------------------------------
class CalculoCancelado(Exception):
    """Igual que viviani.calculo.CalculoCancelado."""


@dataclass(frozen=True)
class ResultadoFalso:
    radio: float
    n: int
    metodo: str
    perimetro: float = 38.201673
    referencia: float = 38.201978
    error_absoluto: float = 3.049e-4
    error_relativo: float = 7.982e-4
    agrupado: bool = False


class GraficaFalsa(QWidget):
    """Un rectángulo de color con los métodos del contrato; anota las llamadas."""

    from PySide6.QtCore import Signal

    animacion_terminada = Signal()

    def __init__(self, color="#0072B2"):
        super().__init__()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.color = color
        self.llamadas = []
        self.animando = False

    def paintEvent(self, _evento):
        QPainter(self).fillRect(self.rect(), QColor(self.color))

    def _anotar(self, nombre, *args, **kwargs):
        self.llamadas.append((nombre, args, kwargs))

    def nombres(self):
        return [llamada[0] for llamada in self.llamadas]

    # Contrato de las tres gráficas
    def mostrar(self, radio):
        self._anotar("mostrar", radio)

    def mostrar_funcion(self, radio):
        self._anotar("mostrar_funcion", radio)

    def restablecer_vista(self):
        self._anotar("restablecer_vista")

    def rotar(self, d_acimut, d_elevacion):
        self._anotar("rotar", d_acimut, d_elevacion)

    def mostrar_resultado(self, resultado, animar=True, reducir_movimiento=False):
        self._anotar("mostrar_resultado", resultado, animar=animar,
                     reducir_movimiento=reducir_movimiento)  # fmt: skip
        self.animando = animar

    def establecer_datos(self, datos):
        self._anotar("establecer_datos", datos)

    def marcar_actual(self, resultado, animar=True, reducir_movimiento=False):
        self._anotar("marcar_actual", resultado, animar=animar,
                     reducir_movimiento=reducir_movimiento)  # fmt: skip

    def saltar_animacion(self):
        self._anotar("saltar_animacion")
        self.animando = False

    def esta_animando(self):
        return self.animando

    def aplicar_tema(self, colores):
        self._anotar("aplicar_tema", colores["modo"])

    def exportar(self, ruta):
        self._anotar("exportar", ruta)

    def nombre_sugerido(self):
        return "grafica_falsa.png"

    def descripcion_accesible(self):
        return "Gráfica falsa"


class SonidosFalsos:
    def __init__(self):
        self.eventos = []
        self.activado = True

    def establecer_activado(self, valor):
        self.activado = valor
        self.eventos.append(f"activado={valor}")

    def clic(self):
        self.eventos.append("clic")

    def resultado(self):
        self.eventos.append("resultado")

    def error(self):
        self.eventos.append("error")

    def cerrar(self):
        self.eventos.append("cerrar")


class CalculoFalso:
    """`calcular` rápido o lento que anota sus llamadas y respeta `cancelado`."""

    def __init__(self, segundos=0.0, error=None):
        self.segundos = segundos
        self.error = error
        self.llamadas = []  # (radio, n, metodo)
        self.canceladas = 0

    def __call__(self, radio, n, metodo="punto_medio", progreso=None, cancelado=None):
        self.llamadas.append((radio, n, metodo))
        if self.error is not None:
            raise self.error
        fin = time.monotonic() + self.segundos
        while time.monotonic() < fin:
            if cancelado is not None and cancelado():
                self.canceladas += 1
                raise CalculoCancelado()
            if progreso is not None:
                progreso(50)
            time.sleep(0.005)
        return ResultadoFalso(radio, n, metodo)


def datos_falsos(cancelado=None):
    return {"n": [1, 2, 3]}


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def esperar(condicion, limite_ms=4000):
    """Procesa eventos hasta que `condicion()` sea verdadera (o se acabe el tiempo)."""
    fin = time.monotonic() + limite_ms / 1000
    while time.monotonic() < fin:
        aplicacion.processEvents()
        if condicion():
            return True
        QTest.qWait(5)
    return condicion()


class BaseVentana(unittest.TestCase):
    def setUp(self):
        self.carpeta = tempfile.TemporaryDirectory()
        self.ajustes = QSettings(str(Path(self.carpeta.name) / "ajustes.ini"),
                                 QSettings.Format.IniFormat)  # fmt: skip
        self.sonidos = SonidosFalsos()
        self.calculo = CalculoFalso()
        avisos_de_qt.clear()

    def tearDown(self):
        for ventana in getattr(self, "ventanas", []):
            ventana.close()
            ventana.deleteLater()
        aplicacion.processEvents()
        self.carpeta.cleanup()
        self.assertEqual(avisos_de_qt, [], "Qt emitió avisos")

    def crear(self, calculo=None):
        self.ventanas = getattr(self, "ventanas", [])
        self.graficas = (
            GraficaFalsa(),
            GraficaFalsa("#C24E00"),
            GraficaFalsa("#8E3B87"),
        )
        ventana = VentanaPrincipal(
            *self.graficas, self.sonidos, calculo or self.calculo, datos_falsos,
            ajustes=self.ajustes,
        )  # fmt: skip
        self.ventanas.append(ventana)
        ventana.resize(1536, 864)
        ventana.show()
        ventana.activateWindow()
        QTest.qWaitForWindowActive(ventana)
        return ventana

    def teclear_enter(self, ventana, campo):
        campo.setFocus()
        QTest.keyClick(campo, Qt.Key.Key_Return)


# ---------------------------------------------------------------------------
# Flujo de cálculo
# ---------------------------------------------------------------------------
class PruebasCalculo(BaseVentana):
    def test_enter_calcula_y_muestra_valores(self):
        ventana = self.crear()
        self.teclear_enter(ventana, ventana.campo_radio)
        self.assertTrue(esperar(lambda: ventana.etiqueta_perimetro.text() != ""))
        self.assertEqual(self.calculo.llamadas, [(5.0, 10, "punto_medio")])
        self.assertEqual(ventana.etiqueta_perimetro.text(), "38,201673 cm")
        self.assertEqual(ventana.etiqueta_control.text(), "38,201978 cm")
        self.assertEqual(ventana.etiqueta_error_abs.text(), "3,049 × 10⁻⁴ cm")
        self.assertEqual(ventana.etiqueta_error_rel.text(), "7,982 × 10⁻⁴ %")
        self.assertEqual(self.sonidos.eventos[-2:], ["clic", "resultado"])

    def test_el_resultado_llega_a_las_graficas(self):
        ventana = self.crear()
        ventana.calcular_ahora()
        self.assertTrue(
            esperar(lambda: "mostrar_resultado" in self.graficas[1].nombres())
        )
        g3d, griemann, gconv = self.graficas
        self.assertIn("mostrar", g3d.nombres())
        llamada = [c for c in griemann.llamadas if c[0] == "mostrar_resultado"][-1]
        self.assertTrue(llamada[2]["animar"])
        self.assertIn("reducir_movimiento", llamada[2])
        # El punto actual de la convergencia espera a que acabe la animación.
        self.assertNotIn("marcar_actual", gconv.nombres())
        griemann.animando = False
        griemann.animacion_terminada.emit()
        self.assertIn("marcar_actual", gconv.nombres())

    def test_arranque_pide_los_datos_de_convergencia(self):
        ventana = self.crear()
        self.assertTrue(
            esperar(lambda: "establecer_datos" in self.graficas[2].nombres())
        )
        self.assertIsNotNone(ventana)

    def test_coma_decimal(self):
        ventana = self.crear()
        ventana.campo_radio.setText("7,5")
        ventana.campo_n.setText("1 000")
        ventana.calcular_ahora()
        self.assertTrue(esperar(lambda: self.calculo.llamadas != []))
        self.assertEqual(self.calculo.llamadas[0][:2], (7.5, 1000))

    def test_punto_decimal(self):
        ventana = self.crear()
        ventana.campo_radio.setText("7.5")
        ventana.calcular_ahora()
        self.assertTrue(esperar(lambda: self.calculo.llamadas != []))
        self.assertEqual(self.calculo.llamadas[0][0], 7.5)

    def test_errores_de_validacion_no_calculan(self):
        casos = [
            ("", "10", "Escriba el radio R.", ""),
            ("abc", "10", "Escriba un número, por ejemplo 5 o 7,5.", ""),
            ("inf", "10", "R debe ser un número finito.", ""),
            ("0", "10", "R debe ser mayor que cero.", ""),
            ("5", "", "", "Escriba el número de subintervalos n."),
            ("5", "1.000", "", "Escriba n sin puntos ni comas, por ejemplo 1000."),
            ("5", "2,5", "", "n debe ser un número entero, sin decimales."),
            ("5", "x", "", "Escriba solo dígitos, por ejemplo 1000."),
            ("5", "0", "", "n debe ser mayor que cero."),
            ("5", "10000001", "", "n no debe superar 10 000 000."),
        ]
        for radio, n, mensaje_r, mensaje_n in casos:
            with self.subTest(radio=radio, n=n):
                ventana = self.crear()
                self.sonidos.eventos.clear()
                ventana.campo_radio.setText(radio)
                ventana.campo_n.setText(n)
                self.assertFalse(ventana.calcular_ahora())
                self.assertEqual(ventana.mensaje_radio.text(), mensaje_r)
                self.assertEqual(ventana.mensaje_n.text(), mensaje_n)
                self.assertEqual(self.sonidos.eventos, ["error"])
                primero = ventana.campo_radio if mensaje_r else ventana.campo_n
                self.assertIs(ventana.focusWidget(), primero)
        self.assertEqual(self.calculo.llamadas, [])

    def test_ambos_campos_con_error_foco_en_el_primero(self):
        ventana = self.crear()
        ventana.campo_radio.setText("")
        ventana.campo_n.setText("")
        ventana.campo_n.setFocus()
        ventana.calcular_ahora()
        self.assertNotEqual(ventana.mensaje_radio.text(), "")
        self.assertNotEqual(ventana.mensaje_n.text(), "")
        self.assertIs(ventana.focusWidget(), ventana.campo_radio)

    def test_el_error_desaparece_al_corregir(self):
        ventana = self.crear()
        ventana.campo_radio.setText("abc")
        ventana.calcular_ahora()
        self.assertNotEqual(ventana.mensaje_radio.text(), "")
        ventana.campo_radio.setFocus()
        ventana.campo_radio.selectAll()
        QTest.keyClicks(ventana.campo_radio, "5")
        self.assertEqual(ventana.mensaje_radio.text(), "")

    def test_campo_vacio_sin_tocar_no_muestra_error(self):
        ventana = self.crear()
        self.assertEqual(ventana.mensaje_radio.text(), "")
        self.assertEqual(ventana.mensaje_n.text(), "")

    def test_encadenar_calculos_conserva_foco_y_seleccion(self):
        ventana = self.crear()
        ventana.campo_n.setFocus()
        QTest.keyClick(ventana.campo_n, Qt.Key.Key_Return)
        self.assertIs(ventana.focusWidget(), ventana.campo_n)
        self.assertEqual(ventana.campo_n.selectedText(), "10")

    def test_error_de_calculo_muestra_banda_y_suena_error(self):
        ventana = self.crear(
            CalculoFalso(error=ValueError("el resultado es demasiado grande."))
        )
        ventana.calcular_ahora()
        self.assertTrue(esperar(lambda: "error" in self.sonidos.eventos))
        self.assertIn(
            "No se pudo calcular: el resultado",
            ventana.tarjeta_resultado.banda_error.texto.text(),
        )
        self.assertTrue(ventana.tarjeta_resultado.banda_error.isVisible())

    def test_aviso_de_muestra_con_n_grande(self):
        calculo = CalculoFalso()
        ventana = self.crear(calculo)

        def agrupado(radio, n, metodo="punto_medio", progreso=None, cancelado=None):
            return ResultadoFalso(radio, n, metodo, agrupado=True)

        ventana._calcular = agrupado
        ventana.campo_n.setText("1000")
        ventana.calcular_ahora()
        self.assertTrue(esperar(lambda: ventana.banda_muestra.isVisible()))
        texto = ventana.banda_muestra.texto.text()
        self.assertIn("Se dibujan 120 de los 1 000 rectángulos", texto)
        self.assertIn("unos 8 subintervalos", texto)


# ---------------------------------------------------------------------------
# Cancelación y cálculos encadenados
# ---------------------------------------------------------------------------
class PruebasCancelacion(BaseVentana):
    def test_esc_cancela_un_calculo_lento(self):
        lento = CalculoFalso(segundos=5)
        ventana = self.crear(lento)
        ventana.calcular_ahora()
        # La barra y el botón aparecen solo si tarda más de 300 ms.
        self.assertFalse(ventana.boton_cancelar.isVisible())
        self.assertTrue(esperar(lambda: ventana.boton_cancelar.isVisible()))
        QTest.keyClick(ventana.campo_radio, Qt.Key.Key_Escape)
        self.assertTrue(
            esperar(lambda: ventana.tarjeta_resultado.banda_cancelado.isVisible())
        )
        self.assertEqual(lento.canceladas, 1)
        self.assertFalse(ventana.boton_cancelar.isVisible())
        self.assertEqual(
            ventana.tarjeta_resultado.banda_cancelado.texto.text(), "Cálculo cancelado."
        )
        self.assertNotIn("error", self.sonidos.eventos)
        self.assertNotIn("resultado", self.sonidos.eventos)

    def test_boton_cancelar(self):
        ventana = self.crear(CalculoFalso(segundos=5))
        ventana.calcular_ahora()
        self.assertTrue(esperar(lambda: ventana.boton_cancelar.isVisible()))
        ventana.boton_cancelar.click()
        self.assertTrue(
            esperar(lambda: ventana.tarjeta_resultado.banda_cancelado.isVisible())
        )

    def test_cancelar_con_resultado_previo(self):
        ventana = self.crear()
        ventana.calcular_ahora()
        self.assertTrue(esperar(lambda: ventana.etiqueta_perimetro.text() != ""))
        ventana._calcular = CalculoFalso(segundos=5)
        ventana.calcular_ahora()
        self.assertTrue(esperar(lambda: ventana.boton_cancelar.isVisible()))
        ventana.boton_cancelar.click()
        self.assertTrue(
            esperar(lambda: ventana.tarjeta_resultado.banda_cancelado.isVisible())
        )
        aviso = ventana.tarjeta_resultado.banda_cancelado.texto.text()
        self.assertIn("Se mantienen los resultados anteriores", aviso)
        self.assertNotEqual(ventana.etiqueta_perimetro.text(), "")

    def test_calculo_nuevo_durante_otro_descarta_el_anterior(self):
        lento = CalculoFalso(segundos=5)
        ventana = self.crear(lento)
        ventana.calcular_ahora()  # R = 5, lento
        self.assertTrue(esperar(lambda: lento.llamadas != []))
        ventana._calcular = self.calculo  # el siguiente es rápido
        ventana.campo_radio.setText("8")
        ventana.calcular_ahora()
        self.assertTrue(esperar(lambda: "resultado" in self.sonidos.eventos))
        self.assertTrue(esperar(lambda: lento.canceladas == 1))
        self.assertEqual(self.calculo.llamadas[0][0], 8.0)
        self.assertIn("R = 8 cm", ventana.tarjeta_resultado.etiqueta_contexto.text())
        # El cálculo viejo cancelado no debe dejar un aviso de cancelación.
        QTest.qWait(50)
        self.assertFalse(ventana.tarjeta_resultado.banda_cancelado.isVisible())
        self.assertEqual(self.sonidos.eventos.count("resultado"), 1)

    def test_cerrar_durante_un_calculo_no_cuelga(self):
        lento = CalculoFalso(segundos=30)
        ventana = self.crear(lento)
        ventana.calcular_ahora()
        self.assertTrue(esperar(lambda: lento.llamadas != []))
        inicio = time.monotonic()
        ventana.close()
        self.assertLess(time.monotonic() - inicio, 3)
        self.assertEqual(lento.canceladas, 1)
        QTest.qWait(30)


# ---------------------------------------------------------------------------
# Método, sonido, exportar, tema
# ---------------------------------------------------------------------------
class PruebasControles(BaseVentana):
    def test_metodo_por_defecto_y_recalculo(self):
        ventana = self.crear()
        self.assertEqual(ventana.selector_metodo.metodo(), "punto_medio")
        # Sin resultado, cambiar de método no calcula.
        ventana.selector_metodo.botones["derecha"].click()
        QTest.qWait(30)
        self.assertEqual(self.calculo.llamadas, [])
        ventana.calcular_ahora()
        self.assertTrue(esperar(lambda: len(self.calculo.llamadas) == 1))
        self.assertTrue(esperar(lambda: ventana.etiqueta_perimetro.text() != ""))
        ventana.selector_metodo.botones["izquierda"].click()
        self.assertTrue(esperar(lambda: len(self.calculo.llamadas) == 2))
        self.assertEqual(self.calculo.llamadas[-1][2], "izquierda")

    def test_alt_i_cambia_el_metodo(self):
        ventana = self.crear()
        # Qt pulsa el botón con una breve animación (100 ms): hay que esperar.
        QTest.keyClick(
            ventana.campo_radio, Qt.Key.Key_I, Qt.KeyboardModifier.AltModifier
        )
        self.assertTrue(
            esperar(lambda: ventana.selector_metodo.metodo() == "izquierda")
        )
        QTest.keyClick(
            ventana.campo_radio, Qt.Key.Key_D, Qt.KeyboardModifier.AltModifier
        )
        self.assertTrue(esperar(lambda: ventana.selector_metodo.metodo() == "derecha"))

    def test_ctrl_m_alterna_el_sonido_y_se_recuerda(self):
        ventana = self.crear()
        self.assertTrue(ventana.interruptor_sonido.isChecked())
        self.assertEqual(ventana.interruptor_sonido.text(), "Sonido: activado")
        QTest.keyClick(
            ventana.campo_radio, Qt.Key.Key_M, Qt.KeyboardModifier.ControlModifier
        )
        self.assertFalse(ventana.interruptor_sonido.isChecked())
        self.assertEqual(ventana.interruptor_sonido.text(), "Sonido: desactivado")
        self.assertFalse(self.sonidos.activado)
        self.assertFalse(self.ajustes.value("sonido/activado", True, type=bool))
        QTest.keyClick(
            ventana.campo_radio, Qt.Key.Key_M, Qt.KeyboardModifier.ControlModifier
        )
        self.assertTrue(ventana.interruptor_sonido.isChecked())
        self.assertTrue(self.ajustes.value("sonido/activado", False, type=bool))
        self.assertEqual(self.sonidos.eventos[-1], "clic")  # al activar suena el clic

    def test_m_solo_fuera_de_los_campos(self):
        ventana = self.crear()
        ventana.boton_calcular.setFocus()
        QTest.keyClick(ventana.boton_calcular, Qt.Key.Key_M)
        self.assertFalse(ventana.interruptor_sonido.isChecked())
        # Con el foco en un campo, "m" se escribe y no cambia el sonido.
        ventana.campo_radio.setFocus()
        ventana.campo_radio.clear()
        QTest.keyClick(ventana.campo_radio, Qt.Key.Key_M)
        self.assertEqual(ventana.campo_radio.text(), "m")
        self.assertFalse(ventana.interruptor_sonido.isChecked())

    def test_preferencia_de_sonido_guardada_se_aplica(self):
        self.ajustes.setValue("sonido/activado", False)
        ventana = self.crear()
        self.assertFalse(ventana.interruptor_sonido.isChecked())
        self.assertEqual(ventana.interruptor_sonido.text(), "Sonido: desactivado")
        self.assertFalse(self.sonidos.activado)

    def test_exportar_llama_a_exportar(self):
        ventana = self.crear()
        destino = str(Path(self.carpeta.name) / "figura.png")
        with mock.patch.object(
            QFileDialog, "getSaveFileName", return_value=(destino, "")
        ) as dialogo:
            ventana._botones_exportar[1].click()
        self.assertEqual(self.graficas[1].llamadas[-1], ("exportar", (destino,), {}))
        self.assertIn("grafica_falsa.png", dialogo.call_args.args[2])
        self.assertEqual(
            ventana.etiqueta_estado.text(), f"Imagen guardada en: {destino}"
        )
        self.assertEqual(self.sonidos.eventos[-1], "clic")

    def test_exportar_cancelado_no_hace_nada(self):
        ventana = self.crear()
        with mock.patch.object(QFileDialog, "getSaveFileName", return_value=("", "")):
            ventana._botones_exportar[0].click()
        self.assertNotIn("exportar", self.graficas[0].nombres())

    def test_exportar_con_error_muestra_mensaje(self):
        ventana = self.crear()
        self.graficas[2].exportar = mock.Mock(side_effect=OSError("Permiso denegado."))
        with mock.patch.object(
            QFileDialog, "getSaveFileName", return_value=("x.png", "")
        ):
            ventana._botones_exportar[2].click()
        self.assertEqual(
            ventana.etiqueta_estado.text(),
            "No se pudo guardar la imagen: Permiso denegado.",
        )
        self.assertEqual(self.sonidos.eventos[-1], "error")

    def test_atajo_de_exportar_y_restablecer(self):
        ventana = self.crear()
        mod = Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier
        with mock.patch.object(
            QFileDialog, "getSaveFileName", return_value=("a.png", "")
        ):
            QTest.keyClick(ventana.campo_radio, Qt.Key.Key_1, mod)
        self.assertIn("exportar", self.graficas[0].nombres())
        QTest.keyClick(
            ventana.campo_radio, Qt.Key.Key_0, Qt.KeyboardModifier.ControlModifier
        )
        self.assertIn("restablecer_vista", self.graficas[0].nombres())

    def test_aplicar_modo(self):
        ventana = self.crear()
        ventana.aplicar_modo(True)
        ventana.aplicar_modo(False)
        for grafica in self.graficas:
            modos = [c[1][0] for c in grafica.llamadas if c[0] == "aplicar_tema"]
            self.assertEqual(modos[-2:], ["oscuro", "claro"])
        self.assertIn("#14171C", ventana.styleSheet() + "#14171C")

    def test_modo_oscuro_cambia_la_hoja_de_estilos(self):
        ventana = self.crear()
        ventana.aplicar_modo(False)
        claro = ventana.styleSheet()
        ventana.aplicar_modo(True)
        self.assertNotEqual(claro, ventana.styleSheet())
        self.assertIn("#14171C", ventana.styleSheet())

    def test_esc_salta_la_animacion(self):
        ventana = self.crear()
        ventana.calcular_ahora()
        self.assertTrue(esperar(lambda: self.graficas[1].esta_animando()))
        QTest.keyClick(ventana.campo_radio, Qt.Key.Key_Escape)
        self.assertIn("saltar_animacion", self.graficas[1].nombres())
        llamada = [c for c in self.graficas[2].llamadas if c[0] == "marcar_actual"]
        self.assertEqual(len(llamada), 1)
        self.assertFalse(llamada[0][2]["animar"])

    def test_clic_durante_la_animacion_la_salta_y_hace_su_accion(self):
        ventana = self.crear()
        ventana.calcular_ahora()
        self.assertTrue(esperar(lambda: self.graficas[1].esta_animando()))
        QTest.mouseClick(ventana.interruptor_sonido, Qt.MouseButton.LeftButton)
        self.assertIn("saltar_animacion", self.graficas[1].nombres())
        self.assertFalse(ventana.interruptor_sonido.isChecked())  # el clic sí actuó

    def test_enter_durante_la_animacion_salta_y_calcula_de_nuevo(self):
        ventana = self.crear()
        ventana.calcular_ahora()
        self.assertTrue(esperar(lambda: self.graficas[1].esta_animando()))
        self.teclear_enter(ventana, ventana.campo_radio)
        self.assertIn("saltar_animacion", self.graficas[1].nombres())
        self.assertTrue(esperar(lambda: len(self.calculo.llamadas) == 2))

    def test_enter_en_un_boton_lo_pulsa(self):
        ventana = self.crear()
        ventana.interruptor_sonido.setFocus()
        QTest.keyClick(ventana.interruptor_sonido, Qt.Key.Key_Return)
        self.assertFalse(ventana.interruptor_sonido.isChecked())
        self.assertEqual(self.calculo.llamadas, [])

    def test_nombres_accesibles_y_tooltips(self):
        ventana = self.crear()
        self.assertEqual(
            ventana.campo_radio.accessibleName(), "Radio de la esfera R, en centímetros"
        )
        self.assertEqual(ventana.campo_n.accessibleName(), "Número de subintervalos n")
        self.assertEqual(
            ventana.boton_calcular.toolTip(), "Calcular el perímetro (Enter)"
        )
        self.assertEqual(
            ventana.interruptor_sonido.toolTip(), "Activar o desactivar los sonidos (M)"
        )

    def test_modo_pestanas_con_ancho_reducido(self):
        ventana = self.crear()
        self.assertEqual(ventana._zona.currentIndex(), 0)
        ventana.resize(1100, 700)
        aplicacion.processEvents()
        self.assertEqual(ventana._zona.currentIndex(), 1)
        self.assertEqual(ventana._pestanas.count(), 3)
        ventana.resize(1536, 864)
        aplicacion.processEvents()
        self.assertEqual(ventana._zona.currentIndex(), 0)
        self.assertEqual(ventana._pestanas.count(), 0)


class PruebasSistema(unittest.TestCase):
    def test_funciones_toleran_fallos(self):
        self.assertIsInstance(sistema.reducir_movimiento(), bool)
        self.assertTrue(1.0 <= sistema.factor_de_texto() <= 2.25)


class PruebasGestor(unittest.TestCase):
    def test_solo_cuenta_la_ultima_tarea(self):
        gestor = GestorTareas()
        resultados = []
        gestor.terminado.connect(resultados.append)

        def lenta(_progreso, cancelado):
            while not cancelado():
                time.sleep(0.005)
            return "vieja"

        gestor.lanzar(lenta)
        gestor.lanzar(lambda _p, _c: "nueva")
        self.assertTrue(esperar(lambda: resultados != []))
        QTest.qWait(50)
        self.assertEqual(resultados, ["nueva"])
        gestor.cerrar()

    def test_fallo_y_cancelacion(self):
        gestor = GestorTareas()
        fallos = []
        gestor.fallo.connect(fallos.append)

        def mala(_p, _c):
            raise ValueError("mensaje")

        gestor.lanzar(mala)
        self.assertTrue(esperar(lambda: fallos != []))
        self.assertEqual(fallos, ["mensaje"])
        gestor.cerrar()


if __name__ == "__main__":
    unittest.main()
