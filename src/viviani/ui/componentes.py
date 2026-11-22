"""Piezas visuales reutilizables de la ventana.

FondoVentana    cielo nocturno: degradado, dos resplandores muy tenues y
                estrellas; las estrellas cercanas al cursor se encienden
Separador       línea fina que se desvanece en los extremos
CampoDato       etiqueta + caja de vidrio con un número grande; el borde se
                enciende al escribir y se pone rojo si hay error
Chip            botón pequeño en forma de píldora (atajos y capas)
BotonCalcular   píldora con el degradado de la app: brilla al acercar el
                cursor, se hunde al pulsarla y se llena con el progreso
TituloSeccion   "01  DATOS": número con el color de acento y nombre
Tarjeta         módulo de vidrio translúcido con su título (Datos, Fórmula…)
CapaPulsos      capa transparente encima de todo: cada clic suelta una onda
                de luz que se expande y se apaga
"""

import math
import random

from PySide6.QtCore import (
    QElapsedTimer,
    QEvent,
    QPointF,
    QRectF,
    Qt,
    QTimer,
    QVariantAnimation,
)
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
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from viviani import tema
from viviani.animacion import INTERVALO_MS, salida_suave
from viviani.tema import con_alfa

DURACION_FOCO_MS = 260  # el borde del campo se enciende con un fundido
DISTANCIA_BRILLO = 140  # px: desde aquí el botón empieza a brillar
PERIODO_REFLEJO_MS = 2400  # el reflejo cruza el botón cada 2.4 s
DURACION_PULSO_MS = 520  # lo que dura la onda de luz de un clic
RADIO_PULSO = 90  # px: hasta dónde llega esa onda
RADIO_TARJETA = 22


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


def degradado_acento(x0, x1, alfa=1.0):
    """Degradado horizontal entre los dos acentos de la paleta (sello de la app)."""
    c = tema.paleta()
    degradado = QLinearGradient(x0, 0, x1, 0)
    degradado.setColorAt(0, con_alfa(c["acento"], alfa))
    degradado.setColorAt(1, con_alfa(c["acento_2"], alfa))
    return degradado


