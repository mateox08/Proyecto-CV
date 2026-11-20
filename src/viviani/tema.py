"""Colores, fuentes y medidas de la interfaz.

La aplicación tiene un solo tema, oscuro, tipo "observatorio": fondo azul
noche con una rejilla de puntos, luces suaves y acentos cian y violeta. Cada
color tiene un nombre ("token") para no repetir códigos hexadecimales por
todo el programa: si se quiere cambiar un color, se cambia solo aquí.
"""

_COLORES = {
    # Fondo de la ventana: degradado vertical con una rejilla de puntos
    "fondo":              "#070B14",
    "fondo_2":            "#0D1424",
    "rejilla":            "#2A3550",
    # Superficies (cajas de texto, aviso de error)
    "superficie":         "#111A2E",
    # Fondo de las gráficas en pantalla: transparente. Formato #RRGGBBAA.
    "fondo_grafica":      "#00000000",
    "borde":              "#26324A",
    "borde_brillo":       "#5FD4FF",
    "separador":          "#1C2740",
    # Texto
    "texto":              "#E8EEF9",
    "texto_sec":          "#9AA8C2",
    "etiqueta":           "#8494B2",
    # Acento (botón principal, foco, brillo)
    "acento":             "#4CC9F0",
    "acento_hover":       "#7FDBFF",
    "acento_suave":       "#16314A",
    "brillo":             "#4CC9F0",
    "violeta":            "#9D7BFF",
    "texto_sobre_acento": "#06101C",
    # Estados
    "error":              "#FF7A6B",
    "fondo_error":        "#2A1418",
    # Series de las gráficas
    "serie_azul":         "#4CC9F0",
    "serie_naranja":      "#FFB454",
    "serie_turquesa":     "#9D7BFF",  # la curva 3D va de cian a violeta
    "punto_doble":        "#FF6B8B",
    "esfera":             "#7C93C4",
}

# Colores para las imágenes PNG del reporte: fondo blanco y tonos oscuros,
# porque se van a imprimir.
_COLORES_EXPORTACION = {
    "superficie":         "#FFFFFF",
    "fondo":              "#FFFFFF",
    "fondo_grafica":      "#FFFFFF",
    "texto":              "#000000",
    "texto_sec":          "#000000",
    "etiqueta":           "#333333",
    "borde":              "#7A8494",
    "separador":          "#D5DAE1",
    "serie_azul":         "#1F5FBF",
    "serie_naranja":      "#C24E00",
    "serie_turquesa":     "#6A3FD0",
    "punto_doble":        "#C2183F",
    "esfera":             "#7A8494",
}

# Tipografía: todas vienen con Windows, no hay que instalar nada.
#   - serif para títulos (aire "de libro de matemáticas")
#   - Cambria para cifras (todos los dígitos del mismo alto)
#   - sans para el texto normal
#   - monoespaciada para las etiquetas pequeñas en mayúsculas
FAMILIAS_TITULO = ["Georgia", "Cambria", "Times New Roman"]
FAMILIAS_NUMEROS = ["Cambria", "Georgia", "Times New Roman"]
FAMILIAS_INTERFAZ = ["Segoe UI Variable Text", "Segoe UI Variable", "Segoe UI"]
FAMILIAS_MONO = ["Cascadia Mono", "Consolas", "Courier New"]
FAMILIAS_GRAFICAS = ["Segoe UI", "DejaVu Sans"]


def paleta():
    """Devuelve un diccionario {nombre: "#RRGGBB"} con todos los colores."""
    return dict(_COLORES)


def paleta_exportacion():
    """Paleta para las imágenes PNG del reporte (fondo blanco)."""
    colores = paleta()
    colores.update(_COLORES_EXPORTACION)
    return colores


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
