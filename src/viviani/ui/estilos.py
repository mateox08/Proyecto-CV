"""Hoja de estilos (QSS) de la aplicación, armada con los colores de tema.py.

QSS es el "CSS" de Qt: dice de qué color y forma se dibuja cada control.
Las tarjetas y los botones con brillo se dibujan a mano (componentes.py);
aquí solo se estilizan las cajas de texto, las etiquetas y la barra de
progreso.
"""

from viviani.tema import rgba


def hoja_de_estilos(c):
    return f"""
    QWidget {{
        color: {c["texto"]};
    }}
    QLabel {{
        background: transparent;
    }}
    QLabel[rol="etiqueta"] {{
        color: {c["etiqueta"]};
    }}
    QLabel[rol="error"] {{
        color: {c["error"]};
        font-size: 9.5pt;
    }}
    QLabel[rol="banda_error"] {{
        color: {c["error"]};
        background: {c["fondo_error"]};
        border-radius: 12px;
        padding: 10px 14px;
    }}

    QLineEdit {{
        background: #FFFFFF;
        border: 1px solid {c["borde"]};
        border-radius: 14px;
        padding: 6px 16px;
        selection-background-color: {c["acento_suave"]};
        selection-color: {c["texto"]};
    }}
    QLineEdit:hover {{
        border-color: {c["borde_brillo"]};
    }}
    QLineEdit:focus {{
        border: 2px solid {c["acento"]};
        padding: 5px 15px;
    }}
    QLineEdit[error="true"] {{
        border: 2px solid {c["error"]};
        padding: 5px 15px;
    }}

    QProgressBar {{
        background: {c["separador"]};
        border: none;
        border-radius: 2px;
        max-height: 4px;
        min-height: 4px;
    }}
    QProgressBar::chunk {{
        background: {c["acento"]};
        border-radius: 2px;
    }}

    QPushButton#enlace {{
        background: transparent;
        border: none;
        color: {c["acento"]};
        padding: 2px 4px;
    }}
    QPushButton#enlace:hover {{
        color: {c["acento_hover"]};
        text-decoration: underline;
    }}

    QToolTip {{
        color: {c["texto"]};
        background: #FFFFFF;
        border: 1px solid {rgba(c["borde_brillo"], 0.8)};
        border-radius: 8px;
        padding: 6px 8px;
    }}
    """
