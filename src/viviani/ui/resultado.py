"""Panel de resultados: perímetro aproximado, precisión, valor de control y errores.

El perímetro se pinta en dos colores: en el color del texto las cifras que
coinciden con el valor de control y en el color de "aviso" las que todavía
no. Debajo, un medidor de 16 segmentos dice cuántas cifras significativas son
correctas (16 es todo lo que distingue un número decimal de la computadora).

Animación al llegar un resultado nuevo (se omite con "reducir movimiento"):
  - el perímetro "cuenta" desde el valor anterior hasta el nuevo;
  - el medidor se llena segmento a segmento;
  - las filas de abajo aparecen una tras otra (escalonadas 70 ms).
"""

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import (
    QGraphicsOpacityEffect,
    QGridLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from viviani import tema
from viviani.animacion import Animacion, salida_suave
from viviani.formato import (
    CIFRAS_MAXIMAS,
    cifras_correctas,
    con_exponente,
    formatear_cientifico,
    formatear_medida,
    prefijo_comun,
)
from viviani.tema import con_alfa
from viviani.ui.componentes import (
    Separador,
    degradado_acento,
    etiqueta_pequena,
    fuente,
)

DURACION_TOTAL_MS = 700
DURACION_CONTEO_MS = 450
DURACION_FILA_MS = 260
ESCALON_MS = 70
SIN_VALOR = "—"


class MedidorCifras(QWidget):
    """Fila de 16 segmentos: se encienden tantos como cifras correctas."""

    def __init__(self, colores):
        super().__init__()
        self.colores = colores
        self.cifras = 0.0  # puede ser fraccionario durante la animación
        self.setFixedHeight(40)
        self.setAccessibleName("Cifras correctas: sin calcular")

    def establecer(self, cifras):
        self.cifras = cifras
        self.update()

    def paintEvent(self, _evento):
        c = self.colores
        pintor = QPainter(self)
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing)
        ancho = self.width()
        # Textos de arriba: nombre a la izquierda, cantidad a la derecha
        pintor.setFont(fuente(tema.FAMILIAS_INTERFAZ, 9.5))
        pintor.setPen(QColor(c["etiqueta"]))
        arriba = QRectF(0, 0, ancho, 20)
        pintor.drawText(arriba, Qt.AlignmentFlag.AlignLeft, "Cifras correctas")
        pintor.setPen(QColor(c["texto"]))
        pintor.setFont(fuente(tema.FAMILIAS_MONO, 9.5))
        cantidad = round(self.cifras)
        pintor.drawText(arriba, Qt.AlignmentFlag.AlignRight,
                        f"{cantidad} de {CIFRAS_MAXIMAS}")  # fmt: skip

        # Segmentos
        separacion = 4
        largo = (ancho - separacion * (CIFRAS_MAXIMAS - 1)) / CIFRAS_MAXIMAS
        pintor.setPen(Qt.PenStyle.NoPen)
        lleno = degradado_acento(0, ancho)
        for k in range(CIFRAS_MAXIMAS):
            caja = QRectF(k * (largo + separacion), 26, largo, 6)
            encendido = min(max(self.cifras - k, 0.0), 1.0)
            pintor.setBrush(QColor(c["borde"]))
            pintor.drawRoundedRect(caja, 3, 3)
            if encendido > 0:
                pintor.setOpacity(encendido)
                pintor.setBrush(lleno)
                pintor.drawRoundedRect(caja, 3, 3)
                pintor.setOpacity(1.0)
        # Un brillo en el último segmento encendido
        if 0 < self.cifras:
            k = min(int(self.cifras - 1e-9), CIFRAS_MAXIMAS - 1)
            centro = QPointF(k * (largo + separacion) + largo / 2, 29)
            pintor.setBrush(con_alfa(c["acento_2"], 0.25))
            pintor.drawEllipse(centro, largo * 0.8, 6)


