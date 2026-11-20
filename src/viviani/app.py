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

matplotlib.use("QtAgg")  # la gráfica de Riemann se dibuja dentro de la ventana

from PySide6.QtGui import QFont  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from viviani import NOMBRE_APP, tema  # noqa: E402
from viviani.calculo import calcular  # noqa: E402
from viviani.graficas import GraficaCurva3D, GraficaRiemann  # noqa: E402
from viviani.sonido import Sonidos  # noqa: E402
from viviani.ui import sistema  # noqa: E402
from viviani.ui.ventana import VentanaPrincipal  # noqa: E402


def crear_ventana():
    """Construye la ventana principal con todas sus piezas ya conectadas."""
    colores = tema.paleta()
    return VentanaPrincipal(
        # Si Windows tiene las animaciones desactivadas, la curva no gira
        grafica_3d=GraficaCurva3D(colores, sistema.reducir_movimiento()),
        grafica_riemann=GraficaRiemann(colores, sistema.factor_de_texto()),
        sonidos=Sonidos(activado=True),  # los sonidos siempre están activos
        calcular=calcular,
    )


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(NOMBRE_APP)
    app.setOrganizationName("ESPOL")

    # Fuente del sistema (Windows 11), 10,5 pt por el factor de texto
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
