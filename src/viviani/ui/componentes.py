"""Piezas visuales reutilizables de la ventana (tema oscuro).

FondoVentana   cielo azul noche con rejilla de puntos y auroras; los
               puntos se encienden alrededor del cursor
Separador      línea fina con degradado cian-violeta
CampoLinea     etiqueta + número grande sobre una línea que se ilumina
               al escribir + mensaje de error
BotonOrbe      botón circular "Calcular": respira, brilla al acercar el
               cursor, lanza una onda al pulsarlo y muestra el progreso
               como un arco a su alrededor
"""

import math

from PySide6.QtCore import QElapsedTimer, QPointF, QRectF, Qt, QTimer, QVariantAnimation
from PySide6.QtGui import (
    QColor,
    QConicalGradient,
    QFont,
    QLinearGradient,
    QPainter,
    QPen,
    QPixmap,
    QRadialGradient,
)
from PySide6.QtWidgets import QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from viviani import tema

DURACION_FOCO_MS = 260  # la línea del campo se enciende desde el centro
DISTANCIA_BRILLO = 140  # px: desde aquí el orbe empieza a brillar


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
    rotulo.setFont(fuente(tema.FAMILIAS_MONO, 8.5, espaciado=2.2))
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

        # Auroras: manchas de luz muy suaves de colores
        for x, y, radio, nombre, alfa in (
            (0.12, 0.05, 0.45, "acento", 0.13),
            (0.55, 0.40, 0.35, "violeta", 0.09),
            (0.95, 0.95, 0.45, "violeta", 0.10),
            (0.30, 1.00, 0.40, "acento", 0.07),
        ):
            centro = QPointF(x * ancho, y * alto)
            mancha = QRadialGradient(centro, radio * max(ancho, alto))
            mancha.setColorAt(0, con_alfa(c[nombre], alfa))
            mancha.setColorAt(1, con_alfa(c[nombre], 0.0))
            pintor.fillRect(imagen.rect(), mancha)

        # Rejilla de puntos, como papel punteado
        pintor.setPen(Qt.PenStyle.NoPen)
        pintor.setBrush(con_alfa(c["rejilla"], 0.55))
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
        resplandor.setColorAt(0, con_alfa(c["acento"], 0.10))
        resplandor.setColorAt(0.6, con_alfa(c["violeta"], 0.03))
        resplandor.setColorAt(1, con_alfa(c["violeta"], 0.0))
        pintor.setPen(Qt.PenStyle.NoPen)
        pintor.setBrush(resplandor)
        pintor.drawEllipse(centro, r, r)

        # Los puntos se encienden: su relleno es un degradado que se apaga
        # con la distancia al cursor
        puntos = QRadialGradient(centro, 0.75 * r)
        puntos.setColorAt(0, con_alfa(c["acento"], 0.6))
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
        degradado.setColorAt(0.0, con_alfa(c["acento"], 0.0))
        degradado.setColorAt(0.3, con_alfa(c["acento"], 0.45))
        degradado.setColorAt(0.7, con_alfa(c["violeta"], 0.45))
        degradado.setColorAt(1.0, con_alfa(c["violeta"], 0.0))
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
        self.caja.setFont(fuente(tema.FAMILIAS_NUMEROS, 26))
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
            for grosor, alfa in ((8, 0.10), (4, 0.22), (2, 1.0)):
                pluma = QPen(degradado_cian_violeta(0, ancho, alfa), grosor)
                pluma.setCapStyle(Qt.PenCapStyle.RoundCap)
                pintor.setPen(pluma)
                pintor.drawLine(QPointF(x0, y), QPointF(x1, y))

        if self.unidad:
            pintor.setPen(QColor(c["texto_sec"]))
            pintor.setFont(fuente(tema.FAMILIAS_MONO, 11))
            derecha = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            pintor.drawText(QRectF(caja), derecha, self.unidad)


