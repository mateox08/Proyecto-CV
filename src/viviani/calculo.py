"""Cálculo del perímetro de la Ventana de Viviani con numpy (sin Qt).

Hace lo mismo que `suma_de_riemann` de perimetro_viviani.py, pero:
  - suma por bloques con numpy (mucho más rápido que un `for` de Python);
  - avisa el progreso y permite cancelar entre bloques;
  - además entrega los rectángulos que hay que dibujar.
"""

import math
from dataclasses import dataclass

import numpy as np

from perimetro_viviani import (
    MAX_SUBINTERVALOS,
    METODOS_VALIDOS,
    RAZON_REFERENCIA,
    T_FINAL,
    T_INICIAL,
)

MAX_BARRAS = 120  # rectángulos que se dibujan como máximo
TAMANO_BLOQUE = 1_000_000  # subintervalos por bloque (progreso y cancelación)

# Desplazamiento del punto de muestra dentro de cada subintervalo:
# 0 -> extremo izquierdo, 1 -> extremo derecho, 0.5 -> punto medio
DESPLAZAMIENTO = {"izquierda": 0.0, "derecha": 1.0, "punto_medio": 0.5}

# Valores de n de la gráfica de convergencia (DISENO 8.4)
N_PEQUENOS = list(range(1, 65))
N_GRANDES = sorted(set(np.rint(np.logspace(np.log10(80), 7, 24)).astype(int).tolist()))


class CalculoCancelado(Exception):
    """Se lanza cuando el usuario cancela un cálculo en curso."""


@dataclass(frozen=True)
class Resultado:
    radio: float
    n: int
    metodo: str  # "izquierda" | "derecha" | "punto_medio"
    perimetro: float  # cm
    referencia: float  # RAZON_REFERENCIA * radio
    error_absoluto: float  # cm
    error_relativo: float  # en porcentaje
    barras_inicio: np.ndarray  # borde izquierdo (t) de cada barra dibujada
    barras_ancho: np.ndarray
    barras_altura: np.ndarray
    puntos_t: np.ndarray | None  # puntos de muestra t_i si n <= MAX_BARRAS
    agrupado: bool  # True si n > MAX_BARRAS


def _validar(radio, n, metodo):
    """Mismas reglas y mensajes que `suma_de_riemann`."""
    if not math.isfinite(radio) or radio <= 0:
        raise ValueError("El radio R debe ser un número real positivo.")
    if not isinstance(n, int) or isinstance(n, bool) or n <= 0:
        raise ValueError("El número de subintervalos debe ser un entero positivo.")
    if n > MAX_SUBINTERVALOS:
        raise ValueError(
            f"El número de subintervalos no debe superar {MAX_SUBINTERVALOS:,}."
        )
    if metodo not in METODOS_VALIDOS:
        raise ValueError(f"Método no válido. Opciones: {METODOS_VALIDOS}.")


def _revisar_cancelacion(cancelado):
    if cancelado is not None and cancelado():
        raise CalculoCancelado("Cálculo cancelado por el usuario.")


def _suma_por_bloques(radio, n, metodo, progreso=None, cancelado=None, grupos=0):
    """Suma f(t_i) para i = 0..n-1 recorriendo el intervalo por bloques.

    Si `grupos` > 0 también suma f dentro de cada grupo de subintervalos
    (para las barras agrupadas), sin guardar los n valores.
    Devuelve (suma_total, sumas_por_grupo o None).
    """
    delta_t = (T_FINAL - T_INICIAL) / n
    desplazamiento = DESPLAZAMIENTO[metodo]
    sumas_bloque = []  # una suma parcial por bloque
    sumas_grupo = np.zeros(grupos) if grupos else None

    for inicio in range(0, n, TAMANO_BLOQUE):
        _revisar_cancelacion(cancelado)
        fin = min(inicio + TAMANO_BLOQUE, n)
        i = np.arange(inicio, fin)
        t = T_INICIAL + (i + desplazamiento) * delta_t
        with np.errstate(all="ignore"):  # que numpy no imprima avisos
            f = radio * np.sqrt(1 + np.cos(t) ** 2)
            sumas_bloque.append(float(np.sum(f)))
        if grupos:
            # El subintervalo i pertenece al grupo k que cumple
            # floor(k*n/g) <= i < floor((k+1)*n/g)  (DISENO 6.3)
            grupo = (grupos * (i + 1) + n - 1) // n - 1
            sumas_grupo += np.bincount(grupo, weights=f, minlength=grupos)
        if progreso is not None:
            progreso(int(100 * fin / n))

    try:
        suma = math.fsum(sumas_bloque)
    except OverflowError:
        raise ValueError(
            "El resultado es demasiado grande para representarse."
        ) from None
    return suma, sumas_grupo


