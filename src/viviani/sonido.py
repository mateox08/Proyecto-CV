"""Sonidos de la aplicación: se fabrican con `math.sin` y se reproducen con `winsound`.

Un sonido digital es una lista de números llamados *muestras*: cada una dice
qué tan separada está la membrana del parlante de su posición de reposo en un
instante. A 44 100 muestras por segundo el oído oye una onda continua.

Aquí generamos tres sonidos muy cortos (clic, resultado listo y error suave),
los guardamos como archivos WAV en memoria y los hacemos sonar en un hilo
aparte para que la ventana nunca se congele.
"""

import array
import io
import math
import queue
import threading
import time
import wave

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


# ---------------------------------------------------------------------------
# Síntesis: de las fórmulas a los bytes del WAV
# ---------------------------------------------------------------------------


def _decibelios_a_razon(decibelios):
    """Convierte decibelios a razón de amplitudes (-18 dB es aprox. 0,126)."""
    return 10 ** (decibelios / 20)


def _nota(frecuencia, duracion, ataque, tau, armonico=None):
    """Genera las muestras (decimales) de una nota con su envolvente.

    armonico: (número de armónico, nivel en dB) o None. Un armónico es una
    onda de frecuencia múltiplo de la principal; cambia el timbre.

    La envolvente es lo que "da forma" al volumen en el tiempo:
    - ataque lineal: sube de 0 a 1, para que la onda no arranque de golpe;
    - caída exponencial: baja como e^(-t/tau), como una campana al golpearla;
    - fundido final: baja a 0 en los últimos 5 ms. Sin esto la onda podría
      cortarse en un valor distinto de cero y el salto se oiría como un
      chasquido.
    """
    total = round(duracion * FRECUENCIA_MUESTREO)
    muestras_fundido = round(TIEMPO_FUNDIDO_FINAL * FRECUENCIA_MUESTREO)
    muestras = []
    for i in range(total):
        t = i / FRECUENCIA_MUESTREO
        onda = math.sin(2 * math.pi * frecuencia * t)
        if armonico is not None:
            numero, nivel_db = armonico
            onda += _decibelios_a_razon(nivel_db) * math.sin(
                2 * math.pi * numero * frecuencia * t
            )
        subida = min(1.0, t / ataque)
        caida = math.exp(-max(0.0, t - ataque) / tau)
        # Cuántas muestras faltan para el final (0 en la última): da el fundido.
        restantes = total - 1 - i
        fundido = min(1.0, restantes / muestras_fundido)
        muestras.append(onda * subida * caida * fundido)
    return muestras


def _silencio(duracion):
    """Muestras en cero durante `duracion` segundos."""
    return [0.0] * round(duracion * FRECUENCIA_MUESTREO)


def _a_wav(muestras, amplitud_pico):
    """Escala las muestras para que el pico valga `amplitud_pico` y arma el WAV.

    Se normaliza al final para que el nivel de cada sonido sea exacto, sin
    importar cuánto sume el armónico.
    """
    pico = max(abs(m) for m in muestras)
    enteros = array.array("h", (round(m / pico * amplitud_pico) for m in muestras))
    memoria = io.BytesIO()
    with wave.open(memoria, "wb") as archivo:
        archivo.setnchannels(1)  # mono
        archivo.setsampwidth(2)  # 16 bits = 2 bytes por muestra
        archivo.setframerate(FRECUENCIA_MUESTREO)
        archivo.writeframes(enteros.tobytes())
    return memoria.getvalue()


def sintetizar_clic():
    """Clic de confirmación: 1 760 Hz, 45 ms, pico de -24 dBFS."""
    muestras = _nota(1760, 0.045, ataque=0.002, tau=0.012)
    return _a_wav(muestras, 2067)


def sintetizar_resultado():
    """Resultado listo: dos notas ascendentes, 250 ms, pico de -20 dBFS."""
    armonico = (2, -18)
    primera = _nota(880, 0.090, 0.005, 0.060, armonico)
    segunda = _nota(1318.5, 0.140, 0.005, 0.060, armonico)
    return _a_wav(primera + _silencio(0.020) + segunda, 3277)


def sintetizar_error():
    """Error suave: dos notas descendentes, 280 ms, pico de -22 dBFS."""
    armonico = (3, -19)
    primera = _nota(523.25, 0.110, 0.008, 0.070, armonico)
    segunda = _nota(392, 0.150, 0.008, 0.070, armonico)
    return _a_wav(primera + _silencio(0.020) + segunda, 2603)


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
    """Reproduce los tres sonidos sin bloquear la interfaz ni lanzar errores."""

    def __init__(self, activado=True, reproductor=None):
        self._activado = bool(activado)
        self._reproductor = reproductor or _reproducir_con_winsound
        # Los WAV se fabrican una sola vez, al arrancar.
        self._datos = {
            "clic": sintetizar_clic(),
            "resultado": sintetizar_resultado(),
            "error": sintetizar_error(),
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

    @property
    def activado(self):
        """True si los sonidos están habilitados."""
        return self._activado

    def establecer_activado(self, valor):
        """Activa o silencia todos los sonidos."""
        self._activado = bool(valor)

    def clic(self):
        self._pedir("clic")

    def resultado(self):
        self._pedir("resultado")

    def error(self):
        self._pedir("error")

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
            if not self._activado or self._cerrado.is_set():
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
