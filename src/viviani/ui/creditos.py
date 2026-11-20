"""Panel de créditos: aparece sobre la ventana al pulsar "Créditos".

Se cierra con Esc, con el botón "Cerrar" o haciendo clic fuera de la
tarjeta. Aparece y desaparece con un fundido corto.

Para completar los nombres, edite las listas de abajo.
"""

from PySide6.QtCore import QRectF, Qt, QVariantAnimation
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QGraphicsOpacityEffect,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from viviani import tema
from viviani.ui.componentes import Separador, con_alfa, etiqueta_pequena, fuente
from viviani.ui.logo import dibujar_logo

# --- Datos que el grupo debe completar ------------------------------------
INTEGRANTES = [
    "(Integrante 1)",
    "(Integrante 2)",
    "(Integrante 3)",
    "(Integrante 4)",
]
PROFESOR = "(Nombre del profesor)"
CURSO = "Cálculo Vectorial (MATG1046) · ESPOL · PAO II 2026"
HERRAMIENTAS = "Python · PySide6 · numpy · matplotlib · iconos Lucide (ISC)"

DURACION_FUNDIDO_MS = 200
ANCHO_TARJETA, ALTO_TARJETA = 460, 520


class _Logo(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(72, 72)

    def paintEvent(self, _evento):
        dibujar_logo(QPainter(self), QRectF(self.rect()))


class PanelCreditos(QWidget):
    """Capa oscura sobre toda la ventana con una tarjeta en el centro."""

    def __init__(self, padre):
        super().__init__(padre)
        self.colores = tema.paleta()
        self.hide()

        self.tarjeta = QWidget(self)
        self.tarjeta.setFixedSize(ANCHO_TARJETA, ALTO_TARJETA)
        diseno = QVBoxLayout(self.tarjeta)
        diseno.setContentsMargins(40, 34, 40, 30)
        diseno.setSpacing(6)
        diseno.addWidget(_Logo(), 0, Qt.AlignmentFlag.AlignHCenter)
        titulo = QLabel("Ventana de Viviani")
        titulo.setFont(fuente(tema.FAMILIAS_TITULO, 20))
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        diseno.addWidget(titulo)
        curso = QLabel(CURSO)
        curso.setProperty("rol", "etiqueta")
        curso.setAlignment(Qt.AlignmentFlag.AlignCenter)
        curso.setWordWrap(True)
        diseno.addWidget(curso)
        diseno.addSpacing(8)
        diseno.addWidget(Separador())
        diseno.addSpacing(8)

        diseno.addWidget(
            etiqueta_pequena("Integrantes"), 0, Qt.AlignmentFlag.AlignHCenter
        )
        for nombre in INTEGRANTES:
            rotulo = QLabel(nombre)
            rotulo.setFont(fuente(tema.FAMILIAS_TITULO, 12.5))
            rotulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            diseno.addWidget(rotulo)
        diseno.addSpacing(10)
        diseno.addWidget(etiqueta_pequena("Profesor"), 0, Qt.AlignmentFlag.AlignHCenter)
        profesor = QLabel(PROFESOR)
        profesor.setFont(fuente(tema.FAMILIAS_TITULO, 12.5))
        profesor.setAlignment(Qt.AlignmentFlag.AlignCenter)
        diseno.addWidget(profesor)
        diseno.addStretch(1)
        herramientas = QLabel(HERRAMIENTAS)
        herramientas.setProperty("rol", "etiqueta")
        herramientas.setFont(fuente(tema.FAMILIAS_MONO, 8))
        herramientas.setAlignment(Qt.AlignmentFlag.AlignCenter)
        diseno.addWidget(herramientas)
        diseno.addSpacing(10)
        self.boton_cerrar = QPushButton("Cerrar")
        self.boton_cerrar.setObjectName("fantasma")
        self.boton_cerrar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.boton_cerrar.clicked.connect(self.cerrar)
        diseno.addWidget(self.boton_cerrar, 0, Qt.AlignmentFlag.AlignHCenter)

        # Fundido: un efecto de opacidad sobre todo el panel
        self._opacidad = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacidad)
        self._fundido = QVariantAnimation(self)
        self._fundido.setDuration(DURACION_FUNDIDO_MS)
        self._fundido.valueChanged.connect(
            lambda v: self._opacidad.setOpacity(float(v))
        )
        self._fundido.finished.connect(self._al_terminar_fundido)

    # --- abrir y cerrar ---------------------------------------------------
    def abrir(self):
        self.setGeometry(self.parentWidget().rect())
        self._centrar_tarjeta()
        self.show()
        self.raise_()
        self._fundir(0.0, 1.0)
        self.boton_cerrar.setFocus()

    def cerrar(self):
        if self.isVisible():
            self._fundir(1.0, 0.0)

    def _fundir(self, desde, hasta):
        self._fundido.stop()
        self._fundido.setStartValue(desde)
        self._fundido.setEndValue(hasta)
        self._fundido.start()

    def _al_terminar_fundido(self):
        if self._opacidad.opacity() < 0.01:
            self.hide()

    def _centrar_tarjeta(self):
        self.tarjeta.move(
            (self.width() - ANCHO_TARJETA) // 2, (self.height() - ALTO_TARJETA) // 2
        )

    def resizeEvent(self, evento):
        self._centrar_tarjeta()
        super().resizeEvent(evento)

    def mousePressEvent(self, evento):
        # Clic fuera de la tarjeta: se cierra
        if not self.tarjeta.geometry().contains(evento.position().toPoint()):
            self.cerrar()

    def paintEvent(self, _evento):
        c = self.colores
        pintor = QPainter(self)
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing)
        pintor.fillRect(self.rect(), QColor(3, 6, 12, 190))  # velo oscuro
        caja = QRectF(self.tarjeta.geometry())
        pintor.setPen(QPen(con_alfa(c["acento"], 0.35), 1))
        pintor.setBrush(QColor(c["fondo_2"]))
        pintor.drawRoundedRect(caja, 24, 24)
