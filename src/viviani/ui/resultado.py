"""Tarjeta "Resultado": perímetro aproximado, valor de control y errores."""

from PySide6.QtCore import Qt, QVariantAnimation
from PySide6.QtWidgets import (
    QGraphicsOpacityEffect,
    QGridLayout,
    QLabel,
    QSizePolicy,
    QWidget,
)

from viviani import tema
from viviani.formato import formatear_cientifico, formatear_medida
from viviani.ui.componentes import Tarjeta, etiqueta_pequena, fuente

DURACION_APARECER_MS = 220
SIN_VALOR = "—"


class TarjetaResultado(Tarjeta):
    def __init__(self, colores):
        super().__init__(colores, "Resultado")

        # Bloque de valores (se desvanece al aparecer un resultado nuevo)
        self._valores = QWidget()
        rejilla = QGridLayout(self._valores)
        rejilla.setContentsMargins(0, 0, 0, 0)
        rejilla.setHorizontalSpacing(12)
        rejilla.setVerticalSpacing(10)

        rejilla.addWidget(etiqueta_pequena("Perímetro aproximado"), 0, 0, 1, 2)
        self.etiqueta_perimetro = QLabel(SIN_VALOR)
        self.etiqueta_perimetro.setFont(fuente(tema.FAMILIAS_NUMEROS, 26))
        self.etiqueta_perimetro.setSizePolicy(
            QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred
        )
        rejilla.addWidget(self.etiqueta_perimetro, 1, 0, 1, 2)

        filas = (("Valor de control", 2), ("Error absoluto", 3), ("Error relativo", 4))
        etiquetas = []
        for texto, fila in filas:
            rejilla.addWidget(etiqueta_pequena(texto), fila, 0)
            valor = QLabel(SIN_VALOR)
            valor.setFont(fuente(tema.FAMILIAS_NUMEROS, 14))
            valor.setAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            rejilla.addWidget(valor, fila, 1)
            etiquetas.append(valor)
        self.etiqueta_control, self.etiqueta_error_abs, self.etiqueta_error_rel = (
            etiquetas
        )
        rejilla.setRowMinimumHeight(1, 54)
        self.contenido.addWidget(self._valores)

        # Mensaje cuando el cálculo falla (por ejemplo, un radio enorme)
        self.banda_error = QLabel()
        self.banda_error.setProperty("rol", "banda_error")
        self.banda_error.setWordWrap(True)
        self.banda_error.hide()
        self.contenido.addWidget(self.banda_error)
        self.contenido.addStretch(1)

        self._opacidad = QGraphicsOpacityEffect(self._valores)
        self._opacidad.setOpacity(1.0)
        self._valores.setGraphicsEffect(self._opacidad)
        self._opacidad.setEnabled(False)  # solo se activa mientras aparece
        self._aparicion = QVariantAnimation(self)
        self._aparicion.setDuration(DURACION_APARECER_MS)
        self._aparicion.setStartValue(0.0)
        self._aparicion.setEndValue(1.0)
        self._aparicion.valueChanged.connect(
            lambda v: self._opacidad.setOpacity(float(v))
        )
        self._aparicion.finished.connect(lambda: self._opacidad.setEnabled(False))

    def mostrar_resultado(self, r, animar=True):
        """Escribe los cuatro valores con punto decimal."""
        self.banda_error.hide()
        self._valores.show()
        self.etiqueta_perimetro.setText(f"{formatear_medida(r.perimetro)} cm")
        self.etiqueta_control.setText(f"{formatear_medida(r.referencia)} cm")
        self.etiqueta_error_abs.setText(f"{formatear_cientifico(r.error_absoluto)} cm")
        self.etiqueta_error_rel.setText(f"{formatear_cientifico(r.error_relativo)} %")
        perimetro = formatear_medida(r.perimetro)
        self.setAccessibleName(f"Resultado. Perímetro aproximado {perimetro} cm.")
        if animar:
            self._opacidad.setEnabled(True)
            self._aparicion.start()

    def mostrar_error(self, mensaje):
        """Reemplaza los valores por el motivo del fallo."""
        if not mensaje.startswith("No se pudo"):
            mensaje = "No se pudo calcular: " + mensaje[:1].lower() + mensaje[1:]
        if "demasiado grande" in mensaje and "Pruebe" not in mensaje:
            mensaje += " Pruebe con un radio menor."
        for etiqueta in (self.etiqueta_perimetro, self.etiqueta_control,
                         self.etiqueta_error_abs, self.etiqueta_error_rel):  # fmt: skip
            etiqueta.setText(SIN_VALOR)
        self._valores.hide()
        self.banda_error.setText(mensaje)
        self.banda_error.show()
        self.setAccessibleName(f"Resultado. {mensaje}")

    def esta_animando(self):
        return self._aparicion.state() == QVariantAnimation.State.Running

    def saltar_animacion(self):
        if self.esta_animando():
            self._aparicion.setCurrentTime(DURACION_APARECER_MS)
            self._aparicion.stop()
            self._opacidad.setEnabled(False)