# ---------------------------------------------------------------------------
# Fondo
# ---------------------------------------------------------------------------
class FondoVentana(QWidget):
    """Fondo de toda la ventana. Se dibuja una vez por tamaño y se guarda
    como imagen; luego solo se repinta el círculo de luz del cursor."""

    RADIO_LUZ = 230
    ESTRELLAS_POR_MEGAPIXEL = 260

    def __init__(self, colores):
        super().__init__()
        self.colores = colores
        self._imagen = None  # el cielo ya dibujado
        self._estrellas = []  # (x, y, radio, brillo)
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
            self._imagen = self._dibujar_cielo()
        pintor = QPainter(self)
        pintor.drawPixmap(evento.rect(), self._imagen, evento.rect())
        if self._luz is not None:
            self._dibujar_luz(pintor)

    def _sembrar_estrellas(self, ancho, alto):
        """Estrellas al azar, pero siempre las mismas (semilla fija)."""
        azar = random.Random(1046)
        cantidad = round(self.ESTRELLAS_POR_MEGAPIXEL * ancho * alto / 1e6)
        self._estrellas = [
            (azar.uniform(0, ancho), azar.uniform(0, alto),
             azar.choice((0.6, 0.7, 0.8, 1.1)), azar.uniform(0.15, 0.55))
            for _ in range(cantidad)
        ]  # fmt: skip

    def _dibujar_cielo(self):
        c = self.colores
        ancho, alto = self.width(), self.height()
        imagen = QPixmap(self.size())
        pintor = QPainter(imagen)
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing)

        degradado = QLinearGradient(0, 0, 0, alto)
        degradado.setColorAt(0, QColor(c["fondo"]))
        degradado.setColorAt(1, QColor(c["fondo_2"]))
        pintor.fillRect(imagen.rect(), degradado)

        # Dos resplandores muy suaves con los acentos, en esquinas opuestas
        for x, y, color, alfa in ((0.12, -0.05, c["acento_2"], 0.09),
                                  (0.92, 1.05, c["acento"], 0.07)):  # fmt: skip
            aurora = QRadialGradient(
                QPointF(x * ancho, y * alto), 0.6 * max(ancho, alto)
            )
            aurora.setColorAt(0, con_alfa(color, alfa))
            aurora.setColorAt(1, con_alfa(color, 0.0))
            pintor.fillRect(imagen.rect(), aurora)

        # Estrellas
        self._sembrar_estrellas(ancho, alto)
        pintor.setPen(Qt.PenStyle.NoPen)
        for x, y, radio, brillo in self._estrellas:
            pintor.setBrush(con_alfa(c["estrella"], brillo))
            pintor.drawEllipse(QPointF(x, y), radio, radio)

        # Viñeta: las esquinas un poco más oscuras centran la mirada
        vineta = QRadialGradient(QPointF(ancho / 2, alto / 2), 0.75 * max(ancho, alto))
        vineta.setColorAt(0.55, QColor(0, 0, 0, 0))
        vineta.setColorAt(1.0, QColor(0, 0, 0, 120))
        pintor.fillRect(imagen.rect(), vineta)
        pintor.end()
        return imagen

    def _dibujar_luz(self, pintor):
        """Un resplandor y las estrellas cercanas al cursor, encendidas."""
        c = self.colores
        centro = QPointF(self._luz)
        r = self.RADIO_LUZ
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing)

        resplandor = QRadialGradient(centro, r)
        resplandor.setColorAt(0, con_alfa(c["acento"], 0.045))
        resplandor.setColorAt(1, con_alfa(c["acento"], 0.0))
        pintor.setPen(Qt.PenStyle.NoPen)
        pintor.setBrush(resplandor)
        pintor.drawEllipse(centro, r, r)

        # Las estrellas cercanas se encienden: su relleno es un degradado que
        # se apaga con la distancia al cursor
        encendido = QRadialGradient(centro, 0.8 * r)
        encendido.setColorAt(0, con_alfa(c["acento"], 0.95))
        encendido.setColorAt(1, con_alfa(c["acento"], 0.0))
        pintor.setBrush(encendido)
        for x, y, radio, _ in self._estrellas:
            if abs(x - centro.x()) < r and abs(y - centro.y()) < r:
                pintor.drawEllipse(QPointF(x, y), radio + 0.5, radio + 0.5)


# ---------------------------------------------------------------------------
# Separador
# ---------------------------------------------------------------------------
class Separador(QWidget):
    """Línea horizontal que se desvanece en los extremos."""

    def __init__(self):
        super().__init__()
        self.setFixedHeight(9)

    def paintEvent(self, _evento):
        borde = tema.paleta()["borde"]
        pintor = QPainter(self)
        y = self.height() / 2
        degradado = QLinearGradient(0, 0, self.width(), 0)
        degradado.setColorAt(0.0, con_alfa(borde, 0.0))
        degradado.setColorAt(0.2, con_alfa(borde, 1.0))
        degradado.setColorAt(0.8, con_alfa(borde, 1.0))
        degradado.setColorAt(1.0, con_alfa(borde, 0.0))
        pintor.setPen(QPen(degradado, 1))
        pintor.drawLine(QPointF(0, y), QPointF(self.width(), y))


