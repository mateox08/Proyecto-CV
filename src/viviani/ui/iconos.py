"""Iconos Lucide (licencia ISC) en SVG, recoloreados según el tema.

Los archivos viven en src/viviani/recursos/iconos/. La ruta se calcula a
partir de este mismo archivo (__file__), así funciona igual al ejecutar desde
el código fuente que dentro del .exe de PyInstaller (que debe incluir la
carpeta `recursos`).

Cada SVG usa `stroke="currentColor"`: para pintarlo de otro color basta
reemplazar esa palabra por el color deseado.
"""

from functools import cache
from pathlib import Path

from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QGuiApplication, QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

CARPETA = Path(__file__).resolve().parent.parent / "recursos" / "iconos"


@cache
def _leer_svg(nombre):
    return (CARPETA / f"{nombre}.svg").read_text(encoding="utf-8")


def pixmap(nombre, color, tamano=16):
    """Dibuja el icono `nombre` en `color` ("#RRGGBB") de tamano x tamano DIP.

    Se dibuja con el doble de píxeles (o más en pantallas de alta densidad)
    para que se vea nítido al escalar la pantalla al 125 % o 150 %.
    """
    svg = _leer_svg(nombre).replace("currentColor", color)
    dibujante_svg = QSvgRenderer(QByteArray(svg.encode("utf-8")))

    pantalla = QGuiApplication.primaryScreen()
    proporcion = max(2.0, pantalla.devicePixelRatio() if pantalla else 1.0)
    lado = round(tamano * proporcion)

    imagen = QPixmap(lado, lado)
    imagen.fill(Qt.GlobalColor.transparent)
    pincel = QPainter(imagen)
    dibujante_svg.render(pincel)
    pincel.end()
    imagen.setDevicePixelRatio(proporcion)
    return imagen


def icono(nombre, color, tamano=16):
    """Lo mismo que `pixmap`, pero como QIcon (para botones)."""
    return QIcon(pixmap(nombre, color, tamano))
