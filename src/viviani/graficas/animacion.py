"""Animación por tiempo real y repintado rápido (blitting).

El estado de la animación se calcula con el tiempo que realmente pasó
(QElapsedTimer), no contando cuadros: así nunca dura más de lo previsto,
aunque el equipo sea lento.
"""

from PySide6.QtCore import QElapsedTimer, QTimer

INTERVALO_MS = 33  # unos 30 cuadros por segundo


def salida_suave(p):
    """Curva OutCubic: empieza rápido y frena al final. p y el resultado en [0, 1]."""
    p = min(max(p, 0.0), 1.0)
    return 1 - (1 - p) ** 3


class Animador:
    """Llama a `al_cuadro(ms)` cada ~33 ms hasta cumplir la duración."""

    def __init__(self, padre):
        self._temporizador = QTimer(padre)
        self._temporizador.setInterval(INTERVALO_MS)
        self._temporizador.timeout.connect(self._cuadro)
        self._reloj = QElapsedTimer()
        self._duracion = 0
        self._al_cuadro = None
        self._al_terminar = None

    def activo(self):
        return self._temporizador.isActive()

    def iniciar(self, duracion_ms, al_cuadro, al_terminar):
        self.cancelar()
        self._duracion = duracion_ms
        self._al_cuadro = al_cuadro
        self._al_terminar = al_terminar
        self._reloj.start()
        al_cuadro(0)
        self._temporizador.start()

    def cancelar(self):
        """Detiene sin dibujar el final (por ejemplo, si llega otro cálculo)."""
        self._temporizador.stop()
        self._al_cuadro = None
        self._al_terminar = None

    def terminar(self):
        """Salta al estado final y avisa que terminó."""
        if not self.activo():
            return
        al_cuadro, al_terminar = self._al_cuadro, self._al_terminar
        self.cancelar()
        al_cuadro(self._duracion)
        al_terminar()

    def _cuadro(self):
        ms = self._reloj.elapsed()
        if ms >= self._duracion:
            self.terminar()
        else:
            self._al_cuadro(ms)


class Repintado:
    """Repinta solo los artistas que cambian (blitting).

    El fondo (todo lo que no se anima) se guarda como imagen cada vez que
    matplotlib dibuja la figura completa; en cada cuadro se restaura ese
    fondo y se dibujan encima los artistas animados.
    """

    def __init__(self, lienzo):
        self._lienzo = lienzo
        self._fondo = None
        self.artistas = []
        lienzo.mpl_connect("draw_event", self._al_dibujar)

    def reiniciar(self, artistas):
        """Se llama cada vez que la figura se reconstruye."""
        for artista in self.artistas:
            artista.set_animated(False)
        self.artistas = list(artistas)
        for artista in self.artistas:
            artista.set_animated(True)
        self._fondo = None

    def liberar(self):
        """Los artistas vuelven a dibujarse con el resto de la figura."""
        for artista in self.artistas:
            artista.set_animated(False)
        self.artistas = []
        self._fondo = None

    def _dibujar_animados(self):
        for artista in self.artistas:
            self._lienzo.figure.draw_artist(artista)

    def _al_dibujar(self, _evento):
        self._fondo = self._lienzo.copy_from_bbox(self._lienzo.figure.bbox)
        self._dibujar_animados()

    def actualizar(self):
        if self._fondo is None:
            self._lienzo.draw()  # el dibujo completo guarda el fondo
            return
        self._lienzo.restore_region(self._fondo)
        self._dibujar_animados()
        self._lienzo.blit(self._lienzo.figure.bbox)
