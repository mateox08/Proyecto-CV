"""Validación de los datos que escribe el usuario (sin Qt, solo texto).

Cada función recibe el texto del campo y devuelve una pareja:

    (valor, "")        si el texto es válido
    (None, mensaje)    si no lo es; el mensaje dice cómo corregirlo

Los mensajes y el orden en que se revisan las condiciones salen de
docs/DISENO.md.

Decisión sobre los dígitos Unicode: Python acepta dígitos de otros alfabetos
(por ejemplo "１２" de ancho completo) como si fueran números. Aquí NO se
aceptan: solo los dígitos ASCII 0-9. Así el comportamiento es el mismo en
cualquier computador y el usuario ve en el campo exactamente lo que se
calcula.
"""

import math
import re

from viviani.formato import formatear_entero

MAX_SUBINTERVALOS = 10_000_000

# "nan", "inf", "infinity" con signo opcional y cualquier mayúscula.
_NO_FINITO = re.compile(r"[+-]?(nan|inf|infinity)", re.IGNORECASE)

# Número decimal sencillo con dígitos ASCII: 5, 7.5, .5, 5., +7, 1e3, 1.5E-3
_NUMERO_REAL = re.compile(r"[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?", re.ASCII)

# Separador de miles escrito por error: 1.000, 10,000, 1.000.000
_MILES = re.compile(r"\d{1,3}([.,]\d{3})+", re.ASCII)

# Número escrito con punto o coma decimal: 2,5  10.5  1,2,3
_CON_SEPARADOR = re.compile(r"[+-]?[\d.,]*[.,][\d.,]*", re.ASCII)

# Notación científica: 1e6, 2,5e3
_CIENTIFICA = re.compile(r"[+-]?\d+([.,]\d+)?[eE][+-]?\d+", re.ASCII)

# Entero con signo opcional: 1000, +7, -5
_ENTERO = re.compile(r"[+-]?\d+", re.ASCII)


def validar_radio(texto):
    """Revisa el radio R. Devuelve (radio, "") o (None, mensaje)."""
    texto = texto.strip()
    if not texto:
        return None, "Escriba el radio R."

    # Se acepta coma o punto decimal: se unifica a punto antes de convertir.
    texto = texto.replace(",", ".")

    if _NO_FINITO.fullmatch(texto):
        return None, "R debe ser un número finito."

    # Se exige la forma exacta del número para rechazar lo que float()
    # tolera pero no es lo que se espera ("1_0", "１２", espacios internos).
    if not _NUMERO_REAL.fullmatch(texto):
        return None, "Escriba un número, por ejemplo 5 o 7.5."

    radio = float(texto)
    if math.isinf(radio):  # por ejemplo "1e999"
        return None, "R debe ser un número finito."
    if radio <= 0:
        return None, "R debe ser mayor que cero."
    # Un radio enorme (1e300) es válido aquí: el desbordamiento lo detecta
    # el cálculo, que es quien sabe cuándo el resultado deja de caber.
    return radio, ""


def validar_subintervalos(texto):
    """Revisa el número de subintervalos n. Devuelve (n, "") o (None, mensaje)."""
    # Los espacios (también el espacio fino U+202F) se usan como separador de
    # miles, así que "10 000" vale 10000.
    texto = "".join(texto.split())
    if not texto:
        return None, "Escriba el número de subintervalos n."

    if _NO_FINITO.fullmatch(texto):
        return None, "n debe ser un número finito."

    if _MILES.fullmatch(texto):
        return None, "Escriba n sin puntos ni comas, por ejemplo 1000."

    if _CON_SEPARADOR.fullmatch(texto) or _CIENTIFICA.fullmatch(texto):
        return None, "n debe ser un número entero, sin decimales."

    if not _ENTERO.fullmatch(texto):
        return None, "Escriba solo dígitos, por ejemplo 1000."

    try:
        n = int(texto)
    except ValueError:
        # Python limita la cantidad de dígitos al convertir; un número tan
        # largo es, sin duda, mayor que el máximo.
        n = MAX_SUBINTERVALOS + 1 if texto[0] != "-" else 0
    if n <= 0:
        return None, "n debe ser mayor que cero."
    if n > MAX_SUBINTERVALOS:
        return None, f"n no debe superar {formatear_entero(MAX_SUBINTERVALOS)}."
    return n, ""
