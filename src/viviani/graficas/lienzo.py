"""Lienzo base de las tres gráficas: tema, exportación y animación.

Cada gráfica concreta solo escribe `_dibujar(fig, colores, estilo)`, que
dibuja el estado FINAL sobre la figura que reciba. Esa misma función se usa
para la pantalla y para el PNG exportado (en una figura nueva).
"""

import matplotlib
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPalette

from viviani.graficas.animacion import Animador, Repintado
from viviani.graficas.estilo import (
    METADATOS,
    estilo_exportacion,
    estilo_pantalla,
    rc_de,
)
from viviani.tema import paleta_exportacion


class LienzoBase(FigureCanvasQTAgg):
    animacion_terminada = Signal()  # al acabar la animación o al saltarla

    TAMANO_EXPORTACION_CM = (16, 10)
    DISENO = "constrained"  # reparte los márgenes automáticamente

    def __init__(self, colores, escala_texto=1.0):
        super().__init__(Figure(layout=self.DISENO))
        self.colores = colores
        self.escala_texto = escala_texto
        self._duracion = 0
        self._animador = Animador(self)
        self._repintado = Repintado(self)
        self.setFocusPolicy(Qt.StrongFocus)

    # --- Lo que escribe cada gráfica ---------------------------------
    def _dibujar(self, fig, colores, estilo):
        """Dibuja el estado final en `fig` y devuelve un dict de artistas."""
        raise NotImplementedError

    def titulo(self):
        """Título del PNG (va en los metadatos)."""
        raise NotImplementedError

    def nombre_sugerido(self):
        raise NotImplementedError

    def descripcion_accesible(self):
        raise NotImplementedError

    # --- Dibujo en pantalla ------------------------------------------
    def redibujar(self, repintar=True):
        """Reconstruye la figura de pantalla con el estado actual.

        Con repintar=False no pide repintado: sirve cuando enseguida se
        dibuja el primer cuadro de una animación (así no se dibuja dos veces).
        """
        self._detener_animacion()
        self.figure.clear()
        estilo = estilo_pantalla(self.escala_texto)
        with matplotlib.rc_context(rc_de(self.colores, estilo)):
            self._elementos = self._dibujar(self.figure, self.colores, estilo)
        self._pintar_fondo_del_widget()
        self.setAccessibleName(self.descripcion_accesible())
        if repintar:
            self.draw_idle()

    def _pintar_fondo_del_widget(self):
        """El widget no pinta fondo propio: la figura es transparente y deja
        ver la tarjeta de detrás (y la luz que sigue al cursor).

        matplotlib "borra" el widget con el color Window de la paleta antes de
        dibujar; con un color transparente ese borrado no tapa nada."""
        paleta_qt = self.palette()
        paleta_qt.setColor(QPalette.Window, QColor(0, 0, 0, 0))
        self.setPalette(paleta_qt)
        self.setAutoFillBackground(False)
        # matplotlib marca su lienzo como opaco (Qt no pinta nada debajo);
        # aquí se desmarca para que sí se vea la tarjeta a través.
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)

    def paintEvent(self, evento):
        """Pega en el widget la imagen que dibujó matplotlib.

        matplotlib, por defecto, copia solo el trozo que Qt pide repintar.
        Con la pantalla escalada (125 %) ese trozo se calcula con redondeos y
        queda corrido: al pasar la luz del cursor aparecían rayas y textos
        duplicados. Aquí se pega siempre la imagen COMPLETA y Qt recorta lo
        que haga falta, así nunca queda desalineada.
        """
        self._draw_idle()  # dibuja si había un dibujo pendiente
        if not hasattr(self, "renderer"):
            return
        datos = self.renderer.buffer_rgba()
        alto, ancho = datos.shape[0], datos.shape[1]
        imagen = QImage(datos, ancho, alto, QImage.Format.Format_RGBA8888)
        imagen.setDevicePixelRatio(self.device_pixel_ratio)
        pintor = QPainter(self)
        pintor.setClipRegion(evento.region())
        pintor.drawImage(0, 0, imagen)
        pintor.end()

    def aplicar_tema(self, colores):
        """Cambia entre modo claro y oscuro en caliente."""
        self.colores = colores
        self.redibujar()

    # --- Exportación -------------------------------------------------
    def exportar(self, ruta):
        """Guarda un PNG de 300 ppp, fondo blanco, en estado final."""
        ancho_cm, alto_cm = self.TAMANO_EXPORTACION_CM
        fig = Figure(figsize=(ancho_cm / 2.54, alto_cm / 2.54), layout=self.DISENO)
        colores = paleta_exportacion()
        estilo = estilo_exportacion()
        metadatos = dict(METADATOS, Title=self.titulo())
        decorada = getattr(self, "decorada", True)
        self.decorada = True  # el PNG lleva título y leyenda dentro
        with matplotlib.rc_context(rc_de(colores, estilo)):
            self._dibujar(fig, colores, estilo)
            self.decorada = decorada
            fig.savefig(
                ruta,
                format="png",
                dpi=300,
                bbox_inches="tight",
                pad_inches=0.05,
                facecolor=colores["fondo"],
                metadata=metadatos,
            )

    # --- Animación ---------------------------------------------------
    def esta_animando(self):
        return self._animador.activo()

    def saltar_animacion(self):
        """Dibuja el estado final y avisa que terminó."""
        self._animador.terminar()

    def _detener_animacion(self):
        """Detiene sin avisar (otro dibujo reemplaza a la animación)."""
        self._animador.cancelar()
        self._repintado.liberar()

    def _animar(self, duracion_ms, artistas, al_cuadro):
        """Anima `artistas`: en cada cuadro llama a al_cuadro(ms)."""
        self._duracion = duracion_ms
        self._repintado.reiniciar(artistas)
        self._animador.iniciar(
            duracion_ms, lambda ms: self._paso(al_cuadro, ms), self._al_terminar
        )

    def _paso(self, al_cuadro, ms):
        al_cuadro(ms)
        if ms < self._duracion:  # el último cuadro lo dibuja _al_terminar
            self._repintado.actualizar()

    def _al_terminar(self):
        self._repintado.liberar()
        self.draw()  # un solo repintado completo
        self.animacion_terminada.emit()
