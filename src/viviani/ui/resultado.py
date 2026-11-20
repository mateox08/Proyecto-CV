"""Panel de resultados: perímetro aproximado, valor de control y errores.

Animación al llegar un resultado nuevo (se omite con "reducir movimiento"):
  - el perímetro "cuenta" desde el valor anterior hasta el nuevo (400 ms);
  - las filas de abajo aparecen una tras otra (escalonadas 70 ms).
"""

from PySide6.QtCore import QElapsedTimer, Qt, QTimer, QVariantAnimation
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QGraphicsOpacityEffect,
    QGridLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from viviani import tema
from viviani.formato import formatear_cientifico, formatear_medida
from viviani.ui.componentes import (
    Separador,
    etiqueta_pequena,
    fuente,
)

DURACION_CONTEO_MS = 400
DURACION_FILA_MS = 260
ESCALON_MS = 70
SIN_VALOR = "—"

# Superíndices Unicode -> texto normal, para escribirlos con <sup> (HTML).
# La fuente de la interfaz no tiene el signo menos en superíndice "⁻".
_NORMALES = str.maketrans("⁻⁰¹²³⁴⁵⁶⁷⁸⁹", "−0123456789")


def con_exponente(texto):
    """'7.105 × 10⁻¹⁵ cm' -> '7.105 × 10<sup>−15</sup> cm' (para QLabel)."""
    if "×" not in texto:
        return texto
    antes, despues = texto.split("× 10", 1)
    exponente = ""
    while despues and despues[0] in "⁻⁰¹²³⁴⁵⁶⁷⁸⁹":
        exponente += despues[0]
        despues = despues[1:]
    return f"{antes}× 10<sup>{exponente.translate(_NORMALES)}</sup>{despues}"


class PanelResultado(QWidget):
    def __init__(self, colores, reducir_movimiento=False):
        super().__init__()
        self._quieto = reducir_movimiento
        diseno = QVBoxLayout(self)
        diseno.setContentsMargins(0, 0, 0, 0)
        diseno.setSpacing(6)

        diseno.addWidget(etiqueta_pequena("Perímetro aproximado"))
        self.etiqueta_perimetro = QLabel(SIN_VALOR)
        self.etiqueta_perimetro.setFont(
            fuente(tema.FAMILIAS_NUMEROS, 32, QFont.Weight.Light)
        )
        self.etiqueta_perimetro.setMinimumHeight(64)
        self.etiqueta_perimetro.setSizePolicy(
            QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed
        )
        diseno.addWidget(self.etiqueta_perimetro)
        diseno.addSpacing(6)
        diseno.addWidget(Separador())
        diseno.addSpacing(6)

        # Filas: etiqueta a la izquierda, valor a la derecha
        self._filas = []
        etiquetas = []
        for texto in ("Valor de control", "Error absoluto", "Error relativo"):
            fila = QWidget()
            rejilla = QGridLayout(fila)
            rejilla.setContentsMargins(0, 4, 0, 4)
            rejilla.addWidget(etiqueta_pequena(texto), 0, 0)
            valor = QLabel(SIN_VALOR)
            valor.setFont(fuente(tema.FAMILIAS_NUMEROS, 13))
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
        diseno.addStretch(1)

        # Animaciones
        self._valor_anterior = None
        self._conteo = QVariantAnimation(self)
        self._conteo.setDuration(DURACION_CONTEO_MS)
        self._conteo.valueChanged.connect(self._mostrar_perimetro)
        self._efectos = []
        for fila in self._filas:
            efecto = QGraphicsOpacityEffect(fila)
            efecto.setEnabled(False)  # solo se activa mientras aparece
            fila.setGraphicsEffect(efecto)
            self._efectos.append(efecto)
        self._reloj_filas = QElapsedTimer()
        self._tic = QTimer(self)
        self._tic.setInterval(16)
        self._tic.timeout.connect(self._avanzar_filas)

    # --- interfaz pública ----------------------------------------------
    def mostrar_resultado(self, r, animar=True):
        """Escribe los cuatro valores con punto decimal."""
        self.banda_error.hide()
        for fila in self._filas:
            fila.show()
        self.etiqueta_control.setText(f"{formatear_medida(r.referencia)} cm")
        error_abs = f"{formatear_cientifico(r.error_absoluto)} cm"
        error_rel = f"{formatear_cientifico(r.error_relativo)} %"
        self.etiqueta_error_abs.setText(con_exponente(error_abs))
        self.etiqueta_error_rel.setText(con_exponente(error_rel))
        perimetro = formatear_medida(r.perimetro)
        self.setAccessibleName(f"Resultado. Perímetro aproximado {perimetro} cm.")

        if animar and not self._quieto:
            inicio = self._valor_anterior if self._valor_anterior is not None else 0.0
            self._conteo.stop()
            self._conteo.setStartValue(float(inicio))
            self._conteo.setEndValue(float(r.perimetro))
            self._conteo.start()
            self._reloj_filas.start()
            for efecto in self._efectos:
                efecto.setOpacity(0.0)
                efecto.setEnabled(True)
            self._tic.start()
        else:
            self._mostrar_perimetro(r.perimetro)
        self._valor_anterior = r.perimetro

    def mostrar_error(self, mensaje):
        """Reemplaza los valores por el motivo del fallo."""
        if not mensaje.startswith("No se pudo"):
            mensaje = "No se pudo calcular: " + mensaje[:1].lower() + mensaje[1:]
        if "demasiado grande" in mensaje and "Pruebe" not in mensaje:
            mensaje += " Pruebe con un radio menor."
        self.saltar_animacion()
        self.etiqueta_perimetro.setText(SIN_VALOR)
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
        return self._tic.isActive() or (
            self._conteo.state() == QVariantAnimation.State.Running
        )

    def saltar_animacion(self):
        if self._conteo.state() == QVariantAnimation.State.Running:
            self._conteo.setCurrentTime(DURACION_CONTEO_MS)
            self._conteo.stop()
        self._tic.stop()
        for efecto in self._efectos:
            efecto.setEnabled(False)

    # --- pasos de la animación ------------------------------------------
    def _mostrar_perimetro(self, valor):
        self.etiqueta_perimetro.setText(f"{formatear_medida(float(valor))} cm")

    def _avanzar_filas(self):
        ms = self._reloj_filas.elapsed()
        for k, efecto in enumerate(self._efectos):
            avance = (ms - (k + 1) * ESCALON_MS) / DURACION_FILA_MS
            efecto.setOpacity(1 - (1 - min(max(avance, 0.0), 1.0)) ** 3)
        if ms >= len(self._efectos) * ESCALON_MS + DURACION_FILA_MS + ESCALON_MS:
            self.saltar_animacion()
