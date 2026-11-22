"""Gráfica 1: la Ventana de Viviani sobre la esfera, girando sola.

No se usa matplotlib aquí: dibujar una escena 3D con matplotlib en cada
cuadro es lento, y la animación se vería a saltos. En cambio, la escena se
dibuja "a mano" con QPainter, usando lo que se ve en Cálculo Vectorial:

  1. Cada punto (x, y, z) se gira con una matriz de rotación.
  2. Se proyecta sobre la pantalla quitando la coordenada de profundidad
     (proyección ortogonal).
  3. La profundidad decide cómo se ve cada punto: lo de atrás de la esfera
     tenue y delgado, lo de adelante brillante y grueso.

Qué se ve:
  - la esfera x² + y² + z² = R² (malla de meridianos y paralelos);
  - el cilindro (x − R/2)² + y² = (R/2)²: la curva es justo donde el
    cilindro corta a la esfera, así que sus generatrices van de una rama de
    la curva a la otra;
  - la curva r(t), con un "cometa" que la recorre para mostrar el sentido
    en que crece t;
  - después de calcular, los puntos de muestra r(tᵢ) aparecen uno a uno, al
    mismo ritmo que los rectángulos de la suma de Riemann;
  - al pasar el mouse sobre la gráfica de Riemann, el punto r(t) y su
    vector velocidad r′(t): la altura f(t) de cada rectángulo es justamente
    la rapidez ‖r′(t)‖;
  - alrededor, la órbita: un anillo con marcas que giran despacio, un
    satélite que lo recorre y los hilos que lo unen con cada tarjeta. Al
    calcular, un destello viaja por los hilos: de los datos a la esfera y de
    la esfera a los resultados.

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
    QPixmap,
    QPolygonF,
    QRadialGradient,
    QRegion,
)
from PySide6.QtWidgets import QSizePolicy, QWidget

from viviani.animacion import Animacion, salida_suave
from viviani.formato import formatear_radio
from viviani.graficas.barrido import (
    DURACION_BARRA_MS,
    DURACION_BARRIDO_MS,
    inicios_escalonados,
)
from viviani.tema import FAMILIAS_MONO, con_alfa

GRADOS_POR_SEGUNDO = 15  # una vuelta completa cada 24 s: lento, no distrae
ELEVACION = math.radians(22)  # la cámara mira un poco desde arriba
ACIMUT_INICIAL = math.radians(35)
INTERVALO_MS = 16  # unos 60 cuadros por segundo
DURACION_INTRO_MS = 1600  # al abrir, la curva se dibuja de t = 0 a t = 2π
DURACION_CAMBIO_MS = 350  # la esfera crece o se encoge al cambiar R
TAMANO_CAMBIO = (0.55, 1.45)  # límites del tamaño inicial de esa transición
PERIODO_COMETA_S = 7.0  # el cometa da una vuelta a la curva cada 7 s
COLA_COMETA = 1.1  # largo de la cola del cometa (en radianes de t)
MARCAS = (-1.0, -0.5, 0.5, 1.0)  # posiciones de los números en los ejes (en R)
NIVELES = 6  # tonos de profundidad de la curva (3 detrás, 3 delante)
ESCALA_VECTOR = 0.45  # r′(t) se dibuja a esta escala para que quepa
ORBITA = 1.45  # radio del anillo orbital (en radios de la esfera)
MARCAS_ORBITA = 120  # marcas del anillo (una de cada 10 más larga)
GRADOS_ORBITA_POR_SEGUNDO = -4  # el anillo gira despacio, al revés que la esfera
PERIODO_SATELITE_S = 30.0
DURACION_ENVIO_MS = 550  # lo que tarda un destello en recorrer un hilo
CAPAS = ("malla", "cilindro", "ejes")


# ---------------------------------------------------------------------------
# Geometría (con R = 1)
# ---------------------------------------------------------------------------
def punto(t):
    """r(t) = (cos²t, sen t cos t, sen t). t puede ser un número o un arreglo."""
    t = np.asarray(t, dtype=float)
    return np.array([np.cos(t) ** 2, np.sin(t) * np.cos(t), np.sin(t)])


def velocidad(t):
    """r′(t) = (−sen 2t, cos 2t, cos t). Su norma es √(1 + cos²t) = f(t)/R."""
    t = np.asarray(t, dtype=float)
    return np.array([-np.sin(2 * t), np.cos(2 * t), np.cos(t)])


def puntos_curva(cantidad=721):
    """La curva completa, t en [0, 2π]. Arreglo de 3 x cantidad."""
    return punto(np.linspace(0, 2 * math.pi, cantidad))


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


def generatrices_cilindro(cantidad=28):
    """Segmentos verticales del cilindro (x − ½)² + y² = ¼ dentro de la esfera.

    En el cilindro x² + y² = x, así que la esfera deja z² ≤ 1 − x: cada
    generatriz va de z = −√(1 − x) a z = √(1 − x), es decir, de una rama
    de la curva a la otra.
    """
    lineas = []
    for k in range(cantidad):
        theta = 2 * math.pi * (k + 0.5) / cantidad
        x = 0.5 + 0.5 * math.cos(theta)
        y = 0.5 * math.sin(theta)
        alto = math.sqrt(max(0.0, 1 - x))
        z = np.linspace(-alto, alto, 17)
        lineas.append(np.array([np.full_like(z, x), np.full_like(z, y), z]))
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


def tramos(horizontal, vertical, grupo):
    """Corta una línea en tramos donde `grupo` (arreglo de enteros) no cambia.

    Devuelve una lista de (QPolygonF, grupo del tramo).
    """
    cortes = np.flatnonzero(np.diff(grupo)) + 1
    resultado = []
    inicio = 0
    for fin in [*cortes.tolist(), len(grupo)]:
        # Se toma un punto más para que los tramos queden unidos
        tramo = slice(inicio, min(fin + 1, len(grupo)))
        poligono = QPolygonF(
            [
                QPointF(h, v)
                for h, v in zip(horizontal[tramo], vertical[tramo], strict=True)
            ]
        )
        resultado.append((poligono, int(grupo[inicio])))
        inicio = fin
    return resultado


def nivel_de_profundidad(profundidad):
    """Profundidad en [−1, 1] -> nivel entero 0..NIVELES−1 (0 = lo más lejano)."""
    nivel = np.floor((profundidad + 1) / 2 * NIVELES).astype(int)
    return np.clip(nivel, 0, NIVELES - 1)


class _Camara:
    """Convierte puntos 3D (con R = 1) en puntos de la pantalla."""

    def __init__(self, centro, factor, acimut):
        self.centro, self.factor, self.acimut = centro, factor, acimut

    def proyectar(self, puntos):
        """Devuelve (h, v, profundidad) en píxeles; puntos: arreglo 3 x k."""
        h, v, d = girar(puntos, self.acimut)
        return self.centro.x() + self.factor * h, self.centro.y() - self.factor * v, d

    def a_punto(self, xyz):
        """Un solo punto 3D -> (QPointF, profundidad)."""
        h, v, d = self.proyectar(np.reshape(xyz, (3, 1)))
        return QPointF(float(h[0]), float(v[0])), float(d[0])


# ---------------------------------------------------------------------------
# El widget
# ---------------------------------------------------------------------------
class GraficaCurva3D(QWidget):
    def __init__(self, colores, reducir_movimiento=False, parent=None):
        super().__init__(parent)
        self.colores = colores
        self.radio = 5.0
        self._quieto = reducir_movimiento
        self._curva = puntos_curva()
        self._malla = lineas_esfera()
        self._cilindro = generatrices_cilindro()
        self.capas = dict.fromkeys(CAPAS, True)
        self._acimut = ACIMUT_INICIAL
        self._escena = None  # (centro, escala) del último dibujo
        self._cuadro = None  # la escena ya dibujada (ver paintEvent)
        self._pendiente = QRegion()  # zonas de esa imagen que hay que rehacer
        self._zona = None  # rectángulo libre donde va la esfera (o None)

        # Transición al cambiar el radio: tamaño de partida y su reloj
        self._tamano_inicial = 1.0
        self._cambio = QElapsedTimer()
        # Presentación: la curva se va dibujando al abrir la ventana
        self._intro = 0.0 if not reducir_movimiento else 1.0
        self._reloj_intro = QElapsedTimer()

        # Puntos de muestra r(tᵢ) y el barrido que los va mostrando
        self._muestras = None  # arreglo con los tᵢ (o None antes de calcular)
        self._barrido_ms = None  # ms del barrido (None: sin barrido activo)
        self._barrido = Animacion(self, self._al_barrer, self._al_terminar_barrido)
        self._resaltado = None  # t que se señala desde la gráfica de Riemann
        # Hilos a las tarjetas: (punto de la tarjeta, "izquierda"/"derecha")
        self._anclas = []
        self._envio = QElapsedTimer()  # destello que viaja por los hilos
        self._envio_entrante = True  # True: de las tarjetas de la izquierda

        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.setMinimumSize(280, 280)
        self.setAccessibleName(self.descripcion_accesible())

        # Giro continuo. El ángulo sale del tiempo real transcurrido, así la
        # velocidad es la misma aunque algún cuadro se atrase.
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
        if not self._quieto and radio != self.radio:
            minimo, maximo = TAMANO_CAMBIO
            self._tamano_inicial = min(max(self.radio / radio, minimo), maximo)
            self._cambio.start()
        self.radio = radio
        self.setAccessibleName(self.descripcion_accesible())
        self._invalidar()

    def barrer(self, puntos_t):
        """Muestra los puntos r(tᵢ): uno a uno, al ritmo de los rectángulos."""
        self._muestras = np.asarray(puntos_t, dtype=float)
        if self._quieto:
            self._barrido_ms = None
            self._invalidar()
        else:
            self._barrido.iniciar(DURACION_BARRIDO_MS)

    def esta_animando(self):
        return self._barrido.activa()

    def saltar_animacion(self):
        self._barrido.terminar()

    def resaltar(self, t):
        """Señala r(t) y su vector velocidad; t = None lo quita."""
        if t != self._resaltado:
            self._resaltado = t
            self._repintar_escena()

    def establecer_capa(self, nombre, visible):
        """Muestra u oculta una capa: "malla", "cilindro" o "ejes"."""
        self.capas[nombre] = visible
        self._repintar_escena()

    def establecer_zona(self, zona, anclas=()):
        """Indica el rectángulo libre para la esfera y dónde están las tarjetas.

        anclas: lista de (QPointF, lado) con el punto de cada tarjeta donde se
        ata su hilo y de qué lado de la esfera está ("izquierda"/"derecha").
        """
        self._zona = zona
        self._anclas = list(anclas)
        self._invalidar()

    def enviar(self, entrante):
        """Un destello recorre los hilos: entrante (de los datos a la esfera)
        o saliente (de la esfera a los resultados)."""
        if not self._quieto:
            self._envio_entrante = entrante
            self._envio.start()

    def descripcion_accesible(self):
        radio = formatear_radio(self.radio)
        return (
            "Gráfica 3D de la Ventana de Viviani sobre una esfera de radio "
            f"{radio} centímetros, girando. Punto doble en ({radio}, 0, 0)."
        )

    # --- Tiempo ---------------------------------------------------------
    def showEvent(self, evento):
        super().showEvent(evento)
        if self._quieto:
            return
        if self._intro < 1:
            self._reloj_intro.start()
        self._acimut_base = self._acimut
        self._reloj.start()
        self._temporizador.start()

    def hideEvent(self, evento):
        super().hideEvent(evento)
        self._temporizador.stop()  # no se gasta nada si no se ve

    def _avanzar(self):
        segundos = self._reloj.elapsed() / 1000
        self._acimut = self._acimut_base + math.radians(GRADOS_POR_SEGUNDO * segundos)
        if self._intro < 1:
            self._intro = min(1.0, self._reloj_intro.elapsed() / DURACION_INTRO_MS)
        self._repintar_escena()

    def _al_barrer(self, ms):
        self._barrido_ms = ms  # el giro continuo ya repinta 60 veces por segundo

    def _al_terminar_barrido(self):
        self._barrido_ms = None
        self._repintar_escena()

    def _repintar_escena(self):
        """Pide repintar solo el cuadrado donde está la esfera.

        La gráfica ocupa toda la ventana, pero la escena está en el centro:
        así no se redibujan, 60 veces por segundo, los controles de los lados.
        """
        if self._escena is None:
            self._invalidar()
            return
        centro, _ = self._escena
        region = QRegion(self._cuadro_escena())
        if self._envio_activo():
            # El destello sale del cuadrado de la esfera: se agregan los hilos
            for ancla, _ in self._anclas:
                caja = QRectF(ancla, centro).normalized().adjusted(-12, -12, 12, 12)
                region = region.united(caja.toAlignedRect())
        self._invalidar(region)

    def _invalidar(self, region=None):
        """Marca una zona para volver a dibujarla (None: toda la gráfica)."""
        region = QRegion(self.rect()) if region is None else region
        self._pendiente = self._pendiente.united(region)
        self.update(region)

    def _envio_activo(self):
        return self._envio.isValid() and self._envio.elapsed() < DURACION_ENVIO_MS + 50

    def _tamano_actual(self):
        """Tamaño de la esfera durante la transición (1 = normal)."""
        if not self._cambio.isValid():
            inicial, avance = 1.0, 1.0
        else:
            inicial = self._tamano_inicial
            avance = self._cambio.elapsed() / DURACION_CAMBIO_MS
            if avance >= 1:
                self._cambio.invalidate()
        intro = 0.86 + 0.14 * salida_suave(self._intro / 0.6)
        return intro * (inicial + (1 - inicial) * salida_suave(avance))

    # --- Dibujo --------------------------------------------------------
    def resizeEvent(self, evento):
        super().resizeEvent(evento)
        self._cuadro = None  # la imagen guardada ya no sirve
        self._invalidar()

    def paintEvent(self, evento):
        """Pega en pantalla el último cuadro de la escena, guardado en una imagen.

        La escena solo se recalcula en las zonas "sucias" (las que cambiaron
        desde el último cuadro). Si Qt pide repintar por otra razón (la onda
        de un clic, el fundido de los créditos, el logo que gira encima),
        basta con copiar la imagen: así nunca se dibuja la escena dos veces
        en el mismo cuadro y la animación no da tirones.
        """
        if self._cuadro is None:
            proporcion = self.devicePixelRatioF()
            self._cuadro = QPixmap(self.size() * proporcion)
            self._cuadro.setDevicePixelRatio(proporcion)
            # Llenarla de transparente la crea con canal alfa; sin esto queda
            # negra donde no hay escena y tapa el cielo con estrellas
            self._cuadro.fill(Qt.GlobalColor.transparent)
            self._pendiente = QRegion(self.rect())
        if not self._pendiente.isEmpty():
            pintor = QPainter(self._cuadro)
            pintor.setClipRegion(self._pendiente)
            pintor.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
            pintor.fillRect(self.rect(), Qt.GlobalColor.transparent)
            pintor.setCompositionMode(
                QPainter.CompositionMode.CompositionMode_SourceOver
            )
            self._pintar(pintor, self.width(), self.height())
            pintor.end()
            self._pendiente = QRegion()
        pintor = QPainter(self)
        pintor.setClipRegion(evento.region())
        pintor.drawPixmap(0, 0, self._cuadro)
        pintor.end()

    def _cuadro_escena(self):
        """El cuadrado (QRect) que ocupa la escena: esfera, órbita y rótulos.

        Es lo único que cambia de un cuadro a otro. Antes del primer dibujo:
        toda la gráfica.
        """
        if self._escena is None:
            return self.rect()
        centro, escala = self._escena
        mitad = 1.75 * escala + 60
        return QRectF(centro.x() - mitad, centro.y() - mitad,
                      2 * mitad, 2 * mitad).toAlignedRect()  # fmt: skip

    def _pintar(self, pintor, ancho, alto):
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = self.colores
        # La esfera se centra en la zona libre que indica la ventana
        zona = QRectF(0, 0, ancho, alto) if self._zona is None else self._zona
        lado = min(zona.width(), zona.height())
        escala = 0.33 * lado  # radio de la esfera en píxeles
        centro = zona.center() + QPointF(0, 0.02 * lado)
        self._escena = (centro, escala)  # para repintar solo esa zona
        grosor = lado / 600  # los grosores crecen con el tamaño

        # La esfera y la curva usan el tamaño de la transición; los ejes no
        camara = _Camara(centro, escala * self._tamano_actual(), self._acimut)
        ejes = _Camara(centro, escala, self._acimut)
        aparicion = salida_suave(self._intro / 0.5)  # la malla aparece al abrir

        self._pintar_halo(pintor, centro, escala)
        self._pintar_orbita(pintor, centro, escala, grosor)
        if self.capas["ejes"]:
            self._pintar_ejes(pintor, ejes, grosor, lado, delante=False)
        malla = self._caminos(self._malla, camara) if self.capas["malla"] else None
        cilindro = (
            self._caminos(self._cilindro, camara) if self.capas["cilindro"] else None
        )
        curva = self._caminos_curva(camara)

        # 1. Lo que está detrás de la esfera: tenue
        if malla:
            self._trazar(pintor, malla[0], c["esfera"], 0.20 * aparicion, 0.9 * grosor)
        if cilindro:
            self._trazar(pintor, cilindro[0], c["cilindro"], 0.10, 0.9 * grosor)
        self._trazar_curva(pintor, curva, grosor, ancho, delante=False)

        # 2. La esfera como un vidrio con el borde iluminado
        self._pintar_esfera(pintor, centro, camara.factor, grosor)

        # 3. Lo que está delante: más marcado, y la curva con brillo
        if malla:
            self._trazar(pintor, malla[1], c["esfera"], 0.45 * aparicion, grosor)
        if cilindro:
            self._trazar(pintor, cilindro[1], c["cilindro"], 0.26, grosor)
        self._trazar_curva(pintor, curva, grosor, ancho, delante=True)

        # 4. Lo que se mueve sobre la curva
        self._pintar_muestras(pintor, camara, grosor)
        self._pintar_cometa(pintor, camara, grosor)
        self._pintar_punto_doble(pintor, camara, grosor, lado)
        if self._resaltado is not None:
            self._pintar_velocidad(pintor, camara, grosor, lado)

        # 5. Ejes (la parte que sobresale), números y radio
        if self.capas["ejes"]:
            self._pintar_ejes(pintor, ejes, grosor, lado, delante=True)
            self._pintar_marcas(pintor, ejes, grosor, lado)
        pintor.setPen(QColor(c["texto_sec"]))
        pintor.setFont(self._fuente(FAMILIAS_MONO, 0.022 * lado))
        radio = f"R = {formatear_radio(self.radio)} cm"
        pintor.drawText(centro + QPointF(-1.05 * escala, 1.12 * escala), radio)

    # --- Piezas del dibujo ----------------------------------------------
    @staticmethod
    def _caminos(lineas, camara):
        """Une los tramos de atrás en un camino (índice 0) y los de adelante (1)."""
        caminos = [QPainterPath(), QPainterPath()]
        for linea in lineas:
            h, v, d = camara.proyectar(linea)
            for poligono, delante in tramos(h, v, (d >= 0).astype(int)):
                caminos[delante].addPolygon(poligono)
        return caminos

    def _caminos_curva(self, camara):
        """Un camino por nivel de profundidad. Al abrir, solo lo ya dibujado."""
        cuantos = max(2, round(self._intro * (self._curva.shape[1] - 1)) + 1)
        h, v, d = camara.proyectar(self._curva[:, :cuantos])
        caminos = [QPainterPath() for _ in range(NIVELES)]
        for poligono, nivel in tramos(h, v, nivel_de_profundidad(d)):
            caminos[nivel].addPolygon(poligono)
        return caminos

    def _degradado(self, ancho, alfa):
        """Un acento a la izquierda y el otro a la derecha."""
        degradado = QLinearGradient(0, 0, ancho, 0)
        degradado.setColorAt(0.0, con_alfa(self.colores["acento"], alfa))
        degradado.setColorAt(1.0, con_alfa(self.colores["acento_2"], alfa))
        return QBrush(degradado)

    def _trazar_curva(self, pintor, caminos, grosor, ancho, delante):
        """La curva por niveles: más lejos, más tenue y delgada.

        Lo de adelante lleva además un halo ancho y suave debajo.
        """
        niveles = range(NIVELES // 2, NIVELES) if delante else range(NIVELES // 2)
        if delante:
            for nivel in niveles:
                self._pluma_redonda(pintor, self._degradado(ancho, 0.10), 9 * grosor)
                pintor.drawPath(caminos[nivel])
        for nivel in niveles:
            cercania = nivel / (NIVELES - 1)  # 0 lo más lejano, 1 lo más cercano
            alfa = 0.14 + 0.22 * cercania if not delante else 0.45 + 0.55 * cercania
            ancho_pluma = (1.4 + 1.5 * cercania) * grosor
            self._pluma_redonda(pintor, self._degradado(ancho, alfa), ancho_pluma)
            pintor.drawPath(caminos[nivel])

    @staticmethod
    def _pluma_redonda(pintor, pincel, ancho):
        pluma = QPen(pincel, ancho)
        pluma.setCapStyle(Qt.PenCapStyle.RoundCap)
        pluma.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        pintor.setPen(pluma)
        pintor.setBrush(Qt.BrushStyle.NoBrush)

    @staticmethod
    def _trazar(pintor, camino, color, alfa, ancho):
        pluma = QPen(con_alfa(color, alfa), ancho)
        pluma.setCapStyle(Qt.PenCapStyle.RoundCap)
        pintor.setPen(pluma)
        pintor.setBrush(Qt.BrushStyle.NoBrush)
        pintor.drawPath(camino)

    def _pintar_halo(self, pintor, centro, escala):
        """Un resplandor muy suave detrás de la esfera."""
        halo = QRadialGradient(centro, 1.6 * escala)
        halo.setColorAt(0.0, con_alfa(self.colores["acento"], 0.07))
        halo.setColorAt(0.6, con_alfa(self.colores["acento_2"], 0.025))
        halo.setColorAt(1.0, con_alfa(self.colores["acento_2"], 0.0))
        pintor.setPen(Qt.PenStyle.NoPen)
        pintor.setBrush(halo)
        pintor.drawEllipse(centro, 1.6 * escala, 1.6 * escala)

    def _pintar_orbita(self, pintor, centro, escala, grosor):
        """El anillo orbital con sus marcas, el satélite y los hilos."""
        c = self.colores
        radio = ORBITA * escala
        segundos = 0.0 if self._quieto else self._reloj.elapsed() / 1000
        pintor.setBrush(Qt.BrushStyle.NoBrush)
        pintor.setPen(QPen(con_alfa(c["acento"], 0.16), grosor))
        pintor.drawEllipse(centro, radio, radio)

        # Marcas: como la escala de un instrumento, girando despacio
        giro = math.radians(GRADOS_ORBITA_POR_SEGUNDO * segundos)
        marcas = QPainterPath()
        for k in range(MARCAS_ORBITA):
            angulo = giro + 2 * math.pi * k / MARCAS_ORBITA
            largo = (9 if k % 10 == 0 else 4) * grosor
            ux, uy = math.cos(angulo), math.sin(angulo)
            marcas.moveTo(centro.x() + radio * ux, centro.y() + radio * uy)
            marcas.lineTo(centro.x() + (radio + largo) * ux,
                          centro.y() + (radio + largo) * uy)  # fmt: skip
        pintor.setPen(QPen(con_alfa(c["acento"], 0.30), grosor))
        pintor.drawPath(marcas)

        # Satélite
        if not self._quieto:
            angulo = 2 * math.pi * (segundos / PERIODO_SATELITE_S % 1) - math.pi / 2
            lugar = centro + QPointF(radio * math.cos(angulo), radio * math.sin(angulo))
            self._brillo(pintor, lugar, c["acento_2"], 2.6 * grosor)
        self._pintar_hilos(pintor, centro, escala, grosor)

    def _pintar_hilos(self, pintor, centro, escala, grosor):
        """De cada tarjeta, un hilo al punto del anillo que la mira."""
        c = self.colores
        radio = ORBITA * escala
        segundos = 0.0 if self._quieto else self._reloj.elapsed() / 1000
        latido = 0.5 + 0.5 * math.sin(2 * math.pi * segundos / 2.4)
        for ancla, lado in self._anclas:
            dx, dy = ancla.x() - centro.x(), ancla.y() - centro.y()
            distancia = math.hypot(dx, dy)
            if distancia <= radio:
                continue
            nudo = centro + QPointF(dx / distancia * radio, dy / distancia * radio)
            hilo = QLinearGradient(ancla, nudo)
            hilo.setColorAt(0, con_alfa(c["acento"], 0.55))
            hilo.setColorAt(1, con_alfa(c["acento"], 0.18))
            pintor.setPen(QPen(QBrush(hilo), grosor))
            pintor.drawLine(ancla, nudo)
            pintor.setPen(QPen(con_alfa(c["acento"], 0.8), 1.2 * grosor))
            pintor.setBrush(con_alfa(c["fondo"], 1.0))
            pintor.drawEllipse(nudo, 4.5 * grosor, 4.5 * grosor)
            self._brillo(pintor, nudo, c["acento"], 1.8 * grosor, 0.6 + 0.4 * latido)
            self._pintar_envio(pintor, ancla, nudo, lado, grosor)

    def _pintar_envio(self, pintor, ancla, nudo, lado, grosor):
        """El destello que viaja por un hilo (si corresponde a este lado)."""
        if not self._envio_activo():
            return
        if (lado == "izquierda") != self._envio_entrante:
            return
        avance = salida_suave(self._envio.elapsed() / DURACION_ENVIO_MS)
        if avance >= 1:
            return
        if not self._envio_entrante:  # sale de la esfera hacia la tarjeta
            ancla, nudo = nudo, ancla
        lugar = ancla + (nudo - ancla) * avance
        self._brillo(pintor, lugar, "#FFFFFF", 3 * grosor, 1 - avance**3)

    def _pintar_esfera(self, pintor, centro, escala, grosor):
        """Vidrio oscuro: casi transparente al centro y con el borde iluminado."""
        c = self.colores
        borde = QRadialGradient(centro, escala)
        borde.setColorAt(0.0, con_alfa(c["acento"], 0.0))
        borde.setColorAt(0.72, con_alfa(c["acento"], 0.02))
        borde.setColorAt(0.96, con_alfa(c["acento"], 0.09))
        borde.setColorAt(1.0, con_alfa(c["acento_2"], 0.16))
        pintor.setPen(QPen(con_alfa(c["esfera"], 0.55), 1.2 * grosor))
        pintor.setBrush(borde)
        pintor.drawEllipse(centro, escala, escala)
        # Reflejo de una luz arriba a la izquierda
        luz = centro + QPointF(-0.42 * escala, -0.48 * escala)
        reflejo = QRadialGradient(luz, 0.55 * escala)
        reflejo.setColorAt(0.0, QColor(255, 255, 255, 20))
        reflejo.setColorAt(1.0, QColor(255, 255, 255, 0))
        pintor.setPen(Qt.PenStyle.NoPen)
        pintor.setBrush(reflejo)
        pintor.drawEllipse(centro, escala, escala)

    @staticmethod
    def _brillo(pintor, punto, color, radio, intensidad=1.0):
        """Un punto luminoso: halo difuso y centro nítido."""
        halo = QRadialGradient(punto, 3 * radio)
        halo.setColorAt(0.0, con_alfa(color, 0.45 * intensidad))
        halo.setColorAt(1.0, con_alfa(color, 0.0))
        pintor.setPen(Qt.PenStyle.NoPen)
        pintor.setBrush(halo)
        pintor.drawEllipse(punto, 3 * radio, 3 * radio)
        pintor.setBrush(con_alfa(color, intensidad))
        pintor.drawEllipse(punto, radio, radio)

    def _pintar_muestras(self, pintor, camara, grosor):
        """Los puntos r(tᵢ). Durante el barrido aparecen con un destello."""
        if self._muestras is None:
            return
        cantidad = len(self._muestras)
        h, v, d = camara.proyectar(punto(self._muestras))
        if self._barrido_ms is None:
            edades = np.full(cantidad, 1e9)  # todos visibles hace rato
        else:
            # Cada punto aparece cuando su rectángulo termina de crecer
            aparece = inicios_escalonados(cantidad) + DURACION_BARRA_MS
            edades = self._barrido_ms - aparece
        tamano = (2.6 if cantidad <= 40 else 1.9) * grosor
        color = self.colores["muestra"]
        pintor.setPen(Qt.PenStyle.NoPen)
        for k in np.flatnonzero(edades >= 0):
            centro = QPointF(float(h[k]), float(v[k]))
            opacidad = 1.0 if d[k] >= 0 else 0.35
            destello = max(0.0, 1 - edades[k] / 300)  # 300 ms de destello
            if destello > 0:
                self._brillo(pintor, centro, color, tamano * (1 + destello), opacidad)
            else:
                pintor.setBrush(con_alfa(color, 0.9 * opacidad))
                pintor.drawEllipse(centro, tamano, tamano)

    def _parametro_cometa(self):
        """Dónde va la cabeza del cometa (un t), o None si no se muestra."""
        if self._barrido_ms is not None and self._muestras is not None:
            # Durante el barrido la cabeza va justo por el punto que aparece
            cantidad = len(self._muestras)
            momentos = inicios_escalonados(cantidad) + DURACION_BARRA_MS
            return float(
                np.interp(
                    self._barrido_ms,
                    [0, *momentos, DURACION_BARRIDO_MS],
                    [0, *self._muestras, 2 * math.pi],
                )
            )
        if self._intro < 1:
            return 2 * math.pi * self._intro  # la cabeza va dibujando la curva
        if self._quieto:
            return None
        vueltas = self._reloj.elapsed() / 1000 / PERIODO_COMETA_S
        return 2 * math.pi * (vueltas % 1)

    def _pintar_cometa(self, pintor, camara, grosor):
        """Una luz que recorre la curva en el sentido en que crece t."""
        cabeza = self._parametro_cometa()
        if cabeza is None:
            return
        cola = np.linspace(cabeza - COLA_COMETA, cabeza, 24)
        h, v, d = camara.proyectar(punto(cola))
        blanco = QColor("#FFFFFF")
        for k in range(len(cola) - 1):
            avance = (k + 1) / (len(cola) - 1)  # 0 al final de la cola, 1 en la cabeza
            opacidad = avance**2 * (1.0 if d[k] >= 0 else 0.3)
            pluma = QPen(con_alfa(blanco, 0.9 * opacidad), (1 + 2.4 * avance) * grosor)
            pluma.setCapStyle(Qt.PenCapStyle.RoundCap)
            pintor.setPen(pluma)
            pintor.drawLine(QPointF(h[k], v[k]), QPointF(h[k + 1], v[k + 1]))
        intensidad = 1.0 if d[-1] >= 0 else 0.35
        self._brillo(pintor, QPointF(h[-1], v[-1]), blanco, 3.2 * grosor, intensidad)

    def _pintar_punto_doble(self, pintor, camara, grosor, lado):
        """El punto doble (R, 0, 0), con un pequeño halo, y su rótulo."""
        lugar, profundidad = camara.a_punto((1.0, 0.0, 0.0))
        opacidad = 1.0 if profundidad >= 0 else 0.35
        self._brillo(pintor, lugar, self.colores["punto_doble"], 4 * grosor, opacidad)
        pintor.setPen(con_alfa(self.colores["texto"], opacidad))
        pintor.setFont(self._fuente(FAMILIAS_MONO, 0.024 * lado))
        pintor.drawText(lugar + QPointF(10 * grosor, -12 * grosor), "(R, 0, 0)")

    def _pintar_velocidad(self, pintor, camara, grosor, lado):
        """r(t) y la flecha de r′(t), el punto que se señala en la otra gráfica."""
        t = self._resaltado
        inicio = punto(t)
        fin = inicio + ESCALA_VECTOR * velocidad(t)
        a, profundidad = camara.a_punto(inicio)
        b, _ = camara.a_punto(fin)
        color = self.colores["muestra"]
        opacidad = 1.0 if profundidad >= 0 else 0.55

        # Flecha: el segmento y una punta triangular
        pintor.setPen(QPen(con_alfa(color, opacidad), 2.2 * grosor))
        pintor.drawLine(a, b)
        direccion = b - a
        largo = math.hypot(direccion.x(), direccion.y())
        if largo > 1:
            ux, uy = direccion.x() / largo, direccion.y() / largo
            punta = 11 * grosor
            izquierda = b - QPointF(punta * ux - 0.5 * punta * uy,
                                    punta * uy + 0.5 * punta * ux)  # fmt: skip
            derecha = b - QPointF(punta * ux + 0.5 * punta * uy,
                                  punta * uy - 0.5 * punta * ux)  # fmt: skip
            pintor.setPen(Qt.PenStyle.NoPen)
            pintor.setBrush(con_alfa(color, opacidad))
            pintor.drawPolygon(QPolygonF([b, izquierda, derecha]))

        # El punto r(t) con un anillo
        pintor.setPen(QPen(con_alfa(color, opacidad), 1.6 * grosor))
        pintor.setBrush(Qt.BrushStyle.NoBrush)
        pintor.drawEllipse(a, 8 * grosor, 8 * grosor)
        self._brillo(pintor, a, color, 3.4 * grosor, opacidad)

        pintor.setPen(con_alfa(self.colores["texto"], opacidad))
        pintor.setFont(self._fuente(FAMILIAS_MONO, 0.024 * lado))
        pintor.drawText(b + QPointF(8 * grosor, -6 * grosor), "r′(t)")

    def _pintar_ejes(self, pintor, camara, grosor, lado, delante):
        """Ejes X, Y, Z. Primero la parte de adentro (bajo la esfera), al
        final la que sobresale, con su nombre en mayúscula."""
        color = QColor(self.colores["etiqueta"])
        for indice, nombre in enumerate("XYZ"):
            extremo = np.zeros((3, 2))
            extremo[indice] = (1.0, 1.32) if delante else (-1.32, 1.0)
            h, v, _ = camara.proyectar(extremo)
            color.setAlphaF(0.75 if delante else 0.35)
            pintor.setPen(QPen(color, 1.1 * grosor))
            pintor.drawLine(QPointF(h[0], v[0]), QPointF(h[1], v[1]))
            if delante:
                pintor.setFont(self._fuente(FAMILIAS_MONO, 0.03 * lado, negrita=True))
                rotulo = QPointF(h[1], v[1]) + QPointF(6 * grosor, -6 * grosor)
                pintor.drawText(rotulo, nombre)

    def _pintar_marcas(self, pintor, camara, grosor, lado):
        """Números en cm sobre cada eje: -R, -R/2, R/2 y R."""
        pintor.setFont(self._fuente(FAMILIAS_MONO, 0.021 * lado))
        for indice in range(3):
            puntos = np.zeros((3, len(MARCAS)))
            puntos[indice] = MARCAS
            h, v, d = camara.proyectar(puntos)
            for k, posicion in enumerate(MARCAS):
                if indice == 0 and posicion == 1.0:
                    continue  # ahí está el punto doble, que ya tiene su rótulo
                color = con_alfa(self.colores["texto_sec"], 0.9 if d[k] >= 0 else 0.45)
                lugar = QPointF(h[k], v[k])
                pintor.setPen(Qt.PenStyle.NoPen)
                pintor.setBrush(color)
                pintor.drawEllipse(lugar, 1.8 * grosor, 1.8 * grosor)
                pintor.setPen(color)
                texto = formatear_radio(posicion * self.radio)
                pintor.drawText(lugar + QPointF(5 * grosor, 13 * grosor), texto)

    @staticmethod
    def _fuente(familias, pixeles, negrita=False):
        fuente = QFont()
        fuente.setFamilies(familias)
        fuente.setPixelSize(max(10, round(pixeles)))
        fuente.setBold(negrita)
        return fuente