# ---------------------------------------------------------------------------
# Campo de datos
# ---------------------------------------------------------------------------
class CampoDato(QWidget):
    """Etiqueta, caja de vidrio con el número y mensaje de error debajo.

    `validar` es una función de viviani.validacion: recibe el texto y
    devuelve (valor, mensaje). `paso(valor, sentido)`, opcional, da el
    valor siguiente al pulsar ↑ (sentido 1) o ↓ (sentido -1).
    """

    RELLENO = (16, 6, 16, 6)  # espacio entre el borde de la caja y el texto

    def __init__(self, colores, titulo, validar, valor_inicial, marcador,
                 unidad="", paso=None):  # fmt: skip
        super().__init__()
        self.colores = colores
        self.unidad = unidad
        self._validar = validar
        self._paso = paso
        self._foco = 0.0  # 0 = borde apagado, 1 = encendido

        self.caja = QLineEdit(valor_inicial)
        self.caja.setObjectName("dato")
        self.caja.setPlaceholderText(marcador)
        self.caja.setAccessibleName(titulo)
        self.caja.setFont(fuente(tema.FAMILIAS_TITULO, 21, QFont.Weight.Light))
        if unidad:
            self.caja.setTextMargins(0, 0, 36, 0)
        self.caja.installEventFilter(self)

        self.mensaje = QLabel("")
        self.mensaje.setProperty("rol", "error")
        self.mensaje.setWordWrap(True)
        self.mensaje.setMinimumHeight(20)  # reserva el lugar: nada salta

        marco = QHBoxLayout()
        marco.setContentsMargins(*self.RELLENO)
        marco.addWidget(self.caja)
        diseno = QVBoxLayout(self)
        diseno.setContentsMargins(0, 0, 0, 0)
        diseno.setSpacing(6)
        diseno.addWidget(etiqueta_pequena(titulo))
        diseno.addLayout(marco)
        diseno.addWidget(self.mensaje)

        self._animacion = QVariantAnimation(self)
        self._animacion.setDuration(DURACION_FOCO_MS)
        self._animacion.valueChanged.connect(self._al_animar)
        self.caja.textEdited.connect(self._al_editar)

    # --- validación ------------------------------------------------------
    def valor(self):
        """El valor escrito si es válido, o None (sin mostrar mensajes)."""
        return self._validar(self.caja.text())[0]

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

    def escribir(self, texto):
        """Pone un valor como si lo hubiera escrito el usuario."""
        self.caja.setText(texto)
        self.caja.textEdited.emit(texto)
        self.caja.setFocus()
        self.caja.selectAll()

    def _al_editar(self, _texto):
        # El mensaje desaparece en cuanto el texto vuelve a ser válido
        if self.hay_error() and not self._validar(self.caja.text())[1]:
            self.mostrar_error("")

    # --- teclado, foco y dibujo -------------------------------------------
    def eventFilter(self, objeto, evento):
        if objeto is self.caja:
            if evento.type() in (QEvent.Type.FocusIn, QEvent.Type.FocusOut):
                self._animacion.stop()
                self._animacion.setStartValue(self._foco)
                encendido = evento.type() == QEvent.Type.FocusIn
                self._animacion.setEndValue(1.0 if encendido else 0.0)
                self._animacion.start()
            elif evento.type() == QEvent.Type.KeyPress and self._paso is not None:
                sentido = {Qt.Key.Key_Up: 1, Qt.Key.Key_Down: -1}.get(evento.key())
                valor = self.valor()
                if sentido is not None and valor is not None:
                    nuevo = self._paso(valor, sentido)
                    if self._validar(nuevo)[0] is not None:
                        self.escribir(nuevo)
                    return True
        return super().eventFilter(objeto, evento)

    def _al_animar(self, valor):
        self._foco = float(valor)
        self.update()

    def _marco(self):
        """Rectángulo de la caja de vidrio (alrededor del QLineEdit)."""
        izquierda, arriba, _, abajo = self.RELLENO
        caja = self.caja.geometry()
        return QRectF(0.5, caja.top() - arriba + 0.5,
                      self.width() - 1, caja.height() + arriba + abajo - 1)  # fmt: skip

    def paintEvent(self, _evento):
        c = self.colores
        pintor = QPainter(self)
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing)
        marco = self._marco()
        radio = 14

        # Cuerpo: superficie translúcida, un poco más clara con el foco
        cuerpo = QLinearGradient(marco.topLeft(), marco.bottomLeft())
        cuerpo.setColorAt(0, con_alfa(c["superficie_2"], 0.85 + 0.1 * self._foco))
        cuerpo.setColorAt(1, con_alfa(c["superficie"], 0.85))
        pintor.setPen(QPen(QColor(c["borde"]), 1))
        pintor.setBrush(cuerpo)
        pintor.drawRoundedRect(marco, radio, radio)

        if self.hay_error():
            pintor.setPen(QPen(QColor(c["error"]), 1.5))
            pintor.setBrush(Qt.BrushStyle.NoBrush)
            pintor.drawRoundedRect(marco, radio, radio)
        elif self._foco > 0:
            # Borde con el degradado de la app y un halo hacia afuera
            for crecer, grosor, alfa in ((3, 4, 0.10), (0, 1.4, 0.95)):
                pluma = QPen(degradado_acento(marco.left(), marco.right(),
                                              alfa * self._foco), grosor)  # fmt: skip
                pintor.setPen(pluma)
                pintor.setBrush(Qt.BrushStyle.NoBrush)
                pintor.drawRoundedRect(
                    marco.adjusted(-crecer, -crecer, crecer, crecer),
                    radio + crecer, radio + crecer,
                )  # fmt: skip

        if self.unidad:
            pintor.setPen(QColor(c["texto_sec"]))
            pintor.setFont(fuente(tema.FAMILIAS_INTERFAZ, 11))
            derecha = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            pintor.drawText(marco.adjusted(0, 0, -16, 0), derecha, self.unidad)


