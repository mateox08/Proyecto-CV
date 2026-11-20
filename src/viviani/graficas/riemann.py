"""Gráfica 2: la suma de Riemann con rectángulos (DISENO 8.3 y 6.2-6.5)."""

import math

import numpy as np
from matplotlib.collections import PolyCollection
from matplotlib.colors import to_rgba
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from viviani.formato import (
    formatear_decimal,
    formatear_entero,
    formatear_radio,
)
from viviani.graficas.animacion import salida_suave
from viviani.graficas.estilo import (
    FORMATO_MARCAS,
    poner_leyenda,
    preparar_ejes_2d,
)
from viviani.graficas.lienzo import LienzoBase

DURACION_TOTAL_MS = 1500  # todos los rectángulos
DURACION_BARRA_MS = 250  # lo que tarda en crecer cada rectángulo
DURACION_FUNDIDO_MS = 150  # con "reducir movimiento"
ALFA_RELLENO = 0.22


def funcion(t, radio):
    """Rapidez f(t) = R·√(1 + cos²t), con t en un arreglo de numpy."""
    return radio * np.sqrt(1 + np.cos(t) ** 2)


def vertices_de_barras(inicio, ancho, altura):
    """Cuatro esquinas de cada rectángulo (base en el eje t)."""
    x0, x1 = inicio, inicio + ancho
    cero = np.zeros_like(altura)
    esquinas = [(x0, cero), (x0, altura), (x1, altura), (x1, cero)]
    return np.stack([np.column_stack(par) for par in esquinas], axis=1)


def progreso_de_barras(ms, cantidad):
    """Avance (0 a 1, con salida suave) de cada barra en el instante `ms`.

    La barra k empieza en k·(1500 − 250)/(m − 1) ms y crece durante 250 ms.
    """
    if cantidad == 1:
        inicios = np.zeros(1)
    else:
        inicios = (
            np.arange(cantidad)
            * (DURACION_TOTAL_MS - DURACION_BARRA_MS)
            / (cantidad - 1)
        )
    avance = np.clip((ms - inicios) / DURACION_BARRA_MS, 0, 1)
    return 1 - (1 - avance) ** 3, avance >= 1


