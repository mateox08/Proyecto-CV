"""Sonidos de la aplicación: se fabrican con senos y se reproducen con `winsound`.

Un sonido digital es una lista de números llamados *muestras*: cada una dice
qué tan separada está la membrana del parlante de su posición de reposo en un
instante. A 44 100 muestras por segundo el oído oye una onda continua.

Aquí se generan cuatro sonidos cortos con timbre de marimba, es decir, de
madera (clic, resultado listo, error suave y apertura de los créditos), se
guardan como archivos WAV en memoria y se hacen sonar en un hilo aparte para
que la ventana nunca se congele.
"""

import io
import queue
import threading
import time
import wave

import numpy as np

# `winsound` solo existe en Windows; con este import protegido el módulo se
# puede importar (y probar) en cualquier sistema.
try:
    import winsound
except ImportError:  # pragma: no cover - depende del sistema operativo
    winsound = None

FRECUENCIA_MUESTREO = 44_100  # muestras por segundo
TIEMPO_FUNDIDO_FINAL = 0.005  # s: bajada lineal a cero al final de cada nota
ESPERA_ANTIREPETICION = 0.150  # s: el mismo sonido no se repite antes de esto
ESPERA_COLA = 0.1  # s: cada cuánto el hilo revisa si debe terminar

# Timbres: listas de (múltiplo de la frecuencia, nivel en dB).
# Una barra de marimba vibra con parciales 1, 3.93 y 9.2 veces la nota: por
# eso suena a madera y no a cuerda ni a campana. Los agudos se apagan rápido.
MARIMBA = ((1.0, 0), (3.93, -15), (9.2, -30))
SUAVE = ((1.0, 0), (2.0, -20))


# ---------------------------------------------------------------------------
# Síntesis: de las fórmulas a los bytes del WAV
# ---------------------------------------------------------------------------


def _decibelios_a_razon(decibelios):
    """Convierte decibelios a razón de amplitudes (-18 dB es aprox. 0.126)."""
    return 10 ** (decibelios / 20)


def _nota(frecuencia, duracion, ataque, tau, timbre=SUAVE):
    """Muestras (decimales) de una nota: una suma de senos por su envolvente.

    Cada parcial es una onda de frecuencia `múltiplo · frecuencia`; los
    agudos se apagan antes (tau / múltiplo), como en una campana real.

    La envolvente es lo que "da forma" al volumen en el tiempo:
    - ataque lineal: sube de 0 a 1, para que la onda no arranque de golpe;
    - caída exponencial: baja como e^(-t/tau);
    - fundido final: baja a 0 en los últimos 5 ms. Sin esto la onda podría
      cortarse en un valor distinto de cero y el salto se oiría como un
      chasquido.
    """
    t = np.arange(round(duracion * FRECUENCIA_MUESTREO)) / FRECUENCIA_MUESTREO
    onda = np.zeros_like(t)
    for multiplo, nivel in timbre:
        caida = np.exp(-np.maximum(t - ataque, 0) * multiplo / tau)
        seno = np.sin(2 * np.pi * multiplo * frecuencia * t)
        onda += _decibelios_a_razon(nivel) * seno * caida
    subida = np.minimum(1.0, t / ataque)
    # Muestras que faltan para el final (0 en la última): da el fundido
    restantes = np.arange(len(t) - 1, -1, -1)
    fundido = np.minimum(1.0, restantes / (TIEMPO_FUNDIDO_FINAL * FRECUENCIA_MUESTREO))
    return onda * subida * fundido


def _mezclar(duracion, notas):
    """Suma varias notas que empiezan en distintos instantes.

    notas: lista de (inicio en s, muestras). Las notas se pueden solapar:
    la cola de una sigue sonando cuando empieza la siguiente.
    """
    total = np.zeros(round(duracion * FRECUENCIA_MUESTREO))
    for inicio, muestras in notas:
        k = round(inicio * FRECUENCIA_MUESTREO)
        largo = min(len(muestras), len(total) - k)
        total[k : k + largo] += muestras[:largo]
    return total


def _a_wav(muestras, decibelios_pico):
    """Escala las muestras para que el pico quede en `decibelios_pico` y arma el WAV.

    dBFS: decibelios respecto al máximo que cabe en 16 bits (32 767). Se
    normaliza al final para que el nivel de cada sonido sea exacto, sin
    importar cuánto sumen los parciales.
    """
    pico = 32767 * _decibelios_a_razon(decibelios_pico)
    enteros = np.round(muestras / np.max(np.abs(muestras)) * pico).astype("<i2")
    memoria = io.BytesIO()
    with wave.open(memoria, "wb") as archivo:
        archivo.setnchannels(1)  # mono
        archivo.setsampwidth(2)  # 16 bits = 2 bytes por muestra
        archivo.setframerate(FRECUENCIA_MUESTREO)
        archivo.writeframes(enteros.tobytes())
    return memoria.getvalue()


def _arpegio(frecuencias, separacion, duracion, tau):
    """Notas de marimba que entran una tras otra y suenan juntas hasta el final."""
    notas = [
        (k * separacion, _nota(f, duracion - k * separacion, 0.003, tau, MARIMBA))
        for k, f in enumerate(frecuencias)
    ]
    return _mezclar(duracion, notas)


