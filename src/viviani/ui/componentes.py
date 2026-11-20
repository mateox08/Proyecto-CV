"""Piezas visuales reutilizables de la ventana (tema oscuro grafito).

FondoVentana    fondo carbón con rejilla de puntos; los puntos se
                encienden suavemente alrededor del cursor
Separador       línea fina que se desvanece en los extremos
CampoLinea      etiqueta + número grande sobre una línea que se ilumina
                al escribir + mensaje de error
BotonCalcular   botón en forma de píldora: se aclara al acercar el cursor,
                se hunde al pulsarlo y se llena para mostrar el progreso
"""

import math

from PySide6.QtCore import QPointF, QRectF, Qt, QVariantAnimation
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
from PySide6.QtWidgets import QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from viviani import tema

DURACION_FOCO_MS = 260  # la línea del campo se enciende desde el centro
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
    """Etiqueta discreta: letra normal, pequeña y en gris."""
    rotulo = QLabel(texto)
    rotulo.setFont(fuente(tema.FAMILIAS_INTERFAZ, 9.5))
    rotulo.setProperty("rol", "etiqueta")
    return rotulo


def degradado_cian_violeta(x0, x1, alfa=1.0):
    """Degradado horizontal de cian a violeta (el sello de la app)."""
    colores = tema.paleta()
    degradado = QLinearGradient(x0, 0, x1, 0)
    degradado.setColorAt(0, con_alfa(colores["acento"], alfa))
    degradado.setColorAt(1, con_alfa(colores["violeta"], alfa))
    return degradado


# ---------------------------------------------------------------------------
# Fondo
# ---------------------------------------------------------------------------
class FondoVentana(QWidget):
    """Fondo de toda la ventana. Se dibuja una vez por tamaño y se guarda
    como imagen; luego solo se repinta el círculo de luz del cursor."""

    PASO_PUNTOS = 28  # px entre puntos de la rejilla
    RADIO_LUZ = 220

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

    def _puntos_de_rejilla(self, x0, y0, x1, y1):
        paso = self.PASO_PUNTOS
        for x in range(max(0, int(x0) - int(x0) % paso), int(x1) + 1, paso):
            for y in range(max(0, int(y0) - int(y0) % paso), int(y1) + 1, paso):
                yield x, y

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

        # Una luz neutra muy suave en el centro
        centro = QPointF(0.5 * ancho, 0.45 * alto)
        luz = QRadialGradient(centro, 0.7 * max(ancho, alto))
        luz.setColorAt(0, con_alfa("#FFFFFF", 0.035))
        luz.setColorAt(1, con_alfa("#FFFFFF", 0.0))
        pintor.fillRect(imagen.rect(), luz)

        # Rejilla de puntos, como papel punteado
        pintor.setPen(Qt.PenStyle.NoPen)
        pintor.setBrush(con_alfa(c["rejilla"], 0.45))
        for x, y in self._puntos_de_rejilla(0, 0, ancho, alto):
            pintor.drawEllipse(QPointF(x, y), 1.0, 1.0)
        pintor.end()
        return imagen

    def _dibujar_luz(self, pintor):
        """Un resplandor y los puntos de la rejilla encendidos cerca del cursor."""
        c = self.colores
        centro = QPointF(self._luz)
        r = self.RADIO_LUZ
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing)

        resplandor = QRadialGradient(centro, r)
        resplandor.setColorAt(0, con_alfa("#FFFFFF", 0.04))
        resplandor.setColorAt(1, con_alfa("#FFFFFF", 0.0))
        pintor.setPen(Qt.PenStyle.NoPen)
        pintor.setBrush(resplandor)
        pintor.drawEllipse(centro, r, r)

        # Los puntos se encienden: su relleno es un degradado que se apaga
        # con la distancia al cursor
        puntos = QRadialGradient(centro, 0.75 * r)
        puntos.setColorAt(0, con_alfa(c["acento"], 0.45))
        puntos.setColorAt(1, con_alfa(c["acento"], 0.0))
        pintor.setBrush(puntos)
        for x, y in self._puntos_de_rejilla(
            centro.x() - r, centro.y() - r, centro.x() + r, centro.y() + r
        ):
            pintor.drawEllipse(QPointF(x, y), 1.4, 1.4)


