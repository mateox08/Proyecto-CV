"""Tarjeta "Resultado": valores del cálculo y avisos de error o cancelación.

Estados (DISENO 4.7): vacía, con resultado, error de cálculo. Encima de
cualquiera de ellos puede aparecer la banda "Cálculo cancelado".
"""

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QGraphicsOpacityEffect, QGridLayout, QWidget

from viviani.formato import (
    formatear_cientifico,
    formatear_entero,
    formatear_medida,
    formatear_radio,
    nombre_metodo,
)
from viviani.ui.componentes import Banda, Tarjeta, etiqueta

DURACION_APARICION_MS = 200
_SUPERINDICES_A_TEXTO = str.maketrans("⁻⁰¹²³⁴⁵⁶⁷⁸⁹", "-0123456789")


def cientifica_en_palabras(valor):
    """El número como lo leería el Narrador.

    7,982 × 10⁻⁴  ->  "7,982 por 10 a la menos 4"
    """
    texto = formatear_cientifico(valor, 4)
    if " × 10" not in texto:
        return texto
    mantisa, potencia = texto.split(" × 10")
    exponente = potencia.translate(_SUPERINDICES_A_TEXTO).replace("-", "menos ")
    return f"{mantisa} por 10 a la {exponente}"


def _fuente_de_cifras(base, puntos, peso):
    """Fuente con cifras tabulares (todas las cifras del mismo ancho)."""
    fuente = QFont(base)
    fuente.setPointSizeF(puntos)
    fuente.setWeight(peso)
    try:
        fuente.setFeature(QFont.Tag("tnum"), 1)
    except Exception:  # pragma: no cover - versiones de Qt sin esta función
        pass
    return fuente


