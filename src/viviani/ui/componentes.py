"""Piezas visuales reutilizables de la ventana.

FondoVentana     fondo degradado con una rejilla tenue (se dibuja una vez)
Tarjeta          panel blanco con esquinas redondeadas que se ilumina
                 cuando el mouse pasa por encima
BotonBrillante   botón en forma de píldora que brilla más cuanto más
                 cerca está el cursor
CampoNumerico    etiqueta + caja de texto + mensaje de error
"""

import math

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, QVariantAnimation
from PySide6.QtGui import (
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QRadialGradient,
)
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from viviani import tema
from viviani.ui import iconos

DURACION_BRILLO_MS = 220  # encender/apagar el brillo de una tarjeta
DISTANCIA_BRILLO = 120  # px: desde aquí el botón empieza a brillar


def mezclar(color_a, color_b, proporcion):
    """Color intermedio entre a (proporcion 0) y b (proporcion 1)."""
    a, b = QColor(color_a), QColor(color_b)
    return QColor(
        round(a.red() + (b.red() - a.red()) * proporcion),
        round(a.green() + (b.green() - a.green()) * proporcion),
        round(a.blue() + (b.blue() - a.blue()) * proporcion),
    )


def con_alfa(color, alfa):
    tono = QColor(color)
    tono.setAlphaF(max(0.0, min(1.0, alfa)))
    return tono


def fuente(familias, puntos, peso=QFont.Weight.Normal, espaciado=0.0):
    """Crea una fuente. `espaciado` separa las letras (en píxeles)."""
    resultado = QFont()
    resultado.setFamilies(familias)
    resultado.setPointSizeF(puntos)
    resultado.setWeight(peso)
    if espaciado:
        resultado.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, espaciado)
    return resultado


def etiqueta_pequena(texto):
    """Etiqueta en mayúsculas, monoespaciada y con letras separadas."""
    rotulo = QLabel(texto.upper())
    rotulo.setFont(fuente(tema.FAMILIAS_MONO, 8.5, espaciado=1.8))
    rotulo.setProperty("rol", "etiqueta")
    return rotulo


# ---------------------------------------------------------------------------
# Fondo
# ---------------------------------------------------------------------------
class FondoVentana(QWidget):
    """Fondo de toda la ventana. Se dibuja una sola vez por tamaño y se
    guarda como imagen, así redibujarlo no cuesta casi nada."""

    LADO_REJILLA = 36
    RADIO_LUZ = 200  # px: tamaño del círculo de luz que sigue al cursor

    def __init__(self, colores):
        super().__init__()
        self.colores = colores
        self._imagen = None
        self._luz = None  # posición del cursor (None si está fuera)

    def mover_luz(self, posicion):
        """Mueve la luz al punto `posicion` (coordenadas de este widget).

        Solo se repintan dos círculos: donde estaba la luz y donde está
        ahora. Así el costo no depende del tamaño de la ventana.
        """
        if posicion is not None and not self.rect().contains(posicion):
            posicion = None
        anterior = self._luz
        if posicion == anterior:
            return
        self._luz = posicion
        for punto in (anterior, posicion):
            if punto is not None:
                r = self.RADIO_LUZ
                self.update(punto.x() - r, punto.y() - r, 2 * r, 2 * r)

    def resizeEvent(self, evento):
        self._imagen = None  # cambió el tamaño: hay que volver a dibujarlo
        super().resizeEvent(evento)

    def paintEvent(self, evento):
        if self._imagen is None or self._imagen.size() != self.size():
            self._imagen = self._dibujar_fondo()
        pintor = QPainter(self)
        pintor.drawPixmap(evento.rect(), self._imagen, evento.rect())
        if self._luz is not None:
            self._dibujar_luz(pintor)

    def _dibujar_luz(self, pintor):
        """Un resplandor suave y la rejilla más marcada cerca del cursor."""
        c = self.colores
        centro = QPointF(self._luz)
        r = self.RADIO_LUZ
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing)

        resplandor = QRadialGradient(centro, r)
        resplandor.setColorAt(0, con_alfa("#FFFFFF", 0.55))
        resplandor.setColorAt(0.5, con_alfa(c["brillo"], 0.10))
        resplandor.setColorAt(1, con_alfa(c["brillo"], 0.0))
        pintor.setPen(Qt.PenStyle.NoPen)
        pintor.setBrush(resplandor)
        pintor.drawEllipse(centro, r, r)

        # Las líneas de la rejilla se encienden: el color de la pluma es un
        # degradado que se apaga con la distancia al cursor
        lineas = QRadialGradient(centro, r * 0.8)
        lineas.setColorAt(0, con_alfa(c["brillo"], 0.55))
        lineas.setColorAt(1, con_alfa(c["brillo"], 0.0))
        pintor.setPen(QPen(lineas, 1))
        lado = self.LADO_REJILLA
        x0, y0 = int(centro.x() - r), int(centro.y() - r)
        for x in range(max(0, x0 - x0 % lado), int(centro.x() + r), lado):
            pintor.drawLine(x, y0, x, y0 + 2 * r)
        for y in range(max(0, y0 - y0 % lado), int(centro.y() + r), lado):
            pintor.drawLine(x0, y, x0 + 2 * r, y)

    def _dibujar_fondo(self):
        c = self.colores
        ancho, alto = self.width(), self.height()
        imagen = QPixmap(self.size())
        pintor = QPainter(imagen)
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing)

        degradado = QLinearGradient(0, 0, 0, alto)
        degradado.setColorAt(0, QColor(c["fondo"]))
        degradado.setColorAt(1, QColor(c["fondo_2"]))
        pintor.fillRect(imagen.rect(), degradado)

        # Dos manchas de luz muy suaves (azul arriba a la izquierda,
        # turquesa abajo a la derecha)
        for x, y, radio, nombre in (
            (0.15, 0.10, 0.55, "brillo"),
            (0.90, 0.95, 0.50, "serie_turquesa"),
        ):
            centro = QPointF(x * ancho, y * alto)
            mancha = QRadialGradient(centro, radio * max(ancho, alto))
            mancha.setColorAt(0, con_alfa(c[nombre], 0.16))
            mancha.setColorAt(1, con_alfa(c[nombre], 0.0))
            pintor.fillRect(imagen.rect(), mancha)

        # Rejilla tenue, como una hoja cuadriculada
        pintor.setPen(QPen(con_alfa(c["rejilla"], 0.55), 1))
        for x in range(0, ancho, self.LADO_REJILLA):
            pintor.drawLine(x, 0, x, alto)
        for y in range(0, alto, self.LADO_REJILLA):
            pintor.drawLine(0, y, ancho, y)
        pintor.end()
        return imagen


