"""Formato de números para mostrarlos (punto decimal).

Este módulo no depende de la interfaz: solo convierte números en texto.
"""

import math

ESPACIO_FINO = " "  # separador de miles que no parte la línea: 10 000 000
_SUPERINDICES = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")
# Superíndices -> texto normal, para escribirlos con <sup> (HTML). La fuente
# de la interfaz no tiene el signo menos en superíndice "⁻".
_NORMALES = str.maketrans("⁻⁰¹²³⁴⁵⁶⁷⁸⁹", "−0123456789")
CIFRAS_MAXIMAS = 16  # lo que distingue un número decimal (float) de 64 bits


def formatear_decimal(valor, decimales=6):
    """Número con decimales fijos. Ej.: 38.2016729 -> '38.201673'."""
    return f"{valor:.{decimales}f}"


def formatear_entero(n):
    """Entero con los miles separados por un espacio fino. Ej.: '10 000 000'."""
    return f"{n:,}".replace(",", ESPACIO_FINO)


def formatear_cientifico(valor, cifras=4):
    """Número con `cifras` cifras significativas.

    Si es muy grande o muy pequeño se escribe en notación científica con
    superíndices: 0.0003049 -> '3.049 × 10⁻⁴'. Si su exponente está entre
    -2 y 3 se escribe normal: 0.05 -> '0.05000'. El cero se escribe '0'.
    """
    if valor == 0:
        return "0"
    # Python ya sabe separar mantisa y exponente: '3.049e-04'
    mantisa, exponente = f"{valor:.{cifras - 1}e}".split("e")
    exponente = int(exponente)
    if -2 <= exponente <= 3:
        decimales = max(0, cifras - 1 - exponente)
        return formatear_decimal(valor, decimales)
    exponente_texto = str(exponente).translate(_SUPERINDICES)
    return f"{mantisa} × 10{exponente_texto}"


def formatear_medida(valor):
    """Una longitud en cm: 6 decimales, o científica si no cabe bien."""
    if valor != 0 and (abs(valor) >= 1e7 or abs(valor) < 1e-2):
        return formatear_cientifico(valor, cifras=7)
    return formatear_decimal(valor, 6)


def formatear_radio(radio):
    """El radio tal como conviene mostrarlo: sin ceros de más. Ej.: '7.5'."""
    if radio != 0 and (abs(radio) >= 1e7 or abs(radio) < 1e-3):
        return formatear_cientifico(radio, cifras=4)
    return f"{radio:.6f}".rstrip("0").rstrip(".")


def con_exponente(texto):
    """'7.105 × 10⁻¹⁵ cm' -> '7.105 × 10<sup>−15</sup> cm' (para un QLabel)."""
    if "× 10" not in texto:
        return texto
    antes, despues = texto.split("× 10", 1)
    exponente = ""
    while despues and despues[0] in "⁻⁰¹²³⁴⁵⁶⁷⁸⁹":
        exponente += despues[0]
        despues = despues[1:]
    return f"{antes}× 10<sup>{exponente.translate(_NORMALES)}</sup>{despues}"


def cifras_correctas(error_relativo):
    """Cifras significativas en que coinciden la aproximación y el valor de control.

    error_relativo viene en porcentaje. Un error relativo de 10⁻⁵ (0.001 %)
    son 5 cifras correctas. Error cero: todas las que caben en un float (16).
    """
    if error_relativo <= 0:
        return CIFRAS_MAXIMAS
    cifras = math.floor(-math.log10(error_relativo / 100))
    return min(max(cifras, 0), CIFRAS_MAXIMAS)


def prefijo_comun(texto_a, texto_b):
    """Cuántos caracteres iniciales coinciden. Ej.: ('38.2019', '38.2020') -> 6."""
    cantidad = 0
    for a, b in zip(texto_a, texto_b, strict=False):
        if a != b:
            break
        cantidad += 1
    return cantidad
