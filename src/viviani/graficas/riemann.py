"""Gráfica 2: la suma de Riemann con rectángulos, dibujada con QPainter.

Muestra la función f(t) = R·√(1 + cos²t) en [0, 2π] y, después de calcular,
un rectángulo por subintervalo (como máximo 120: con más, cada barra es el
promedio de un grupo). El área total de los rectángulos es el perímetro.

Al calcular, los rectángulos crecen uno tras otro desde el eje t y su punto
de muestra (en ámbar) aparece cuando terminan.

Al pasar el mouse, la barra que está debajo se ilumina, aparece una ficha
con sus valores y se avisa a la curva 3D (señal `t_resaltado`) para que
señale el punto r(t) correspondiente.
"""

import math

import numpy as np
from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontMetricsF,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPolygonF,
)
from PySide6.QtWidgets import QSizePolicy, QWidget

from viviani.animacion import Animacion
from viviani.formato import formatear_decimal, formatear_entero, formatear_radio
from viviani.graficas.barrido import (
    DURACION_BARRA_MS,
    DURACION_BARRIDO_MS,
    inicios_escalonados,
)
from viviani.tema import FAMILIAS_INTERFAZ, FAMILIAS_MONO, con_alfa

MARGENES = (46, 16, 22, 58)  # izquierda, arriba, derecha, abajo (px)
TOPE = 1.5  # el eje vertical va de 0 a 1.5·R, fijo: se pueden comparar cálculos
MARCAS_T = [(0, "0"), (math.pi / 2, "π/2"), (math.pi, "π"),
            (3 * math.pi / 2, "3π/2"), (2 * math.pi, "2π")]  # fmt: skip


def funcion(t, radio):
    """Rapidez f(t) = R·√(1 + cos²t), con t en un arreglo de numpy."""
    return radio * np.sqrt(1 + np.cos(t) ** 2)