# ---------------------------------------------------------------------------
# Tarjeta
# ---------------------------------------------------------------------------
class Tarjeta(QFrame):
    """Panel blanco redondeado. Al pasar el mouse, su borde se ilumina."""

    MARGEN_BRILLO = 10  # espacio alrededor del panel para dibujar el halo

    def __init__(self, colores, titulo=None):
        super().__init__()
        self.colores = colores
        self._luz = 0.0  # 0 = apagada, 1 = iluminada
        self._animacion = QVariantAnimation(self)
        self._animacion.setDuration(DURACION_BRILLO_MS)
        self._animacion.valueChanged.connect(self._al_cambiar_luz)

        m = self.MARGEN_BRILLO
        self.contenido = QVBoxLayout(self)
        self.contenido.setContentsMargins(m + 22, m + 18, m + 22, m + 20)
        self.contenido.setSpacing(10)

        self.cabecera = QHBoxLayout()
        self.cabecera.setSpacing(8)
        if titulo:
            self.cabecera.addWidget(etiqueta_pequena(titulo))
        self.cabecera.addStretch(1)
        self.contenido.addLayout(self.cabecera)

    def enterEvent(self, evento):
        self._encender(1.0)
        super().enterEvent(evento)

    def leaveEvent(self, evento):
        self._encender(0.0)
        super().leaveEvent(evento)

    def _encender(self, destino):
        self._animacion.stop()
        self._animacion.setStartValue(self._luz)
        self._animacion.setEndValue(destino)
        self._animacion.start()

    def _al_cambiar_luz(self, valor):
        self._luz = float(valor)
        self.update()

    def paintEvent(self, _evento):
        c = self.colores
        pintor = QPainter(self)
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing)
        panel = QRectF(self.rect()).adjusted(*(self.MARGEN_BRILLO,) * 2,
                                             *(-self.MARGEN_BRILLO,) * 2)  # fmt: skip
        radio = tema.RADIO_TARJETA

        # Sombra suave debajo del panel
        pintor.setPen(Qt.PenStyle.NoPen)
        for desplazamiento, alfa in ((6, 0.035), (3, 0.05)):
            pintor.setBrush(con_alfa("#1E3C6E", alfa))
            pintor.drawRoundedRect(panel.translated(0, desplazamiento), radio, radio)

        # Halo de luz (solo cuando el mouse está encima)
        if self._luz > 0:
            for crecer, alfa in ((8, 0.06), (5, 0.10), (2.5, 0.16)):
                pintor.setBrush(con_alfa(c["brillo"], alfa * self._luz))
                pintor.drawRoundedRect(
                    panel.adjusted(-crecer, -crecer, crecer, crecer),
                    radio + crecer,
                    radio + crecer,
                )

        borde = mezclar(c["borde"], c["borde_brillo"], self._luz)
        pintor.setPen(QPen(borde, 1.2))
        # Algo transparente, como vidrio: deja pasar la luz del cursor
        pintor.setBrush(con_alfa(c["superficie"], 0.78))
        pintor.drawRoundedRect(panel, radio, radio)


