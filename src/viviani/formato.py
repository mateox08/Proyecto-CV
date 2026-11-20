"""Formato de números para mostrarlos (punto decimal).

Este módulo no depende de la interfaz: solo convierte números en texto.
"""

ESPACIO_FINO = " "  # separador de miles que no parte la línea: 10 000 000
_SUPERINDICES = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")

NOMBRES_METODO = {
    "izquierda": "izquierda",
    "derecha": "derecha",
    "punto_medio": "punto medio",
}


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


def nombre_metodo(metodo):
    """Nombre legible del método. Ej.: 'punto_medio' -> 'punto medio'."""
    return NOMBRES_METODO[metodo]
