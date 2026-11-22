"""Hoja de estilos (QSS) de la aplicación, armada con los colores de tema.py.

QSS es el "CSS" de Qt: dice de qué color y forma se dibuja cada control.
El fondo, el botón Calcular y las cajas de los datos se dibujan a mano
(componentes.py); aquí solo se estilizan textos, chips y botones simples.
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
    QLabel[rol="formula"] {{
        color: {c["texto_sec"]};
    }}

    QLineEdit#dato {{
        background: transparent;
        border: none;
        padding: 0px;
        color: {c["texto"]};
        selection-background-color: {c["acento_suave"]};
        selection-color: {c["texto"]};
    }}

    QPushButton#chip {{
        background: {rgba(c["superficie"], 0.7)};
        border: 1px solid {c["borde"]};
        border-radius: 13px;
        color: {c["texto_sec"]};
        padding: 4px 12px;
        min-height: 18px;
    }}
    QPushButton#chip:hover {{
        border-color: {c["acento"]};
        color: {c["texto"]};
    }}
    QPushButton#chip:focus {{
        border-color: {c["acento"]};
    }}
    QPushButton#chip:checked {{
        background: {rgba(c["acento"], 0.12)};
        border-color: {rgba(c["acento"], 0.55)};
        color: {c["acento"]};
    }}

    QPushButton#enlace {{
        background: transparent;
        border: 1px solid transparent;
        /* Qt no redondea si el radio pasa de la mitad del alto: por eso el
           alto mínimo (18 + 2·5 de relleno + 2 de borde = 30 px) */
        border-radius: 13px;
        min-height: 18px;
        color: {c["texto_sec"]};
        padding: 5px 14px;
    }}
    QPushButton#enlace:hover {{
        color: {c["texto"]};
        border-color: {c["borde"]};
        background: {rgba(c["superficie"], 0.6)};
    }}
    QPushButton#enlace:focus {{
        color: {c["acento"]};
        border-color: {rgba(c["acento"], 0.6)};
    }}

    QToolTip {{
        color: {c["texto"]};
        background: {c["superficie"]};
        border: 1px solid {c["borde"]};
        border-radius: 8px;
        padding: 6px 8px;
    }}
    """
