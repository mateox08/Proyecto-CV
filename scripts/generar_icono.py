"""Genera el icono de la aplicación a partir del logo dibujado en código.

Uso (desde la raíz del repositorio):

    .venv\\Scripts\\python.exe scripts\\generar_icono.py

Crea dos archivos en src/viviani/recursos/:
    icono.png   512 x 512, para la ventana y la pantalla de carga
    icono.ico   varios tamaños (16 a 256), para el .exe de Windows
"""

import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PIL import Image  # noqa: E402  (Pillow ya viene con matplotlib)
from PySide6.QtGui import QGuiApplication  # noqa: E402

from viviani.ui.logo import imagen_logo  # noqa: E402

TAMANOS_ICO = [16, 24, 32, 48, 64, 128, 256]


def main():
    _app = QGuiApplication([])
    carpeta = RAIZ / "src" / "viviani" / "recursos"
    png = carpeta / "icono.png"
    imagen_logo(512).save(str(png), "PNG")

    # Cada tamaño se dibuja por separado (más nítido que achicar uno grande)
    capas = []
    for lado in TAMANOS_ICO:
        temporal = carpeta / f"_icono_{lado}.png"
        imagen_logo(lado).save(str(temporal), "PNG")
        capas.append(Image.open(temporal).convert("RGBA"))
    grande = capas[-1]
    grande.save(
        carpeta / "icono.ico",
        format="ICO",
        sizes=[(lado, lado) for lado in TAMANOS_ICO],
        append_images=capas[:-1],
    )
    for lado in TAMANOS_ICO:
        (carpeta / f"_icono_{lado}.png").unlink()
    print(f"Listo: {png} y {carpeta / 'icono.ico'}")


if __name__ == "__main__":
    main()
