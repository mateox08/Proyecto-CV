"""Gráfica 1: la Ventana de Viviani sobre la esfera, en 3D (DISENO 8.2)."""

import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from mpl_toolkits.mplot3d.art3d import Line3DCollection
from PySide6.QtCore import Qt

from viviani.formato import formatear_radio
from viviani.graficas.estilo import (
    FORMATO_MARCAS,
    poner_leyenda,
    poner_titulo,
)
from viviani.graficas.lienzo import LienzoBase
from viviani.tema import FAMILIAS_GRAFICAS

ELEVACION_INICIAL = 22  # grados
ACIMUT_INICIAL = 35  # grados
ZOOM_INICIAL = 1.0
PASO_FLECHAS = 10  # grados por pulsación de flecha
RADIO_PREDETERMINADO = 5.0


def curva_de_viviani(radio, puntos=600):
    """Puntos de r(t) = (R cos²t, R sen t cos t, R sen t), t en [0, 2π]."""
    t = np.linspace(0, 2 * np.pi, puntos)
    return radio * np.cos(t) ** 2, radio * np.sin(t) * np.cos(t), radio * np.sin(t)


def superficie_esfera(radio, filas=24, columnas=48):
    """Malla de la esfera: `filas` paralelos por `columnas` meridianos."""
    u = np.linspace(0, 2 * np.pi, columnas)  # longitud
    v = np.linspace(0, np.pi, filas)  # latitud (desde el polo)
    x = radio * np.outer(np.sin(v), np.cos(u))
    y = radio * np.outer(np.sin(v), np.sin(u))
    z = radio * np.outer(np.cos(v), np.ones_like(u))
    return x, y, z


def malla_de_lineas(radio, meridianos=12, paralelos=6, puntos=60):
    """Lista de polilíneas: meridianos y paralelos de la esfera."""
    lineas = []
    v = np.linspace(0, np.pi, puntos)
    for u in np.linspace(0, 2 * np.pi, meridianos, endpoint=False):
        lineas.append(
            np.column_stack(
                [
                    radio * np.sin(v) * np.cos(u),
                    radio * np.sin(v) * np.sin(u),
                    radio * np.cos(v),
                ]
            )
        )
    u = np.linspace(0, 2 * np.pi, puntos)
    for v in np.linspace(0, np.pi, paralelos + 2)[1:-1]:  # sin los polos
        lineas.append(
            np.column_stack(
                [
                    radio * np.sin(v) * np.cos(u),
                    radio * np.sin(v) * np.sin(u),
                    radio * np.cos(v) * np.ones_like(u),
                ]
            )
        )
    return lineas


