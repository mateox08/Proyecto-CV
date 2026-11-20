"""Gráfica 1: la Ventana de Viviani sobre la esfera, girando sola.

No se usa matplotlib aquí: dibujar una escena 3D con matplotlib en cada
cuadro es lento (unos 50 ms), y la animación se vería a saltos. En cambio,
la escena se dibuja "a mano" con QPainter, usando lo que se ve en Cálculo
Vectorial:

  1. Cada punto (x, y, z) se gira con una matriz de rotación.
  2. Se proyecta sobre la pantalla quitando la coordenada de profundidad
     (proyección ortogonal).
  3. La profundidad decide si el punto está delante o detrás de la esfera:
     lo de atrás se dibuja tenue y lo de adelante con brillo.

Toda la geometría se calcula para R = 1 y luego se escala: la forma de la
curva es la misma para cualquier radio; solo cambian los rótulos.
"""

import math

import numpy as np
from PySide6.QtCore import QElapsedTimer, QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPolygonF,
    QRadialGradient,
)
from PySide6.QtWidgets import QSizePolicy, QWidget

from viviani.formato import formatear_radio
from viviani.tema import FAMILIAS_MONO

GRADOS_POR_SEGUNDO = 15  # una vuelta completa cada 24 s: lento, no distrae
ELEVACION = math.radians(22)  # la cámara mira un poco desde arriba
ACIMUT_INICIAL = math.radians(35)
INTERVALO_MS = 16  # unos 60 cuadros por segundo
DURACION_CAMBIO_MS = 350  # la esfera crece o se encoge al cambiar R
TAMANO_CAMBIO = (0.55, 1.45)  # límites del tamaño inicial de esa transición
MARCAS = (-1.0, -0.5, 0.5, 1.0)  # posiciones de los números en los ejes (en R)


# ---------------------------------------------------------------------------
# Geometría (con R = 1)
# ---------------------------------------------------------------------------
def puntos_curva(cantidad=721):
    """r(t) = (cos²t, sen t cos t, sen t), t en [0, 2π]. Arreglo de 3 x cantidad."""
    t = np.linspace(0, 2 * math.pi, cantidad)
    return np.array([np.cos(t) ** 2, np.sin(t) * np.cos(t), np.sin(t)])


def lineas_esfera(meridianos=12, paralelos=(-60, -30, 0, 30, 60)):
    """Malla de la esfera: lista de arreglos 3 x k (meridianos y paralelos)."""
    lineas = []
    latitud = np.linspace(-math.pi / 2, math.pi / 2, 49)
    for k in range(meridianos):
        lon = 2 * math.pi * k / meridianos
        lineas.append(
            np.array(
                [
                    np.cos(latitud) * math.cos(lon),
                    np.cos(latitud) * math.sin(lon),
                    np.sin(latitud),
                ]
            )
        )
    longitud = np.linspace(0, 2 * math.pi, 97)
    for grados in paralelos:
        lat = math.radians(grados)
        lineas.append(
            np.array(
                [
                    math.cos(lat) * np.cos(longitud),
                    math.cos(lat) * np.sin(longitud),
                    np.full_like(longitud, math.sin(lat)),
                ]
            )
        )
    return lineas


def girar(puntos, acimut, elevacion=ELEVACION):
    """Gira los puntos y devuelve (horizontal, vertical, profundidad).

    Primero se gira `acimut` alrededor del eje Z y luego se inclina
    `elevacion` hacia la cámara. La profundidad es positiva para lo que está
    del lado de quien mira.
    """
    x, y, z = puntos
    # Rotación alrededor del eje Z
    x1 = x * math.cos(acimut) - y * math.sin(acimut)
    y1 = x * math.sin(acimut) + y * math.cos(acimut)
    # Inclinación: la cámara está arriba, mirando hacia el origen
    profundidad = x1 * math.cos(elevacion) + z * math.sin(elevacion)
    vertical = -x1 * math.sin(elevacion) + z * math.cos(elevacion)
    return y1, vertical, profundidad


def tramos(horizontal, vertical, delante):
    """Corta una línea en tramos que están todos delante o todos detrás.

    Devuelve una lista de (QPolygonF, esta_delante).
    """
    cortes = np.flatnonzero(np.diff(delante.astype(int))) + 1
    resultado = []
    inicio = 0
    for fin in [*cortes.tolist(), len(delante)]:
        # Se toma un punto más para que los tramos queden unidos
        tramo = slice(inicio, min(fin + 1, len(delante)))
        poligono = QPolygonF(
            [
                QPointF(h, v)
                for h, v in zip(horizontal[tramo], vertical[tramo], strict=True)
            ]
        )
        resultado.append((poligono, bool(delante[inicio])))
        inicio = fin
    return resultado