# ---------------------------------------------------------------------------
# Botón con brillo
# ---------------------------------------------------------------------------
class BotonBrillante(QPushButton):
    """Botón en forma de píldora.

    La ventana le avisa dónde está el cursor (`acercar`); cuanto más cerca,
    más brilla y más se "levanta". Al presionarlo se hunde un poco.
    variante: "principal" (relleno azul) o "secundario" (blanco con borde).
    """

    MARGEN = 12  # espacio para el halo

    def __init__(self, colores, texto, nombre_icono=None, variante="principal"):
        super().__init__(texto)
        self.colores = colores
        self.variante = variante
        self._nombre_icono = nombre_icono
        self._cerca = 0.0
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFont(fuente(tema.FAMILIAS_INTERFAZ, 11, QFont.Weight.DemiBold))
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self._alto_pildora = 44 if variante == "principal" else 34

    def sizeHint(self):
        ancho_texto = self.fontMetrics().horizontalAdvance(self.text())
        ancho = ancho_texto + 48 + (24 if self._nombre_icono else 0)
        return QSize(ancho + 2 * self.MARGEN, self._alto_pildora + 2 * self.MARGEN)

    def minimumSizeHint(self):
        return self.sizeHint()

    def acercar(self, cursor_global):
        """Calcula el brillo según la distancia del cursor a la píldora."""
        if not self.isVisible():
            return
        esquina = self.mapToGlobal(self.rect().topLeft())
        pildora = QRectF(self._pildora()).translated(esquina.x(), esquina.y())
        dx = max(
            pildora.left() - cursor_global.x(), 0, cursor_global.x() - pildora.right()
        )
        dy = max(
            pildora.top() - cursor_global.y(), 0, cursor_global.y() - pildora.bottom()
        )
        cerca = max(0.0, 1 - math.hypot(dx, dy) / DISTANCIA_BRILLO) ** 1.5
        if abs(cerca - self._cerca) > 0.01:
            self._cerca = cerca
            self.update()

    def _pildora(self):
        alto = self._alto_pildora
        arriba = (self.height() - alto) / 2
        return QRectF(self.MARGEN, arriba, self.width() - 2 * self.MARGEN, alto)

    def paintEvent(self, _evento):
        c = self.colores
        pintor = QPainter(self)
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing)
        pildora = self._pildora()
        # Se levanta 2 px al acercarse y se hunde 1 px al presionar
        pildora.translate(0, 1 if self.isDown() else -2 * self._cerca)
        radio = pildora.height() / 2
        brillo = self._cerca

        pintor.setPen(Qt.PenStyle.NoPen)
        if brillo > 0:
            for crecer, alfa in ((10, 0.08), (6, 0.14), (3, 0.22)):
                pintor.setBrush(con_alfa(c["brillo"], alfa * brillo))
                pintor.drawRoundedRect(
                    pildora.adjusted(-crecer, -crecer, crecer, crecer),
                    radio + crecer,
                    radio + crecer,
                )

        if self.variante == "principal":
            relleno = QLinearGradient(pildora.topLeft(), pildora.bottomLeft())
            relleno.setColorAt(0, mezclar(c["acento"], "#FFFFFF", 0.18 + 0.12 * brillo))
            relleno.setColorAt(
                1, QColor(c["acento_hover"] if self.isDown() else c["acento"])
            )
            pintor.setBrush(relleno)
            color_texto = QColor(c["texto_sobre_acento"])
        else:
            pintor.setPen(QPen(mezclar(c["borde"], c["borde_brillo"], brillo), 1.2))
            pintor.setBrush(mezclar("#FFFFFF", c["acento_suave"], 0.5 * brillo))
            color_texto = QColor(c["acento"])
        pintor.drawRoundedRect(pildora, radio, radio)

        # Reflejo blanco en la mitad de arriba: da el aspecto de vidrio
        reflejo = QPainterPath()
        reflejo.addRoundedRect(
            pildora.adjusted(2, 2, -2, -pildora.height() / 2), radio, radio
        )
        pintor.setPen(Qt.PenStyle.NoPen)
        pintor.setBrush(con_alfa("#FFFFFF", 0.10 + 0.08 * brillo))
        pintor.drawPath(reflejo)

        if self.hasFocus():  # anillo de foco para quien usa el teclado
            pintor.setPen(QPen(con_alfa(c["acento"], 0.6), 2))
            pintor.setBrush(Qt.BrushStyle.NoBrush)
            pintor.drawRoundedRect(pildora.adjusted(-4, -4, 4, 4), radio + 4, radio + 4)

        # Icono y texto centrados
        ancho_texto = self.fontMetrics().horizontalAdvance(self.text())
        ancho_icono = 22 if self._nombre_icono else 0
        x = pildora.center().x() - (ancho_texto + ancho_icono) / 2
        if self._nombre_icono:
            imagen = iconos.pixmap(self._nombre_icono, color_texto.name(), 16)
            pintor.drawPixmap(QPointF(x, pildora.center().y() - 8), imagen)
        pintor.setPen(color_texto)
        pintor.setFont(self.font())
        caja = QRectF(x + ancho_icono, pildora.top(), ancho_texto + 2, pildora.height())
        izquierda = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
        pintor.drawText(caja, izquierda, self.text())


