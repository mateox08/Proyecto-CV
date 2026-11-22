"""Animaciones por tiempo real (solo Qt: la usa también la pantalla de carga).

El estado de cada animación se calcula con el tiempo que realmente pasó
(QElapsedTimer), no contando cuadros: así nunca dura más de lo previsto,
aunque el equipo sea lento o algún cuadro se atrase.
"""

from PySide6.QtCore import QElapsedTimer, QTimer

INTERVALO_MS = 16  # unos 60 cuadros por segundo


def salida_suave(p):
    """Curva "OutCubic": empieza rápido y frena al final. p y el resultado en [0, 1]."""
    p = min(max(p, 0.0), 1.0)
    return 1 - (1 - p) ** 3


class Animacion:
    """Llama a `al_cuadro(ms)` unas 60 veces por segundo durante `duracion_ms`.

    El último cuadro siempre recibe exactamente `duracion_ms`, aunque se
    salte la animación: así el dibujo final es siempre el mismo.
    """

    def __init__(self, padre, al_cuadro, al_terminar=None):
        self._al_cuadro = al_cuadro
        self._al_terminar = al_terminar
        self._duracion = 0
        self._reloj = QElapsedTimer()
        self._temporizador = QTimer(padre)
        self._temporizador.setInterval(INTERVALO_MS)
        self._temporizador.timeout.connect(self._cuadro)

    def iniciar(self, duracion_ms):
        self._duracion = duracion_ms
        self._reloj.start()
        self._al_cuadro(0)
        self._temporizador.start()

    def activa(self):
        return self._temporizador.isActive()

    def cancelar(self):
        """Detiene sin dibujar el final (por ejemplo, si llega otro cálculo)."""
        self._temporizador.stop()

    def terminar(self):
        """Salta al estado final y avisa que terminó."""
        if not self.activa():
            return
        self._temporizador.stop()
        self._al_cuadro(self._duracion)
        if self._al_terminar is not None:
            self._al_terminar()

    def _cuadro(self):
        ms = self._reloj.elapsed()
        if ms >= self._duracion:
            self.terminar()
        else:
            self._al_cuadro(ms)
