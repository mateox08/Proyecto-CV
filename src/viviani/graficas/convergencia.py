"""Gráfica 3: convergencia del error relativo según n (DISENO 8.4)."""

import numpy as np
from matplotlib.lines import Line2D

from viviani.formato import formatear_entero, nombre_metodo
from viviani.graficas.animacion import salida_suave
from viviani.graficas.estilo import poner_leyenda, poner_titulo, preparar_ejes_2d
from viviani.graficas.lienzo import LienzoBase

DURACION_FUNDIDO_MS = 300
DURACION_FUNDIDO_REDUCIDO_MS = 150
ERROR_EJE_MINIMO = 1e-16  # deja sitio bajo la línea del límite para su rótulo
NIVEL_REDONDEO = 1e-14  # error típico por redondeo del computador
# Todo error hasta este valor (incluido 0) es ruido de redondeo: se dibuja
# sobre la línea del límite con un marcador hueco, y la meseta queda plana.
LIMITE_RUIDO = 2e-14

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
        self.redibujar(repintar=not animar)
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
        n, metodo = formatear_entero(r.n), nombre_metodo(r.metodo)
        inicio = f"Convergencia: con n = {n} y {metodo}, "
        if r.error_relativo <= LIMITE_RUIDO:
            return inicio + (
                "el error relativo es menor que el límite de precisión del computador."
            )
        return (
            inicio + f"el error relativo es "
            f"{texto_cientifico_hablado(r.error_relativo)} por ciento."
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
        self._poner_leyenda(fig, colores, estilo)
        return self._dibujar_actual(eje, colores, estilo)

    def _dar_formato_ejes(self, eje, estilo):
        eje.set_xscale("log")
        eje.set_yscale("log")
        eje.set_xlim(1, 1e7)
        eje.set_ylim(ERROR_EJE_MINIMO, 1e2)
        eje.set_yticks([10.0**e for e in range(-14, 3, 4)])
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
        # Justo debajo de la línea, donde no hay datos
        eje.text(
            0.55,
            NIVEL_REDONDEO / 6,
            "Límite de precisión del computador",
            transform=eje.get_yaxis_transform(),
            ha="center",
            va="top",
            fontsize=estilo.marcas * 0.9,
            color=colores["texto_sec"],
        )

    def _dibujar_serie(self, eje, metodo, colores, estilo):
        formato = SERIES[metodo]
        color = colores[formato["color"]]
        valores_n, errores = self.datos[metodo]
        errores = np.asarray(errores, dtype=float)
        # Ruido de redondeo (incluido 0): sobre la línea del límite, marcador hueco
        ruido = errores <= LIMITE_RUIDO
        alturas = np.where(ruido, NIVEL_REDONDEO, errores)
        # Con n = 1…64 habría una mancha de marcadores: se dibuja uno de cada cuatro
        marcar = (valores_n > 64) | (valores_n % 4 == 0) | (valores_n == 1)
        tamano = formato["tamano"] * estilo.marcadores
        eje.plot(
            valores_n,
            alturas,
            color=color,
            linestyle=formato["trazo"],
            linewidth=1.5 * estilo.lineas,
            zorder=3,
        )
        for ruidosos, hueco in ((~ruido, formato["hueco"]), (ruido, True)):
            visibles = ruidosos & marcar
            eje.plot(
                valores_n[visibles],
                alturas[visibles],
                linestyle="",
                zorder=4,
                marker=formato["marcador"],
                markersize=tamano,
                markerfacecolor="none" if hueco else color,
                markeredgecolor=color,
                markeredgewidth=1.2 * estilo.lineas,
            )

    def _dibujar_actual(self, eje, colores, estilo):
        """Rombo del cálculo actual con anillo y rótulo (solo de su método)."""
        r = self.resultado
        if r is None:
            return {"punto": None, "rotulo": None}
        altura = (
            NIVEL_REDONDEO if r.error_relativo <= LIMITE_RUIDO else r.error_relativo
        )
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
        a_la_derecha = r.n > 3000
        rotulo = eje.annotate(
            f"n = {formatear_entero(r.n)} (actual)",
            (r.n, altura),
            xytext=(-8 if a_la_derecha else 8, 10),
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

    def _poner_leyenda(self, fig, colores, estilo):
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
        # Debajo del eje, compacta y fuera del área de datos
        leyenda = fig.legend(
            elementos,
            rotulos,
            loc="outside lower center",
            ncols=len(elementos),
            frameon=False,
            columnspacing=1.0,
            handlelength=1.8,
        )
        poner_leyenda(leyenda, colores)