class GraficaRiemann(LienzoBase):
    def __init__(self, colores, escala_texto=1.0):
        super().__init__(colores, escala_texto)
        self.radio = 5.0
        self.resultado = None  # None: todavía no se ha calculado
        self.decorada = False  # título y leyenda dentro de la figura
        self._elementos = {}
        self.redibujar()

    # --- Interfaz pública ----------------------------------------------
    def mostrar_funcion(self, radio):
        """Estado previo al primer cálculo: solo la curva f(t)."""
        self.radio = radio
        self.resultado = None
        self.redibujar()

    def mostrar_resultado(self, resultado, animar=True, reducir_movimiento=False):
        self.radio = resultado.radio
        self.resultado = resultado
        self.redibujar(repintar=not animar)
        if not animar:
            self.animacion_terminada.emit()
            return
        elementos = self._elementos
        artistas = [elementos["rectangulos"]]
        if elementos["puntos"] is not None:
            artistas.append(elementos["puntos"])
        if reducir_movimiento:
            self._animar(DURACION_FUNDIDO_MS, artistas, self._fundir)
        else:
            self._animar(DURACION_TOTAL_MS, artistas, self._hacer_crecer)

    # --- Pasos de la animación ---------------------------------------------
    def _hacer_crecer(self, ms):
        """Cada rectángulo crece desde el eje; su punto aparece al terminar."""
        r = self.resultado
        avance, terminadas = progreso_de_barras(ms, len(r.barras_altura))
        vertices = vertices_de_barras(
            r.barras_inicio, r.barras_ancho, r.barras_altura * avance
        )
        self._elementos["rectangulos"].set_verts(vertices)
        puntos = self._elementos["puntos"]
        if puntos is not None:
            visibles = np.column_stack([r.puntos_t, r.barras_altura])[terminadas]
            puntos.set_offsets(visibles.reshape(-1, 2))

    def _fundir(self, ms):
        """Con 'reducir movimiento': todo aparece a la vez, solo cambia la opacidad."""
        opacidad = salida_suave(ms / DURACION_FUNDIDO_MS)
        colores = self.colores
        rectangulos = self._elementos["rectangulos"]
        rectangulos.set_facecolor(
            to_rgba(colores["serie_azul"], ALFA_RELLENO * opacidad)
        )
        rectangulos.set_edgecolor(to_rgba(colores["serie_azul"], opacidad))
        puntos = self._elementos["puntos"]
        if puntos is not None:
            puntos.set_alpha(opacidad)

    # --- Textos ---------------------------------------------------------
    def titulo(self):
        r = self.resultado
        if r is None:
            return f"f(t) = R√(1 + cos²t) con R = {formatear_radio(self.radio)} cm"
        return f"Suma de Riemann con n = {formatear_entero(r.n)}"

    def nombre_sugerido(self):
        radio = formatear_radio(self.radio).replace(".", "-")
        if self.resultado is None:
            return f"riemann_R{radio}cm_funcion.png"
        r = self.resultado
        return f"riemann_R{radio}cm_n{r.n}_{r.metodo}.png"

    def descripcion_accesible(self):
        r = self.resultado
        if r is None:
            return (
                "Gráfica de la función f(t) = R√(1 + cos²t) con R = "
                f"{formatear_radio(self.radio)} centímetros. Aún no se ha calculado."
            )
        return (
            f"Suma de Riemann con {r.n} rectángulos (punto medio). "
            f"Suma igual a {formatear_decimal(r.perimetro)} centímetros."
        )

    # --- Dibujo (pantalla y exportación) -----------------------------------
    def _dibujar(self, fig, colores, estilo):
        radio, r = self.radio, self.resultado
        eje = fig.add_subplot()
        preparar_ejes_2d(eje, colores, estilo)
        fig.set_facecolor(colores["fondo_grafica"])
        # En pantalla el título y la leyenda los pone la ventana (con letra
        # de la interfaz); en el PNG exportado van dentro de la imagen.
        if self.decorada:
            separacion = 2.2 * estilo.leyenda if self.resultado is not None else 6
            eje.set_title(
                self.titulo(),
                fontsize=estilo.titulo,
                fontweight="semibold",
                color=colores["texto"],
                pad=separacion,
            )

        t = np.linspace(0, 2 * math.pi, 400)
        eje.plot(
            t,
            funcion(t, radio),
            color=colores["texto"],
            linewidth=2 * estilo.lineas,
            zorder=3,
        )
        self._dar_formato_ejes(eje, radio, estilo)
        if r is None:
            return {"rectangulos": None, "puntos": None}

        rectangulos = PolyCollection(
            vertices_de_barras(r.barras_inicio, r.barras_ancho, r.barras_altura),
            facecolor=to_rgba(colores["serie_azul"], ALFA_RELLENO),
            edgecolor=colores["serie_azul"],
            zorder=2,
            linewidth=(1 if len(r.barras_altura) <= 60 else 0.5) * estilo.lineas,
        )
        eje.add_collection(rectangulos)
        puntos = None
        if r.puntos_t is not None:  # con n > 120 no se dibujan puntos
            puntos = eje.scatter(
                r.puntos_t,
                r.barras_altura,
                zorder=4,
                s=(5 * estilo.marcadores) ** 2,
                color=colores["serie_naranja"],
                linewidths=0,
            )
        if self.decorada:
            self._poner_anotacion(eje, colores, estilo)
            self._poner_leyenda(eje, colores, estilo, con_puntos=puntos is not None)
        return {"rectangulos": rectangulos, "puntos": puntos}

    def _dar_formato_ejes(self, eje, radio, estilo):
        eje.set_xlim(0, 2 * math.pi)
        eje.set_xticks(
            [0, math.pi / 2, math.pi, 3 * math.pi / 2, 2 * math.pi],
            ["0", "π/2", "π", "3π/2", "2π"],
        )
        eje.set_ylim(0, 1.5 * radio)  # fijo: la altura es comparable entre cálculos
        eje.yaxis.set_major_formatter(FORMATO_MARCAS)
        eje.set_xlabel("t", fontsize=estilo.rotulo)
        eje.set_ylabel("f(t)", fontsize=estilo.rotulo)

    def _poner_anotacion(self, eje, colores, estilo):
        texto = f"Σ f(tᵢ)·Δt = {formatear_decimal(self.resultado.perimetro)} cm"
        if self.resultado.agrupado:
            # Con n > 120 cada barra agrupa varios subintervalos (ver calculo.py)
            barras = len(self.resultado.barras_altura)
            texto += f"  ·  {barras} barras agrupadas"
        # Subtítulo, debajo del título: así no tapa los rectángulos
        eje.annotate(
            texto,
            xy=(0.5, 1),
            xycoords="axes fraction",
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=estilo.leyenda,
            color=colores["texto_sec"],
        )

    def _poner_leyenda(self, eje, colores, estilo, con_puntos):
        azul = colores["serie_azul"]
        elementos = [
            Line2D([], [], color=colores["texto"], linewidth=2 * estilo.lineas),
            Patch(facecolor=to_rgba(azul, ALFA_RELLENO), edgecolor=azul),
        ]
        rotulos = ["f(t)", "Rectángulos"]
        if con_puntos:
            elementos.append(
                Line2D(
                    [],
                    [],
                    linestyle="",
                    marker="o",
                    markersize=5 * estilo.marcadores,
                    color=colores["serie_naranja"],
                )
            )
            rotulos.append("Puntos de muestra")
        # Debajo del gráfico, centrada bajo el EJE. La separación está en
        # "alturas de letra": deja sitio al rótulo "t (rad)".
        leyenda = eje.legend(
            elementos,
            rotulos,
            loc="upper center",
            bbox_to_anchor=(0.5, 0),
            borderaxespad=3.4,
            ncols=len(elementos),
            frameon=False,
            columnspacing=1.2,
            handlelength=1.4,
        )
        poner_leyenda(leyenda, colores)