# ---------------------------------------------------------------------------
# Botón orbe
# ---------------------------------------------------------------------------
class BotonOrbe(QPushButton):
    """Botón circular con el símbolo ∫.

    - Respira: su halo sube y baja lentamente (periodo de 3,2 s).
    - Brilla más cuanto más cerca está el cursor (la ventana llama a
      `acercar`).
    - Al pulsarlo lanza una onda que se expande y se desvanece.
    - Durante un cálculo largo dibuja el progreso como un arco.
    """

    DIAMETRO = 124
    MARGEN = 34  # espacio para el halo y la onda
    PERIODO_S = 3.2
    DURACION_ONDA_MS = 650

    def __init__(self, colores, reducir_movimiento=False):
        super().__init__("Calcular")
        self.colores = colores
        self._quieto = reducir_movimiento
        self._cerca = 0.0
        self._progreso = None
        lado = self.DIAMETRO + 2 * self.MARGEN
        self.setFixedSize(lado, lado)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAccessibleName("Calcular el perímetro")

        self._reloj = QElapsedTimer()
        self._reloj.start()
        self._onda = QElapsedTimer()
        self.clicked.connect(self._lanzar_onda)
        # Repinta ~30 veces por segundo (solo este botón, que es pequeño)
        self._latido = QTimer(self)
        self._latido.setInterval(33)
        self._latido.timeout.connect(self.update)
        if not self._quieto:
            self._latido.start()

    # --- lo que llama la ventana -----------------------------------------
    def acercar(self, cursor_global):
        """Calcula el brillo según la distancia del cursor al orbe."""
        if not self.isVisible():
            return
        centro = self.mapToGlobal(self.rect().center())
        distancia = math.hypot(
            cursor_global.x() - centro.x(), cursor_global.y() - centro.y()
        )
        distancia = max(0.0, distancia - self.DIAMETRO / 2)
        self._cerca = max(0.0, 1 - distancia / DISTANCIA_BRILLO) ** 1.5
        if self._quieto:
            self.update()

    def establecer_progreso(self, fraccion):
        """fraccion entre 0 y 1, o None para ocultar el arco."""
        self._progreso = fraccion
        self.update()

    def _lanzar_onda(self):
        if not self._quieto:
            self._onda.start()

    # --- dibujo --------------------------------------------------------
    def paintEvent(self, _evento):
        c = self.colores
        pintor = QPainter(self)
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing)
        centro = QPointF(self.width() / 2, self.height() / 2)
        radio = self.DIAMETRO / 2 * (0.96 if self.isDown() else 1.0)
        segundos = self._reloj.elapsed() / 1000
        respiracion = 0.5 + 0.5 * math.sin(2 * math.pi * segundos / self.PERIODO_S)
        if self._quieto:
            respiracion = 0.5

        self._pintar_halo(pintor, centro, radio, respiracion)
        self._pintar_onda(pintor, centro, radio)
        self._pintar_cuerpo(pintor, centro, radio, segundos)
        self._pintar_progreso(pintor, centro, radio)
        self._pintar_textos(pintor, centro, radio)

        if self.hasFocus():  # anillo punteado para quien usa el teclado
            pluma = QPen(con_alfa(c["acento"], 0.8), 1.5, Qt.PenStyle.DashLine)
            pintor.setPen(pluma)
            pintor.setBrush(Qt.BrushStyle.NoBrush)
            pintor.drawEllipse(centro, radio + 14, radio + 14)

    def _pintar_halo(self, pintor, centro, radio, respiracion):
        c = self.colores
        fuerza = 0.18 + 0.18 * respiracion + 0.55 * self._cerca
        exterior = radio + self.MARGEN
        halo = QRadialGradient(centro, exterior)
        borde = radio / exterior
        halo.setColorAt(0, con_alfa(c["acento"], 0.0))
        halo.setColorAt(borde * 0.9, con_alfa(c["acento"], 0.45 * fuerza))
        halo.setColorAt(
            borde + (1 - borde) * 0.35, con_alfa(c["violeta"], 0.20 * fuerza)
        )
        halo.setColorAt(1, con_alfa(c["violeta"], 0.0))
        pintor.setPen(Qt.PenStyle.NoPen)
        pintor.setBrush(halo)
        pintor.drawEllipse(centro, exterior, exterior)

    def _pintar_onda(self, pintor, centro, radio):
        if not self._onda.isValid():
            return
        avance = self._onda.elapsed() / self.DURACION_ONDA_MS
        if avance >= 1:
            self._onda.invalidate()
            return
        suave = 1 - (1 - avance) ** 3
        pintor.setBrush(Qt.BrushStyle.NoBrush)
        pintor.setPen(QPen(con_alfa(self.colores["acento"], 0.7 * (1 - avance)), 2))
        alcance = radio + suave * (self.MARGEN - 2)
        pintor.drawEllipse(centro, alcance, alcance)

    def _pintar_cuerpo(self, pintor, centro, radio, segundos):
        c = self.colores
        # Esfera de vidrio oscuro con luz arriba a la izquierda
        luz = centro + QPointF(-0.35 * radio, -0.45 * radio)
        cuerpo = QRadialGradient(luz, 1.6 * radio)
        cuerpo.setColorAt(0, mezclar("#2A5490", c["acento"], 0.15 * self._cerca))
        cuerpo.setColorAt(0.55, QColor("#132544"))
        cuerpo.setColorAt(1, QColor("#0A1222"))
        # Borde que gira despacio: cian, violeta y de nuevo cian
        borde = QConicalGradient(centro, -40 * segundos)
        borde.setColorAt(0.0, con_alfa(c["acento"], 0.95))
        borde.setColorAt(0.5, con_alfa(c["violeta"], 0.95))
        borde.setColorAt(1.0, con_alfa(c["acento"], 0.95))
        pintor.setPen(QPen(borde, 2))
        pintor.setBrush(cuerpo)
        pintor.drawEllipse(centro, radio, radio)

    def _pintar_progreso(self, pintor, centro, radio):
        if self._progreso is None:
            return
        caja = QRectF(centro.x() - radio - 8, centro.y() - radio - 8,
                      2 * radio + 16, 2 * radio + 16)  # fmt: skip
        pintor.setBrush(Qt.BrushStyle.NoBrush)
        pintor.setPen(QPen(con_alfa(self.colores["borde"], 0.9), 3))
        pintor.drawEllipse(caja)
        pluma = QPen(QColor(self.colores["acento"]), 3)
        pluma.setCapStyle(Qt.PenCapStyle.RoundCap)
        pintor.setPen(pluma)
        # Qt mide los ángulos en 1/16 de grado; negativo = sentido horario
        pintor.drawArc(caja, 90 * 16, round(-360 * 16 * self._progreso))

    def _pintar_textos(self, pintor, centro, radio):
        c = self.colores
        simbolo = QRectF(centro.x() - radio, centro.y() - 0.78 * radio,
                         2 * radio, 1.15 * radio)  # fmt: skip
        pintor.setPen(mezclar(c["texto"], c["acento_hover"], self._cerca))
        pintor.setFont(fuente(tema.FAMILIAS_TITULO, radio * 0.42))
        pintor.drawText(simbolo, Qt.AlignmentFlag.AlignCenter, "∫")
        rotulo = QRectF(centro.x() - radio, centro.y() + 0.30 * radio,
                        2 * radio, 0.35 * radio)  # fmt: skip
        pintor.setPen(mezclar(c["etiqueta"], c["acento"], self._cerca))
        pintor.setFont(fuente(tema.FAMILIAS_MONO, 8.5, espaciado=2.5))
        pintor.drawText(rotulo, Qt.AlignmentFlag.AlignCenter, "CALCULAR")
