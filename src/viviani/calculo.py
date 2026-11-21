"""Cálculo del perímetro de la Ventana de Viviani con numpy (sin Qt).

Hace lo mismo que `suma_de_riemann` de perimetro_viviani.py (con punto
medio), pero:
  - suma por bloques con numpy (mucho más rápido que un `for` de Python);
  - avisa el progreso y permite cancelar entre bloques;
  - además entrega los rectángulos que hay que dibujar.
"""

import math
from dataclasses import dataclass

import numpy as np

from perimetro_viviani import MAX_SUBINTERVALOS, RAZON_REFERENCIA, T_FINAL, T_INICIAL

MAX_BARRAS = 120  # rectángulos que se dibujan como máximo
TAMANO_BLOQUE = 1_000_000  # subintervalos por bloque (progreso y cancelación)


class CalculoCancelado(Exception):
    """Se lanza cuando el usuario cancela un cálculo en curso."""


@dataclass(frozen=True)
class Resultado:
    radio: float
    n: int
    metodo: str  # siempre "punto_medio"
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
    if metodo != "punto_medio":
        raise ValueError("Método no válido: solo se usa el punto medio.")


def _suma_por_bloques(radio, n, grupos, progreso=None, cancelado=None):
    """Suma f(t_i), con t_i el punto medio de cada subintervalo, por bloques.

    También suma f dentro de cada uno de los `grupos` (las barras), sin
    guardar los n valores. Con grupos == n cada grupo es un solo
    subintervalo, así que esa suma ya es la altura de cada barra.
    Devuelve (suma_total, sumas_por_grupo).
    """
    delta_t = (T_FINAL - T_INICIAL) / n
    suma = 0.0  # un float de Python no lanza error al desbordar: queda inf
    sumas_grupo = np.zeros(grupos)

    for inicio in range(0, n, TAMANO_BLOQUE):
        if cancelado is not None and cancelado():
            raise CalculoCancelado("Cálculo cancelado por el usuario.")
        fin = min(inicio + TAMANO_BLOQUE, n)
        i = np.arange(inicio, fin)
        f = radio * np.sqrt(1 + np.cos(T_INICIAL + (i + 0.5) * delta_t) ** 2)
        suma += float(np.sum(f))
        # El subintervalo i pertenece al grupo k que cumple
        # floor(k*n/g) <= i < floor((k+1)*n/g)  (DISENO 6.3)
        grupo = (grupos * (i + 1) + n - 1) // n - 1
        sumas_grupo += np.bincount(grupo, weights=f, minlength=grupos)
        if progreso is not None:
            progreso(int(100 * fin / n))

    return suma, sumas_grupo


def _barras(n, sumas_grupo):
    """Una barra por grupo; la altura es el promedio de f en el grupo."""
    delta_t = (T_FINAL - T_INICIAL) / n
    k = np.arange(len(sumas_grupo))
    i_ini = (k * n) // len(sumas_grupo)
    cuantos = ((k + 1) * n) // len(sumas_grupo) - i_ini
    return T_INICIAL + i_ini * delta_t, cuantos * delta_t, sumas_grupo / cuantos


def calcular(radio, n, metodo="punto_medio", progreso=None, cancelado=None):
    """Calcula el perímetro aproximado y los rectángulos para dibujarlo.

    progreso(porcentaje) se llama después de cada bloque; si cancelado()
    devuelve True se lanza CalculoCancelado.
    """
    _validar(radio, n, metodo)
    agrupado = n > MAX_BARRAS
    suma, sumas_grupo = _suma_por_bloques(
        radio, n, min(n, MAX_BARRAS), progreso, cancelado
    )
    perimetro = suma * (T_FINAL - T_INICIAL) / n
    if not math.isfinite(perimetro):
        raise ValueError("El resultado es demasiado grande para representarse.")

    inicio, ancho, altura = _barras(n, sumas_grupo)
    referencia = RAZON_REFERENCIA * radio
    error_absoluto = abs(perimetro - referencia)
    return Resultado(
        radio=radio,
        n=n,
        metodo=metodo,
        perimetro=perimetro,
        referencia=referencia,
        error_absoluto=error_absoluto,
        error_relativo=error_absoluto / referencia * 100,
        barras_inicio=inicio,
        barras_ancho=ancho,
        barras_altura=altura,
        puntos_t=None if agrupado else inicio + ancho / 2,
        agrupado=agrupado,
    )
