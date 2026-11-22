"""Fórmulas matemáticas bien dibujadas: integrales, sumas, fracciones y raíces.

Un QLabel con HTML no sabe poner los límites de una suma arriba y abajo, ni
dibujar una fracción con su raya, y recorta los exponentes. Aquí cada pieza de
una fórmula es una "caja" que sabe dos cosas:

    medir()    cuánto mide: ancho, cuánto sube sobre la línea base y cuánto
               baja por debajo de ella
    dibujar()  pintarse en (x, línea base)

Con esas medidas, las cajas se acomodan unas junto a otras (Fila), unas sobre
otras (Fraccion, los límites de Operador) o dentro de otras (Raiz), y cada
una ocupa justo el espacio que necesita: nada se recorta ni se encima.

Cada caja también se puede leer como texto plano (`texto()`): eso es lo que
recibe el lector de pantalla.

Las medidas son proporcionales al tamaño de la letra (tam), no las métricas
de la fuente: Cambria Math declara alturas enormes (para sus símbolos
grandes) y con ellas las líneas quedarían muy separadas.
"""

from PySide6.QtCore import QPointF, QSize, Qt
from PySide6.QtGui import QColor, QFont, QFontMetricsF, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

from viviani import tema

SUBE = 0.74  # lo que sube una letra sobre la línea base (en tamaños de letra)
BAJA = 0.24  # lo que baja (la "p", la "g", los paréntesis)
REDUCCION = 0.68  # tamaño de exponentes, subíndices y límites
EJE = 0.30  # altura de la raya de las fracciones sobre la línea base


def _fuente(tam, italica=False):
    fuente = QFont()
    fuente.setFamilies(tema.FAMILIAS_MATEMATICA)
    fuente.setPixelSize(max(6, round(tam)))
    fuente.setItalic(italica)
    return fuente


class Caja:
    """Pieza de una fórmula. `escala` multiplica el tamaño de letra recibido."""

    escala = 1.0

    def medir(self, tam):
        """Devuelve (ancho, sube, baja) en píxeles para un tamaño de letra."""
        raise NotImplementedError

    def dibujar(self, pintor, x, base, tam, colores):
        raise NotImplementedError

    def texto(self):
        """La fórmula escrita en una sola línea, por ejemplo '(2π)/(n)'."""
        raise NotImplementedError


class Texto(Caja):
    """Texto simple. rol: 'texto', 'valor' (resaltado) o 'suave'.

    Las letras en cursiva (variables como r, f, t) se inclinan y sobresalen
    de su caja: la "f" hacia la izquierda por abajo y todas hacia la derecha
    por arriba. Sin un pequeño margen a cada lado se montan sobre los
    paréntesis vecinos, como en "f(t)".
    """

    MARGEN_CURSIVA = (0.06, 0.12)  # antes y después, en tamaños de letra

    def __init__(self, contenido, rol="texto", italica=False):
        self.contenido, self.rol, self.italica = contenido, rol, italica

    def margenes(self, tam):
        if not self.italica:
            return 0.0, 0.0
        antes, despues = self.MARGEN_CURSIVA
        return antes * tam, despues * tam

    def medir(self, tam):
        medidas = QFontMetricsF(_fuente(tam, self.italica))
        antes, despues = self.margenes(tam)
        ancho = antes + medidas.horizontalAdvance(self.contenido) + despues
        return ancho, SUBE * tam, BAJA * tam

    def dibujar(self, pintor, x, base, tam, colores):
        color = {"texto": "texto", "valor": "acento", "suave": "texto_sec"}[self.rol]
        pintor.setFont(_fuente(tam, self.italica))
        pintor.setPen(QColor(colores[color]))
        pintor.drawText(QPointF(x + self.margenes(tam)[0], base), self.contenido)

    def texto(self):
        return self.contenido


class Espacio(Caja):
    def __init__(self, em):
        self.em = em

    def medir(self, tam):
        return self.em * tam, 0.0, 0.0

    def dibujar(self, pintor, x, base, tam, colores):
        pass

    def texto(self):
        return " "


class Fila(Caja):
    """Cajas una junto a otra, sobre la misma línea base."""

    def __init__(self, *cajas):
        self.cajas = cajas

    def medir(self, tam):
        medidas = [caja.medir(tam) for caja in self.cajas]
        return (
            sum(m[0] for m in medidas),
            max((m[1] for m in medidas), default=0.0),
            max((m[2] for m in medidas), default=0.0),
        )

    def dibujar(self, pintor, x, base, tam, colores):
        for caja in self.cajas:
            caja.dibujar(pintor, x, base, tam, colores)
            x += caja.medir(tam)[0]

    def texto(self):
        return "".join(caja.texto() for caja in self.cajas)


