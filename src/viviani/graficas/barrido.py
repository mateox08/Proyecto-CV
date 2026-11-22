"""Ritmo del barrido que sigue a cada resultado.

Los rectángulos de Riemann crecen uno tras otro y, al mismo ritmo, aparecen
los puntos de muestra r(tᵢ) sobre la curva 3D. Las dos gráficas toman los
tiempos de aquí para ir sincronizadas.
"""

import numpy as np

DURACION_BARRIDO_MS = 1500  # todo el barrido
DURACION_BARRA_MS = 250  # lo que tarda en crecer cada rectángulo


def inicios_escalonados(cantidad):
    """Instante (ms) en que empieza a crecer cada una de `cantidad` barras.

    La barra k empieza en k·(1500 − 250)/(cantidad − 1) ms: la primera en 0
    y la última justo a tiempo para terminar a los 1500 ms.
    """
    if cantidad == 1:
        return np.zeros(1)
    paso = (DURACION_BARRIDO_MS - DURACION_BARRA_MS) / (cantidad - 1)
    return np.arange(cantidad) * paso
