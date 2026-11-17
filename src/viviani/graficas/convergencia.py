"""Gráfica 3: convergencia del error relativo según n (DISENO 8.4)."""

import numpy as np
from matplotlib.lines import Line2D

from viviani.formato import formatear_entero, nombre_metodo
from viviani.graficas.animacion import salida_suave
from viviani.graficas.estilo import poner_leyenda, poner_titulo, preparar_ejes_2d
from viviani.graficas.lienzo import LienzoBase

DURACION_FUNDIDO_MS = 300
DURACION_FUNDIDO_REDUCIDO_MS = 150
ERROR_MINIMO = 1e-15  # por debajo se dibuja sobre la línea inferior
NIVEL_REDONDEO = 1e-14  # error típico por redondeo del computador

# Cómo se dibuja cada método: color, trazo, marcador, tamaño, relleno
SERIES = {
    "punto_medio": {
        "rotulo": "Punto medio",
        "color": "serie_azul",
        "trazo": "-",
        "marcador": "o",
        "tamano": 4,
        "hueco": False,
    },
    "izquierda": {
        "rotulo": "Izquierda",
        "color": "serie_naranja",
        "trazo": (0, (6, 3)),
        "marcador": "^",
        "tamano": 5,
        "hueco": False,
    },
    "derecha": {
        "rotulo": "Derecha",
        "color": "serie_morado",
        "trazo": (0, (1, 2)),
        "marcador": "v",
        "tamano": 6,
        "hueco": True,
    },
}


def texto_cientifico_hablado(valor):
    """Número para leer en voz alta: 7.982e-04 -> '7,982 por 10 a la menos 4'."""
    if valor == 0:
        return "0"
    mantisa, exponente = f"{valor:.3e}".split("e")
    exponente = int(exponente)
    signo = "menos " if exponente < 0 else ""
    return f"{mantisa.replace('.', ',')} por 10 a la {signo}{abs(exponente)}"


