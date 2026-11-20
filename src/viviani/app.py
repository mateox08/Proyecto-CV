"""Punto de entrada de la aplicación: crea las piezas y las conecta.

Cada pieza vive en su propio módulo y no conoce a las demás:

    calculo   -> hace la suma de Riemann (no sabe nada de ventanas)
    graficas  -> dibujan (no saben quién las llama)
    sonido    -> hace sonar los avisos
    ui        -> la ventana: recibe todo lo anterior ya construido

Arranque por etapas: primero se muestra la pantalla de carga (solo necesita
Qt) y después se importan las librerías pesadas (numpy, matplotlib),
avisando el avance. Por eso esas importaciones están dentro de las
funciones y no al principio del archivo.
"""

import sys
from pathlib import Path

from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QApplication

from viviani import NOMBRE_APP, tema
from viviani.ui import sistema
from viviani.ui.carga import PantallaCarga

ICONO = Path(__file__).resolve().parent / "recursos" / "icono.png"


def crear_ventana(avisar=None):
    """Construye la ventana principal con todas sus piezas ya conectadas.

    avisar(fraccion, texto): opcional, para mostrar el avance de la carga.
    """
    avisar = avisar or (lambda _fraccion, _texto: None)

    avisar(0.15, "Preparando el cálculo…")
    from viviani.calculo import calcular
    from viviani.sonido import Sonidos

    avisar(0.40, "Preparando las gráficas…")
    import matplotlib

    matplotlib.use("QtAgg")  # la gráfica de Riemann va dentro de la ventana
    from viviani.graficas import GraficaCurva3D, GraficaRiemann

    avisar(0.70, "Armando la ventana…")
    from viviani.ui.ventana import VentanaPrincipal

    colores = tema.paleta()
    ventana = VentanaPrincipal(
        # Si Windows tiene las animaciones desactivadas, la curva no gira
        grafica_3d=GraficaCurva3D(colores, sistema.reducir_movimiento()),
        # letra algo menor: la gráfica de Riemann ahora es compacta
        grafica_riemann=GraficaRiemann(colores, 0.88 * sistema.factor_de_texto()),
        sonidos=Sonidos(activado=True),  # los sonidos siempre están activos
        calcular=calcular,
    )
    avisar(0.90, "Dibujando…")
    return ventana


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(NOMBRE_APP)
    app.setOrganizationName("ESPOL")
    app.setWindowIcon(QIcon(str(ICONO)))

    # Fuente del sistema (Windows 11), 10,5 pt por el factor de texto
    fuente = QFont()
    fuente.setFamilies(tema.FAMILIAS_INTERFAZ)
    fuente.setPointSizeF(10.5 * sistema.factor_de_texto())
    app.setFont(fuente)

    carga = PantallaCarga()
    carga.show()
    carga.avanzar(0.05, "Iniciando…")

    ventana = crear_ventana(carga.avanzar)

    # Maximizada en pantallas de hasta 1920x1080 (así se graba el video);
    # en pantallas más grandes, una ventana de 1600x900 centrada.
    pantalla = app.primaryScreen().availableGeometry()
    if pantalla.width() <= 1920:
        ventana.showMaximized()
    else:
        ventana.resize(1600, 900)
        ventana.move(pantalla.center() - ventana.rect().center())
        ventana.show()
    carga.avanzar(1.0, "Listo")
    carga.raise_()
    carga.terminar()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
