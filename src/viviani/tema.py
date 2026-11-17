"""Colores y medidas de la interfaz (modo claro y oscuro).

Los valores vienen de docs/DISENO.md, sección 2, donde está calculada la
razón de contraste de cada par texto/fondo (WCAG AA). Si se cambia un color
aquí hay que volver a ejecutar tests/test_tema.py, que revisa el contraste.
"""

# Cada color tiene un nombre ("token") y dos valores: claro y oscuro.
_TOKENS = {
    #  nombre:              (claro,     oscuro)
    "fondo":               ("#F4F6F9", "#14171C"),
    "superficie":          ("#FFFFFF", "#1E2229"),
    "superficie_deshab":   ("#EEF0F3", "#262B33"),
    "texto":               ("#1A1D23", "#E8EAED"),
    "texto_sec":           ("#4A5361", "#A9B1BC"),
    "texto_deshab":        ("#5C6573", "#8B939E"),
    "acento":              ("#1F5FBF", "#7AAEFF"),
    "acento_hover":        ("#174C99", "#A3C6FF"),
    "texto_sobre_acento":  ("#FFFFFF", "#0B1220"),
    "error":               ("#B3261E", "#FF8A80"),
    "fondo_error":         ("#FDECEA", "#3B1A18"),
    "exito":               ("#1B7A3A", "#6FD08C"),
    "aviso":               ("#8A5A00", "#F2C14E"),
    "fondo_aviso":         ("#FFF4DB", "#3A2E10"),
    "borde":               ("#7A8494", "#7D8693"),
    "separador":           ("#D5DAE1", "#3A404A"),
    "foco":                ("#0B57D0", "#9CC3FF"),
    "tooltip_fondo":       ("#2B3038", "#E8EAED"),
    "tooltip_texto":       ("#FFFFFF", "#14171C"),
    # Series de las gráficas (derivadas de la paleta Okabe-Ito, apta para
    # personas con daltonismo).
    "serie_azul":          ("#0072B2", "#56B4E9"),
    "serie_naranja":       ("#C24E00", "#F28E2B"),
    "serie_verde":         ("#00805C", "#3CC79A"),
    "serie_morado":        ("#8E3B87", "#D98CD0"),
    "punto_doble":         ("#B3261E", "#FF8A80"),
    "esfera":              ("#7A8494", "#7D8693"),
}

# Transparencia de la superficie de la esfera en cada modo.
ALFA_ESFERA = {"claro": 0.12, "oscuro": 0.18}

# Espaciado (en píxeles lógicos) y radios de las esquinas.
ESPACIO = {1: 4, 2: 8, 3: 12, 4: 16, 5: 24, 6: 32}
RADIO_CONTROL = 6
RADIO_TARJETA = 10

# Tipografía: fuente del sistema en Windows 11, con respaldos.
FAMILIAS_INTERFAZ = ["Segoe UI Variable Text", "Segoe UI Variable", "Segoe UI", "Inter"]
FAMILIAS_GRAFICAS = ["Segoe UI", "DejaVu Sans"]


def paleta(oscuro):
    """Devuelve un diccionario {nombre: "#RRGGBB"} para el modo pedido.

    Incluye además la clave "modo" ("claro" u "oscuro") y "alfa_esfera".
    """
    indice = 1 if oscuro else 0
    colores = {nombre: valores[indice] for nombre, valores in _TOKENS.items()}
    colores["modo"] = "oscuro" if oscuro else "claro"
    colores["alfa_esfera"] = ALFA_ESFERA[colores["modo"]]
    return colores


def paleta_exportacion():
    """Paleta para las imágenes PNG del reporte: siempre fondo blanco."""
    colores = paleta(oscuro=False)
    colores["texto"] = "#000000"
    colores["texto_sec"] = "#000000"
    colores["fondo"] = "#FFFFFF"
    return colores


def razon_de_contraste(color_a, color_b):
    """Razón de contraste WCAG 2.x entre dos colores "#RRGGBB" (de 1 a 21)."""

    def luminancia(color):
        canales = []
        for i in (1, 3, 5):
            c = int(color[i : i + 2], 16) / 255
            canales.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
        return 0.2126 * canales[0] + 0.7152 * canales[1] + 0.0722 * canales[2]

    clara, oscura = sorted((luminancia(color_a), luminancia(color_b)), reverse=True)
    return (clara + 0.05) / (oscura + 0.05)