# ---------------------------------------------------------------------------
# Chip
# ---------------------------------------------------------------------------
class Chip(QPushButton):
    """Botón pequeño en forma de píldora. Con `marcable`, se enciende y apaga."""

    def __init__(self, texto, marcable=False, descripcion=""):
        super().__init__(texto)
        self.setObjectName("chip")
        self.setCheckable(marcable)
        self.setChecked(marcable)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFont(fuente(tema.FAMILIAS_INTERFAZ, 9))
        if descripcion:
            self.setToolTip(descripcion)
            self.setAccessibleName(descripcion)


# ---------------------------------------------------------------------------
# Botón Calcular
# ---------------------------------------------------------------------------
class BotonCalcular(QPushButton):
    """Botón en forma de píldora con el degradado de los dos acentos.

    - Brilla y lo cruza un reflejo cuanto más cerca está el cursor (la
      ventana llama a `acercar`).
    - Al pulsarlo se hunde 1 px.
    - Durante un cálculo largo se llena de izquierda a derecha con el progreso.
    """

    ALTO = 52
    MARGEN = 10  # espacio para el halo

    def __init__(self, colores, ancho=300):
        super().__init__("Calcular")
        self.colores = colores
        self._cerca = 0.0
        self._progreso = None
        self._reloj = QElapsedTimer()
        self._reloj.start()
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
        # Con el cursor cerca se repinta siempre: el reflejo se está moviendo
        if cerca > 0 or abs(cerca - self._cerca) > 0.01:
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
        forma = QPainterPath()
        forma.addRoundedRect(pildora, radio, radio)

        # Halo suave al acercar el cursor
        if self._cerca > 0:
            pintor.setPen(Qt.PenStyle.NoPen)
            for crecer, alfa in ((9, 0.07), (4, 0.12)):
                pintor.setBrush(degradado_acento(pildora.left(), pildora.right(),
                                                 alfa * self._cerca))  # fmt: skip
                pintor.drawRoundedRect(
                    pildora.adjusted(-crecer, -crecer, crecer, crecer),
                    radio + crecer, radio + crecer,
                )  # fmt: skip

        pintor.save()
        pintor.setClipPath(forma)
        if self._progreso is None:
            pintor.fillRect(pildora, degradado_acento(pildora.left(), pildora.right()))
            # Brillo de arriba, como un vidrio pulido
            brillo = QLinearGradient(pildora.topLeft(), pildora.bottomLeft())
            brillo.setColorAt(0, QColor(255, 255, 255, round(40 + 40 * self._cerca)))
            brillo.setColorAt(0.5, QColor(255, 255, 255, 0))
            pintor.fillRect(pildora, brillo)
            if self._cerca > 0:
                self._pintar_reflejo(pintor, pildora)
        else:
            # Pista oscura y relleno de progreso
            pintor.fillRect(pildora, QColor(c["acento_suave"]))
            lleno = QRectF(pildora)
            lleno.setWidth(pildora.width() * self._progreso)
            # Translúcido: el texto claro se sigue leyendo encima
            pintor.fillRect(
                lleno, degradado_acento(pildora.left(), pildora.right(), 0.35)
            )
        pintor.restore()

        if self._progreso is not None:
            pintor.setPen(QPen(con_alfa(c["acento"], 0.5), 1))
            pintor.setBrush(Qt.BrushStyle.NoBrush)
            pintor.drawPath(forma)
        if self.hasFocus():  # anillo para quien usa el teclado
            pintor.setPen(QPen(con_alfa(c["acento"], 0.8), 1.5))
            pintor.setBrush(Qt.BrushStyle.NoBrush)
            pintor.drawRoundedRect(pildora.adjusted(-4, -4, 4, 4), radio + 4, radio + 4)

        self._pintar_textos(pintor, pildora, radio)

    def _pintar_reflejo(self, pintor, pildora):
        """Una franja de luz diagonal que cruza el botón de izquierda a derecha."""
        avance = (self._reloj.elapsed() % PERIODO_REFLEJO_MS) / PERIODO_REFLEJO_MS
        x = pildora.left() - 80 + avance * (pildora.width() + 160)
        franja = QLinearGradient(x - 40, 0, x + 40, 0)
        alfa = round(70 * self._cerca)
        franja.setColorAt(0.0, QColor(255, 255, 255, 0))
        franja.setColorAt(0.5, QColor(255, 255, 255, alfa))
        franja.setColorAt(1.0, QColor(255, 255, 255, 0))
        pintor.fillRect(pildora, franja)

    def _pintar_textos(self, pintor, pildora, radio):
        c = self.colores
        oscuro = QColor(c["texto_sobre_acento"])
        if self._progreso is None:
            texto, tecla, color = "Calcular", "Enter", oscuro
        else:
            texto = f"Calculando…  {round(100 * self._progreso)} %"
            tecla, color = "Esc", QColor(c["texto"])
        pintor.setPen(color)
        pintor.setFont(fuente(tema.FAMILIAS_INTERFAZ, 11.5, QFont.Weight.DemiBold))
        pintor.drawText(pildora, Qt.AlignmentFlag.AlignCenter, texto)
        pintor.setFont(fuente(tema.FAMILIAS_INTERFAZ, 8.5))
        pintor.setPen(con_alfa(color.name(), 0.6))
        caja = pildora.adjusted(0, 0, -radio * 0.7, 0)
        derecha = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        pintor.drawText(caja, derecha, tecla)


