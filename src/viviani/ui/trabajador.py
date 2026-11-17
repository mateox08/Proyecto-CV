"""Cálculos en segundo plano, para que la ventana nunca se congele.

`GestorTareas` ejecuta una función en un hilo (QThread) y avisa con señales:

    progreso(int)    avance de 0 a 100
    terminado(obj)   el resultado de la función
    cancelado()      alguien pidió cancelar y la función se detuvo
    fallo(str)       la función lanzó un error (mensaje en español)

Regla de oro: solo importa la ÚLTIMA tarea lanzada. Si se lanza otra mientras
la anterior sigue corriendo, a la anterior se le pide detenerse y se ignoran
todas sus señales; así un resultado viejo nunca pisa a uno nuevo.
"""

from PySide6.QtCore import QObject, QThread, Signal


class _Tarea(QThread):
    """Un hilo que ejecuta `funcion(progreso, cancelado)` una sola vez."""

    progreso = Signal(int)
    terminado = Signal(object)
    cancelado = Signal()
    fallo = Signal(str)

    def __init__(self, funcion):
        super().__init__()
        self._funcion = funcion
        self._pidieron_cancelar = False

    def cancelar(self):
        """Pide detener el cálculo. Se revisa entre bloques, no es inmediato."""
        self._pidieron_cancelar = True

    def _esta_cancelado(self):
        return self._pidieron_cancelar

    def run(self):
        try:
            resultado = self._funcion(self.progreso.emit, self._esta_cancelado)
        except Exception as error:
            # El módulo de cálculo avisa que lo detuvieron con una excepción
            # llamada CalculoCancelado; se reconoce por el nombre para no
            # depender de él aquí.
            if self._pidieron_cancelar or type(error).__name__ == "CalculoCancelado":
                self.cancelado.emit()
            else:
                self.fallo.emit(str(error))
            return
        if self._pidieron_cancelar:
            self.cancelado.emit()
        else:
            self.terminado.emit(resultado)


class GestorTareas(QObject):
    """Lanza tareas una a la vez y reenvía las señales de la más reciente."""

    progreso = Signal(int)
    terminado = Signal(object)
    cancelado = Signal()
    fallo = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._actual = None  # la tarea cuyos resultados sí importan
        self._vivas = []  # todos los hilos que aún no terminaron

    def lanzar(self, funcion):
        """Empieza `funcion(progreso, cancelado)`; cancela y descarta la anterior."""
        if self._actual is not None:
            self._actual.cancelar()  # la anterior sigue viva hasta que se detenga
        tarea = _Tarea(funcion)
        self._actual = tarea
        tarea.progreso.connect(self._recibir_progreso)
        tarea.terminado.connect(self._recibir_terminado)
        tarea.cancelado.connect(self._recibir_cancelado)
        tarea.fallo.connect(self._recibir_fallo)
        tarea.finished.connect(self._limpiar)
        self._vivas.append(tarea)
        tarea.start()

    def cancelar(self):
        """Cancela la tarea actual (si hay). Llegará la señal `cancelado`."""
        if self._actual is not None:
            self._actual.cancelar()

    def en_curso(self):
        return self._actual is not None

    def cerrar(self):
        """Detiene todos los hilos y espera a que terminen (al cerrar la ventana)."""
        self._actual = None
        for tarea in list(self._vivas):
            tarea.cancelar()
        for tarea in list(self._vivas):
            tarea.wait()
        self._vivas.clear()

    # Cada señal llega con `sender()` = la tarea que la emitió. Si no es la
    # actual, es de una tarea descartada y se ignora.
    def _es_actual(self):
        return self.sender() is self._actual

    def _recibir_progreso(self, porcentaje):
        if self._es_actual():
            self.progreso.emit(porcentaje)

    def _recibir_terminado(self, resultado):
        if self._es_actual():
            self._actual = None
            self.terminado.emit(resultado)

    def _recibir_cancelado(self):
        if self._es_actual():
            self._actual = None
            self.cancelado.emit()

    def _recibir_fallo(self, mensaje):
        if self._es_actual():
            self._actual = None
            self.fallo.emit(mensaje)

    def _limpiar(self):
        """Un hilo terminó: se olvida (y Qt lo borra cuando pueda)."""
        tarea = self.sender()
        if tarea in self._vivas:
            self._vivas.remove(tarea)
            tarea.deleteLater()
