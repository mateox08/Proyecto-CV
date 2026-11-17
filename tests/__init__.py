"""Pruebas de la aplicación. Ejecutar desde la raíz:  python -m unittest -v

Estas líneas permiten importar el paquete `viviani` (que vive en src/) y el
módulo `perimetro_viviani` (que vive en la raíz) sin instalar nada.
"""

import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
for carpeta in (RAIZ, RAIZ / "src"):
    if str(carpeta) not in sys.path:
        sys.path.insert(0, str(carpeta))

# Las pruebas de la interfaz se ejecutan sin abrir ventanas en pantalla.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
