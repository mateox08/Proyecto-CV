"""Hoja de estilos (QSS) de la ventana, generada desde la paleta.

QSS es el "CSS" de Qt. Aquí no hay ningún color escrito a mano: todos salen
de `viviani.tema.paleta`, de modo que cambiar de modo claro a oscuro es
volver a generar este texto con otra paleta.

Los controles se identifican por su `objectName` (con #) o por una propiedad
(entre corchetes), que se asignan en componentes.py y ventana.py.

Anillo de foco (DISENO 5.3): cada control enfocable va dentro de un marco
llamado "anillo" cuyo borde de 2 DIP es transparente y se pinta del color
`foco` solo cuando el control tiene el foco. El relleno (padding) de 2 DIP
del marco deja el hueco que separa el anillo del control.
"""

from viviani.tema import RADIO_CONTROL, RADIO_TARJETA

# Margen total que el marco "anillo" añade a cada lado del control:
# 2 DIP de hueco + 2 DIP de anillo.
MARGEN_ANILLO = 4


def generar(c, escala=1.0):
    """Devuelve el QSS completo. `c` es la paleta y `escala` el factor de texto."""

    def pt(tamano):
        # Tamaño de letra en puntos, ya multiplicado por el texto ampliado.
        return f"{tamano * escala:g}pt"

    radio = RADIO_CONTROL
    radio_anillo = radio + MARGEN_ANILLO
    radio_tarjeta_anillo = RADIO_TARJETA + MARGEN_ANILLO

    return f"""
/* ---------- Base ---------- */
QMainWindow, QWidget#raiz {{ background: {c["fondo"]}; }}
QWidget {{ color: {c["texto"]}; }}
QToolTip {{
    background: {c["tooltip_fondo"]}; color: {c["tooltip_texto"]};
    border: none; padding: 4px 8px; font-size: {pt(10)};
}}
QScrollArea {{ background: transparent; border: none; }}

/* ---------- Textos ---------- */
QLabel[rol="titulo_app"] {{ font-size: {pt(16)}; font-weight: 600; }}
QLabel[rol="subtitulo"] {{ font-size: {pt(10.5)}; color: {c["texto_sec"]}; }}
QLabel[rol="encabezado"] {{ font-size: {pt(12)}; font-weight: 600; }}
QLabel[rol="etiqueta_campo"] {{ font-size: {pt(11)}; font-weight: 600; }}
QLabel[rol="ayuda"] {{ font-size: {pt(10)}; color: {c["texto_sec"]}; }}
QLabel[rol="mensaje_error"] {{ font-size: {pt(10)}; color: {c["error"]}; }}
QLabel[rol="rotulo"] {{ font-size: {pt(10.5)}; color: {c["texto_sec"]}; }}
QLabel[rol="contexto"] {{ font-size: {pt(10.5)}; color: {c["texto_sec"]}; }}
QLabel[rol="sufijo"] {{ font-size: {pt(11)}; color: {c["texto_sec"]}; }}
QLabel[rol="progreso"] {{ font-size: {pt(10)}; color: {c["texto_sec"]}; }}
QLabel[rol="estado_exito"] {{ font-size: {pt(10)}; color: {c["exito"]}; }}
QLabel[rol="estado_error"] {{ font-size: {pt(10)}; color: {c["error"]}; }}
QLabel[rol="estado_normal"] {{ font-size: {pt(10)}; color: {c["texto_sec"]}; }}
QLabel[rol="sugerencia"] {{ font-size: {pt(10)}; color: {c["texto_sec"]}; }}

/* ---------- Tarjetas ---------- */
QFrame#tarjeta {{
    background: {c["superficie"]}; border: 1px solid {c["separador"]};
    border-radius: {RADIO_TARJETA}px;
}}

/* ---------- Anillo de foco ---------- */
QFrame#anillo {{
    border: 2px solid transparent; padding: 2px; background: transparent;
}}
QFrame#anillo[tipo="control"] {{ border-radius: {radio_anillo}px; }}
QFrame#anillo[tipo="tarjeta"] {{ border-radius: {radio_tarjeta_anillo}px; }}
QFrame#anillo[enfocado="true"] {{ border-color: {c["foco"]}; }}

/* ---------- Campos de texto ---------- */
QFrame#campo {{
    background: {c["superficie"]}; border: 1px solid {c["borde"]};
    border-radius: {radio}px; padding: 1px; min-height: 36px;
}}
QFrame#campo[hover="true"] {{ border-color: {c["texto_sec"]}; }}
QFrame#campo[error="true"] {{ border: 2px solid {c["error"]}; padding: 0px; }}
QLineEdit#entrada {{
    background: transparent; border: none; padding: 0px 8px;
    font-size: {pt(14)}; selection-background-color: {c["acento"]};
    selection-color: {c["texto_sobre_acento"]};
}}
QFrame#campo QLabel {{ background: transparent; padding-right: 10px; }}

/* ---------- Botones ---------- */
QPushButton {{ font-size: {pt(11)}; font-weight: 600; }}
QPushButton#primario {{
    background: {c["acento"]}; color: {c["texto_sobre_acento"]}; border: none;
    border-radius: {radio}px; min-height: 40px; min-width: 120px;
    padding: 0px 16px 0px 16px;
}}
QPushButton#primario:hover {{ background: {c["acento_hover"]}; }}
QPushButton#primario:pressed {{
    background: {c["acento_hover"]}; padding: 2px 16px 0px 16px;
}}
QPushButton#secundario, QPushButton#icono_sec {{
    background: transparent; color: {c["texto"]};
    border: 1px solid {c["borde"]}; border-radius: {radio}px;
    min-height: 34px; padding: 0px 12px;
}}
QPushButton#icono_sec {{ min-width: 30px; max-width: 30px; padding: 0px; }}
QPushButton#secundario:hover, QPushButton#icono_sec:hover {{
    background: {c["superficie_deshab"]};
}}
QPushButton#secundario:pressed, QPushButton#icono_sec:pressed {{
    background: {c["separador"]};
}}
QPushButton#secundario:disabled, QPushButton#icono_sec:disabled {{
    color: {c["texto_deshab"]}; border-color: {c["separador"]};
    background: transparent;
}}
QPushButton#segmento {{
    background: transparent; color: {c["texto"]}; font-weight: 400;
    border: 1px solid {c["borde"]}; border-radius: {radio}px;
    min-height: 34px; padding: 0px 8px;
}}
QPushButton#segmento:hover:!checked {{ background: {c["superficie_deshab"]}; }}
QPushButton#segmento:checked {{
    background: {c["acento"]}; color: {c["texto_sobre_acento"]};
    border-color: {c["acento"]}; font-weight: 600;
}}

/* ---------- Progreso ---------- */
QProgressBar {{
    background: {c["separador"]}; border: none; border-radius: 3px;
    min-height: 6px; max-height: 6px;
}}
QProgressBar::chunk {{ background: {c["acento"]}; border-radius: 3px; }}

/* ---------- Bandas de aviso / error / información ---------- */
QFrame#banda {{ border-radius: {radio}px; background: transparent; }}
QFrame#banda[rol="aviso"] {{ background: {c["fondo_aviso"]}; }}
QFrame#banda[rol="error"] {{ background: {c["fondo_error"]}; }}
QFrame#banda QLabel {{ background: transparent; font-size: {pt(10.5)}; }}
QFrame#banda[rol="error"] QLabel[rol="texto_banda"] {{ color: {c["error"]}; }}
QFrame#banda[rol="vacio"] QLabel[rol="texto_banda"] {{ color: {c["texto_sec"]}; }}

/* ---------- Pestañas (modo ancho reducido) ---------- */
QTabWidget::pane {{ border: none; }}
QTabBar::tab {{
    padding: 8px 16px; color: {c["texto_sec"]}; font-size: {pt(11)};
    border-bottom: 2px solid transparent; margin-right: 8px;
}}
QTabBar::tab:selected {{
    color: {c["texto"]}; font-weight: 600; border-bottom: 2px solid {c["acento"]};
}}
QTabBar::tab:selected:focus {{ border-bottom: 2px solid {c["foco"]}; }}
QTabBar::tab:hover:!selected {{ color: {c["texto"]}; }}

/* ---------- Barra de estado ---------- */
QStatusBar {{
    background: {c["fondo"]}; border-top: 1px solid {c["separador"]};
    min-height: 28px;
}}
QStatusBar::item {{ border: none; }}

/* ---------- Barras de desplazamiento ---------- */
QScrollBar:vertical {{ background: transparent; width: 12px; margin: 0px; }}
QScrollBar::handle:vertical {{
    background: {c["borde"]}; border-radius: 4px; min-height: 24px;
    margin: 2px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: transparent;
}}
"""
