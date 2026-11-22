# -*- mode: python ; coding: utf-8 -*-
"""Receta de PyInstaller para "Perímetro de la Ventana de Viviani".

Sirve para los dos modos; se elige con la variable de entorno VIVIANI_MODO:

    onedir   (por defecto)  carpeta dist\\PerimetroViviani\\ con el .exe y sus
                            librerías al lado. Abre más rápido.
    onefile                 un único dist\\PerimetroViviani.exe que se descomprime
                            en una carpeta temporal en cada arranque (más lento).

Uso directo (lo normal es scripts\\construir.ps1, que además prueba antes):

    $env:VIVIANI_MODO = "onedir"
    .venv\\Scripts\\python.exe -m PyInstaller viviani.spec --noconfirm --clean ^
        --distpath dist --workpath build\\onedir

Si algún día el .exe falla al abrir con "No module named ...", quite esa
exclusión de la lista EXCLUIR.
"""

import os
from pathlib import Path

# SPECPATH la define PyInstaller: es la carpeta donde está este archivo.
RAIZ = Path(SPECPATH).resolve()  # noqa: F821

MODO = os.environ.get("VIVIANI_MODO", "onedir").strip().lower()
if MODO not in ("onedir", "onefile"):
    raise SystemExit(f"VIVIANI_MODO debe ser 'onedir' o 'onefile', no '{MODO}'.")

NOMBRE = "PerimetroViviani"
# Icono del .exe (se genera con scripts/generar_icono.py)
ICONO = str(RAIZ / "src" / "viviani" / "recursos" / "icono.ico")

# --- Qué NO se incluye -----------------------------------------------------
EXCLUIR = [
    # Bibliotecas que la app no usa pero están instaladas en .venv (scipy
    # para verificar el valor de control, Pillow para generar el icono,
    # matplotlib de la versión 2): PyInstaller podría arrastrarlas.
    "tkinter", "_tkinter", "scipy", "PIL", "matplotlib",
    "pydoc", "test", "distutils", "setuptools",
    "pkg_resources", "IPython", "pytest",
    # Pruebas internas de numpy.
    "numpy.testing", "numpy.tests",
    "PyQt5", "PyQt6", "PySide2",
    # Red / criptografía: la app no usa internet. Quitar ssl y _hashlib
    # elimina libcrypto-3.dll y libssl-3.dll (~7 MB).
    "ssl", "_ssl", "_hashlib",
    # Módulos de Qt que la app no importa (solo usa QtCore, QtGui y QtWidgets).
    "PySide6.QtQml", "PySide6.QtQuick", "PySide6.QtQuickWidgets",
    "PySide6.QtQuickControls2", "PySide6.QtNetwork", "PySide6.QtPdf",
    "PySide6.QtPdfWidgets", "PySide6.QtOpenGL", "PySide6.QtOpenGLWidgets",
    "PySide6.QtDBus", "PySide6.QtConcurrent", "PySide6.QtTest",
    "PySide6.QtSql", "PySide6.QtXml", "PySide6.QtPrintSupport",
    "PySide6.QtSvg", "PySide6.QtSvgWidgets", "PySide6.QtDesigner",
    "PySide6.QtHelp", "PySide6.QtUiTools", "PySide6.QtWebChannel",
]

# Trozos de archivos de datos/binarios que se descartan después del análisis.
# Se comparan con la ruta de destino dentro del paquete (en minúsculas).
DESCARTAR = [
    "pyside6/translations",              # traducciones de Qt (.qm)
    "pyside6/qml",                       # carpeta QML
    "pyside6/plugins/platforminputcontexts",
    "pyside6/plugins/generic",
    "pyside6/plugins/networkinformation",
    "pyside6/plugins/tls",
    "pyside6/plugins/imageformats/qtiff",
    "pyside6/plugins/imageformats/qwebp",
    "pyside6/plugins/imageformats/qgif",
    "pyside6/plugins/imageformats/qico",
    "pyside6/plugins/imageformats/qpdf",
    "pyside6/plugins/imageformats/qicns",
    "pyside6/plugins/imageformats/qtga",
    "pyside6/plugins/imageformats/qwbmp",
    "pyside6/qt6network", "pyside6/qt6qml", "pyside6/qt6quick",
    "pyside6/qt6pdf", "pyside6/qt6opengl", "pyside6/qt6virtualkeyboard",
    "pyside6/plugins/imageformats/qsvg",
    "pyside6/plugins/iconengines/qsvgicon",
    "pyside6/opengl32sw",                # renderizador por software de OpenGL
    "pyside6/d3dcompiler",
    "numpy/tests", "numpy/_core/tests",
]
# Excepciones: aunque coincidan con DESCARTAR, estas SÍ se conservan.
CONSERVAR = [
    "pyside6/plugins/imageformats/qjpeg",
    "pyside6/plugins/imageformats/qpng",  # el icono de la ventana es un PNG
]


def _se_descarta(destino):
    ruta = str(destino).replace("\\", "/").lower()
    if any(c in ruta for c in CONSERVAR):
        return False
    return any(d in ruta for d in DESCARTAR)


a = Analysis(  # noqa: F821
    [str(RAIZ / "viviani_app.py")],
    pathex=[str(RAIZ), str(RAIZ / "src")],
    binaries=[],
    # (origen, destino dentro del paquete). app.py busca el icono con una
    # ruta relativa a su propio __file__: .../viviani/recursos/icono.png
    datas=[(str(RAIZ / "src" / "viviani" / "recursos"), "viviani/recursos")],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=EXCLUIR,
    noarchive=False,
)

a.binaries = [b for b in a.binaries if not _se_descarta(b[0])]
a.datas = [d for d in a.datas if not _se_descarta(d[0])]

pyz = PYZ(a.pure)  # noqa: F821

if MODO == "onefile":
    exe = EXE(  # noqa: F821
        pyz, a.scripts, a.binaries, a.datas, [],
        name=NOMBRE,
        icon=ICONO,
        console=False,       # ventana normal, sin consola negra
        upx=False,           # sin UPX (más rápido y menos falsos positivos)
        debug=False,
        strip=False,
    )
else:
    exe = EXE(  # noqa: F821
        pyz, a.scripts, [],
        exclude_binaries=True,
        name=NOMBRE,
        icon=ICONO,
        console=False,
        upx=False,
        debug=False,
        strip=False,
    )
    coll = COLLECT(  # noqa: F821
        exe, a.binaries, a.datas,
        name=NOMBRE,
        upx=False,
        strip=False,
    )