class GraficaCurva3D(LienzoBase):
    TAMANO_EXPORTACION_CM = (12, 12)
    DISENO = None  # en 3D los márgenes se fijan a mano

    def __init__(self, colores, escala_texto=1.0):
        super().__init__(colores, escala_texto)
        self.radio = RADIO_PREDETERMINADO
        self._elevacion = ELEVACION_INICIAL
        self._acimut = ACIMUT_INICIAL
        self._zoom = ZOOM_INICIAL
        self._elementos = {}
        self.redibujar()

    # --- Interfaz pública ----------------------------------------------
    def mostrar(self, radio):
        """Redibuja la curva para el radio R (la vista se conserva)."""
        if radio == self.radio:
            return  # mismo radio: no hay nada que redibujar (cuesta ~90 ms)
        self.radio = radio
        self._guardar_vista()
        self.redibujar()

    def restablecer_vista(self):
        self._elevacion = ELEVACION_INICIAL
        self._acimut = ACIMUT_INICIAL
        self._zoom = ZOOM_INICIAL
        self._aplicar_vista()

    def rotar(self, d_acimut, d_elevacion):
        """Gira la vista; la elevación se limita a [-90, 90] grados."""
        self._guardar_vista()
        self._acimut += d_acimut
        self._elevacion = min(max(self._elevacion + d_elevacion, -90), 90)
        self._aplicar_vista()

    def titulo(self):
        radio = formatear_radio(self.radio)
        return f"Ventana de Viviani sobre la esfera de radio R = {radio} cm"

    def nombre_sugerido(self):
        return f"viviani_3d_R{formatear_radio(self.radio).replace(',', '-')}cm.png"

    def descripcion_accesible(self):
        r = formatear_radio(self.radio)
        return (
            f"Gráfica 3D de la Ventana de Viviani sobre una esfera de radio {r} "
            f"centímetros. Punto doble en ({r}, 0, 0)."
        )

    # --- Teclado y rueda --------------------------------------------------
    def keyPressEvent(self, evento):
        giros = {
            Qt.Key_Left: (-PASO_FLECHAS, 0),
            Qt.Key_Right: (PASO_FLECHAS, 0),
            Qt.Key_Up: (0, PASO_FLECHAS),
            Qt.Key_Down: (0, -PASO_FLECHAS),
        }
        if evento.key() in giros:
            self.rotar(*giros[evento.key()])
            evento.accept()
        else:
            super().keyPressEvent(evento)

    def wheelEvent(self, evento):
        """La rueda acerca o aleja la gráfica."""
        pasos = evento.angleDelta().y() / 120
        self._guardar_vista()
        self._zoom = min(max(self._zoom * 1.1**pasos, 0.5), 3.0)
        self._aplicar_vista()
        evento.accept()

    # --- Vista --------------------------------------------------------
    def _eje(self):
        return self._elementos["ejes"]

    def _guardar_vista(self):
        """Lee los ángulos actuales (el mouse de matplotlib los cambia)."""
        eje = self._eje()
        self._elevacion, self._acimut = eje.elev, eje.azim

    def _aplicar_vista(self):
        eje = self._eje()
        eje.view_init(elev=self._elevacion, azim=self._acimut)
        eje.set_box_aspect((1, 1, 1), zoom=self._zoom)
        self.draw_idle()

    # --- Dibujo (pantalla y exportación) -----------------------------------
    def _dibujar(self, fig, colores, estilo):
        radio = self.radio
        # computed_zorder=False: se respeta el zorder, así la curva y el
        # punto doble quedan siempre por encima de la esfera.
        eje = fig.add_subplot(projection="3d", computed_zorder=False)
        fig.subplots_adjust(left=0, right=1, bottom=0.14, top=0.95)
        poner_titulo(fig, self.titulo(), colores, estilo)

        self._dibujar_esfera(eje, radio, colores, estilo)
        x, y, z = curva_de_viviani(radio)
        eje.plot(
            x,
            y,
            z,
            color=colores["serie_azul"],
            linewidth=2.5 * estilo.lineas,
            zorder=5,
        )
        eje.plot(
            [radio],
            [0],
            [0],
            linestyle="",
            marker="o",
            zorder=6,
            markersize=9 * estilo.marcadores,
            markerfacecolor=colores["punto_doble"],
            markeredgecolor=colores["superficie"],
            markeredgewidth=1.5 * estilo.lineas,
        )
        eje.text(
            radio * 1.02,
            0,
            radio * 0.12,
            "Punto doble (R, 0, 0)",
            ha="left",
            va="bottom",
            color=colores["texto"],
            fontsize=estilo.marcas,
            zorder=7,
        )

        self._dar_formato_ejes(eje, radio, colores, estilo)
        self._poner_leyenda(fig, colores, estilo)
        eje.view_init(elev=self._elevacion, azim=self._acimut)
        eje.set_box_aspect((1, 1, 1), zoom=self._zoom)
        return {"ejes": eje}

    def _dibujar_esfera(self, eje, radio, colores, estilo):
        x, y, z = superficie_esfera(radio)
        eje.plot_surface(
            x,
            y,
            z,
            color=colores["esfera"],
            alpha=colores["alfa_esfera"],
            linewidth=0,
            shade=False,
            antialiased=False,
            zorder=0,
        )
        malla = Line3DCollection(
            malla_de_lineas(radio),
            colors=colores["esfera"],
            linewidths=0.6 * estilo.lineas,
            alpha=0.35,
            zorder=1,
        )
        eje.add_collection3d(malla)

    def _dar_formato_ejes(self, eje, radio, colores, estilo):
        eje.set_xlim(-radio, radio)
        eje.set_ylim(-radio, radio)
        eje.set_zlim(-radio, radio)
        eje.set_xlabel("X (cm)", fontsize=estilo.rotulo, labelpad=2)
        eje.set_ylabel("Y (cm)", fontsize=estilo.rotulo, labelpad=2)
        eje.set_zlabel("Z (cm)", fontsize=estilo.rotulo, labelpad=2)
        for nombre in ("x", "y", "z"):
            eje.tick_params(
                axis=nombre,
                colors=colores["texto_sec"],
                labelsize=estilo.marcas,
                pad=0,
                labelfontfamily=FAMILIAS_GRAFICAS,
            )
            getattr(eje, f"{nombre}axis").set_major_formatter(FORMATO_MARCAS)
            getattr(eje, f"{nombre}axis").set_pane_color(colores["superficie"])
        eje.set_facecolor(colores["superficie"])

    def _poner_leyenda(self, fig, colores, estilo):
        gris = colores["esfera"]
        elementos = [
            Line2D([], [], color=colores["serie_azul"], linewidth=2.5 * estilo.lineas),
            Patch(facecolor=gris, edgecolor=gris, alpha=0.5),
            Line2D(
                [],
                [],
                linestyle="",
                marker="o",
                markersize=7 * estilo.marcadores,
                markerfacecolor=colores["punto_doble"],
                markeredgecolor=colores["superficie"],
            ),
        ]
        rotulos = [
            "Curva de Viviani",
            "Esfera $x^2 + y^2 + z^2 = R^2$",
            "Punto doble (R, 0, 0)",
        ]
        # En la esquina inferior izquierda de la figura, fuera de los ejes 3D
        leyenda = fig.legend(elementos, rotulos, loc="lower left", frameon=False)
        poner_leyenda(leyenda, colores)
