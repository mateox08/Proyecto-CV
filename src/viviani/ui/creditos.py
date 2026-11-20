"""Panel de créditos: aparece sobre la ventana al pulsar "Créditos".

Efecto "vidrio líquido": la tarjeta deja ver lo que hay detrás, pero
desenfocado, con un borde luminoso y un reflejo en la parte de arriba.
El desenfoque se consigue de forma muy simple: se toma una foto de la
ventana, se achica mucho (pierde detalle) y se vuelve a agrandar suavizada.

Se cierra con Esc, con el botón "Cerrar" o haciendo clic fuera de la
tarjeta. Aparece y desaparece con un fundido corto.
"""

from PySide6.QtCore import QPointF, QRectF, Qt, QVariantAnimation
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen
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

# --- Datos del grupo (orden alfabético por apellido) ----------------------
INTEGRANTES = [
    "Darlyn Acosta",
    "Juan Carrasco",
    "Juan Espinoza",
    "Mateo Saltos",
]
PROFESORA = "Dra. Soveny Solís"

DURACION_FUNDIDO_MS = 220
ANCHO_TARJETA, ALTO_TARJETA = 400, 440
RADIO = 28
REDUCCION_DESENFOQUE = 18  # cuánto se achica la foto: más = más borroso


class _Logo(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(64, 64)

    def paintEvent(self, _evento):
        pintor = QPainter(self)
        dibujar_logo(pintor, QRectF(self.rect()))


def _nombre(texto, puntos=13):
    rotulo = QLabel(texto)
    rotulo.setFont(fuente(tema.FAMILIAS_INTERFAZ, puntos))
    rotulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return rotulo


class PanelCreditos(QWidget):
    """Capa sobre toda la ventana con una tarjeta de vidrio en el centro."""

    def __init__(self, padre):
        super().__init__(padre)
        self.colores = tema.paleta()
        self._borroso = None  # foto desenfocada de la ventana
        self.hide()

        self.tarjeta = QWidget(self)
        self.tarjeta.setFixedSize(ANCHO_TARJETA, ALTO_TARJETA)
        diseno = QVBoxLayout(self.tarjeta)
        diseno.setContentsMargins(40, 34, 40, 28)
        diseno.setSpacing(6)
        diseno.addWidget(_Logo(), 0, Qt.AlignmentFlag.AlignHCenter)
        diseno.addSpacing(4)
        titulo = _nombre("Ventana de Viviani", 18)
        titulo.setFont(fuente(tema.FAMILIAS_TITULO, 18, QFont.Weight.Light))
        diseno.addWidget(titulo)
        diseno.addSpacing(10)
        diseno.addWidget(Separador())
        diseno.addSpacing(10)

        centrado = Qt.AlignmentFlag.AlignHCenter
        diseno.addWidget(etiqueta_pequena("Integrantes"), 0, centrado)
        for nombre in INTEGRANTES:
            diseno.addWidget(_nombre(nombre))
        diseno.addSpacing(14)
        diseno.addWidget(etiqueta_pequena("Profesora"), 0, centrado)
        diseno.addWidget(_nombre(PROFESORA))
        diseno.addStretch(1)

        self.boton_cerrar = QPushButton("Cerrar")
        self.boton_cerrar.setObjectName("enlace")
        self.boton_cerrar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.boton_cerrar.clicked.connect(self.cerrar)
        diseno.addWidget(self.boton_cerrar, 0, centrado)

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
        padre = self.parentWidget()
        self._borroso = self._desenfocar(padre.grab())
        self.setGeometry(padre.rect())
        self._centrar_tarjeta()
        self.show()
        self.raise_()
        self._fundir(0.0, 1.0)
        self.boton_cerrar.setFocus()

    def cerrar(self):
        if self.isVisible():
            self._fundir(1.0, 0.0)

    @staticmethod
    def _desenfocar(foto):
        """Achica la foto y la vuelve a agrandar suavizada: queda borrosa.

        Se hace en dos pasadas (una fuerte y otra suave) para que no se
        noten "cuadritos".
        """
        suave = Qt.TransformationMode.SmoothTransformation
        libre = Qt.AspectRatioMode.IgnoreAspectRatio
        for reduccion in (REDUCCION_DESENFOQUE, 4):
            pequena = foto.scaled(
                max(1, foto.width() // reduccion),
                max(1, foto.height() // reduccion),
                libre,
                suave,
            )
            foto = pequena.scaled(foto.size(), libre, suave)
        return foto

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

    # --- dibujo ---------------------------------------------------------
    def paintEvent(self, _evento):
        pintor = QPainter(self)
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing)
        pintor.fillRect(self.rect(), QColor(4, 5, 7, 150))  # velo oscuro

        caja = QRectF(self.tarjeta.geometry())
        forma = QPainterPath()
        forma.addRoundedRect(caja, RADIO, RADIO)

        # Sombra suave debajo de la tarjeta
        pintor.setPen(Qt.PenStyle.NoPen)
        for crecer, alfa in ((18, 0.10), (9, 0.16)):
            pintor.setBrush(QColor(0, 0, 0, round(255 * alfa)))
            pintor.drawRoundedRect(
                caja.adjusted(-crecer, -crecer + 10, crecer, crecer + 10),
                RADIO + crecer, RADIO + crecer,
            )  # fmt: skip

        # Cuerpo: el fondo desenfocado visto "a través" del vidrio
        pintor.save()
        pintor.setClipPath(forma)
        if self._borroso is not None:
            proporcion = self._borroso.devicePixelRatio()
            origen = QRectF(
                caja.x() * proporcion, caja.y() * proporcion,
                caja.width() * proporcion, caja.height() * proporcion,
            )  # fmt: skip
            pintor.drawPixmap(caja, self._borroso, origen)
        pintor.fillRect(caja, QColor(255, 255, 255, 18))  # vidrio apenas lechoso
        # Reflejo: un brillo que baja desde el borde de arriba
        reflejo = QLinearGradient(
            caja.topLeft(), QPointF(caja.left(), caja.top() + 160)
        )
        reflejo.setColorAt(0, QColor(255, 255, 255, 34))
        reflejo.setColorAt(1, QColor(255, 255, 255, 0))
        pintor.fillRect(caja, reflejo)
        pintor.restore()

        # Borde luminoso: más claro arriba a la izquierda, casi nada abajo
        borde = QLinearGradient(caja.topLeft(), caja.bottomRight())
        borde.setColorAt(0, QColor(255, 255, 255, 110))
        borde.setColorAt(0.5, QColor(255, 255, 255, 25))
        borde.setColorAt(1, con_alfa(self.colores["acento"], 0.25))
        pintor.setPen(QPen(borde, 1.2))
        pintor.setBrush(Qt.BrushStyle.NoBrush)
        pintor.drawRoundedRect(caja.adjusted(0.5, 0.5, -0.5, -0.5), RADIO, RADIO)