class TarjetaResultado(Tarjeta):
    def __init__(self, escala=1.0):
        super().__init__("Resultado")
        self._escala = escala
        self._animacion = None

        self.banda_cancelado = Banda("aviso", "info", "aviso")
        self.banda_cancelado.setVisible(False)
        self.banda_error = Banda("error", "circle-alert", "error")
        self.banda_error.setVisible(False)
        self.vacio = Banda(
            "vacio", "info", "texto_sec",
            "Aún no hay resultados. Escriba R y n y presione Enter.",
        )  # fmt: skip
        self.contenido = self._crear_contenido()
        self.contenido.setVisible(False)

        # "Vacío" y "contenido" comparten celda: la tarjeta no cambia de
        # altura al llegar el primer resultado.
        celda = QGridLayout()
        celda.setContentsMargins(0, 0, 0, 0)
        celda.addWidget(self.vacio, 0, 0, Qt.AlignmentFlag.AlignVCenter)
        celda.addWidget(self.contenido, 0, 0)
        for pieza in (self.vacio, self.contenido):
            politica = pieza.sizePolicy()
            politica.setRetainSizeWhenHidden(True)
            pieza.setSizePolicy(politica)

        self.diseno.addWidget(self.banda_cancelado)
        self.diseno.addWidget(self.banda_error)
        self.diseno.addLayout(celda)

    # --- construcción -----------------------------------------------------
    def _crear_contenido(self):
        base = self.font()
        derecha = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter

        self.etiqueta_contexto = etiqueta("", "contexto", palabras=True)
        rotulo_principal = etiqueta("Perímetro aproximado", "rotulo")
        self.etiqueta_perimetro = etiqueta("", "valor")
        self.etiqueta_perimetro.setFont(
            _fuente_de_cifras(base, 28 * self._escala, QFont.Weight.DemiBold)
        )
        self.etiqueta_control = etiqueta("", "valor")
        self.etiqueta_error_abs = etiqueta("", "valor")
        self.etiqueta_error_rel = etiqueta("", "valor")
        for valor in (
            self.etiqueta_control,
            self.etiqueta_error_abs,
            self.etiqueta_error_rel,
        ):
            valor.setFont(
                _fuente_de_cifras(base, 14 * self._escala, QFont.Weight.Normal)
            )
            valor.setAlignment(derecha)

        self.nota_control = etiqueta("7,640395578 · R", "ayuda")
        self.nota_cero = etiqueta(
            "Coincide con el valor de control dentro de la precisión del computador.",
            "ayuda", palabras=True,
        )  # fmt: skip
        self.nota_cero.setVisible(False)

        pagina = QWidget()
        filas = QGridLayout(pagina)
        filas.setContentsMargins(0, 0, 0, 0)
        filas.setHorizontalSpacing(12)
        filas.setVerticalSpacing(0)
        filas.addWidget(self.etiqueta_contexto, 0, 0, 1, 2)
        filas.addWidget(rotulo_principal, 1, 0, 1, 2)
        filas.addWidget(self.etiqueta_perimetro, 2, 0, 1, 2)
        filas.setRowMinimumHeight(3, 6)
        filas.addWidget(etiqueta("Valor de control", "rotulo"), 4, 0)
        filas.addWidget(self.etiqueta_control, 4, 1)
        filas.addWidget(self.nota_control, 5, 0, 1, 2)
        filas.addWidget(etiqueta("Error absoluto", "rotulo"), 6, 0)
        filas.addWidget(self.etiqueta_error_abs, 6, 1)
        filas.addWidget(self.nota_cero, 7, 0, 1, 2)
        filas.addWidget(etiqueta("Error relativo", "rotulo"), 8, 0)
        filas.addWidget(self.etiqueta_error_rel, 8, 1)
        filas.setColumnStretch(1, 1)
        return pagina

    # --- estados -----------------------------------------------------------
    def mostrar_resultado(self, r, animar=True):
        """Muestra los valores de `r` (un viviani.calculo.Resultado)."""
        self.banda_cancelado.setVisible(False)
        self.banda_error.setVisible(False)
        self.etiqueta_contexto.setText(
            f"Para R = {formatear_radio(r.radio)} cm, n = {formatear_entero(r.n)}, "
            f"{nombre_metodo(r.metodo)}"
        )
        self.etiqueta_perimetro.setText(f"{formatear_medida(r.perimetro)} cm")
        self.etiqueta_control.setText(f"{formatear_medida(r.referencia)} cm")
        self.etiqueta_error_abs.setText(f"{formatear_cientifico(r.error_absoluto)} cm")
        self.etiqueta_error_rel.setText(f"{formatear_cientifico(r.error_relativo)} %")
        self.nota_cero.setVisible(r.error_absoluto == 0)
        self.setAccessibleName(
            f"Perímetro aproximado {formatear_medida(r.perimetro)} centímetros. "
            f"Error relativo {cientifica_en_palabras(r.error_relativo)} por ciento."
        )
        self.vacio.setVisible(False)
        self.contenido.setVisible(True)
        self._ajustar_valor_principal()
        if animar:
            self._aparecer()

    def mostrar_error(self, mensaje):
        """Banda roja con la causa del fallo; se ocultan los valores anteriores."""
        self.saltar_animacion()
        if not mensaje.startswith("No se pudo"):
            mensaje = f"No se pudo calcular: {mensaje}"
        self.banda_cancelado.setVisible(False)
        self.banda_error.mostrar(mensaje)
        self.contenido.setVisible(False)
        self.vacio.setVisible(False)
        self.setAccessibleName("Resultado. " + mensaje)

    def mostrar_cancelado(self, hay_resultados):
        """Aviso "Cálculo cancelado"; los resultados anteriores se conservan."""
        self.banda_error.setVisible(False)
        texto = "Cálculo cancelado."
        if hay_resultados:
            texto += " Se mantienen los resultados anteriores."
        self.banda_cancelado.mostrar(texto)

    def ocultar_avisos(self):
        self.banda_cancelado.setVisible(False)
        self.banda_error.setVisible(False)

    def aplicar_colores(self, colores):
        for banda in (self.banda_cancelado, self.banda_error, self.vacio):
            banda.aplicar_colores(colores)

    # --- animación de entrada ----------------------------------------------
    def _aparecer(self):
        """Los números aparecen ya completos, con un fundido de 200 ms."""
        self.saltar_animacion()
        efecto = QGraphicsOpacityEffect(self.contenido)
        efecto.setOpacity(0.0)
        self.contenido.setGraphicsEffect(efecto)
        animacion = QPropertyAnimation(efecto, b"opacity", self)
        animacion.setDuration(DURACION_APARICION_MS)
        animacion.setStartValue(0.0)
        animacion.setEndValue(1.0)
        animacion.setEasingCurve(QEasingCurve.Type.OutCubic)
        animacion.finished.connect(self._quitar_efecto)
        self._animacion = animacion
        animacion.start()

    def _quitar_efecto(self):
        self._animacion = None
        self.contenido.setGraphicsEffect(None)

    def esta_animando(self):
        return self._animacion is not None

    def saltar_animacion(self):
        if self._animacion is not None:
            self._animacion.stop()
            self._quitar_efecto()

    # --- ajuste del tamaño del perímetro ----------------------------------
    def resizeEvent(self, evento):
        super().resizeEvent(evento)
        self._ajustar_valor_principal()

    def _ajustar_valor_principal(self):
        """Reduce los 28 pt si el número no cabe (radios muy grandes o pequeños)."""
        etiqueta_valor = self.etiqueta_perimetro
        disponible = self.contenido.width() - 8
        if disponible <= 8:
            return
        puntos = 28 * self._escala
        fuente = _fuente_de_cifras(self.font(), puntos, QFont.Weight.DemiBold)
        while puntos > 14:
            etiqueta_valor.setFont(fuente)
            ancho = etiqueta_valor.fontMetrics().horizontalAdvance(
                etiqueta_valor.text()
            )
            if ancho <= disponible:
                break
            puntos -= 1
            fuente.setPointSizeF(puntos)
        etiqueta_valor.setFont(fuente)
