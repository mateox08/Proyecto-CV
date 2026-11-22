"""Pantalla de carga: aparece en cuanto se abre el programa.

Cargar numpy y armar la ventana tarda un momento. En vez de dejar la
pantalla vacía, se muestra esta tarjeta donde la propia curva de Viviani hace
de barra de progreso: se va trazando de t = 0 a t = 2π a medida que avanza
la carga, mientras gira despacio.

Solo usa Qt y el logo (nada pesado), para poder mostrarse de inmediato.
"""

import math

from PySide6.QtCore import QElapsedTimer, QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import (
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPen,
    QRadialGradient,
)
from PySide6.QtWidgets import QApplication, QWidget

from viviani import tema
from viviani.animacion import Animacion, salida_suave
from viviani.ui.logo import dibujar_logo

ANCHO, ALTO = 460, 320
DURACION_CIERRE_MS = 650  # termina de trazar la curva (400 ms) y se desvanece
SEGUIMIENTO = 0.18  # qué tanto se acerca el trazo al avance real en cada cuadro


class PantallaCarga(QWidget):
    def __init__(self):
        super().__init__(
            None,
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.SplashScreen
            | Qt.WindowType.WindowStaysOnTopHint,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowTitle("Cargando…")
        self.setFixedSize(ANCHO, ALTO)
        self.colores = tema.paleta()
        self._fraccion = 0.0  # avance real de la carga (0 a 1)
        self._trazo = 0.0  # parte de la curva ya dibujada (persigue al avance)
        self._texto = "Iniciando…"
        self._trazo_al_cerrar = 0.0
        self._reloj = QElapsedTimer()
        self._reloj.start()
        # La curva gira mientras el programa tenga tiempo de repintar
        self._tic = QTimer(self)
        self._tic.setInterval(16)
        self._tic.timeout.connect(self._avanzar_trazo)
        self._tic.start()
        self._cierre = Animacion(self, self._al_cerrar, self.close)

        pantalla = QApplication.primaryScreen().availableGeometry()
        self.move(pantalla.center() - self.rect().center())

    def avanzar(self, fraccion, texto):
        """Mueve el avance y cambia el texto; deja que la pantalla se repinte."""
        self._fraccion = fraccion
        self._texto = texto
        self._avanzar_trazo()
        self.repaint()
        QApplication.processEvents()

    def terminar(self):
        """Completa la curva, se desvanece y se cierra."""
        self._tic.stop()
        self._trazo_al_cerrar = self._trazo
        self._cierre.iniciar(DURACION_CIERRE_MS)

    def _avanzar_trazo(self):
        self._trazo += (self._fraccion - self._trazo) * SEGUIMIENTO
        self.update()

    def _al_cerrar(self, ms):
        completar = salida_suave(ms / 400)
        self._trazo = self._trazo_al_cerrar + (1 - self._trazo_al_cerrar) * completar
        self.setWindowOpacity(1 - salida_suave((ms - 400) / 250))
        self.update()

    def paintEvent(self, _evento):
        c = self.colores
        pintor = QPainter(self)
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing)
        caja = QRectF(self.rect()).adjusted(8, 8, -8, -8)

        # Tarjeta oscura con un resplandor del segundo acento arriba
        fondo = QLinearGradient(caja.topLeft(), caja.bottomLeft())
        fondo.setColorAt(0, QColor(c["fondo_2"]))
        fondo.setColorAt(1, QColor(c["fondo"]))
        borde = QColor(c["acento"])
        borde.setAlphaF(0.30)
        pintor.setPen(QPen(borde, 1))
        pintor.setBrush(fondo)
        pintor.drawRoundedRect(caja, 24, 24)
        aurora = QRadialGradient(
            QPointF(caja.center().x(), caja.top()), 0.7 * caja.width()
        )
        tono = QColor(c["acento_2"])
        tono.setAlphaF(0.16)
        aurora.setColorAt(0, tono)
        tono.setAlphaF(0.0)
        aurora.setColorAt(1, tono)
        pintor.setPen(Qt.PenStyle.NoPen)
        pintor.setBrush(aurora)
        pintor.drawRoundedRect(caja, 24, 24)

        # La curva se traza con el avance y gira (una vuelta cada 5 s)
        giro = 2 * math.pi * self._reloj.elapsed() / 5000
        lado = 138
        dibujar_logo(
            pintor,
            QRectF(caja.center().x() - lado / 2, caja.top() + 22, lado, lado),
            giro=giro,
            con_fondo=False,
            fraccion=max(self._trazo, 0.002),
        )

        # Título, paso actual y porcentaje
        titulo = QFont()
        titulo.setFamilies(tema.FAMILIAS_TITULO)
        titulo.setPointSizeF(19)
        titulo.setWeight(QFont.Weight.Light)
        pintor.setFont(titulo)
        pintor.setPen(QColor(c["texto"]))
        pintor.drawText(
            QRectF(caja.left(), caja.top() + 172, caja.width(), 36),
            Qt.AlignmentFlag.AlignCenter,
            "Ventana de Viviani",
        )
        paso = QFont()
        paso.setFamilies(tema.FAMILIAS_MONO)
        paso.setPointSizeF(8.5)
        paso.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.2)
        pintor.setFont(paso)
        pintor.setPen(QColor(c["etiqueta"]))
        pintor.drawText(
            QRectF(caja.left(), caja.top() + 222, caja.width(), 20),
            Qt.AlignmentFlag.AlignCenter,
            self._texto,
        )
        pintor.setPen(QColor(c["acento"]))
        pintor.drawText(
            QRectF(caja.left(), caja.top() + 246, caja.width(), 20),
            Qt.AlignmentFlag.AlignCenter,
            f"t = {2 * self._trazo:.2f}π",
        )