# ---------------------------------------------------------------------------
# Campo numérico
# ---------------------------------------------------------------------------
class CajaConUnidad(QLineEdit):
    """Caja de texto que muestra la unidad (por ejemplo "cm") a la derecha."""

    def __init__(self, unidad=""):
        super().__init__()
        self.unidad = unidad
        if unidad:
            self.setTextMargins(0, 0, 34, 0)

    def paintEvent(self, evento):
        super().paintEvent(evento)
        if self.unidad:
            pintor = QPainter(self)
            pintor.setPen(QColor(tema.paleta()["texto_sec"]))
            pintor.setFont(fuente(tema.FAMILIAS_MONO, 10))
            caja = self.rect().adjusted(0, 0, -16, 0)
            derecha = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight
            pintor.drawText(caja, derecha, self.unidad)


class CampoNumerico(QWidget):
    """Etiqueta, caja de texto y, debajo, el mensaje de error (si hay).

    `validar` es una función de viviani.validacion: recibe el texto y
    devuelve (valor, mensaje).
    """

    def __init__(self, colores, titulo, validar, valor_inicial, marcador, unidad=""):
        super().__init__()
        self._validar = validar
        self.caja = CajaConUnidad(unidad)
        self.caja.setText(valor_inicial)
        self.caja.setPlaceholderText(marcador)
        self.caja.setAccessibleName(titulo)
        self.caja.setFont(fuente(tema.FAMILIAS_NUMEROS, 15))
        self.caja.setMinimumHeight(48)

        # Brillo azul alrededor de la caja cuando tiene el foco
        self._halo = QGraphicsDropShadowEffect(self.caja)
        self._halo.setOffset(0, 0)
        self._halo.setColor(con_alfa(colores["brillo"], 0.0))
        self._halo.setBlurRadius(24)
        self.caja.setGraphicsEffect(self._halo)
        self._animacion = QVariantAnimation(self)
        self._animacion.setDuration(DURACION_BRILLO_MS)
        self._animacion.valueChanged.connect(
            lambda v: self._halo.setColor(con_alfa(colores["brillo"], float(v)))
        )
        self.caja.installEventFilter(self)

        self.mensaje = QLabel("")
        self.mensaje.setProperty("rol", "error")
        self.mensaje.setWordWrap(True)
        self.mensaje.setMinimumHeight(18)  # reserva el lugar: el diseño no salta

        diseno = QVBoxLayout(self)
        diseno.setContentsMargins(0, 0, 0, 0)
        diseno.setSpacing(6)
        diseno.addWidget(etiqueta_pequena(titulo))
        diseno.addWidget(self.caja)
        diseno.addWidget(self.mensaje)

        self.caja.textEdited.connect(self._al_editar)

    def validar_y_mostrar(self):
        """Valida, muestra el mensaje si hay error y devuelve el valor (o None)."""
        valor, mensaje = self._validar(self.caja.text())
        self.mostrar_error(mensaje)
        return valor

    def mostrar_error(self, mensaje):
        self.mensaje.setText(mensaje)
        self.caja.setProperty("error", bool(mensaje))
        self.caja.style().unpolish(self.caja)
        self.caja.style().polish(self.caja)

    def hay_error(self):
        return bool(self.mensaje.text())

    def _al_editar(self, _texto):
        # El mensaje desaparece en cuanto el texto vuelve a ser válido
        if self.hay_error() and not self._validar(self.caja.text())[1]:
            self.mostrar_error("")

    def eventFilter(self, objeto, evento):
        if objeto is self.caja and evento.type() in (
            evento.Type.FocusIn,
            evento.Type.FocusOut,
        ):
            entra = evento.type() == evento.Type.FocusIn
            self._animacion.stop()
            self._animacion.setStartValue(self._halo.color().alphaF())
            self._animacion.setEndValue(0.55 if entra else 0.0)
            self._animacion.start()
        return super().eventFilter(objeto, evento)