class GraficaConvergencia(LienzoBase):
    def __init__(self, colores, escala_texto=1.0):
        super().__init__(colores, escala_texto)
        self.datos = None  # lo que devuelve datos_convergencia()
        self.resultado = None  # cálculo actual (para el punto)
        self._elementos = {}
        self.redibujar()

    # --- Interfaz pública ----------------------------------------------
    def establecer_datos(self, datos):
        self.datos = datos
        self.redibujar()

    def marcar_actual(self, resultado, animar=True, reducir_movimiento=False):
        """Muestra el punto del cálculo actual con un fundido."""
        self.resultado = resultado
        self.redibujar()
        punto = self._elementos["punto"]
        if not animar:
            self.animacion_terminada.emit()
            return
        duracion = (
            DURACION_FUNDIDO_REDUCIDO_MS if reducir_movimiento else DURACION_FUNDIDO_MS
        )
        self._animar(
            duracion,
            [punto, self._elementos["rotulo"]],
            lambda ms: self._fundir(ms, duracion),
        )

    def _fundir(self, ms, duracion):
        opacidad = salida_suave(ms / duracion)
        self._elementos["punto"].set_alpha(opacidad)
        self._elementos["rotulo"].set_alpha(opacidad)

    # --- Textos ---------------------------------------------------------
    def titulo(self):
        return "Convergencia del error relativo según n"

    def nombre_sugerido(self):
        r = self.resultado
        if r is None:
            return "convergencia.png"
        return f"convergencia_n{r.n}_{r.metodo}.png"

    def descripcion_accesible(self):
        r = self.resultado
        if r is None:
            return (
                "Gráfica de convergencia del error relativo según n para los "
                "métodos punto medio, izquierda y derecha."
            )
        return (
            f"Convergencia: con n = {formatear_entero(r.n)} y "
            f"{nombre_metodo(r.metodo)}, "
            f"el error relativo es {texto_cientifico_hablado(r.error_relativo)} "
            "por ciento."
        )

    # --- Dibujo (pantalla y exportación) -----------------------------------
    def _dibujar(self, fig, colores, estilo):
        eje = fig.add_subplot()
        preparar_ejes_2d(eje, colores, estilo)
        poner_titulo(fig, self.titulo(), colores, estilo)
        self._dar_formato_ejes(eje, estilo)
        self._dibujar_limite(eje, colores, estilo)
        if self.datos is not None:
            # Se dibuja primero el punto medio para que quede debajo de los demás
            for metodo in ("punto_medio", "izquierda", "derecha"):
                self._dibujar_serie(eje, metodo, colores, estilo)
        self._poner_leyenda(eje, colores, estilo)
        return self._dibujar_actual(eje, colores, estilo)

    def _dar_formato_ejes(self, eje, estilo):
        eje.set_xscale("log")
        eje.set_yscale("log")
        eje.set_xlim(1, 1e7)
        eje.set_ylim(ERROR_MINIMO, 1e2)
        eje.set_yticks([10.0**e for e in range(-14, 3, 2)])
        eje.minorticks_off()
        eje.set_xlabel("Número de subintervalos n", fontsize=estilo.rotulo)
        eje.set_ylabel("Error relativo (%)", fontsize=estilo.rotulo)

    def _dibujar_limite(self, eje, colores, estilo):
        eje.axhline(
            NIVEL_REDONDEO,
            color=colores["texto_sec"],
            linestyle="--",
            linewidth=1 * estilo.lineas,
            zorder=2,
        )
        eje.text(
            0.99,
            NIVEL_REDONDEO * 1.6,
            "Límite de precisión del computador",
            transform=eje.get_yaxis_transform(),
            ha="right",
            va="bottom",
            fontsize=estilo.marcas,
            color=colores["texto_sec"],
        )

    def _dibujar_serie(self, eje, metodo, colores, estilo):
        formato = SERIES[metodo]
        color = colores[formato["color"]]
        valores_n, errores = self.datos[metodo]
        errores = np.asarray(errores, dtype=float)
        # Errores nulos o diminutos: se dibujan sobre la línea inferior
        en_el_piso = errores < ERROR_MINIMO
        alturas = np.where(en_el_piso, ERROR_MINIMO, errores)
        tamano = formato["tamano"] * estilo.marcadores
        grosor = 1.5 * estilo.lineas
        eje.plot(
            valores_n,
            alturas,
            color=color,
            linestyle=formato["trazo"],
            linewidth=grosor,
            zorder=3,
        )
        relleno = "none" if formato["hueco"] else color
        eje.plot(
            valores_n[~en_el_piso],
            alturas[~en_el_piso],
            linestyle="",
            zorder=4,
            marker=formato["marcador"],
            markersize=tamano,
            markerfacecolor=relleno,
            markeredgecolor=color,
            markeredgewidth=1.2 * estilo.lineas,
        )
        eje.plot(
            valores_n[en_el_piso],
            alturas[en_el_piso],
            linestyle="",
            zorder=4,
            marker=formato["marcador"],
            markersize=tamano,
            markerfacecolor="none",
            markeredgecolor=color,
            markeredgewidth=1.2 * estilo.lineas,
            clip_on=False,
        )

    def _dibujar_actual(self, eje, colores, estilo):
        """Rombo del cálculo actual con anillo y rótulo (solo de su método)."""
        r = self.resultado
        if r is None:
            return {"punto": None, "rotulo": None}
        altura = max(r.error_relativo, ERROR_MINIMO)
        (punto,) = eje.plot(
            [r.n],
            [altura],
            linestyle="",
            marker="D",
            zorder=6,
            clip_on=False,
            markersize=10 * estilo.marcadores,
            markerfacecolor=colores["texto"],
            markeredgecolor=colores["acento"],
            markeredgewidth=2 * estilo.lineas,
        )
        # Cerca del borde derecho el rótulo se escribe hacia la izquierda
        a_la_derecha = r.n > 1e5
        rotulo = eje.annotate(
            f"n = {formatear_entero(r.n)} (actual)",
            (r.n, altura),
            xytext=(-12 if a_la_derecha else 12, 12),
            textcoords="offset points",
            ha="right" if a_la_derecha else "left",
            va="bottom",
            fontsize=estilo.marcas,
            color=colores["texto"],
            zorder=7,
            bbox={
                "facecolor": colores["superficie"],
                "edgecolor": "none",
                "alpha": 0.85,
                "pad": 1.5,
            },
        )
        return {"punto": punto, "rotulo": rotulo}

    def _poner_leyenda(self, eje, colores, estilo):
        elementos, rotulos = [], []
        for metodo in ("punto_medio", "izquierda", "derecha"):
            formato = SERIES[metodo]
            color = colores[formato["color"]]
            elementos.append(
                Line2D(
                    [],
                    [],
                    color=color,
                    linestyle=formato["trazo"],
                    linewidth=1.5 * estilo.lineas,
                    marker=formato["marcador"],
                    markersize=formato["tamano"] * estilo.marcadores,
                    markerfacecolor="none" if formato["hueco"] else color,
                )
            )
            rotulos.append(formato["rotulo"])
        elementos.append(
            Line2D(
                [],
                [],
                linestyle="",
                marker="D",
                markersize=7 * estilo.marcadores,
                markerfacecolor=colores["texto"],
                markeredgecolor=colores["acento"],
                markeredgewidth=1.5 * estilo.lineas,
            )
        )
        rotulos.append("Cálculo actual")
        # La nota va como última fila de la leyenda, sin símbolo
        elementos.append(Line2D([], [], linestyle=""))
        rotulos.append("Izquierda y derecha coinciden.")
        # Arriba a la derecha: abajo a la izquierda taparía la caída del error
        leyenda = eje.legend(elementos, rotulos, loc="upper right")
        poner_leyenda(leyenda, colores)
        leyenda.get_texts()[-1].set_color(colores["texto_sec"])
