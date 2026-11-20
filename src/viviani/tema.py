"""Colores, fuentes y medidas de la interfaz.

La aplicación tiene un solo tema, claro, de tonos blanco azulado con brillos
suaves. Cada color tiene un nombre ("token") para no repetir códigos
hexadecimales por todo el programa: si se quiere cambiar un color, se cambia
solo aquí.
"""

_COLORES = {
    # Fondo de la ventana: degradado vertical con una rejilla muy tenue
    "fondo":              "#EDF2FA",
    "fondo_2":            "#F8FAFE",
    "rejilla":            "#D3DDEC",
    # Tarjetas tipo "vidrio"
    "superficie":         "#FBFCFE",
    # Fondo de las gráficas en pantalla: transparente (se ve la tarjeta y,
    # a través de ella, la luz del cursor). Formato #RRGGBBAA.
    "fondo_grafica":      "#FFFFFF00",
    "borde":              "#D9E2EF",
    "borde_brillo":       "#8DBBF0",
    "separador":          "#E3E9F2",
    # Texto
    "texto":              "#1B2232",
    "texto_sec":          "#55617A",
    "etiqueta":           "#5C6880",
    # Acento (botón principal, foco, brillo)
    "acento":             "#2F76CC",
    "acento_hover":       "#245FA8",
    "acento_suave":       "#DDEBFB",
    "brillo":             "#6FA9EE",
    "texto_sobre_acento": "#FFFFFF",
    # Estados
    "error":              "#B83A27",
    "fondo_error":        "#FCEDEA",
    # Series de las gráficas
    "serie_azul":         "#2F76CC",
    "serie_naranja":      "#D9672B",
    "serie_turquesa":     "#1E9C8A",
    "punto_doble":        "#E0533D",
    "esfera":             "#8EA3C2",
}

# Espaciado (en píxeles lógicos) y radios de las esquinas.
ESPACIO = {1: 4, 2: 8, 3: 12, 4: 16, 5: 24, 6: 32}
RADIO_CONTROL = 12
RADIO_TARJETA = 22

# Tipografía: todas vienen con Windows, no hay que instalar nada.
#   - serif para títulos y números grandes (aire "de libro de matemáticas")
#   - sans para el texto normal
#   - monoespaciada para las etiquetas pequeñas en mayúsculas
FAMILIAS_TITULO = ["Georgia", "Cambria", "Times New Roman"]
# Para cifras: Cambria dibuja todos los dígitos del mismo alto (Georgia no)
FAMILIAS_NUMEROS = ["Cambria", "Georgia", "Times New Roman"]
FAMILIAS_INTERFAZ = ["Segoe UI Variable Text", "Segoe UI Variable", "Segoe UI"]
FAMILIAS_MONO = ["Cascadia Mono", "Consolas", "Courier New"]
FAMILIAS_GRAFICAS = ["Segoe UI", "DejaVu Sans"]


def paleta():
    """Devuelve un diccionario {nombre: "#RRGGBB"} con todos los colores."""
    return dict(_COLORES)


def paleta_exportacion():
    """Paleta para las imágenes PNG del reporte: fondo blanco y texto negro."""
    colores = paleta()
    colores["superficie"] = "#FFFFFF"
    colores["fondo_grafica"] = "#FFFFFF"
    colores["fondo"] = "#FFFFFF"
    colores["texto"] = "#000000"
    colores["texto_sec"] = "#000000"
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
