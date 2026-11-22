"""Panel de créditos: aparece sobre la ventana al pulsar "Créditos".

Es una tarjeta sólida en el centro de la ventana, con el logo, los
integrantes y la profesora. Se cierra con Esc, con el botón "Cerrar" o
haciendo clic fuera de la tarjeta (por eso hay una capa invisible del tamaño
de la ventana que solo recibe ese clic: no pinta nada).

Pensado para no trabar la animación de la esfera:
  - no se oscurece ni se desenfoca la ventana: solo se pinta la tarjeta;
  - el contenido va en un "cuerpo" opaco: si algo de adentro se repinta
    (el foco del botón, por ejemplo), Qt no redibuja lo que hay debajo;
  - al abrir y cerrar, la tarjeta se anima como una sola imagen (aparece y
    crece del 96 % al 100 %): cada cuadro pinta solo ese rectángulo.
"""

from PySide6.QtCore import QPoint, QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPixmap, QRegion
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from viviani import tema
from viviani.animacion import Animacion, salida_suave
from viviani.tema import con_alfa
from viviani.ui.componentes import Separador, etiqueta_pequena, fuente
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
ANCHO_TARJETA, ALTO_TARJETA = 400, 470
RADIO = 24  # radio de las esquinas
MARGEN_CUERPO = 14  # el cuerpo opaco queda dentro de las esquinas redondeadas


class _Logo(QWidget):
    """El logo de la app, quieto."""

    def __init__(self):
        super().__init__()
        self.setFixedSize(72, 72)

    def paintEvent(self, _evento):
        dibujar_logo(QPainter(self), QRectF(self.rect()))


class _Cuerpo(QWidget):
    """El interior de la tarjeta: un rectángulo opaco del color de la tarjeta.

    Al ser opaco, cuando algo de adentro se repinta, Qt no necesita volver a
    pintar la escena 3D que hay debajo.
    """

    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)

    def paintEvent(self, evento):
        QPainter(self).fillRect(evento.rect(), QColor(tema.paleta()["superficie"]))


class _Tarjeta(QWidget):
    """La tarjeta: esquinas redondeadas y borde; adentro, el cuerpo opaco.

    Durante el fundido (`foto` no es None) se pinta como una sola imagen con
    la opacidad y el tamaño de `nivel` (0 = invisible, 1 = normal).
    """

    def __init__(self):
        super().__init__()
        self.setFixedSize(ANCHO_TARJETA, ALTO_TARJETA)
        self.nivel = 0.0
        self.foto = None
        self.cuerpo = _Cuerpo()
        marco = QVBoxLayout(self)
        marco.setContentsMargins(*[MARGEN_CUERPO] * 4)
        marco.addWidget(self.cuerpo)

    def fotografiar(self):
        """La tarjeta completa (borde y contenido) como una imagen."""
        self.layout().activate()
        proporcion = self.devicePixelRatioF()
        foto = QPixmap(self.size() * proporcion)
        foto.setDevicePixelRatio(proporcion)
        foto.fill(Qt.GlobalColor.transparent)
        pintor = QPainter(foto)
        self._dibujar_fondo(pintor)
        pintor.end()
        self.cuerpo.render(
            foto, QPoint(MARGEN_CUERPO, MARGEN_CUERPO), QRegion(),
            QWidget.RenderFlag.DrawChildren,
        )  # fmt: skip
        return foto

    def paintEvent(self, _evento):
        pintor = QPainter(self)
        if self.foto is None:
            self._dibujar_fondo(pintor)
            return
        # Fundido: la foto entera, más transparente y más chica al principio
        pintor.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        centro = QRectF(self.rect()).center()
        escala = 0.96 + 0.04 * self.nivel
        pintor.setOpacity(self.nivel)
        pintor.translate(centro)
        pintor.scale(escala, escala)
        pintor.translate(-centro)
        pintor.drawPixmap(0, 0, self.foto)

    def _dibujar_fondo(self, pintor):
        """Superficie sólida con un borde fino y un brillo en el canto de arriba."""
        c = tema.paleta()
        caja = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing)
        pintor.setPen(QPen(QColor(c["borde"]), 1))
        pintor.setBrush(QColor(c["superficie"]))
        pintor.drawRoundedRect(caja, RADIO, RADIO)
        pintor.setPen(QPen(con_alfa(c["texto"], 0.2), 1))
        pintor.drawLine(QPointF(caja.left() + RADIO, caja.top() + 0.5),
                        QPointF(caja.right() - RADIO, caja.top() + 0.5))  # fmt: skip


def _nombre(texto, puntos=13):
    rotulo = QLabel(texto)
    rotulo.setFont(fuente(tema.FAMILIAS_INTERFAZ, puntos))
    rotulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return rotulo


class PanelCreditos(QWidget):
    """Capa invisible sobre toda la ventana con la tarjeta en el centro."""

    def __init__(self, padre, sonidos):
        super().__init__(padre)
        self._sonidos = sonidos
        self.hide()
        self.tarjeta = _Tarjeta()
        self.tarjeta.setParent(self)
        self._construir_cuerpo(self.tarjeta.cuerpo)
        self._desde = self._hasta = 0.0
        self._fundido = Animacion(self, self._al_fundir, self._al_terminar_fundido)

    def _construir_cuerpo(self, cuerpo):
        diseno = QVBoxLayout(cuerpo)
        diseno.setContentsMargins(26, 18, 26, 12)
        diseno.setSpacing(6)
        centrado = Qt.AlignmentFlag.AlignHCenter
        diseno.addWidget(_Logo(), 0, centrado)
        diseno.addSpacing(4)
        titulo = _nombre("Ventana de Viviani")
        titulo.setFont(fuente(tema.FAMILIAS_TITULO, 19, QFont.Weight.Light))
        diseno.addWidget(titulo)
        diseno.addSpacing(10)
        diseno.addWidget(Separador())
        diseno.addSpacing(8)

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
        self.boton_cerrar.clicked.connect(self._sonidos.clic)
        self.boton_cerrar.clicked.connect(self.cerrar)
        diseno.addWidget(self.boton_cerrar, 0, centrado)

    # --- abrir y cerrar ---------------------------------------------------
    def abrir(self):
        self.setGeometry(self.parentWidget().rect())
        self._centrar_tarjeta()
        self.show()
        self.raise_()
        self._sonidos.creditos()
        self._fundir(0.0, 1.0)

    def cerrar(self):
        if self.isVisible() and self._hasta > 0:
            self._fundir(1.0, 0.0)

    def _fundir(self, desde, hasta):
        """Durante el fundido la tarjeta es una foto: se aclara y agranda
        entera de una vez, sin repintar cada etiqueta."""
        tarjeta = self.tarjeta
        tarjeta.cuerpo.show()  # para fotografiarla tiene que estar armada
        tarjeta.cuerpo.layout().activate()
        tarjeta.foto = tarjeta.fotografiar()
        tarjeta.cuerpo.hide()
        tarjeta.nivel = desde
        self._desde, self._hasta = desde, hasta
        self._fundido.cancelar()
        self._fundido.iniciar(DURACION_FUNDIDO_MS)

    def _al_fundir(self, ms):
        avance = salida_suave(ms / DURACION_FUNDIDO_MS)
        self.tarjeta.nivel = self._desde + (self._hasta - self._desde) * avance
        self.tarjeta.update()

    def _al_terminar_fundido(self):
        self.tarjeta.foto = None
        if self._hasta < 0.01:
            self.hide()
            return
        self.tarjeta.cuerpo.show()
        self.tarjeta.update()
        self.boton_cerrar.setFocus()

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