class Indices(Caja):
    """Una base con exponente (arriba) y/o subíndice (abajo), más pequeños."""

    def __init__(self, base, arriba=None, abajo=None):
        self.base, self.arriba, self.abajo = base, arriba, abajo

    def _posiciones(self, tam):
        """Dónde empiezan (x relativo) el exponente y el subíndice.

        Si la base es una letra en cursiva, el subíndice se acerca: la letra
        se inclina y por abajo le sobra espacio. Arriba se acerca menos.
        """
        ancho = self.base.medir(tam)[0]
        retroceso = 0.0
        if isinstance(self.base, Texto):
            retroceso = self.base.margenes(tam)[1]
        return ancho - 0.3 * retroceso + 0.03 * tam, ancho - retroceso + 0.01 * tam

    def medir(self, tam):
        chico = REDUCCION * tam
        ancho, sube, baja = self.base.medir(tam)
        x_arriba, x_abajo = self._posiciones(tam)
        if self.arriba is not None:
            a = self.arriba.medir(chico)
            ancho = max(ancho, x_arriba + a[0])
            sube = max(sube, 0.42 * tam + a[1])
        if self.abajo is not None:
            b = self.abajo.medir(chico)
            ancho = max(ancho, x_abajo + b[0])
            baja = max(baja, 0.22 * tam + b[2])
        return ancho + 0.04 * tam, sube, baja

    def dibujar(self, pintor, x, base, tam, colores):
        self.base.dibujar(pintor, x, base, tam, colores)
        chico = REDUCCION * tam
        x_arriba, x_abajo = self._posiciones(tam)
        if self.arriba is not None:
            self.arriba.dibujar(pintor, x + x_arriba, base - 0.42 * tam, chico, colores)
        if self.abajo is not None:
            self.abajo.dibujar(pintor, x + x_abajo, base + 0.22 * tam, chico, colores)

    def texto(self):
        texto = self.base.texto()
        if self.abajo is not None:
            texto += "_" + self.abajo.texto()
        if self.arriba is not None:
            texto += "^" + self.arriba.texto()
        return texto


class Fraccion(Caja):
    """Numerador sobre denominador, con una raya entre ambos."""

    def __init__(self, arriba, abajo, chica=False):
        self.arriba, self.abajo = arriba, abajo
        self.factor = 0.8 if chica else 0.92

    def medir(self, tam):
        t = self.factor * tam
        a, b = self.arriba.medir(t), self.abajo.medir(t)
        ancho = max(a[0], b[0]) + 0.3 * tam
        sube = EJE * tam + 0.12 * tam + a[2] + a[1]
        baja = -EJE * tam + 0.12 * tam + b[1] + b[2]
        return ancho, sube, max(baja, BAJA * tam)

    def dibujar(self, pintor, x, base, tam, colores):
        t = self.factor * tam
        ancho = self.medir(tam)[0]
        a, b = self.arriba.medir(t), self.abajo.medir(t)
        raya = base - EJE * tam
        self.arriba.dibujar(pintor, x + (ancho - a[0]) / 2,
                            raya - 0.12 * tam - a[2], t, colores)  # fmt: skip
        self.abajo.dibujar(pintor, x + (ancho - b[0]) / 2,
                           raya + 0.12 * tam + b[1], t, colores)  # fmt: skip
        pintor.setPen(QPen(QColor(colores["texto"]), max(1.0, 0.055 * tam)))
        pintor.drawLine(QPointF(x + 0.08 * tam, raya),
                        QPointF(x + ancho - 0.08 * tam, raya))  # fmt: skip

    def texto(self):
        return f"({self.arriba.texto()})/({self.abajo.texto()})"


