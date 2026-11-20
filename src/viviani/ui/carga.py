"""Pantalla de carga: aparece en cuanto se abre el programa.

Cargar numpy y matplotlib tarda uno o dos segundos. En vez de dejar la
pantalla vacía, se muestra esta tarjeta con el logo girando, una barra que
avanza y el paso actual ("Preparando las gráficas…").

Solo usa Qt y el logo (nada pesado), para poder mostrarse de inmediato.
"""

import math

from PySide6.QtCore import QElapsedTimer, QPointF, QRectF, Qt, QTimer, QVariantAnimation
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
from viviani.ui.logo import dibujar_logo

ANCHO, ALTO = 460, 300
DURACION_FUNDIDO_MS = 220


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
        self._fraccion = 0.0  # avance de la barra (0 a 1)
        self._texto = "Iniciando…"
        self._reloj = QElapsedTimer()
        self._reloj.start()
        # El logo gira mientras el programa tenga tiempo de repintar
        self._tic = QTimer(self)
        self._tic.setInterval(16)
        self._tic.timeout.connect(self.update)
        self._tic.start()

        pantalla = QApplication.primaryScreen().availableGeometry()
        self.move(pantalla.center() - self.rect().center())

    def avanzar(self, fraccion, texto):
        """Mueve la barra y cambia el texto; deja que la pantalla se repinte."""
        self._fraccion = fraccion
        self._texto = texto
        self.repaint()
        QApplication.processEvents()

    def terminar(self):
        """Se desvanece y se cierra."""
        self._tic.stop()
        fundido = QVariantAnimation(self)
        fundido.setDuration(DURACION_FUNDIDO_MS)
        fundido.setStartValue(1.0)
        fundido.setEndValue(0.0)
        fundido.valueChanged.connect(lambda v: self.setWindowOpacity(float(v)))
        fundido.finished.connect(self.close)
        fundido.start()

    def paintEvent(self, _evento):
        c = self.colores
        pintor = QPainter(self)
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing)
        caja = QRectF(self.rect()).adjusted(8, 8, -8, -8)

        # Tarjeta oscura con una aurora cian arriba
        fondo = QLinearGradient(caja.topLeft(), caja.bottomLeft())
        fondo.setColorAt(0, QColor(c["fondo_2"]))
        fondo.setColorAt(1, QColor(c["fondo"]))
        borde = QColor(c["acento"])
        borde.setAlphaF(0.35)
        pintor.setPen(QPen(borde, 1))
        pintor.setBrush(fondo)
        pintor.drawRoundedRect(caja, 24, 24)
        aurora = QRadialGradient(
            QPointF(caja.center().x(), caja.top()), 0.7 * caja.width()
        )
        tono = QColor(c["acento"])
        tono.setAlphaF(0.16)
        aurora.setColorAt(0, tono)
        tono.setAlphaF(0.0)
        aurora.setColorAt(1, tono)
        pintor.setPen(Qt.PenStyle.NoPen)
        pintor.setBrush(aurora)
        pintor.drawRoundedRect(caja, 24, 24)

        # Logo girando (una vuelta cada 4 s)
        giro = 2 * math.pi * self._reloj.elapsed() / 4000
        lado = 104
        dibujar_logo(
            pintor,
            QRectF(caja.center().x() - lado / 2, caja.top() + 30, lado, lado),
            giro=giro,
            con_fondo=False,
        )

        # Título y paso actual
        titulo = QFont()
        titulo.setFamilies(tema.FAMILIAS_TITULO)
        titulo.setPointSizeF(19)
        pintor.setFont(titulo)
        pintor.setPen(QColor(c["texto"]))
        pintor.drawText(
            QRectF(caja.left(), caja.top() + 146, caja.width(), 34),
            Qt.AlignmentFlag.AlignCenter,
            "Ventana de Viviani",
        )
        paso = QFont()
        paso.setFamilies(tema.FAMILIAS_MONO)
        paso.setPointSizeF(8.5)
        paso.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.5)
        pintor.setFont(paso)
        pintor.setPen(QColor(c["etiqueta"]))
        pintor.drawText(
            QRectF(caja.left(), caja.top() + 214, caja.width(), 20),
            Qt.AlignmentFlag.AlignCenter,
            self._texto,
        )

        # Barra de avance con degradado cian-violeta
        x0, y = caja.left() + 70, caja.top() + 196
        largo = caja.width() - 140
        pintor.setPen(
            QPen(QColor(c["borde"]), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        )
        pintor.drawLine(QPointF(x0, y), QPointF(x0 + largo, y))
        if self._fraccion > 0:
            degradado = QLinearGradient(x0, 0, x0 + largo, 0)
            degradado.setColorAt(0, QColor(c["acento"]))
            degradado.setColorAt(1, QColor(c["violeta"]))
            pintor.setPen(
                QPen(degradado, 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            )
            pintor.drawLine(QPointF(x0, y), QPointF(x0 + largo * self._fraccion, y))
