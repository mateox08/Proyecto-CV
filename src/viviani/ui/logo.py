"""El logo de la aplicación: la Ventana de Viviani vista de frente.

Vista desde el eje X, la curva r(t) = (cos²t, sen t cos t, sen t) se ve como
un "8": en pantalla se dibuja (y, z) = (sen t cos t, sen t). El cruce del 8 es
el punto doble (R, 0, 0).

Solo usa `math` y Qt (nada de numpy ni matplotlib) para poder dibujarse en
cuanto arranca el programa, en la pantalla de carga.
"""

import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QImage,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QRadialGradient,
)

from viviani import tema


def _color(hexadecimal, alfa):
    tono = QColor(hexadecimal)
    tono.setAlphaF(alfa)
    return tono


def camino_curva(centro, radio, giro=0.0, puntos=240, fraccion=1.0):
    """La curva de Viviani girada `giro` radianes alrededor del eje Z.

    fraccion: qué parte de la curva se dibuja (de t = 0 a t = 2π·fraccion).
    """
    camino = QPainterPath()
    inclinacion = math.radians(12)  # se mira un poco desde arriba
    for i in range(puntos + 1):
        t = 2 * math.pi * fraccion * i / puntos
        x, y, z = math.cos(t) ** 2, math.sin(t) * math.cos(t), math.sin(t)
        # giro alrededor de Z y luego inclinación (igual que en curva3d.py)
        x1 = x * math.cos(giro) - y * math.sin(giro)
        y1 = x * math.sin(giro) + y * math.cos(giro)
        vertical = -x1 * math.sin(inclinacion) + z * math.cos(inclinacion)
        punto = QPointF(centro.x() + radio * y1, centro.y() - radio * vertical)
        if i == 0:
            camino.moveTo(punto)
        else:
            camino.lineTo(punto)
    return camino


def dibujar_logo(pintor, rect, giro=0.0, con_fondo=True, fraccion=1.0):
    """Dibuja el logo dentro de `rect` (un QRectF cuadrado).

    fraccion < 1 dibuja solo esa parte de la curva (la pantalla de carga la
    va completando a medida que avanza).
    """
    c = tema.paleta()
    pintor.save()
    pintor.setRenderHint(QPainter.RenderHint.Antialiasing)
    lado = min(rect.width(), rect.height())
    centro = rect.center()

    if con_fondo:
        # Cuadrado redondeado oscuro con un borde del color de acento, tenue
        fondo = QLinearGradient(rect.topLeft(), rect.bottomRight())
        fondo.setColorAt(0, QColor(c["superficie_2"]))
        fondo.setColorAt(1, QColor(c["fondo"]))
        radio_esquina = 0.22 * lado
        pintor.setPen(QPen(_color(c["acento"], 0.35), max(1.0, lado / 128)))
        pintor.setBrush(fondo)
        pintor.drawRoundedRect(
            rect.adjusted(1, 1, -1, -1), radio_esquina, radio_esquina
        )

    radio = 0.33 * lado

    # Esfera: un círculo de vidrio con luz arriba a la izquierda
    luz = QRadialGradient(centro + QPointF(-0.35 * radio, -0.4 * radio), 1.5 * radio)
    luz.setColorAt(0, _color(c["acento"], 0.22))
    luz.setColorAt(1, _color(c["acento_2"], 0.04))
    pintor.setBrush(luz)
    pintor.setPen(QPen(_color(c["esfera"], 0.6), max(1.0, lado / 160)))
    pintor.drawEllipse(centro, radio, radio)
    # Ecuador como una elipse aplastada
    pintor.setBrush(Qt.BrushStyle.NoBrush)
    pintor.setPen(QPen(_color(c["esfera"], 0.3), max(0.8, lado / 220)))
    pintor.drawEllipse(centro, radio, 0.22 * radio)

    # La curva con brillo: tres trazos superpuestos con el degradado de acento
    camino = camino_curva(centro, radio, giro, fraccion=fraccion)
    for grosor, alfa in ((0.07, 0.10), (0.035, 0.28), (0.016, 1.0)):
        degradado = QLinearGradient(rect.topLeft(), rect.bottomRight())
        degradado.setColorAt(0, _color(c["acento"], alfa))
        degradado.setColorAt(1, _color(c["acento_2"], alfa))
        pluma = QPen(degradado, max(1.0, grosor * lado))
        pluma.setCapStyle(Qt.PenCapStyle.RoundCap)
        pluma.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        pintor.setPen(pluma)
        pintor.drawPath(camino)

    # Punto doble en el cruce del 8, con un halo
    punto = camino_curva(centro, radio, giro, puntos=4).pointAtPercent(0)
    pintor.setPen(Qt.PenStyle.NoPen)
    for tamano, alfa in ((0.06, 0.25), (0.032, 1.0)):
        pintor.setBrush(_color(c["punto_doble"], alfa))
        pintor.drawEllipse(punto, tamano * lado, tamano * lado)
    pintor.restore()


def imagen_logo(lado):
    """QImage cuadrada de `lado` píxeles con el logo (para iconos)."""

    imagen = QImage(lado, lado, QImage.Format.Format_ARGB32_Premultiplied)
    imagen.fill(Qt.GlobalColor.transparent)
    pintor = QPainter(imagen)
    dibujar_logo(pintor, QRectF(0, 0, lado, lado))
    pintor.end()
    return imagen