# ---------------------------------------------------------------------------
# Separador
# ---------------------------------------------------------------------------
class Separador(QWidget):
    """Línea horizontal que se desvanece en los extremos."""

    def __init__(self):
        super().__init__()
        self.setFixedHeight(9)

    def paintEvent(self, _evento):
        c = tema.paleta()
        pintor = QPainter(self)
        y = self.height() / 2
        degradado = QLinearGradient(0, 0, self.width(), 0)
        degradado.setColorAt(0.0, con_alfa(c["borde"], 0.0))
        degradado.setColorAt(0.2, con_alfa(c["borde"], 1.0))
        degradado.setColorAt(0.8, con_alfa(c["borde"], 1.0))
        degradado.setColorAt(1.0, con_alfa(c["borde"], 0.0))
        pintor.setPen(QPen(degradado, 1))
        pintor.drawLine(QPointF(0, y), QPointF(self.width(), y))


# ---------------------------------------------------------------------------
# Campo con línea
# ---------------------------------------------------------------------------
class CampoLinea(QWidget):
    """Etiqueta, número grande y una línea debajo que se ilumina con el foco.

    `validar` es una función de viviani.validacion: recibe el texto y
    devuelve (valor, mensaje).
    """

    def __init__(self, colores, titulo, validar, valor_inicial, marcador, unidad=""):
        super().__init__()
        self.colores = colores
        self.unidad = unidad
        self._validar = validar
        self._foco = 0.0  # 0 = línea apagada, 1 = encendida

        self.caja = QLineEdit(valor_inicial)
        self.caja.setObjectName("linea")
        self.caja.setPlaceholderText(marcador)
        self.caja.setAccessibleName(titulo)
        self.caja.setFont(fuente(tema.FAMILIAS_NUMEROS, 24, QFont.Weight.Light))
        if unidad:
            self.caja.setTextMargins(0, 0, 44, 0)
        self.caja.installEventFilter(self)

        self.mensaje = QLabel("")
        self.mensaje.setProperty("rol", "error")
        self.mensaje.setWordWrap(True)
        self.mensaje.setMinimumHeight(20)  # reserva el lugar: nada salta

        diseno = QVBoxLayout(self)
        diseno.setContentsMargins(0, 0, 0, 0)
        diseno.setSpacing(4)
        diseno.addWidget(etiqueta_pequena(titulo))
        diseno.addWidget(self.caja)
        diseno.addSpacing(8)  # lugar para la línea
        diseno.addWidget(self.mensaje)

        self._animacion = QVariantAnimation(self)
        self._animacion.setDuration(DURACION_FOCO_MS)
        self._animacion.valueChanged.connect(self._al_animar)
        self.caja.textEdited.connect(self._al_editar)

    # --- validación ------------------------------------------------------
    def validar_y_mostrar(self):
        """Valida, muestra el mensaje si hay error y devuelve el valor (o None)."""
        valor, mensaje = self._validar(self.caja.text())
        self.mostrar_error(mensaje)
        return valor

    def mostrar_error(self, mensaje):
        self.mensaje.setText(mensaje)
        self.update()

    def hay_error(self):
        return bool(self.mensaje.text())

    def _al_editar(self, _texto):
        # El mensaje desaparece en cuanto el texto vuelve a ser válido
        if self.hay_error() and not self._validar(self.caja.text())[1]:
            self.mostrar_error("")

    # --- foco y dibujo -----------------------------------------------------
    def eventFilter(self, objeto, evento):
        tipos = (evento.Type.FocusIn, evento.Type.FocusOut)
        if objeto is self.caja and evento.type() in tipos:
            self._animacion.stop()
            self._animacion.setStartValue(self._foco)
            self._animacion.setEndValue(1.0 if evento.type() == tipos[0] else 0.0)
            self._animacion.start()
        return super().eventFilter(objeto, evento)

    def _al_animar(self, valor):
        self._foco = float(valor)
        self.update()

    def paintEvent(self, _evento):
        c = self.colores
        pintor = QPainter(self)
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing)
        caja = self.caja.geometry()
        y = caja.bottom() + 5
        ancho = self.width()

        # Línea base, tenue
        pintor.setPen(QPen(QColor(c["borde"]), 1))
        pintor.drawLine(QPointF(0, y), QPointF(ancho, y))

        if self.hay_error():
            pintor.setPen(QPen(QColor(c["error"]), 2))
            pintor.drawLine(QPointF(0, y), QPointF(ancho, y))
        elif self._foco > 0:
            # Línea encendida que crece desde el centro, con un brillo debajo
            mitad = ancho * self._foco / 2
            x0, x1 = ancho / 2 - mitad, ancho / 2 + mitad
            for grosor, alfa in ((5, 0.12), (1.5, 1.0)):
                pluma = QPen(con_alfa(c["acento"], alfa), grosor)
                pluma.setCapStyle(Qt.PenCapStyle.RoundCap)
                pintor.setPen(pluma)
                pintor.drawLine(QPointF(x0, y), QPointF(x1, y))

        if self.unidad:
            pintor.setPen(QColor(c["texto_sec"]))
            pintor.setFont(fuente(tema.FAMILIAS_INTERFAZ, 11))
            derecha = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            pintor.drawText(QRectF(caja), derecha, self.unidad)


