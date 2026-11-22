"""Aplicación de escritorio: Perímetro de la Ventana de Viviani.

Organización del paquete (ver docs/EXPLICACION.md):

    calculo.py      Cálculo numérico por bloques (numpy), sin interfaz.
    validacion.py   Revisión de los textos que escribe el usuario, sin interfaz.
    formato.py      Números con punto decimal, notación científica y cifras.
    tema.py         Colores y fuentes del tema oscuro.
    sonido.py       Sonidos sintetizados por código.
    animacion.py    Animaciones por tiempo real (solo Qt).
    graficas/       La curva 3D y la suma de Riemann (QPainter).
    ui/             Ventana, controles e hilo de cálculo (PySide6).
    app.py          Punto de entrada: une todas las piezas.

El núcleo matemático original está en perimetro_viviani.py (raíz del
repositorio) y no depende de nada de este paquete.
"""

NOMBRE_APP = "Perímetro de la Ventana de Viviani"