def _error_relativo(perimetro, referencia):
    return abs(perimetro - referencia) / referencia * 100


def _barras_reales(radio, n, metodo):
    """Las n barras tal cual (n <= MAX_BARRAS): ancho delta_t y altura f(t_i)."""
    delta_t = (T_FINAL - T_INICIAL) / n
    inicio = T_INICIAL + np.arange(n) * delta_t
    puntos_t = inicio + DESPLAZAMIENTO[metodo] * delta_t
    altura = radio * np.sqrt(1 + np.cos(puntos_t) ** 2)
    return inicio, np.full(n, delta_t), altura, puntos_t


def _barras_agrupadas(n, sumas_grupo):
    """MAX_BARRAS barras; la altura es el promedio de f en cada grupo."""
    delta_t = (T_FINAL - T_INICIAL) / n
    k = np.arange(MAX_BARRAS)
    i_ini = (k * n) // MAX_BARRAS
    i_fin = ((k + 1) * n) // MAX_BARRAS - 1
    cuantos = i_fin - i_ini + 1
    return T_INICIAL + i_ini * delta_t, cuantos * delta_t, sumas_grupo / cuantos


def calcular(radio, n, metodo="punto_medio", progreso=None, cancelado=None):
    """Calcula el perímetro aproximado y los rectángulos para dibujarlo.

    progreso(porcentaje) se llama después de cada bloque; si cancelado()
    devuelve True se lanza CalculoCancelado.
    """
    _validar(radio, n, metodo)
    agrupado = n > MAX_BARRAS
    suma, sumas_grupo = _suma_por_bloques(
        radio, n, metodo, progreso, cancelado, MAX_BARRAS if agrupado else 0
    )
    perimetro = suma * (T_FINAL - T_INICIAL) / n
    if not math.isfinite(perimetro):
        raise ValueError("El resultado es demasiado grande para representarse.")

    if agrupado:
        inicio, ancho, altura = _barras_agrupadas(n, sumas_grupo)
        puntos_t = None
    else:
        inicio, ancho, altura, puntos_t = _barras_reales(radio, n, metodo)

    referencia = RAZON_REFERENCIA * radio
    return Resultado(
        radio=radio,
        n=n,
        metodo=metodo,
        perimetro=perimetro,
        referencia=referencia,
        error_absoluto=abs(perimetro - referencia),
        error_relativo=_error_relativo(perimetro, referencia),
        barras_inicio=inicio,
        barras_ancho=ancho,
        barras_altura=altura,
        puntos_t=puntos_t,
        agrupado=agrupado,
    )


def _errores_relativos(metodo, valores_n, cancelado):
    """Error relativo (%) con R = 1 para cada n de la lista."""
    errores = []
    for n in valores_n:
        suma, _ = _suma_por_bloques(1.0, n, metodo, cancelado=cancelado)
        perimetro = suma * (T_FINAL - T_INICIAL) / n
        errores.append(_error_relativo(perimetro, RAZON_REFERENCIA))
    return np.array(errores)


def datos_convergencia(cancelado=None):
    """{método: (valores_de_n, error_relativo_en_%)} con R = 1 (DISENO 8.4)."""
    valores_n = np.array(N_PEQUENOS + N_GRANDES)
    # Izquierda y derecha dan la misma suma (f es periódica): se calcula una.
    errores_borde = _errores_relativos("izquierda", valores_n.tolist(), cancelado)
    errores_medio = _errores_relativos("punto_medio", valores_n.tolist(), cancelado)
    return {
        "izquierda": (valores_n, errores_borde),
        "derecha": (valores_n, errores_borde.copy()),
        "punto_medio": (valores_n, errores_medio),
    }