# ---------------------------------------------------------------------------
# El widget
# ---------------------------------------------------------------------------
class GraficaCurva3D(QWidget):
    def __init__(self, colores, reducir_movimiento=False, parent=None):
        super().__init__(parent)
        self.colores = colores
        self.radio = 5.0
        self._curva = puntos_curva()
        self._malla = lineas_esfera()
        self._acimut = ACIMUT_INICIAL
        # Transición al cambiar el radio: tamaño de partida y su reloj
        self._tamano_inicial = 1.0
        self._escena = None  # (centro, escala) del último dibujo
        self._zona = None  # rectángulo libre donde va la esfera (o None)
        self._cambio = QElapsedTimer()
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.setMinimumSize(280, 280)
        self.setAccessibleName(self.descripcion_accesible())

        # Giro continuo. El ángulo sale del tiempo real transcurrido, así la
        # velocidad es la misma aunque algún cuadro se atrase.
        self._girar = not reducir_movimiento
        self._reloj = QElapsedTimer()
        self._temporizador = QTimer(self)
        self._temporizador.setInterval(INTERVALO_MS)
        self._temporizador.timeout.connect(self._avanzar)

    # --- Interfaz pública ----------------------------------------------
    def mostrar(self, radio):
        """Cambia el radio.

        La esfera siempre ocupa el mismo lugar en la pantalla; lo que cambia
        son los números de los ejes (en cm). Para que se note el cambio, la
        esfera parte del tamaño que tendría el radio anterior con los ejes
        nuevos y crece (o se encoge) hasta su tamaño normal.
        """
        if self._girar and radio != self.radio:
            minimo, maximo = TAMANO_CAMBIO
            self._tamano_inicial = min(max(self.radio / radio, minimo), maximo)
            self._cambio.start()
        self.radio = radio
        self.setAccessibleName(self.descripcion_accesible())
        self.update()

    def establecer_zona(self, zona):
        """Indica el rectángulo libre (sin controles encima) para la esfera."""
        self._zona = zona
        self.update()

    def descripcion_accesible(self):
        radio = formatear_radio(self.radio)
        return (
            "Gráfica 3D de la Ventana de Viviani sobre una esfera de radio "
            f"{radio} centímetros, girando. Punto doble en ({radio}, 0, 0)."
        )

    # --- Giro ---------------------------------------------------------
    def showEvent(self, evento):
        super().showEvent(evento)
        if self._girar:
            self._acimut_base = self._acimut
            self._reloj.start()
            self._temporizador.start()

    def hideEvent(self, evento):
        super().hideEvent(evento)
        self._temporizador.stop()  # no se gasta nada si no se ve

    def _avanzar(self):
        segundos = self._reloj.elapsed() / 1000
        self._acimut = self._acimut_base + math.radians(GRADOS_POR_SEGUNDO * segundos)
        self._repintar_escena()

    def _repintar_escena(self):
        """Pide repintar solo el cuadrado donde está la esfera.

        La gráfica ocupa toda la ventana, pero la escena está en el centro:
        así no se redibujan, 60 veces por segundo, los controles de los lados.
        """
        if self._escena is None:
            self.update()
            return
        centro, escala = self._escena
        mitad = 1.55 * escala + 40
        self.update(
            round(centro.x() - mitad), round(centro.y() - mitad),
            round(2 * mitad), round(2 * mitad),
        )  # fmt: skip

    def _tamano_actual(self):
        """Tamaño de la esfera durante la transición (1 = normal)."""
        if not self._cambio.isValid():
            return 1.0
        avance = self._cambio.elapsed() / DURACION_CAMBIO_MS
        if avance >= 1:
            self._cambio.invalidate()
            return 1.0
        suave = 1 - (1 - avance) ** 3  # empieza rápido y frena al final
        return self._tamano_inicial + (1 - self._tamano_inicial) * suave

    # --- Dibujo --------------------------------------------------------
    def paintEvent(self, _evento):
        pintor = QPainter(self)
        self._pintar(pintor, self.width(), self.height(), self.colores)
        pintor.end()

    def _pintar(self, pintor, ancho, alto, colores):
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing)
        # La esfera se centra en la zona libre que indica la ventana
        zona = QRectF(0, 0, ancho, alto) if self._zona is None else self._zona
        lado = min(zona.width(), zona.height())
        escala = 0.36 * lado  # radio de la esfera en píxeles
        centro = zona.center() + QPointF(0, 0.03 * lado)
        self._escena = (centro, escala)  # para repintar solo esa zona
        grosor = lado / 600  # los grosores crecen con el tamaño

        tamano = self._tamano_actual()

        def proyectar(puntos, factor):
            h, v, d = girar(puntos, self._acimut)
            return centro.x() + factor * h, centro.y() - factor * v, d >= 0

        # La esfera y la curva usan el tamaño de la transición; los ejes no
        def a_pantalla(puntos):
            return proyectar(puntos, escala * tamano)

        def a_ejes(puntos):
            return proyectar(puntos, escala)

        self._pintar_ejes(pintor, a_ejes, colores, grosor, lado, delante=False)
        caminos_malla = self._caminos(self._malla, a_pantalla)
        caminos_curva = self._caminos([self._curva], a_pantalla)

        # 1. Lo que está detrás de la esfera: tenue
        self._trazar(
            pintor, caminos_malla[False], colores["esfera"], 0.22, 0.9 * grosor
        )
        self._trazar(
            pintor, caminos_curva[False], colores["serie_azul"], 0.30, 1.8 * grosor
        )

        # 2. La esfera como un vidrio: degradado radial y contorno
        self._pintar_esfera(pintor, centro, escala * tamano, colores, grosor)

        # 3. Lo que está delante: malla más marcada y la curva con brillo
        self._trazar(pintor, caminos_malla[True], colores["esfera"], 0.50, 1.0 * grosor)
        self._trazar_con_brillo(pintor, caminos_curva[True], colores, grosor, ancho)
        self._pintar_punto_doble(pintor, a_pantalla, colores, grosor, lado)
        self._pintar_ejes(pintor, a_ejes, colores, grosor, lado, delante=True)
        self._pintar_marcas(pintor, a_ejes, colores, grosor, lado)
        self._pintar_rotulos(pintor, lado, colores)

    @staticmethod
    def _caminos(lineas, a_pantalla):
        """Une todos los tramos de delante en un camino y los de atrás en otro."""
        caminos = {True: QPainterPath(), False: QPainterPath()}
        for linea in lineas:
            h, v, delante = a_pantalla(linea)
            for poligono, esta_delante in tramos(h, v, delante):
                caminos[esta_delante].addPolygon(poligono)
        return caminos

    @staticmethod
    def _trazar(pintor, camino, color, alfa, ancho):
        tono = QColor(color)
        tono.setAlphaF(alfa)
        pluma = QPen(tono, ancho)
        pluma.setCapStyle(Qt.PenCapStyle.RoundCap)
        pintor.setPen(pluma)
        pintor.setBrush(Qt.BrushStyle.NoBrush)
        pintor.drawPath(camino)

    @staticmethod
    def _trazar_con_brillo(pintor, camino, colores, grosor, ancho):
        """La curva se dibuja dos veces: un halo tenue y la línea nítida.

        El color pasa de menta a azul cielo de izquierda a derecha.
        """
        for ancho_pluma, alfa in ((8, 0.10), (2.6, 1.0)):
            degradado = QLinearGradient(0, 0, ancho, 0)
            for posicion, nombre in ((0.0, "serie_azul"), (1.0, "serie_turquesa")):
                tono = QColor(colores[nombre])
                tono.setAlphaF(alfa)
                degradado.setColorAt(posicion, tono)
            pluma = QPen(QBrush(degradado), ancho_pluma * grosor)
            pluma.setCapStyle(Qt.PenCapStyle.RoundCap)
            pluma.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            pintor.setPen(pluma)
            pintor.drawPath(camino)

    @staticmethod
    def _pintar_esfera(pintor, centro, escala, colores, grosor):
        luz = QPointF(centro.x() - 0.35 * escala, centro.y() - 0.4 * escala)
        degradado = QRadialGradient(luz, 1.4 * escala)
        # Vidrio oscuro con un reflejo blanco muy leve
        claro, sombra = QColor("#FFFFFF"), QColor(colores["esfera"])
        claro.setAlphaF(0.06)
        sombra.setAlphaF(0.02)
        degradado.setColorAt(0, claro)
        degradado.setColorAt(1, sombra)
        borde = QColor(colores["esfera"])
        borde.setAlphaF(0.55)
        pintor.setPen(QPen(borde, 1.2 * grosor))
        pintor.setBrush(QBrush(degradado))
        pintor.drawEllipse(centro, escala, escala)

    def _pintar_punto_doble(self, pintor, a_pantalla, colores, grosor, lado):
        """El punto doble (R, 0, 0), con un pequeño halo, y su rótulo."""
        h, v, delante = a_pantalla(np.array([[1.0], [0.0], [0.0]]))
        punto = QPointF(float(h[0]), float(v[0]))
        color = QColor(colores["punto_doble"])
        opacidad = 1.0 if delante[0] else 0.35
        for radio, alfa in ((11, 0.15), (7, 0.30), (4.5, 1.0)):
            tono = QColor(color)
            tono.setAlphaF(alfa * opacidad)
            pintor.setPen(Qt.PenStyle.NoPen)
            pintor.setBrush(tono)
            pintor.drawEllipse(punto, radio * grosor, radio * grosor)
        texto = QColor(colores["texto"])
        texto.setAlphaF(opacidad)
        pintor.setPen(texto)
        pintor.setFont(self._fuente(FAMILIAS_MONO, 0.024 * lado))
        pintor.drawText(punto + QPointF(14 * grosor, 26 * grosor), "(R, 0, 0)")

    def _pintar_ejes(self, pintor, a_pantalla, colores, grosor, lado, delante):
        """Ejes X, Y, Z. Primero la parte de adentro (bajo la esfera), al
        final la que sobresale, con su nombre en mayúscula."""
        color = QColor(colores["etiqueta"])
        for indice, nombre in enumerate("XYZ"):
            extremo = np.zeros((3, 2))
            if delante:
                extremo[indice] = (1.0, 1.32)
            else:
                extremo[indice] = (-1.32, 1.0)
            h, v, _ = a_pantalla(extremo)
            color.setAlphaF(0.75 if delante else 0.35)
            pintor.setPen(QPen(color, 1.1 * grosor))
            pintor.drawLine(QPointF(h[0], v[0]), QPointF(h[1], v[1]))
            if delante:
                pintor.setFont(self._fuente(FAMILIAS_MONO, 0.03 * lado, negrita=True))
                rotulo = QPointF(h[1], v[1]) + QPointF(6 * grosor, -6 * grosor)
                pintor.drawText(rotulo, nombre)

    def _pintar_marcas(self, pintor, a_ejes, colores, grosor, lado):
        """Números en cm sobre cada eje: -R, -R/2, R/2 y R."""
        pintor.setFont(self._fuente(FAMILIAS_MONO, 0.021 * lado))
        for indice in range(3):
            puntos = np.zeros((3, len(MARCAS)))
            puntos[indice] = MARCAS
            h, v, delante = a_ejes(puntos)
            for k, posicion in enumerate(MARCAS):
                if indice == 0 and posicion == 1.0:
                    continue  # ahí está el punto doble, que ya tiene su rótulo
                color = QColor(colores["texto_sec"])
                color.setAlphaF(0.9 if delante[k] else 0.45)
                punto = QPointF(h[k], v[k])
                pintor.setPen(Qt.PenStyle.NoPen)
                pintor.setBrush(color)
                pintor.drawEllipse(punto, 1.8 * grosor, 1.8 * grosor)
                pintor.setPen(color)
                texto = formatear_radio(posicion * self.radio)
                pintor.drawText(punto + QPointF(5 * grosor, 13 * grosor), texto)

    def _pintar_rotulos(self, pintor, lado, colores):
        """El radio actual, debajo de la esfera y a la izquierda del eje Z."""
        centro, escala = self._escena
        pintor.setPen(QColor(colores["texto_sec"]))
        pintor.setFont(self._fuente(FAMILIAS_MONO, 0.022 * lado))
        radio = f"R = {formatear_radio(self.radio)} cm"
        pintor.drawText(centro + QPointF(-1.05 * escala, 1.12 * escala), radio)

    @staticmethod
    def _fuente(familias, pixeles, negrita=False):
        fuente = QFont()
        fuente.setFamilies(familias)
        fuente.setPixelSize(max(10, round(pixeles)))
        fuente.setBold(negrita)
        return fuente
