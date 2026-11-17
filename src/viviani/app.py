"""Punto de entrada de la aplicación: crea las piezas y las conecta.

Cada pieza vive en su propio módulo y no conoce a las demás:

    calculo   -> hace la suma de Riemann (no sabe nada de ventanas)
    graficas  -> dibujan (no saben quién las llama)
    sonido    -> hace sonar los avisos
    ui        -> la ventana: recibe todo lo anterior ya construido

Aquí solo se "enchufan" unas con otras.
"""

import sys

import matplotlib

matplotlib.use("QtAgg")  # las gráficas se dibujan dentro de la ventana Qt

from PySide6.QtCore import QSettings, Qt  # noqa: E402
from PySide6.QtGui import QFont, QGuiApplication  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from viviani import NOMBRE_APP, tema  # noqa: E402
from viviani.calculo import calcular, datos_convergencia  # noqa: E402
from viviani.graficas import (  # noqa: E402
    GraficaConvergencia,
    GraficaCurva3D,
    GraficaRiemann,
)
from viviani.sonido import Sonidos  # noqa: E402
from viviani.ui import sistema  # noqa: E402
from viviani.ui.ventana import VentanaPrincipal  # noqa: E402


def crear_ventana(ajustes=None):
    """Construye la ventana principal con todas sus piezas ya conectadas."""
    if ajustes is None:
        ajustes = QSettings("ESPOL", "PerimetroViviani")

    # ¿Windows está en modo oscuro? ¿El usuario pidió texto más grande?
    estilo = QGuiApplication.styleHints()
    oscuro = estilo.colorScheme() == Qt.ColorScheme.Dark
    colores = tema.paleta(oscuro)
    escala = sistema.factor_de_texto()

    # La preferencia de sonido se recuerda entre una ejecución y otra.
    sonido_activado = ajustes.value("sonido/activado", True, type=bool)
    sonidos = Sonidos(activado=sonido_activado)

    return VentanaPrincipal(
        grafica_3d=GraficaCurva3D(colores, escala),
        grafica_riemann=GraficaRiemann(colores, escala),
        grafica_convergencia=GraficaConvergencia(colores, escala),
        sonidos=sonidos,
        calcular=calcular,
        datos_convergencia=datos_convergencia,
        ajustes=ajustes,
    )


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(NOMBRE_APP)
    app.setOrganizationName("ESPOL")

    # Fuente del sistema (Windows 11) con respaldos; el tamaño base es 10,5 pt.
    fuente = QFont()
    fuente.setFamilies(tema.FAMILIAS_INTERFAZ)
    fuente.setPointSizeF(10.5 * sistema.factor_de_texto())
    app.setFont(fuente)

    ventana = crear_ventana()

    # Maximizada en pantallas de hasta 1920x1080 (así se graba el video);
    # en pantallas más grandes, una ventana de 1600x900 centrada.
    pantalla = app.primaryScreen().availableGeometry()
    if pantalla.width() <= 1920:
        ventana.showMaximized()
    else:
        ventana.resize(1600, 900)
        ventana.move(pantalla.center() - ventana.rect().center())
        ventana.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
