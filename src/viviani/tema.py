"""Colores, fuentes y medidas de la interfaz.

La aplicación tiene un solo tema, oscuro y sobrio, tipo "grafito": fondo
carbón neutro, texto casi blanco y un único acento verde menta. El ámbar y
el coral se reservan para marcar puntos en las gráficas. Cada color tiene un
nombre ("token") para no repetir códigos hexadecimales por todo el programa:
si se quiere cambiar un color, se cambia solo aquí.
"""

_COLORES = {
    # Fondo de la ventana: carbón con una rejilla de puntos muy tenue
    "fondo":              "#0B0C0F",
    "fondo_2":            "#111318",
    "rejilla":            "#2A2E36",
    # Superficies (cajas, paneles)
    "superficie":         "#15171C",
    # Fondo de las gráficas en pantalla: transparente. Formato #RRGGBBAA.
    "fondo_grafica":      "#00000000",
    "borde":              "#2A2E36",
    "borde_brillo":       "#7DD3C0",
    "separador":          "#1E2127",
    # Texto
    "texto":              "#ECEDEF",
    "texto_sec":          "#9BA1AB",
    "etiqueta":           "#858B96",
    # Acento único: verde menta
    "acento":             "#7DD3C0",
    "acento_hover":       "#A3E4D5",
    "acento_suave":       "#1C2F2B",
    "brillo":             "#7DD3C0",
    "violeta":            "#8FB8DE",  # segundo tono, azul cielo apagado
    "texto_sobre_acento": "#0B0C0F",
    # Estados
    "error":              "#F28B82",
    "fondo_error":        "#2A1716",
    # Series de las gráficas
    "serie_azul":         "#7DD3C0",
    "serie_naranja":      "#E8B76A",
    "serie_turquesa":     "#8FB8DE",  # la curva 3D va de menta a azul cielo
    "punto_doble":        "#F28B6C",
    "esfera":             "#6B7383",
}

# Tipografía: todas vienen con Windows, no hay que instalar nada.
# Una sola familia (Segoe UI Variable) para casi todo; la monoespaciada solo
# para los números pequeños de los ejes 3D.
FAMILIAS_TITULO = ["Segoe UI Variable Display", "Segoe UI Variable", "Segoe UI"]
FAMILIAS_NUMEROS = ["Segoe UI Variable Display", "Segoe UI Variable", "Segoe UI"]
FAMILIAS_INTERFAZ = ["Segoe UI Variable Text", "Segoe UI Variable", "Segoe UI"]
FAMILIAS_MONO = ["Cascadia Mono", "Consolas", "Courier New"]
FAMILIAS_GRAFICAS = ["Segoe UI", "DejaVu Sans"]


def paleta():
    """Devuelve un diccionario {nombre: "#RRGGBB"} con todos los colores."""
    return dict(_COLORES)


def rgba(color, alfa):
    """Color "#RRGGBB" con transparencia (0 a 1) en formato de hoja de estilos."""
    r, g, b = (int(color[i : i + 2], 16) for i in (1, 3, 5))
    return f"rgba({r}, {g}, {b}, {round(alfa * 255)})"


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
