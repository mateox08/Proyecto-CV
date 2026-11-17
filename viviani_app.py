"""Lanzador de la aplicación gráfica.

Ejecutar desde la raíz del repositorio:

    python viviani_app.py

Solo agrega la carpeta src/ a la lista de lugares donde Python busca
módulos y luego llama a la función principal del paquete `viviani`.
(La versión de consola sigue siendo:  python perimetro_viviani.py)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from viviani.app import main  # noqa: E402

if __name__ == "__main__":
    main()