# ---------------------------------------------------------------------------
# Título de sección y tarjeta
# ---------------------------------------------------------------------------
class TituloSeccion(QWidget):
    """'01  DATOS': el número con el color de acento y el nombre en mayúsculas."""

    def __init__(self, numero, texto):
        super().__init__()
        self.numero, self.texto = numero, texto.upper()
        self._fuente = fuente(tema.FAMILIAS_MONO, 8.5, QFont.Weight.DemiBold, 1.6)
        self.setFixedHeight(18)
        self.setMinimumWidth(160)
        self.setAccessibleName(texto)

    def paintEvent(self, _evento):
        c = tema.paleta()
        pintor = QPainter(self)
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing)
        pintor.setFont(self._fuente)
        alinear = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        pintor.setPen(QColor(c["acento"]))
        pintor.drawText(self.rect(), alinear, self.numero)
        ancho = pintor.fontMetrics().horizontalAdvance(self.numero + "  ")
        pintor.setPen(QColor(c["etiqueta"]))
        pintor.drawText(self.rect().adjusted(ancho, 0, 0, 0), alinear, self.texto)


class Tarjeta(QWidget):
    """Módulo de vidrio: superficie translúcida, borde con brillo arriba y
    un título. El contenido se agrega a `self.contenido` (un QVBoxLayout).

    lado: "izquierda" o "derecha", dónde está la tarjeta respecto de la
    esfera. Del borde que mira a la esfera sale el hilo que la une con la
    órbita (ver `ancla`).
    """

    MARGEN = 20

    def __init__(self, numero, titulo, lado, extra=None):
        super().__init__()
        self.lado = lado
        diseno = QVBoxLayout(self)
        diseno.setContentsMargins(self.MARGEN, 16, self.MARGEN, 18)
        diseno.setSpacing(10)
        cabecera = QHBoxLayout()
        cabecera.addWidget(TituloSeccion(numero, titulo))
        cabecera.addStretch(1)
        if extra is not None:
            cabecera.addWidget(extra)
        diseno.addLayout(cabecera)
        self.contenido = QVBoxLayout()
        self.contenido.setSpacing(8)
        diseno.addLayout(self.contenido)

    def ancla(self):
        """Punto (en coordenadas de la tarjeta) donde se ata el hilo a la órbita."""
        x = self.width() if self.lado == "izquierda" else 0
        return QPointF(x, min(self.height() / 2, 64))

    def paintEvent(self, _evento):
        c = tema.paleta()
        pintor = QPainter(self)
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing)
        caja = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        cuerpo = QLinearGradient(caja.topLeft(), caja.bottomLeft())
        cuerpo.setColorAt(0, con_alfa(c["superficie_2"], 0.74))
        cuerpo.setColorAt(1, con_alfa(c["superficie"], 0.58))
        borde = QLinearGradient(caja.topLeft(), caja.bottomLeft())
        borde.setColorAt(0, con_alfa(c["texto"], 0.16))
        borde.setColorAt(0.35, con_alfa(c["borde"], 0.9))
        borde.setColorAt(1, con_alfa(c["borde"], 0.5))
        pintor.setPen(QPen(borde, 1))
        pintor.setBrush(cuerpo)
        pintor.drawRoundedRect(caja, RADIO_TARJETA, RADIO_TARJETA)
        # Una muesca de luz en el borde que mira a la esfera, donde nace el hilo
        ancla = self.ancla()
        brillo = QLinearGradient(0, ancla.y() - 36, 0, ancla.y() + 36)
        brillo.setColorAt(0, con_alfa(c["acento"], 0.0))
        brillo.setColorAt(0.5, con_alfa(c["acento"], 0.9))
        brillo.setColorAt(1, con_alfa(c["acento"], 0.0))
        pintor.setPen(QPen(brillo, 2))
        x = caja.right() if self.lado == "izquierda" else caja.left()
        pintor.drawLine(QPointF(x, ancla.y() - 36), QPointF(x, ancla.y() + 36))


