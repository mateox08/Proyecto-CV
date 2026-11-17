"""Piezas reutilizables de la interfaz: tarjetas, campos, botones, interruptor.

Cada pieza es un widget de Qt con un `objectName` o una propiedad (`rol`,
`error`, `enfocado`...) que la hoja de estilos de estilos.py usa para
pintarla. Los colores concretos nunca se escriben aquí: o los pone el QSS, o
llegan en el diccionario `colores` de viviani.tema.paleta().
"""

from PySide6.QtCore import QEvent, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFontMetrics, QPainter, QPen
from PySide6.QtWidgets import (
    QAbstractButton,
    QButtonGroup,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from viviani.ui import iconos

SANGRIA = 4  # los textos se corren 4 DIP para alinearse con los controles
RETARDO_MENSAJE_MS = 600  # espera sin escribir antes de mostrar un error

# Razones de foco que son "navegación con teclado": ahí sí se ve el anillo.
_FOCO_POR_TECLADO = (
    Qt.FocusReason.TabFocusReason,
    Qt.FocusReason.BacktabFocusReason,
    Qt.FocusReason.ShortcutFocusReason,
)


def repulir(widget):
    """Obliga a Qt a volver a aplicar el QSS tras cambiar una propiedad."""
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()


def etiqueta(texto, rol, sangria=True, palabras=False):
    """Un QLabel con su rol tipográfico (ver estilos.py)."""
    texto_etiqueta = QLabel(texto)
    texto_etiqueta.setProperty("rol", rol)
    texto_etiqueta.setWordWrap(palabras)
    if sangria:
        texto_etiqueta.setContentsMargins(SANGRIA, 0, SANGRIA, 0)
    return texto_etiqueta


# ---------------------------------------------------------------------------
# Anillo de foco
# ---------------------------------------------------------------------------
class ConAnillo(QFrame):
    """Marco que dibuja el anillo de foco alrededor de otro widget.

    El anillo se enciende cuando `vigilar` (por omisión, el propio contenido)
    recibe el foco. Con `solo_teclado=True` los clics del mouse no lo
    muestran (los botones pueden ocultarlo tras un clic, DISENO 5.3).
    """

    def __init__(self, contenido, vigilar=None, tipo="control", solo_teclado=False):
        super().__init__()
        self.setObjectName("anillo")
        self.setProperty("tipo", tipo)
        self.setProperty("enfocado", False)
        self._solo_teclado = solo_teclado
        self.contenido = contenido

        diseno = QVBoxLayout(self)
        diseno.setContentsMargins(0, 0, 0, 0)
        diseno.addWidget(contenido)

        self._vigilado = vigilar if vigilar is not None else contenido
        self._vigilado.installEventFilter(self)

    def eventFilter(self, objeto, evento):
        if objeto is self._vigilado:
            if evento.type() == QEvent.Type.FocusIn:
                if not self._solo_teclado or evento.reason() in _FOCO_POR_TECLADO:
                    self._encender(True)
            elif evento.type() == QEvent.Type.FocusOut:
                self._encender(False)
        return False

    def _encender(self, encendido):
        self.setProperty("enfocado", encendido)
        repulir(self)


# ---------------------------------------------------------------------------
# Tarjetas
# ---------------------------------------------------------------------------
class Tarjeta(QFrame):
    """Caja con fondo `superficie`, esquinas redondeadas y un encabezado."""

    def __init__(self, titulo):
        super().__init__()
        self.setObjectName("tarjeta")
        self.diseno = QVBoxLayout(self)
        # 16 DIP a los lados; 10 arriba y abajo para que las tres tarjetas de la
        # izquierda quepan sin desplazamiento en la ventana maximizada de
        # 1536 x 793 DIP (1920 x 1080 al 125 % con barra de tareas).
        self.diseno.setContentsMargins(16, 10, 16, 10)
        self.diseno.setSpacing(4)
        self.encabezado = etiqueta(titulo, "encabezado")
        self.diseno.addWidget(self.encabezado)


class BotonSecundario(QPushButton):
    """Botón con contorno e icono Lucide; puede quedar solo con el icono."""

    def __init__(self, texto, nombre_icono, tooltip, tamano_icono=16):
        super().__init__(texto)
        self._texto = texto
        self._nombre_icono = nombre_icono
        self._tamano_icono = tamano_icono
        self._color = "#000000"
        self._tooltip = tooltip
        self.setObjectName("secundario")
        self.setAccessibleName(texto)
        self.setToolTip(tooltip)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setIconSize(QSize(tamano_icono, tamano_icono))

    def compactar(self, compacto):
        """Solo icono (32 x 32) o icono con texto; el texto pasa al tooltip."""
        self.setText("" if compacto else self._texto)
        self.setObjectName("icono_sec" if compacto else "secundario")
        self.setToolTip(
            f"{self._texto}. {self._tooltip}" if compacto else self._tooltip
        )
        self.setIconSize(QSize(20, 20) if compacto else QSize(16, 16))
        self._poner_icono()
        repulir(self)

    def ancho_con_texto(self):
        """Ancho aproximado del botón con icono y texto (más 8 DIP del anillo)."""
        letra_negrita = self.fontMetrics().horizontalAdvance(self._texto) * 1.1
        return round(letra_negrita) + self._tamano_icono + 6 + 24 + 2 + 8

    def aplicar_colores(self, colores):
        self._color = colores["texto"]
        self._poner_icono()

    def _poner_icono(self):
        tamano = 20 if self.objectName() == "icono_sec" else self._tamano_icono
        self.setIcon(iconos.icono(self._nombre_icono, self._color, tamano))


class TarjetaGrafica(ConAnillo):
    """Tarjeta con cabecera (título + botones) y una gráfica enfocable.

    Es un ConAnillo: al enfocar la gráfica, el anillo rodea la tarjeta entera.
    """

    def __init__(self, titulo, grafica, botones):
        self.tarjeta = QFrame()
        self.tarjeta.setObjectName("tarjeta")
        diseno = QVBoxLayout(self.tarjeta)
        diseno.setContentsMargins(16, 12, 16, 12)
        diseno.setSpacing(8)

        cabecera = QHBoxLayout()
        cabecera.setSpacing(0)
        self.titulo = etiqueta(titulo, "encabezado")
        cabecera.addWidget(self.titulo, 1)
        self.botones = botones
        for boton in botones:
            # Cada botón con su anillo; los anillos suman 8 DIP de separación.
            cabecera.addWidget(ConAnillo(boton, solo_teclado=True))
        diseno.addLayout(cabecera)

        self.grafica = grafica
        # "Ignored": el tamaño preferido del lienzo de matplotlib (unos 640 x 480)
        # no cuenta, y las tarjetas se reparten el alto según los pesos 55/45.
        grafica.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        diseno.addWidget(grafica, 1)
        self.diseno_tarjeta = diseno
        self._forzar_compacto = False
        super().__init__(self.tarjeta, vigilar=grafica, tipo="tarjeta")

    def agregar_pie(self, widget):
        """Pone un widget (aviso, sugerencia) debajo de la gráfica."""
        self.diseno_tarjeta.addWidget(widget)

    def forzar_compacto(self, compacto):
        self._forzar_compacto = compacto
        self._ajustar_botones()

    def resizeEvent(self, evento):
        super().resizeEvent(evento)
        self._ajustar_botones()

    def _ajustar_botones(self):
        """Solo icono si el título y los botones con texto no caben en la cabecera."""
        necesario = self.titulo.sizeHint().width() + sum(
            boton.ancho_con_texto() for boton in self.botones
        )
        disponible = self.width() - 32  # márgenes laterales de la tarjeta
        compacto = self._forzar_compacto or necesario > disponible
        for boton in self.botones:
            if (boton.objectName() == "icono_sec") != compacto:
                boton.compactar(compacto)


# ---------------------------------------------------------------------------
# Bandas de aviso, error e información
# ---------------------------------------------------------------------------
class Banda(QFrame):
    """Franja con icono y texto: aviso, error o información (sin cuadros modales).

    `rol` decide el fondo (QSS) y `token_icono` el color del icono.
    """

    def __init__(self, rol, nombre_icono, token_icono, texto=""):
        super().__init__()
        self.setObjectName("banda")
        self.setProperty("rol", rol)
        self._nombre_icono = nombre_icono
        self._token_icono = token_icono

        diseno = QHBoxLayout(self)
        diseno.setContentsMargins(12, 6, 12, 6)
        diseno.setSpacing(8)
        self.icono = QLabel()
        self.icono.setFixedSize(16, 16)
        self.texto = etiqueta(texto, "texto_banda", sangria=False, palabras=True)
        diseno.addWidget(self.icono, 0, Qt.AlignmentFlag.AlignTop)
        diseno.addWidget(self.texto, 1)
        self.aplicar_colores(None)

    def mostrar(self, texto):
        self.texto.setText(texto)
        self.setVisible(True)

    def aplicar_colores(self, colores):
        if colores is not None:
            self.icono.setPixmap(
                iconos.pixmap(self._nombre_icono, colores[self._token_icono], 16)
            )


# ---------------------------------------------------------------------------
# Campo de texto con etiqueta, ayuda y mensaje de error
# ---------------------------------------------------------------------------
class CampoNumerico(QWidget):
    """Etiqueta + campo (con sufijo opcional) + ayuda que se cambia por el error.

    `validar` es una función texto -> (valor, mensaje) como las de
    viviani.validacion. El mensaje se MUESTRA al pulsar Calcular (lo pide la
    ventana), al salir del campo o tras 600 ms sin escribir; y DESAPARECE en
    cuanto el texto pasa a ser válido.
    """

    pausa_al_escribir = Signal()  # pasaron 600 ms sin teclear

    def __init__(self, titulo, validar, valor_inicial, marcador, ayuda, tooltip,
                 nombre_accesible, sufijo=None):  # fmt: skip
        super().__init__()
        self._validar = validar
        self._editado = False

        self.entrada = QLineEdit(valor_inicial)
        self.entrada.setObjectName("entrada")
        self.entrada.setPlaceholderText(marcador)
        self.entrada.setToolTip(tooltip)
        self.entrada.setAccessibleName(nombre_accesible)
        self.entrada.textEdited.connect(self._al_editar)
        self.entrada.installEventFilter(self)

        self.marco = QFrame()
        self.marco.setObjectName("campo")
        self.marco.setProperty("error", False)
        self.marco.setProperty("hover", False)
        interior = QHBoxLayout(self.marco)
        interior.setContentsMargins(0, 0, 0, 0)
        interior.setSpacing(0)
        interior.addWidget(self.entrada, 1)
        if sufijo:
            interior.addWidget(etiqueta(sufijo, "sufijo", sangria=False))
        self.anillo = ConAnillo(self.marco, vigilar=self.entrada)

        self.titulo = etiqueta(titulo, "etiqueta_campo")
        self.titulo.setBuddy(self.entrada)

        # La ayuda y el error comparten la misma celda: el que no se ve
        # conserva su sitio, así el diseño no salta al aparecer un error.
        self.ayuda = etiqueta(ayuda, "ayuda", palabras=True)
        self.mensaje = etiqueta("", "mensaje_error", sangria=False, palabras=True)
        self.icono_error = QLabel()
        self.icono_error.setFixedSize(16, 16)
        self.zona_error = QWidget()
        fila_error = QHBoxLayout(self.zona_error)
        fila_error.setContentsMargins(SANGRIA, 0, SANGRIA, 0)
        fila_error.setSpacing(4)
        fila_error.addWidget(self.icono_error, 0, Qt.AlignmentFlag.AlignTop)
        fila_error.addWidget(self.mensaje, 1)
        celda = QGridLayout()
        celda.setContentsMargins(0, 0, 0, 0)
        celda.addWidget(self.ayuda, 0, 0)
        celda.addWidget(self.zona_error, 0, 0)
        for pieza in (self.ayuda, self.zona_error):
            politica = pieza.sizePolicy()
            politica.setRetainSizeWhenHidden(True)
            pieza.setSizePolicy(politica)
        self.zona_error.setVisible(False)

        diseno = QVBoxLayout(self)
        diseno.setContentsMargins(0, 0, 0, 0)
        diseno.setSpacing(0)
        diseno.addWidget(self.titulo)
        diseno.addWidget(self.anillo)
        diseno.addLayout(celda)

        self._temporizador = QTimer(self)
        self._temporizador.setSingleShot(True)
        self._temporizador.setInterval(RETARDO_MENSAJE_MS)
        self._temporizador.timeout.connect(self._tras_pausa)
        self.aplicar_colores(None)

    # --- lectura y validación -------------------------------------------
    def texto(self):
        return self.entrada.text()

    def validar(self):
        """Valida en silencio: devuelve (valor, mensaje) sin mostrar nada."""
        return self._validar(self.entrada.text())

    def validar_y_mostrar(self):
        """Valida y deja a la vista el error (o lo quita). Devuelve (valor, msg)."""
        valor, mensaje = self.validar()
        self.mostrar_error(mensaje)
        return valor, mensaje

    def hay_error(self):
        return self.mensaje.text() != ""

    # --- mensajes ----------------------------------------------------------
    def mostrar_error(self, mensaje):
        """Muestra `mensaje` en lugar de la ayuda; "" quita el error."""
        hay_error = mensaje != ""
        self.mensaje.setText(mensaje)
        self.zona_error.setVisible(hay_error)
        self.ayuda.setVisible(not hay_error)
        self.marco.setProperty("error", hay_error)
        self.entrada.setAccessibleDescription(mensaje)
        repulir(self.marco)

    def _al_editar(self, _texto):
        self._editado = True
        _valor, mensaje = self.validar()
        if mensaje == "":
            self.mostrar_error("")  # válido: el mensaje desaparece al instante
        self._temporizador.start()

    def _tras_pausa(self):
        self._mostrar_si_corresponde()
        self.pausa_al_escribir.emit()

    def _mostrar_si_corresponde(self):
        # Un campo vacío que nadie tocó no muestra error.
        if self._editado or self.entrada.text().strip() != "":
            self.validar_y_mostrar()

    # --- eventos de la entrada --------------------------------------------
    def eventFilter(self, objeto, evento):
        if objeto is self.entrada:
            tipo = evento.type()
            if tipo == QEvent.Type.FocusOut:
                self._temporizador.stop()
                self._mostrar_si_corresponde()
            elif tipo in (QEvent.Type.Enter, QEvent.Type.Leave):
                # El marco no recibe "hover" cuando el ratón está sobre la
                # entrada (que lo cubre), así que se avisa a mano.
                self.marco.setProperty("hover", tipo == QEvent.Type.Enter)
                repulir(self.marco)
        return False

    def aplicar_colores(self, colores):
        if colores is not None:
            self.icono_error.setPixmap(
                iconos.pixmap("circle-alert", colores["error"], 16)
            )


# ---------------------------------------------------------------------------
# Interruptor
# ---------------------------------------------------------------------------
class Interruptor(QAbstractButton):
    """Interruptor "Sonido: activado/desactivado" pintado a mano.

    Se lee por tres señales a la vez (no solo el color): posición del pulgar,
    icono y texto (DISENO 4.8). Pista 44 x 24 DIP.
    """

    ANCHO_PISTA = 44
    ALTO_PISTA = 24
    ALTO = 32

    def __init__(self):
        super().__init__()
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._colores = None

    def aplicar_colores(self, colores):
        self._colores = colores
        self.update()

    def sizeHint(self):
        ancho_texto = QFontMetrics(self.font()).horizontalAdvance(self.text())
        return QSize(self.ANCHO_PISTA + 8 + 16 + 6 + ancho_texto + 8, self.ALTO)

    def minimumSizeHint(self):
        return self.sizeHint()

    def paintEvent(self, _evento):
        if self._colores is None:
            return
        c = self._colores
        pincel = QPainter(self)
        pincel.setRenderHint(QPainter.RenderHint.Antialiasing)
        y_pista = (self.height() - self.ALTO_PISTA) / 2
        activado = self.isChecked()

        # Pista: llena en `acento` si está activado, solo contorno si no.
        pincel.setPen(Qt.PenStyle.NoPen if activado else QPen(QColor(c["borde"]), 1))
        pincel.setBrush(QColor(c["acento"]) if activado else Qt.BrushStyle.NoBrush)
        margen = 0 if activado else 0.5
        pincel.drawRoundedRect(
            margen, y_pista + margen,
            self.ANCHO_PISTA - 2 * margen, self.ALTO_PISTA - 2 * margen,
            self.ALTO_PISTA / 2, self.ALTO_PISTA / 2,
        )  # fmt: skip

        # Pulgar: a la derecha si está activado, a la izquierda si no.
        diametro = 16
        x_pulgar = self.ANCHO_PISTA - diametro - 4 if activado else 4
        color_pulgar = c["texto_sobre_acento"] if activado else c["borde"]
        pincel.setPen(Qt.PenStyle.NoPen)
        pincel.setBrush(QColor(color_pulgar))
        pincel.drawEllipse(x_pulgar, y_pista + (self.ALTO_PISTA - diametro) / 2,
                           diametro, diametro)  # fmt: skip

        # Icono y texto a la derecha de la pista.
        x = self.ANCHO_PISTA + 8
        nombre = "volume-2" if activado else "volume-x"
        pincel.drawPixmap(
            x, (self.height() - 16) // 2, iconos.pixmap(nombre, c["texto"], 16)
        )
        pincel.setPen(QColor(c["texto"]))
        zona_texto = self.rect().adjusted(x + 16 + 6, 0, 0, 0)
        pincel.drawText(zona_texto, Qt.AlignmentFlag.AlignVCenter, self.text())


# ---------------------------------------------------------------------------
# Selector de método (control segmentado)
# ---------------------------------------------------------------------------
class SelectorMetodo(QWidget):
    """Tres botones exclusivos: izquierda, punto medio y derecha.

    La letra con `&` es el atajo Alt (Alt+I, Alt+P, Alt+D). Con el teclado
    se entra con Tab al botón elegido y las flechas cambian de opción.
    """

    metodo_cambiado = Signal(str)  # "izquierda" | "punto_medio" | "derecha"

    OPCIONES = (
        ("izquierda", "&Izquierda",
         "Evalúa f en el extremo izquierdo de cada subintervalo (Alt+I)"),
        ("punto_medio", "&Punto medio",
         "Evalúa f en el punto medio de cada subintervalo (Alt+P)"),
        ("derecha", "&Derecha",
         "Evalúa f en el extremo derecho de cada subintervalo (Alt+D)"),
    )  # fmt: skip

    def __init__(self):
        super().__init__()
        self.botones = {}
        self._grupo = QButtonGroup(self)
        self._grupo.setExclusive(True)
        diseno = QHBoxLayout(self)
        diseno.setContentsMargins(0, 0, 0, 0)
        diseno.setSpacing(0)
        for clave, texto, ayuda in self.OPCIONES:
            boton = QPushButton(texto)
            boton.setObjectName("segmento")
            boton.setCheckable(True)
            boton.setToolTip(ayuda)
            boton.setAccessibleName("Método " + texto.replace("&", "").lower())
            boton.setCursor(Qt.CursorShape.PointingHandCursor)
            self._grupo.addButton(boton)
            self.botones[clave] = boton
            diseno.addWidget(ConAnillo(boton, solo_teclado=True), 1)
        self.botones["punto_medio"].setChecked(True)  # por omisión
        for clave, boton in self.botones.items():
            boton.toggled.connect(lambda marcado, c=clave: self._al_marcar(c, marcado))

    def metodo(self):
        for clave, boton in self.botones.items():
            if boton.isChecked():
                return clave

    def establecer(self, clave):
        self.botones[clave].setChecked(True)

    def _al_marcar(self, clave, marcado):
        if marcado:
            self.metodo_cambiado.emit(clave)