class PanelResultado(QWidget):
    def __init__(self, colores, reducir_movimiento=False):
        super().__init__()
        self.colores = colores
        self._quieto = reducir_movimiento
        diseno = QVBoxLayout(self)
        diseno.setContentsMargins(0, 0, 0, 0)
        diseno.setSpacing(6)

        diseno.addWidget(etiqueta_pequena("Perímetro aproximado"))
        self.etiqueta_perimetro = QLabel(SIN_VALOR)
        self.etiqueta_perimetro.setTextFormat(Qt.TextFormat.RichText)
        self.etiqueta_perimetro.setFont(
            fuente(tema.FAMILIAS_TITULO, 34, QFont.Weight.Light)
        )
        self.etiqueta_perimetro.setMinimumHeight(66)
        self.etiqueta_perimetro.setSizePolicy(
            QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed
        )
        diseno.addWidget(self.etiqueta_perimetro)
        self.medidor = MedidorCifras(colores)
        diseno.addWidget(self.medidor)
        diseno.addSpacing(4)
        diseno.addWidget(Separador())
        diseno.addSpacing(2)

        # Filas: etiqueta a la izquierda, valor a la derecha
        self._filas = []
        etiquetas = []
        for texto in ("Valor de control", "Error absoluto", "Error relativo"):
            fila = QWidget()
            rejilla = QGridLayout(fila)
            rejilla.setContentsMargins(0, 3, 0, 3)
            rejilla.addWidget(etiqueta_pequena(texto), 0, 0)
            valor = QLabel(SIN_VALOR)
            valor.setFont(fuente(tema.FAMILIAS_TITULO, 13))
            derecha = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            valor.setAlignment(derecha)
            rejilla.addWidget(valor, 0, 1)
            diseno.addWidget(fila)
            etiquetas.append(valor)
            self._filas.append(fila)
        self.etiqueta_control, self.etiqueta_error_abs, self.etiqueta_error_rel = (
            etiquetas
        )

        # Mensaje cuando el cálculo falla (por ejemplo, un radio enorme)
        self.banda_error = QLabel()
        self.banda_error.setProperty("rol", "banda_error")
        self.banda_error.setWordWrap(True)
        self.banda_error.hide()
        diseno.addWidget(self.banda_error)

        # Animación (cada fila aparece con un efecto de opacidad)
        self._resultado = None
        self._valor_anterior = None  # de aquí parte el conteo
        self._inicio = 0.0
        self._cifras_inicio = 0.0
        self._animacion = Animacion(self, self._al_cuadro, self._al_terminar)
        self._efectos = []
        for fila in self._filas:
            efecto = QGraphicsOpacityEffect(fila)
            efecto.setEnabled(False)  # solo se activa mientras aparece
            fila.setGraphicsEffect(efecto)
            self._efectos.append(efecto)

    # --- interfaz pública ----------------------------------------------
    def mostrar_resultado(self, r, animar=True):
        """Escribe los valores (con punto decimal) y anima su llegada."""
        self.banda_error.hide()
        for fila in self._filas:
            fila.show()
        self.etiqueta_control.setText(f"{formatear_medida(r.referencia)} cm")
        error_abs = f"{formatear_cientifico(r.error_absoluto)} cm"
        error_rel = f"{formatear_cientifico(r.error_relativo)} %"
        self.etiqueta_error_abs.setText(con_exponente(error_abs))
        self.etiqueta_error_rel.setText(con_exponente(error_rel))
        cifras = cifras_correctas(r.error_relativo)
        perimetro = formatear_medida(r.perimetro)
        self.setAccessibleName(
            f"Resultado. Perímetro aproximado {perimetro} cm, "
            f"{cifras} cifras correctas."
        )
        self.medidor.setAccessibleName(f"Cifras correctas: {cifras} de 16")

        self._inicio = self._valor_anterior if self._valor_anterior is not None else 0.0
        self._cifras_inicio = self.medidor.cifras
        self._resultado = r
        self._valor_anterior = r.perimetro
        if animar and not self._quieto:
            for efecto in self._efectos:
                efecto.setOpacity(0.0)
                efecto.setEnabled(True)
            self._animacion.iniciar(DURACION_TOTAL_MS)
        else:
            self._al_terminar()

    def mostrar_error(self, mensaje):
        """Reemplaza los valores por el motivo del fallo."""
        if not mensaje.startswith("No se pudo"):
            mensaje = "No se pudo calcular: " + mensaje[:1].lower() + mensaje[1:]
        if "demasiado grande" in mensaje and "Pruebe" not in mensaje:
            mensaje += " Pruebe con un radio menor."
        self.saltar_animacion()
        self.etiqueta_perimetro.setText(SIN_VALOR)
        self.medidor.establecer(0)
        for etiqueta in (self.etiqueta_control, self.etiqueta_error_abs,
                         self.etiqueta_error_rel):  # fmt: skip
            etiqueta.setText(SIN_VALOR)
        for fila in self._filas:
            fila.hide()
        self._valor_anterior = None
        self.banda_error.setText(mensaje)
        self.banda_error.show()
        self.setAccessibleName(f"Resultado. {mensaje}")

    def esta_animando(self):
        return self._animacion.activa()

    def saltar_animacion(self):
        self._animacion.terminar()

    # --- pasos de la animación ------------------------------------------
    def _al_cuadro(self, ms):
        r = self._resultado
        avance = salida_suave(ms / DURACION_CONTEO_MS)
        valor = self._inicio + (r.perimetro - self._inicio) * avance
        self.etiqueta_perimetro.setText(self._html_perimetro(formatear_medida(valor)))
        objetivo = cifras_correctas(r.error_relativo)
        llenado = salida_suave(ms / (DURACION_TOTAL_MS - 100))
        self.medidor.establecer(
            self._cifras_inicio + (objetivo - self._cifras_inicio) * llenado
        )
        for k, efecto in enumerate(self._efectos):
            efecto.setOpacity(
                salida_suave((ms - (k + 1) * ESCALON_MS) / DURACION_FILA_MS)
            )

    def _al_terminar(self):
        r = self._resultado
        self.medidor.establecer(cifras_correctas(r.error_relativo))
        texto = formatear_medida(r.perimetro)
        coinciden = prefijo_comun(texto, formatear_medida(r.referencia))
        self.etiqueta_perimetro.setText(self._html_perimetro(texto, coinciden))
        for efecto in self._efectos:
            efecto.setEnabled(False)

    def _html_perimetro(self, texto, coinciden=None):
        """El número con las cifras correctas en el color del texto y el resto
        en el color de aviso. Mientras cuenta (coinciden = None) va todo igual.
        """
        c = self.colores
        if coinciden is None:
            coinciden = len(texto)
        unidad = f'<span style="color:{c["texto_sec"]}; font-size:18pt"> cm</span>'
        return (
            f'<span style="color:{c["texto"]}">{texto[:coinciden]}</span>'
            f'<span style="color:{c["aviso"]}">{texto[coinciden:]}</span>{unidad}'
        )