# ---------------------------------------------------------------------------
# Pulsos de luz
# ---------------------------------------------------------------------------
class CapaPulsos(QWidget):
    """Capa transparente sobre toda la ventana que dibuja las ondas de los clics.

    No recibe el mouse (los clics pasan a lo que hay debajo). Cada onda es un
    destello que se abre y se apaga, con un anillo que crece; solo se repinta
    el cuadrado que ocupa cada onda.
    """

    def __init__(self, padre):
        super().__init__(padre)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._pulsos = []  # (centro, reloj)
        self._tic = QTimer(self)
        self._tic.setInterval(INTERVALO_MS)
        self._tic.timeout.connect(self._avanzar)

    def pulsar(self, centro):
        reloj = QElapsedTimer()
        reloj.start()
        self._pulsos.append((QPointF(centro), reloj))
        self.raise_()  # siempre encima, también de los créditos
        self._tic.start()

    def _avanzar(self):
        r = RADIO_PULSO + 4
        for centro, _ in self._pulsos:
            self.update(round(centro.x() - r), round(centro.y() - r), 2 * r, 2 * r)
        self._pulsos = [p for p in self._pulsos if p[1].elapsed() < DURACION_PULSO_MS]
        if not self._pulsos:
            self._tic.stop()

    def paintEvent(self, _evento):
        c = tema.paleta()
        pintor = QPainter(self)
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing)
        # Modo "suma": la luz aclara lo que hay debajo, como una luz de verdad
        pintor.setCompositionMode(QPainter.CompositionMode.CompositionMode_Plus)
        for centro, reloj in self._pulsos:
            avance = min(reloj.elapsed() / DURACION_PULSO_MS, 1.0)
            apagar = (1 - avance) ** 2
            radio = 40 + (RADIO_PULSO - 40) * salida_suave(avance)
            # Destello: un círculo de luz que se abre y se desvanece
            destello = QRadialGradient(centro, radio)
            destello.setColorAt(0, con_alfa(c["acento"], 0.22 * apagar))
            destello.setColorAt(0.6, con_alfa(c["acento_2"], 0.08 * apagar))
            destello.setColorAt(1, con_alfa(c["acento_2"], 0.0))
            pintor.setPen(Qt.PenStyle.NoPen)
            pintor.setBrush(destello)
            pintor.drawEllipse(centro, radio, radio)
            # Anillo que crece, cada vez más fino
            grosor = 2.5 * (1 - avance) + 0.5
            pintor.setBrush(Qt.BrushStyle.NoBrush)
            pintor.setPen(QPen(con_alfa(c["acento"], 0.6 * apagar), grosor))
            pintor.drawEllipse(centro, 0.8 * radio, 0.8 * radio)