def _colchon(frecuencias, duracion):
    """Acorde que entra despacio, como un soplo de aire.

    Cada nota suena dos veces, desafinada 1.5 Hz hacia arriba y hacia abajo:
    las dos ondas se adelantan y atrasan entre sí y el sonido "respira"
    (efecto coro).
    """
    notas = [
        (0.0, _nota(f + desvio, duracion, 0.35, 0.5, SUAVE))
        for f in frecuencias
        for desvio in (-1.5, 1.5)
    ]
    return _mezclar(duracion, notas)


def sintetizar_clic():
    """Clic de confirmación: un golpe corto de madera (mi), 70 ms, -24 dBFS."""
    return _a_wav(_nota(659.3, 0.070, 0.002, 0.030, MARIMBA), -24)


def sintetizar_resultado():
    """Resultado listo: acorde mayor de marimba que sube (do-mi-sol-do),
    900 ms, -20 dBFS."""
    return _a_wav(_arpegio((523.3, 659.3, 784.0, 1046.5), 0.060, 0.900, 0.35), -20)


def sintetizar_error():
    """Error suave: dos golpes de madera graves que bajan (fa-re), 320 ms, -22 dBFS."""
    notas = [(0.0, _nota(349.2, 0.140, 0.003, 0.08, MARIMBA)),
             (0.130, _nota(293.7, 0.190, 0.003, 0.10, MARIMBA))]  # fmt: skip
    return _a_wav(_mezclar(0.320, notas), -22)


def sintetizar_creditos():
    """Créditos: un colchón de aire (la mayor) con un arpegio encima,
    1.4 s, -26 dBFS."""
    colchon = _colchon((220.0, 277.2, 329.6), 1.400)
    arpegio = _arpegio((659.3, 880.0, 1108.7), 0.110, 1.400, 0.45)
    return _a_wav(colchon + 0.8 * arpegio, -26)


# ---------------------------------------------------------------------------
# Reproducción
# ---------------------------------------------------------------------------


def _reproducir_con_winsound(datos_wav):
    """Hace sonar el WAV y espera a que termine (por eso se llama desde un hilo).

    `SND_MEMORY` toma los bytes directamente; no se puede combinar con
    `SND_ASYNC`, así que la llamada bloquea hasta el final del sonido.
    """
    if winsound is not None:
        winsound.PlaySound(datos_wav, winsound.SND_MEMORY | winsound.SND_NODEFAULT)


class Sonidos:
    """Reproduce los sonidos sin bloquear la interfaz ni lanzar errores."""

    def __init__(self, reproductor=None):
        self._reproductor = reproductor or _reproducir_con_winsound
        # Los WAV se fabrican una sola vez, al arrancar.
        self._datos = {
            "clic": sintetizar_clic(),
            "resultado": sintetizar_resultado(),
            "error": sintetizar_error(),
            "creditos": sintetizar_creditos(),
        }
        # Para cada sonido, cuándo se pidió por última vez (antirrepetición).
        self._ultimo_instante = {}
        self._cerrado = threading.Event()
        # maxsize=1: si ya hay un sonido esperando, el nuevo se descarta
        # y nunca se acumulan sonidos atrasados.
        self._cola = queue.Queue(maxsize=1)
        # Un hilo propio porque PlaySound espera a que acabe el sonido; si lo
        # llamáramos desde la ventana, ésta se congelaría esos milisegundos.
        # Es "demonio": si algo falla, no impide que el programa se cierre.
        self._hilo = threading.Thread(target=self._trabajar, daemon=True)
        self._hilo.start()

    def clic(self):
        self._pedir("clic")

    def resultado(self):
        self._pedir("resultado")

    def error(self):
        self._pedir("error")

    def creditos(self):
        self._pedir("creditos")

    def cerrar(self):
        """Detiene el hilo. Se puede llamar varias veces."""
        self._cerrado.set()
        self._cortar_sonido_actual()
        if self._hilo.is_alive() and self._hilo is not threading.current_thread():
            self._hilo.join(timeout=0.5)

    # -- piezas internas ----------------------------------------------------

    def _pedir(self, nombre):
        """Encola el sonido si corresponde; nunca bloquea ni lanza errores."""
        try:
            if self._cerrado.is_set():
                return
            ahora = time.monotonic()
            anterior = self._ultimo_instante.get(nombre)
            if anterior is not None and ahora - anterior < ESPERA_ANTIREPETICION:
                return
            self._ultimo_instante[nombre] = ahora
            self._cola.put_nowait(self._datos[nombre])
        except queue.Full:
            pass  # ya hay un sonido esperando: éste se descarta
        except Exception:  # noqa: BLE001 - el sonido nunca debe romper la app
            pass

    def _trabajar(self):
        """Bucle del hilo: toma sonidos de la cola y los hace sonar."""
        while not self._cerrado.is_set():
            try:
                datos = self._cola.get(timeout=ESPERA_COLA)
            except queue.Empty:
                continue  # se vuelve a revisar si hay que terminar
            if self._cerrado.is_set():
                break
            try:
                self._reproductor(datos)
            except Exception:  # noqa: BLE001 - sin dispositivo de audio, se ignora
                pass

    @staticmethod
    def _cortar_sonido_actual():
        """Interrumpe el sonido en curso para que el hilo termine pronto."""
        if winsound is None:
            return
        try:
            winsound.PlaySound(None, winsound.SND_PURGE)
        except Exception:  # noqa: BLE001
            pass
