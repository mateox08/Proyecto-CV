"""Estilo común de las tres gráficas (DISENO 8.1 y 8.5).

Una misma función de dibujo sirve para la pantalla y para exportar el PNG:
solo cambia el `Estilo` (tamaños de letra y grosores) y la paleta de colores.
"""

from dataclasses import dataclass

from matplotlib.ticker import FuncFormatter

from viviani.formato import formatear_radio
from viviani.tema import FAMILIAS_GRAFICAS

METADATOS = {"Software": "Perímetro de la Ventana de Viviani"}


@dataclass(frozen=True)
class Estilo:
    """Tamaños de letra (pt) y factores para grosores y marcadores."""

    titulo: float
    rotulo: float
    marcas: float
    leyenda: float
    lineas: float  # los grosores de DISENO 8.x se multiplican por esto
    marcadores: float  # los tamaños de marcador se multiplican por esto


def estilo_pantalla(escala_texto=1.0):
    """Tamaños de DISENO 3.2, multiplicados por el factor de texto de Windows."""
    return Estilo(
        titulo=12 * escala_texto,
        rotulo=10.5 * escala_texto,
        marcas=9.5 * escala_texto,
        leyenda=9.5 * escala_texto,
        lineas=1.0,
        marcadores=1.0,
    )


def estilo_exportacion():
    """Tamaños de DISENO 8.5: líneas de 1,2 pt (2 · 0,6) y marcadores de 4 pt."""
    return Estilo(titulo=10, rotulo=9, marcas=8, leyenda=8, lineas=0.6, marcadores=0.8)


def rc_de(colores, estilo):
    """Parámetros de matplotlib (se usan con `matplotlib.rc_context`)."""
    return {
        "font.family": FAMILIAS_GRAFICAS,
        "mathtext.fontset": "dejavusans",
        "font.size": estilo.marcas,
        "figure.facecolor": colores["superficie"],
        "axes.facecolor": colores["superficie"],
        "axes.edgecolor": colores["borde"],
        "axes.labelcolor": colores["texto"],
        "axes.labelsize": estilo.rotulo,
        "text.color": colores["texto"],
        "xtick.color": colores["texto_sec"],
        "ytick.color": colores["texto_sec"],
        "xtick.labelsize": estilo.marcas,
        "ytick.labelsize": estilo.marcas,
        "grid.color": colores["separador"],
        "grid.linewidth": 0.8 * estilo.lineas,
        "legend.fontsize": estilo.leyenda,
        "legend.facecolor": colores["superficie"],
        "legend.edgecolor": colores["separador"],
        "legend.framealpha": 0.9,
        "savefig.facecolor": colores["superficie"],
    }


def formatear_marca(valor, _posicion=None):
    """Texto de una marca de eje con coma decimal (7.5 -> '7,5')."""
    if valor == 0:
        return "0"
    return formatear_radio(valor)


FORMATO_MARCAS = FuncFormatter(formatear_marca)


def poner_titulo(fig, texto, colores, estilo):
    """Fondo de la figura y título (dentro de la figura: es el mensaje principal)."""
    fig.set_facecolor(colores["superficie"])
    fig.suptitle(
        texto, fontsize=estilo.titulo, fontweight="semibold", color=colores["texto"]
    )


def preparar_ejes_2d(ax, colores, estilo):
    """Solo ejes izquierdo e inferior, rejilla mayor detrás de los datos."""
    ax.set_facecolor(colores["superficie"])
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color(colores["borde"])
        ax.spines[lado].set_linewidth(1 * estilo.lineas)
    ax.tick_params(
        colors=colores["texto_sec"],
        labelsize=estilo.marcas,
        labelfontfamily=FAMILIAS_GRAFICAS,
    )
    ax.grid(
        True, which="major", color=colores["separador"], linewidth=0.8 * estilo.lineas
    )
    ax.set_axisbelow(True)


def poner_leyenda(leyenda, colores):
    """Texto de la leyenda con el color de texto de la paleta."""
    for texto in leyenda.get_texts():
        texto.set_color(colores["texto"])
