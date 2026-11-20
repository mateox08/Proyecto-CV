"""Hoja de estilos (QSS) de la aplicación, armada con los colores de tema.py.

QSS es el "CSS" de Qt: dice de qué color y forma se dibuja cada control.
El fondo, el botón orbe y las líneas de los campos se dibujan a mano
(componentes.py); aquí solo se estilizan textos, cajas y botones simples.
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
        background: {rgba(c["error"], 0.08)};
        border: 1px solid {rgba(c["error"], 0.35)};
        border-radius: 12px;
        padding: 10px 14px;
    }}
    QLabel#chip {{
        color: {c["texto_sec"]};
        border: 1px solid {c["borde"]};
        border-radius: 13px;
        padding: 4px 12px;
        background: {rgba(c["superficie"], 0.6)};
    }}

    QLineEdit#linea {{
        background: transparent;
        border: none;
        padding: 0px;
        color: {c["texto"]};
        selection-background-color: {c["acento_suave"]};
        selection-color: {c["texto"]};
    }}

    QPushButton#fantasma {{
        background: {rgba(c["superficie"], 0.5)};
        border: 1px solid {c["borde"]};
        border-radius: 16px;
        color: {c["texto_sec"]};
        padding: 6px 16px;
    }}
    QPushButton#fantasma:hover {{
        border-color: {c["acento"]};
        color: {c["acento"]};
        background: {rgba(c["acento"], 0.08)};
    }}
    QPushButton#fantasma:focus {{
        border-color: {c["acento"]};
    }}

    QPushButton#enlace {{
        background: transparent;
        border: none;
        color: {c["texto_sec"]};
        padding: 4px 6px;
    }}
    QPushButton#enlace:hover {{
        color: {c["acento"]};
    }}
    QPushButton#enlace:focus {{
        color: {c["acento"]};
        text-decoration: underline;
    }}

    QToolTip {{
        color: {c["texto"]};
        background: {c["superficie"]};
        border: 1px solid {c["borde"]};
        border-radius: 8px;
        padding: 6px 8px;
    }}
    """