class GraficaRiemann(QWidget):
    t_resaltado = Signal(object)  # el t que señala el mouse, o None

    def __init__(self, colores, escala_texto=1.0):
        super().__init__()
        self.colores = colores
        self.escala_texto = escala_texto
        self.radio = 5.0
        self.resultado = None  # None: todavía no se ha calculado
        self._avance = None  # avance (0 a 1) de cada barra durante la animación
        self._mouse_t = None  # t bajo el mouse (None si está fuera)
        self._animacion = Animacion(self, self._al_cuadro, self._al_terminar)
        self.setMouseTracking(True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setAccessibleName(self.descripcion_accesible())

    # --- Interfaz pública ----------------------------------------------
    def mostrar_funcion(self, radio):
        """Estado previo al primer cálculo: solo la curva f(t)."""
        self.radio = radio
        self.resultado = None
        self._animacion.cancelar()
        self._actualizar()

    def mostrar_resultado(self, resultado, animar=True):
        self.radio = resultado.radio
        self.resultado = resultado
        self._actualizar()
        if animar:
            self._animacion.iniciar(DURACION_BARRIDO_MS)
        else:
            self._animacion.cancelar()
            self._al_terminar()

    def esta_animando(self):
        return self._animacion.activa()

    def saltar_animacion(self):
        self._animacion.terminar()

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

    # --- Animación -------------------------------------------------------
    def _al_cuadro(self, ms):
        """Cada rectángulo crece desde el eje; su punto aparece al terminar."""
        cantidad = len(self.resultado.barras_altura)
        avance = (ms - inicios_escalonados(cantidad)) / DURACION_BARRA_MS
        self._avance = 1 - (1 - np.clip(avance, 0, 1)) ** 3  # salida suave
        self.update()

    def _al_terminar(self):
        self._avance = None
        self.update()

    def _actualizar(self):
        self.setAccessibleName(self.descripcion_accesible())
        self._avisar_mouse()
        self.update()

    # --- Mouse -------------------------------------------------------------
    def mouseMoveEvent(self, evento):
        area = self._area()
        x = evento.position().x()
        if area.left() <= x <= area.right():
            self._mouse_t = (x - area.left()) / area.width() * 2 * math.pi
        else:
            self._mouse_t = None
        self._avisar_mouse()
        self.update()

    def leaveEvent(self, evento):
        self._mouse_t = None
        self._avisar_mouse()
        self.update()
        super().leaveEvent(evento)

    def _barra_bajo_mouse(self):
        """Índice de la barra que está bajo el mouse, o None."""
        r = self.resultado
        if r is None or self._mouse_t is None:
            return None
        fin = r.barras_inicio + r.barras_ancho
        k = int(np.searchsorted(fin, self._mouse_t))
        return min(k, len(fin) - 1)

    def _t_senalado(self):
        """El t que se señala: el centro de la barra, o el t del mouse."""
        k = self._barra_bajo_mouse()
        if k is None:
            return self._mouse_t
        r = self.resultado
        return float(r.barras_inicio[k] + r.barras_ancho[k] / 2)

    def _avisar_mouse(self):
        self.t_resaltado.emit(self._t_senalado())

    # --- Dibujo ------------------------------------------------------------
    def _area(self):
        izquierda, arriba, derecha, abajo = MARGENES
        return QRectF(self.rect()).adjusted(izquierda, arriba, -derecha, -abajo)

    def _fuente(self, familias, puntos, peso=QFont.Weight.Normal):
        fuente = QFont()
        fuente.setFamilies(familias)
        fuente.setPointSizeF(puntos * self.escala_texto)
        fuente.setWeight(peso)
        return fuente

    def paintEvent(self, _evento):
        pintor = QPainter(self)
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing)
        area = self._area()
        tope = TOPE * self.radio

        def x_de(t):
            return area.left() + np.asarray(t) / (2 * math.pi) * area.width()

        def y_de(valor):
            return area.bottom() - np.asarray(valor) / tope * area.height()

        self._pintar_ejes(pintor, area, x_de, y_de)
        if self.resultado is not None:
            self._pintar_barras(pintor, area, x_de, y_de)

        # La función f(t), encima de los rectángulos
        t = np.linspace(0, 2 * math.pi, 300)
        curva = QPolygonF(
            [
                QPointF(x, y)
                for x, y in zip(x_de(t), y_de(funcion(t, self.radio)), strict=True)
            ]  # fmt: skip
        )
        pluma = QPen(con_alfa(self.colores["texto"], 0.95), 2)
        pluma.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        pintor.setPen(pluma)
        pintor.setBrush(Qt.BrushStyle.NoBrush)
        pintor.drawPolyline(curva)

        if self.resultado is not None:
            self._pintar_puntos(pintor, x_de, y_de)
        if self._mouse_t is not None:
            self._pintar_lectura(pintor, area, x_de, y_de)
        pintor.end()

    def _pintar_ejes(self, pintor, area, x_de, y_de):
        c = self.colores
        pintor.setFont(self._fuente(FAMILIAS_INTERFAZ, 8.5))
        medidas = QFontMetricsF(pintor.font())
        # Rejilla horizontal y números del eje vertical (0, R/2, R, 3R/2)
        for fraccion in (0.0, 0.5, 1.0, 1.5):
            y = float(y_de(fraccion * self.radio))
            pintor.setPen(QPen(QColor(c["separador"] if fraccion else c["borde"]), 1))
            pintor.drawLine(QPointF(area.left(), y), QPointF(area.right(), y))
            texto = formatear_radio(fraccion * self.radio) if fraccion else "0"
            caja = QRectF(0, y - 10, area.left() - 8, 20)
            pintor.setPen(QColor(c["texto_sec"]))
            alinear = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            pintor.drawText(caja, alinear, texto)
        # Marcas del eje t
        for t, texto in MARCAS_T:
            x = float(x_de(t))
            pintor.setPen(QPen(QColor(c["borde"]), 1))
            pintor.drawLine(QPointF(x, area.bottom()), QPointF(x, area.bottom() + 4))
            pintor.setPen(QColor(c["texto_sec"]))
            caja = QRectF(x - 30, area.bottom() + 6, 60, medidas.height())
            pintor.drawText(caja, Qt.AlignmentFlag.AlignHCenter, texto)
        # Nombres de los ejes
        pintor.setPen(QColor(c["etiqueta"]))
        pintor.setFont(self._fuente(FAMILIAS_INTERFAZ, 8.5, QFont.Weight.DemiBold))
        # La "t" a la derecha del final del eje, para no taparse con "2π"
        pintor.drawText(QPointF(area.right() + 8, area.bottom() + 4), "t")
        pintor.drawText(QPointF(4, area.top() - 3), "f(t)")
        self._pintar_leyenda(pintor, area)

    def _pintar_leyenda(self, pintor, area):
        """Debajo del eje t: qué es cada cosa, con su color."""
        c = self.colores
        pintor.setFont(self._fuente(FAMILIAS_INTERFAZ, 8.5))
        medidas = QFontMetricsF(pintor.font())
        elementos = [("linea", c["texto"], "f(t)"),
                     ("barra", c["acento"], "rectángulos"),
                     ("punto", c["muestra"], "puntos de muestra")]  # fmt: skip
        ancho = sum(18 + medidas.horizontalAdvance(texto) + 16
                    for _, _, texto in elementos) - 16  # fmt: skip
        x = area.center().x() - ancho / 2
        y = self.height() - 12
        for forma, color, texto in elementos:
            muestra = QColor(color)
            if forma == "linea":
                pintor.setPen(QPen(muestra, 2))
                pintor.drawLine(QPointF(x, y - 4), QPointF(x + 12, y - 4))
            elif forma == "barra":
                pintor.setPen(QPen(muestra, 1))
                pintor.setBrush(con_alfa(color, 0.35))
                pintor.drawRect(QRectF(x + 2, y - 10, 8, 10))
            else:
                pintor.setPen(Qt.PenStyle.NoPen)
                pintor.setBrush(muestra)
                pintor.drawEllipse(QPointF(x + 6, y - 4), 3, 3)
            pintor.setPen(QColor(c["etiqueta"]))
            pintor.drawText(QPointF(x + 18, y), texto)
            x += 18 + medidas.horizontalAdvance(texto) + 16

    def _pintar_barras(self, pintor, area, x_de, y_de):
        c = self.colores
        r = self.resultado
        alturas = (
            r.barras_altura if self._avance is None else r.barras_altura * self._avance
        )
        x0 = x_de(r.barras_inicio)
        x1 = x_de(r.barras_inicio + r.barras_ancho)
        y = y_de(alturas)
        base = area.bottom()

        cuerpo = QPainterPath()
        for k in range(len(alturas)):
            cuerpo.addRect(QRectF(QPointF(x0[k], y[k]), QPointF(x1[k], base)))
        # Un solo degradado para todas: más intenso arriba
        relleno = QLinearGradient(0, area.top(), 0, base)
        relleno.setColorAt(0.0, con_alfa(c["acento"], 0.40))
        relleno.setColorAt(1.0, con_alfa(c["acento_2"], 0.06))
        pintor.setPen(Qt.PenStyle.NoPen)
        pintor.setBrush(relleno)
        pintor.drawPath(cuerpo)

        # Bordes: completos si las barras son anchas, solo el techo si no
        pocas = len(alturas) <= 60
        pintor.setBrush(Qt.BrushStyle.NoBrush)
        pintor.setPen(QPen(con_alfa(c["acento"], 0.85), 1))
        if pocas:
            pintor.drawPath(cuerpo)
        else:
            for k in range(len(alturas)):
                pintor.drawLine(QPointF(x0[k], y[k]), QPointF(x1[k], y[k]))

        # La barra bajo el mouse, iluminada
        k = self._barra_bajo_mouse()
        if k is not None:
            pintor.setPen(QPen(QColor(c["muestra"]), 1.5))
            pintor.setBrush(con_alfa(c["muestra"], 0.22))
            pintor.drawRect(QRectF(QPointF(x0[k], y[k]), QPointF(x1[k], base)))

    def _pintar_puntos(self, pintor, x_de, y_de):
        """Los puntos (tᵢ, f(tᵢ)); solo cuando cada barra es un subintervalo."""
        r = self.resultado
        if r.puntos_t is None:
            return
        visibles = (
            np.ones(len(r.puntos_t), bool)
            if self._avance is None
            else self._avance >= 1
        )
        radio = 3.0 if len(r.puntos_t) <= 40 else 2.2
        pintor.setPen(Qt.PenStyle.NoPen)
        pintor.setBrush(QColor(self.colores["muestra"]))
        for x, y in zip(x_de(r.puntos_t[visibles]), y_de(r.barras_altura[visibles]),
                        strict=True):  # fmt: skip
            pintor.drawEllipse(QPointF(x, y), radio, radio)

    def _pintar_lectura(self, pintor, area, x_de, y_de):
        """Línea vertical en el t señalado y una ficha con sus valores."""
        c = self.colores
        t = self._t_senalado()
        x = float(x_de(t))
        pluma = QPen(con_alfa(c["muestra"], 0.7), 1, Qt.PenStyle.DashLine)
        pintor.setPen(pluma)
        pintor.drawLine(QPointF(x, area.top()), QPointF(x, area.bottom()))

        lineas = self._textos_lectura(t)
        pintor.setFont(self._fuente(FAMILIAS_MONO, 8))
        medidas = QFontMetricsF(pintor.font())
        ancho = max(medidas.horizontalAdvance(linea) for linea in lineas) + 20
        alto = len(lineas) * medidas.height() + 12
        izquierda = x + 12 if x + 12 + ancho <= area.right() else x - 12 - ancho
        ficha = QRectF(izquierda, area.top() + 4, ancho, alto)
        pintor.setPen(QPen(QColor(c["borde"]), 1))
        pintor.setBrush(con_alfa(c["superficie"], 0.94))
        pintor.drawRoundedRect(ficha, 8, 8)
        pintor.setPen(QColor(c["texto"]))
        for i, linea in enumerate(lineas):
            base = ficha.top() + 6 + (i + 1) * medidas.height() - medidas.descent()
            pintor.drawText(QPointF(ficha.left() + 10, base), linea)

    def _textos_lectura(self, t):
        r = self.resultado
        k = self._barra_bajo_mouse()
        if k is None:
            valor = formatear_decimal(funcion(t, self.radio), 4)
            return [f"t    = {t:.4f}", f"f(t) = {valor} cm"]
        altura = float(r.barras_altura[k])
        aporte = altura * float(r.barras_ancho[k])
        cantidad = len(r.barras_altura)
        if r.agrupado:
            return [f"barra {k + 1} de {cantidad} (promedio)",
                    f"t     = {t:.4f}",
                    f"f̄     = {formatear_decimal(altura, 4)} cm",
                    f"área  = {formatear_decimal(aporte, 5)} cm"]  # fmt: skip
        return [f"i     = {formatear_entero(k + 1)} de {formatear_entero(r.n)}",
                f"tᵢ    = {t:.4f}",
                f"f(tᵢ) = {formatear_decimal(altura, 4)} cm",
                f"f·Δt  = {formatear_decimal(aporte, 5)} cm"]  # fmt: skip