class Operador(Caja):
    """Un símbolo grande (∫ o Σ) con sus límites.

    apilado=True pone los límites encima y debajo (como en la suma);
    con False van a la derecha, arriba y abajo (como en la integral).
    """

    def __init__(self, simbolo, arriba, abajo, apilado):
        self.simbolo, self.arriba, self.abajo = simbolo, arriba, abajo
        self.apilado = apilado

    def _medidas(self, tam):
        grande = (1.9 if self.simbolo == "∫" else 1.45) * tam
        fm = QFontMetricsF(_fuente(grande))
        simbolo = fm.horizontalAdvance(self.simbolo)
        chico = REDUCCION * tam
        return grande, simbolo, self.arriba.medir(chico), self.abajo.medir(chico)

    def medir(self, tam):
        grande, simbolo, a, b = self._medidas(tam)
        alto_simbolo = 0.62 * grande  # sube el símbolo sobre la línea base
        bajo_simbolo = 0.30 * grande
        if self.apilado:
            ancho = max(simbolo, a[0], b[0]) + 0.2 * tam
            sube = alto_simbolo + 0.08 * tam + a[2] + a[1]
            baja = bajo_simbolo + 0.08 * tam + b[1] + b[2]
        else:
            ancho = simbolo + max(a[0], b[0]) + 0.25 * tam
            sube = alto_simbolo + 0.25 * a[1]
            baja = bajo_simbolo + 0.25 * b[2]
        return ancho, sube, baja

    def dibujar(self, pintor, x, base, tam, colores):
        grande, simbolo, a, b = self._medidas(tam)
        ancho, _, _ = self.medir(tam)
        chico = REDUCCION * tam
        # El símbolo grande, centrado verticalmente en el eje de la fórmula
        base_simbolo = base + (0.30 - 0.16) * grande
        pintor.setFont(_fuente(grande))
        pintor.setPen(QColor(colores["texto"]))
        if self.apilado:
            x_simbolo = x + (ancho - simbolo) / 2
            pintor.drawText(QPointF(x_simbolo, base_simbolo), self.simbolo)
            arriba = base - 0.62 * grande - 0.08 * tam - a[2]
            abajo = base + 0.30 * grande + 0.08 * tam + b[1]
            self.arriba.dibujar(pintor, x + (ancho - a[0]) / 2, arriba, chico, colores)
            self.abajo.dibujar(pintor, x + (ancho - b[0]) / 2, abajo, chico, colores)
        else:
            pintor.drawText(QPointF(x, base_simbolo), self.simbolo)
            derecha = x + 0.72 * simbolo + 0.12 * tam
            arriba = base - 0.62 * grande + a[1]
            self.arriba.dibujar(pintor, derecha + 0.18 * tam, arriba, chico, colores)
            abajo = base + 0.30 * grande
            self.abajo.dibujar(pintor, derecha - 0.05 * tam, abajo, chico, colores)

    def texto(self):
        return f"{self.simbolo}_({self.abajo.texto()})^({self.arriba.texto()}) "


class Raiz(Caja):
    """Raíz cuadrada que cubre todo su contenido con la raya de arriba."""

    def __init__(self, contenido):
        self.contenido = contenido

    def medir(self, tam):
        ancho, sube, baja = self.contenido.medir(tam)
        return ancho + 0.75 * tam, sube + 0.16 * tam, baja + 0.06 * tam

    def dibujar(self, pintor, x, base, tam, colores):
        ancho, sube, baja = self.medir(tam)
        arriba, abajo = base - sube + 0.04 * tam, base + baja - 0.02 * tam
        signo = QPainterPath()
        signo.moveTo(x + 0.05 * tam, base - 0.30 * tam)
        signo.lineTo(x + 0.18 * tam, base - 0.38 * tam)
        signo.lineTo(x + 0.36 * tam, abajo)
        signo.lineTo(x + 0.62 * tam, arriba)
        signo.lineTo(x + ancho - 0.02 * tam, arriba)
        pluma = QPen(QColor(colores["texto"]), max(1.0, 0.06 * tam))
        pluma.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        pintor.setPen(pluma)
        pintor.setBrush(Qt.BrushStyle.NoBrush)
        pintor.drawPath(signo)
        self.contenido.dibujar(pintor, x + 0.7 * tam, base, tam, colores)

    def texto(self):
        return f"√({self.contenido.texto()})"


# ---------------------------------------------------------------------------
# Atajos para escribir fórmulas cortas
# ---------------------------------------------------------------------------
def t(texto, rol="texto"):
    return Texto(texto, rol)


def var(texto, rol="texto"):
    """Una variable, en cursiva como en los libros."""
    return Texto(texto, rol, italica=True)


def cuadrado(base):
    return Indices(base, arriba=t("2"))


def sub(base, indice):
    return Indices(base, abajo=indice)


# ---------------------------------------------------------------------------
# El widget
# ---------------------------------------------------------------------------
class Formula(QWidget):
    """Muestra una o varias filas de fórmulas, cada una del alto que necesite."""

    def __init__(self, tam=18, separacion=10, centrada=False):
        super().__init__()
        self.tam = tam
        self.separacion = separacion
        self.centrada = centrada
        self.filas = []
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

    def establecer(self, *filas):
        self.filas = list(filas)
        self.setAccessibleName("; ".join(fila.texto() for fila in self.filas))
        self.updateGeometry()
        self.update()

    def _medidas(self):
        return [fila.medir(self.tam) for fila in self.filas]

    def sizeHint(self):
        medidas = self._medidas()
        ancho = max((m[0] for m in medidas), default=0)
        alto = sum(m[1] + m[2] for m in medidas) + self.separacion * max(
            0, len(medidas) - 1
        )
        return QSize(round(ancho) + 4, round(alto) + 4)

    def minimumSizeHint(self):
        return self.sizeHint()

    def paintEvent(self, _evento):
        pintor = QPainter(self)
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing)
        pintor.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        colores = tema.paleta()
        y = 2.0
        for fila, (ancho, sube, baja) in zip(self.filas, self._medidas(), strict=True):
            x = (self.width() - ancho) / 2 if self.centrada else 2.0
            fila.dibujar(pintor, x, y + sube, self.tam, colores)
            y += sube + baja + self.separacion
