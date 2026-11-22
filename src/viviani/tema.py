"""Colores y fuentes de la interfaz.

La aplicación tiene un solo tema, oscuro y plateado: fondo casi negro con
estrellas, texto blanco, un degradado de blanco a gris plata como sello y un
naranja de señal para los puntos de muestra (lo único con color, para que
salten a la vista). Cada color tiene un nombre ("token") para no repetir
códigos hexadecimales por todo el programa: si se quiere cambiar un color,
se cambia solo aquí.
"""

from PySide6.QtGui import QColor

_COLORES = {
    # Fondo de la ventana: casi negro, con estrellas blancas
    "fondo":              "#08090A",
    "fondo_2":            "#101113",
    "estrella":           "#FFFFFF",
    # Superficies (tarjetas, cajas de texto, chips)
    "superficie":         "#131416",
    "superficie_2":       "#1B1C1F",
    "borde":              "#303236",
    "separador":          "#1F2023",
    # Texto
    "texto":              "#F2F2F2",
    "texto_sec":          "#ABADB2",
    "etiqueta":           "#909298",
    # Acentos: blanco y plata (siempre juntos, en degradado)
    "acento":             "#EDEDED",
    "acento_2":           "#8C9099",
    "acento_suave":       "#25272B",
    "texto_sobre_acento": "#0A0A0B",
    # Estados
    "error":              "#FF7A66",
    "fondo_error":        "#2A1512",
    # Gráficas: el naranja de señal marca lo que hay que mirar
    "muestra":            "#FF6A3D",  # puntos de muestra t_i
    "aviso":              "#FF8A5C",  # cifras que aún no son correctas
    "punto_doble":        "#FF3D3D",
    "esfera":             "#71757C",
    "cilindro":           "#FF6A3D",
}

# Tipografía: todas vienen con Windows, no hay que instalar nada.
FAMILIAS_TITULO = ["Segoe UI Variable Display", "Segoe UI Variable", "Segoe UI"]
FAMILIAS_INTERFAZ = ["Segoe UI Variable Text", "Segoe UI Variable", "Segoe UI"]
FAMILIAS_MONO = ["Cascadia Mono", "Consolas", "Courier New"]
# Las fórmulas con la letra de los libros de matemáticas
FAMILIAS_MATEMATICA = ["Cambria Math", "Cambria", "Segoe UI"]


def paleta():
    """Devuelve un diccionario {nombre: "#RRGGBB"} con todos los colores."""
    return dict(_COLORES)


def con_alfa(color, alfa):
    """QColor a partir de "#RRGGBB" con transparencia (0 a 1) para QPainter."""
    tono = QColor(color)
    tono.setAlphaF(min(max(alfa, 0.0), 1.0))
    return tono


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