# ---------------------------------------------------------------------------
# Botón Calcular
# ---------------------------------------------------------------------------
class BotonCalcular(QPushButton):
    """Botón en forma de píldora, relleno con el color de acento.

    - Se aclara un poco y proyecta un halo suave cuanto más cerca está el
      cursor (la ventana llama a `acercar`).
    - Al pulsarlo se hunde 1 px.
    - Durante un cálculo largo se llena de izquierda a derecha con el progreso.
    """

    ALTO = 50
    MARGEN = 10  # espacio para el halo

    def __init__(self, colores, ancho=300):
        super().__init__("Calcular")
        self.colores = colores
        self._cerca = 0.0
        self._progreso = None
        self.setFixedSize(ancho + 2 * self.MARGEN, self.ALTO + 2 * self.MARGEN)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAccessibleName("Calcular el perímetro")

    def acercar(self, cursor_global):
        """Calcula el brillo según la distancia del cursor a la píldora."""
        if not self.isVisible():
            return
        esquina = self.mapToGlobal(self.rect().topLeft())
        caja = self._pildora().translated(esquina.x(), esquina.y())
        x, y = cursor_global.x(), cursor_global.y()
        dx = max(caja.left() - x, 0, x - caja.right())
        dy = max(caja.top() - y, 0, y - caja.bottom())
        cerca = max(0.0, 1 - math.hypot(dx, dy) / DISTANCIA_BRILLO) ** 1.5
        if abs(cerca - self._cerca) > 0.01:
            self._cerca = cerca
            self.update()

    def establecer_progreso(self, fraccion):
        """fraccion entre 0 y 1, o None para quitar el relleno de progreso."""
        self._progreso = fraccion
        self.update()

    def _pildora(self):
        m = self.MARGEN
        return QRectF(m, m, self.width() - 2 * m, self.height() - 2 * m)

    def paintEvent(self, _evento):
        c = self.colores
        pintor = QPainter(self)
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing)
        pildora = self._pildora()
        if self.isDown():
            pildora.translate(0, 1)
        radio = pildora.height() / 2

        # Halo suave al acercar el cursor
        if self._cerca > 0:
            pintor.setPen(Qt.PenStyle.NoPen)
            for crecer, alfa in ((8, 0.06), (4, 0.10)):
                pintor.setBrush(con_alfa(c["acento"], alfa * self._cerca))
                pintor.drawRoundedRect(
                    pildora.adjusted(-crecer, -crecer, crecer, crecer),
                    radio + crecer,
                    radio + crecer,
                )

        if self._progreso is None:
            relleno = mezclar(c["acento"], c["acento_hover"], 0.6 * self._cerca)
            pintor.setPen(Qt.PenStyle.NoPen)
            pintor.setBrush(relleno)
            pintor.drawRoundedRect(pildora, radio, radio)
        else:
            # Pista tenue y relleno de progreso recortado a la píldora
            pintor.setPen(QPen(con_alfa(c["acento"], 0.5), 1))
            pintor.setBrush(QColor(c["acento_suave"]))
            pintor.drawRoundedRect(pildora, radio, radio)
            pintor.save()
            camino = QPainterPath()
            camino.addRoundedRect(pildora, radio, radio)
            pintor.setClipPath(camino)
            lleno = QRectF(pildora)
            lleno.setWidth(pildora.width() * self._progreso)
            pintor.fillRect(lleno, QColor(c["acento"]))
            pintor.restore()

        if self.hasFocus():  # anillo para quien usa el teclado
            pintor.setPen(QPen(con_alfa(c["acento"], 0.7), 1.5))
            pintor.setBrush(Qt.BrushStyle.NoBrush)
            pintor.drawRoundedRect(pildora.adjusted(-4, -4, 4, 4), radio + 4, radio + 4)

        # Texto y, a la derecha, la tecla que también calcula
        pintor.setPen(QColor(c["texto_sobre_acento"]))
        pintor.setFont(fuente(tema.FAMILIAS_INTERFAZ, 11.5, QFont.Weight.DemiBold))
        texto = "Calculando…" if self._progreso is not None else "Calcular"
        pintor.drawText(pildora, Qt.AlignmentFlag.AlignCenter, texto)
        if self._progreso is None:
            pintor.setFont(fuente(tema.FAMILIAS_INTERFAZ, 9))
            pintor.setPen(con_alfa(c["texto_sobre_acento"], 0.55))
            tecla = pildora.adjusted(0, 0, -radio * 0.8, 0)
            derecha = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            pintor.drawText(tecla, derecha, "Enter")
