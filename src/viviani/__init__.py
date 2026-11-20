"""Aplicación de escritorio: Perímetro de la Ventana de Viviani.

Organización del paquete (ver docs/EXPLICACION.md):

    calculo.py      Cálculo numérico por bloques (numpy), sin interfaz.
    validacion.py   Revisión de los textos que escribe el usuario, sin interfaz.
    formato.py      Números con coma decimal y notación científica.
    tema.py         Colores y medidas del modo claro y oscuro.
    sonido.py       Sonidos sintetizados por código.
    graficas/       Las tres gráficas (matplotlib).
    ui/             Ventana, controles e hilo de cálculo (PySide6).
    app.py          Punto de entrada: une todas las piezas.

El núcleo matemático original está en perimetro_viviani.py (raíz del
repositorio) y no depende de nada de este paquete.
"""

NOMBRE_APP = "Perímetro de la Ventana de Viviani"
