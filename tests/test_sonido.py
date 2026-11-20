"""Pruebas del módulo de sonido. Ninguna emite sonido real."""

import array
import io
import math
import threading
import time
import unittest
import wave

from viviani import sonido

ESPERA = 2.0  # s: tiempo máximo para esperar al hilo


def _abrir(datos):
    """Devuelve (parámetros, muestras) de un WAV en memoria."""
    with wave.open(io.BytesIO(datos), "rb") as archivo:
        crudo = archivo.readframes(archivo.getnframes())
        parametros = archivo.getparams()
    muestras = array.array("h")
    muestras.frombytes(crudo)
    return parametros, muestras


def _dbfs(muestras):
    return 20 * math.log10(max(abs(m) for m in muestras) / 32767)


class PruebasSintesis(unittest.TestCase):
    CASOS = (
        ("clic", sonido.sintetizar_clic, 0.045, -24),
        ("resultado", sonido.sintetizar_resultado, 0.250, -20),
        ("error", sonido.sintetizar_error, 0.280, -22),
    )

    def test_formato_duracion_y_nivel(self):
        for nombre, funcion, duracion, nivel in self.CASOS:
            with self.subTest(nombre):
                parametros, muestras = _abrir(funcion())
                self.assertEqual(parametros.nchannels, 1)
                self.assertEqual(parametros.sampwidth, 2)
                self.assertEqual(parametros.framerate, 44_100)
                segundos = parametros.nframes / parametros.framerate
                self.assertAlmostEqual(segundos, duracion, delta=0.002)
                self.assertAlmostEqual(_dbfs(muestras), nivel, delta=1.0)

    def test_empieza_y_termina_en_cero(self):
        for nombre, funcion, _, _ in self.CASOS:
            with self.subTest(nombre):
                _, muestras = _abrir(funcion())
                self.assertLessEqual(abs(muestras[0]), 5)
                self.assertLessEqual(abs(muestras[-1]), 5)


class Reproductor:
    """Reproductor falso: anota lo que le piden y no suena nada."""

    def __init__(self):
        self.llamadas = []
        self.avisar = threading.Event()

    def __call__(self, datos):
        self.llamadas.append(datos)
        self.avisar.set()

    def esperar(self, cantidad=1):
        limite = time.monotonic() + ESPERA
        while len(self.llamadas) < cantidad and time.monotonic() < limite:
            time.sleep(0.005)


class PruebasSonidos(unittest.TestCase):
    def crear(self, **opciones):
        reproductor = opciones.pop("reproductor", Reproductor())
        sonidos = sonido.Sonidos(reproductor=reproductor, **opciones)
        self.addCleanup(sonidos.cerrar)
        return sonidos, reproductor

    def test_reproduce_cuando_esta_activado(self):
        sonidos, reproductor = self.crear()
        sonidos.clic()
        reproductor.esperar()
        self.assertEqual(len(reproductor.llamadas), 1)
        self.assertEqual(reproductor.llamadas[0], sonido.sintetizar_clic())

    def test_no_reproduce_si_esta_desactivado(self):
        sonidos, reproductor = self.crear(activado=False)
        self.assertFalse(sonidos.activado)
        sonidos.clic()
        sonidos.resultado()
        sonidos.error()
        time.sleep(0.3)
        self.assertEqual(reproductor.llamadas, [])

    def test_establecer_activado(self):
        sonidos, reproductor = self.crear(activado=False)
        sonidos.establecer_activado(True)
        self.assertTrue(sonidos.activado)
        sonidos.error()
        reproductor.esperar()
        self.assertEqual(len(reproductor.llamadas), 1)

    def test_antirrepeticion(self):
        sonidos, reproductor = self.crear()
        sonidos.clic()
        sonidos.clic()
        sonidos.clic()
        time.sleep(0.3)
        self.assertEqual(len(reproductor.llamadas), 1)
        # Pasado el tiempo de espera, el mismo sonido vuelve a sonar.
        sonidos.clic()
        reproductor.esperar(2)
        self.assertEqual(len(reproductor.llamadas), 2)

    def test_descarta_con_cola_llena(self):
        entro = threading.Event()
        soltar = threading.Event()
        llamadas = []

        def lento(datos):
            llamadas.append(datos)
            entro.set()
            soltar.wait(ESPERA)

        sonidos, _ = self.crear(reproductor=lento)
        sonidos.clic()  # el hilo lo toma y se queda sonando
        self.assertTrue(entro.wait(ESPERA))
        sonidos.resultado()  # ocupa la cola
        sonidos.error()  # cola llena: se descarta
        soltar.set()
        time.sleep(0.3)
        self.assertEqual(len(llamadas), 2)
        self.assertNotIn(sonido.sintetizar_error(), llamadas)

    def test_cerrar_termina_rapido(self):
        sonidos, _ = self.crear()
        inicio = time.monotonic()
        sonidos.cerrar()
        self.assertLess(time.monotonic() - inicio, 1.0)
        self.assertFalse(sonidos._hilo.is_alive())

    def test_metodos_despues_de_cerrar_no_fallan(self):
        sonidos, reproductor = self.crear()
        sonidos.cerrar()
        sonidos.clic()
        sonidos.resultado()
        sonidos.error()
        sonidos.establecer_activado(False)
        sonidos.cerrar()
        self.assertEqual(reproductor.llamadas, [])

    def test_reproductor_que_falla_no_rompe_nada(self):
        intentos = []

        def roto(datos):
            intentos.append(datos)
            raise OSError("sin dispositivo de audio")

        sonidos, _ = self.crear(reproductor=roto)
        sonidos.clic()
        limite = time.monotonic() + ESPERA
        while not intentos and time.monotonic() < limite:
            time.sleep(0.005)
        self.assertEqual(len(intentos), 1)
        # El hilo sigue vivo y atiende el siguiente sonido.
        time.sleep(0.2)
        sonidos.resultado()
        limite = time.monotonic() + ESPERA
        while len(intentos) < 2 and time.monotonic() < limite:
            time.sleep(0.005)
        self.assertEqual(len(intentos), 2)


if __name__ == "__main__":
    unittest.main()
