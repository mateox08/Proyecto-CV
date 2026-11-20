"""Panel de créditos: aparece sobre la ventana al pulsar "Créditos".

Efecto "vidrio líquido": la tarjeta deja ver lo que hay detrás, pero
desenfocado, con un borde luminoso y un reflejo en la parte de arriba.
El desenfoque se consigue de forma muy simple: se dibuja en una imagen lo
que hay detrás de la tarjeta (el fondo y la esfera), se achica mucho (pierde
detalle) y se vuelve a agrandar suavizada.

Esa imagen se rehace ~20 veces por segundo mientras el panel está abierto,
así a través del vidrio se ve la curva girando. Es barato: solo se dibuja el
pedazo que queda detrás de la tarjeta, no toda la ventana.

Se cierra con Esc, con el botón "Cerrar" o haciendo clic fuera de la
tarjeta. Aparece y desaparece con un fundido corto.
"""

from PySide6.QtCore import QPoint, QPointF, QRect, QRectF, Qt, QTimer, QVariantAnimation
from PySide6.QtGui import (
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QRegion,
)
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
INTERVALO_VIVO_MS = 50  # cada cuánto se rehace el fondo del vidrio (20 por s)
ESCALA_FOTO = 6  # el recorte se dibuja a 1/6 de su tamaño


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

    def __init__(self, padre, escena):
        """padre: el fondo de la ventana; escena: la gráfica 3D (detrás)."""
        super().__init__(padre)
        self.colores = tema.paleta()
        self._escena = escena
        self._borroso = None  # lo que hay detrás de la tarjeta, desenfocado
        self.hide()
        self._vivo = QTimer(self)
        self._vivo.setInterval(INTERVALO_VIVO_MS)
        self._vivo.timeout.connect(self._refrescar_vidrio)

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

        # Fundido: un efecto de opacidad sobre todo el panel. Solo se activa
        # mientras dura el fundido (con él activo, cada repintado costaría más).
        self._opacidad = QGraphicsOpacityEffect(self)
        self._opacidad.setEnabled(False)
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
        self._borroso = self._fotografiar_detras()
        self.show()
        self.raise_()
        self._fundir(0.0, 1.0)
        self._vivo.start()
        self.boton_cerrar.setFocus()

    def cerrar(self):
        if self.isVisible():
            self._fundir(1.0, 0.0)

    def _refrescar_vidrio(self):
        self._borroso = self._fotografiar_detras()
        self.update(self.tarjeta.geometry())

    def _fotografiar_detras(self):
        """Dibuja en una imagen el fondo y la esfera que quedan detrás de la
        tarjeta, y la devuelve desenfocada."""
        caja = self.tarjeta.geometry()
        # Se dibuja directamente en pequeño (1/6 del tamaño): de todas formas
        # se va a desenfocar, y así cuesta muchísimo menos.
        foto = QPixmap(
            caja.width() // ESCALA_FOTO + 1, caja.height() // ESCALA_FOTO + 1
        )
        foto.fill(QColor(self.colores["fondo"]))
        pintor = QPainter(foto)
        pintor.scale(1 / ESCALA_FOTO, 1 / ESCALA_FOTO)
        fondo = getattr(self.parentWidget(), "_imagen", None)
        if fondo is not None:
            pintor.drawPixmap(QRect(QPoint(0, 0), caja.size()), fondo, caja)
        # La gráfica 3D ocupa todo el fondo: misma posición que la tarjeta
        self._escena.render(pintor, QPoint(0, 0), QRegion(caja))
        pintor.end()
        return self._desenfocar(foto, caja.size())

    def _desenfocar(self, foto, tamano):
        """Achica más la foto y la agranda suavizada hasta `tamano`.

        Se agranda en dos pasos para que no se noten "cuadritos".
        """
        suave = Qt.TransformationMode.SmoothTransformation
        libre = Qt.AspectRatioMode.IgnoreAspectRatio
        reduccion = REDUCCION_DESENFOQUE // ESCALA_FOTO
        foto = foto.scaled(
            max(1, foto.width() // reduccion), max(1, foto.height() // reduccion),
            libre, suave,
        )  # fmt: skip
        foto = foto.scaled(tamano.width() // 4, tamano.height() // 4, libre, suave)
        proporcion = self.devicePixelRatioF()
        foto = foto.scaled(
            round(tamano.width() * proporcion), round(tamano.height() * proporcion),
            libre, suave,
        )  # fmt: skip
        foto.setDevicePixelRatio(proporcion)
        return foto

    def _fundir(self, desde, hasta):
        self._opacidad.setEnabled(True)
        self._fundido.stop()
        self._fundido.setStartValue(desde)
        self._fundido.setEndValue(hasta)
        self._fundido.start()

    def _al_terminar_fundido(self):
        if self._opacidad.opacity() < 0.01:
            self._vivo.stop()
            self.hide()
        self._opacidad.setEnabled(False)

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
            pintor.drawPixmap(caja.topLeft(), self._borroso)
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
