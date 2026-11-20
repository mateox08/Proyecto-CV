"""Ventana principal: une los campos, el resultado y las dos gráficas.

La ventana NO calcula, ni dibuja gráficas, ni fabrica sonidos: recibe esas
piezas ya hechas en el constructor (ver app.py) y solo coordina:

    escribir R y n -> validar -> calcular en un hilo -> mostrar -> animar

Distribución: la curva 3D ocupa toda la ventana (es la protagonista) y lo
demás flota encima, a los lados:

    [logo] Ventana de Viviani                                [Créditos]

    RADIO R                 ( esfera 3D )            PERÍMETRO APROXIMADO
    ____5_______ cm         (  girando  )            38.201978 cm
    SUBINTERVALOS n         (  grande   )            VALOR DE CONTROL ...
    ____10______                                     ERROR ...
       ( orbe Calcular )                             [ suma de Riemann ]
    [Exportar PNG]                                   [   compacta      ]
"""

from pathlib import Path

from PySide6.QtCore import QEvent, QRectF, QSize, QStandardPaths, Qt, QTimer
from PySide6.QtGui import QCursor, QKeySequence, QPainter, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from viviani import tema, validacion
from viviani.ui import estilos, iconos, sistema
from viviani.ui.componentes import (
    BotonOrbe,
    CampoLinea,
    FondoVentana,
    fuente,
)
from viviani.ui.creditos import PanelCreditos
from viviani.ui.logo import dibujar_logo
from viviani.ui.resultado import PanelResultado
from viviani.ui.trabajador import GestorTareas

TITULO = "Ventana de Viviani"
RETARDO_PROGRESO_MS = 300  # el arco de progreso solo aparece si tarda más
INTERVALO_CURSOR_MS = 33  # cada cuánto se revisa dónde está el cursor
DURACION_AVISO_MS = 2500  # "Imagen guardada"
METODO = "punto_medio"  # en esta curva los tres métodos coinciden en la práctica


class Logo(QWidget):
    """El logo de la app, pequeño, en el encabezado."""

    def __init__(self, lado=46):
        super().__init__()
        self.setFixedSize(QSize(lado, lado))

    def paintEvent(self, _evento):
        pintor = QPainter(self)
        dibujar_logo(pintor, QRectF(self.rect()))


class VentanaPrincipal(QMainWindow):
    def __init__(self, grafica_3d, grafica_riemann, sonidos, calcular):
        super().__init__()
        self.setWindowTitle("Perímetro de la Ventana de Viviani")
        self.setMinimumSize(1100, 680)
        self.colores = tema.paleta()
        self.setStyleSheet(estilos.hoja_de_estilos(self.colores))

        self.grafica_3d = grafica_3d
        self.grafica_riemann = grafica_riemann
        self.sonidos = sonidos
        self._calcular = calcular
        self._calculo = GestorTareas(self)
        self._quieto = sistema.reducir_movimiento()

        self._construir_interfaz()
        self._conectar()

        self.grafica_riemann.mostrar_funcion(5.0)
        self.campo_radio.setFocus()
        self.campo_radio.selectAll()

    # =====================================================================
    # Construcción
    # =====================================================================
    def _construir_interfaz(self):
        fondo = FondoVentana(self.colores)
        self.setCentralWidget(fondo)
        # Dos capas en la misma celda de la rejilla: abajo, la escena 3D a
        # pantalla completa (la protagonista); encima, todo lo demás flotando.
        capas = QGridLayout(fondo)
        capas.setContentsMargins(0, 0, 0, 0)
        capas.addWidget(self.grafica_3d, 0, 0)
        encima = QWidget()
        capas.addWidget(encima, 0, 0)

        raiz = QVBoxLayout(encima)
        raiz.setContentsMargins(40, 22, 40, 20)
        raiz.setSpacing(0)
        raiz.addLayout(self._crear_encabezado())
        cuerpo = QHBoxLayout()
        cuerpo.addLayout(self._crear_columna_datos())
        cuerpo.addStretch(1)  # el centro queda libre para la esfera
        cuerpo.addLayout(self._crear_columna_resultado())
        raiz.addLayout(cuerpo, 1)

        self.creditos = PanelCreditos(fondo)

    def _crear_encabezado(self):
        titulo = QLabel(TITULO)
        titulo.setFont(fuente(tema.FAMILIAS_TITULO, 22))

        self.boton_creditos = QPushButton("Créditos")
        self.boton_creditos.setObjectName("fantasma")
        self.boton_creditos.setCursor(Qt.CursorShape.PointingHandCursor)
        self.boton_creditos.setToolTip("Integrantes del grupo y herramientas usadas")

        encabezado = QHBoxLayout()
        encabezado.setSpacing(14)
        encabezado.addWidget(Logo())
        encabezado.addWidget(titulo)
        encabezado.addStretch(1)
        encabezado.addWidget(self.boton_creditos, 0, Qt.AlignmentFlag.AlignVCenter)
        return encabezado

    def _crear_columna_datos(self):
        self.bloque_r = CampoLinea(
            self.colores, "Radio de la esfera R", validacion.validar_radio,
            "5", "Ej.: 7.5", unidad="cm",
        )  # fmt: skip
        self.bloque_n = CampoLinea(
            self.colores, "Número de subintervalos n",
            validacion.validar_subintervalos, "10", "Ej.: 1000",
        )  # fmt: skip
        self.campo_radio, self.mensaje_radio = self.bloque_r.caja, self.bloque_r.mensaje
        self.campo_n, self.mensaje_n = self.bloque_n.caja, self.bloque_n.mensaje
        for bloque in (self.bloque_r, self.bloque_n):
            bloque.setFixedWidth(300)

        self.boton_calcular = BotonOrbe(self.colores, self._quieto)
        self.boton_calcular.setToolTip("Calcular el perímetro (Enter)")

        self.boton_exportar = QPushButton(" Exportar curva PNG")
        self.boton_exportar.setObjectName("fantasma")
        self.boton_exportar.setIcon(
            iconos.icono("image-down", self.colores["texto_sec"], 16)
        )
        self.boton_exportar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.boton_exportar.setToolTip("Guardar la curva 3D como imagen PNG (Ctrl+S)")

        columna = QVBoxLayout()
        columna.setSpacing(8)
        columna.addStretch(2)
        columna.addWidget(self.bloque_r)
        columna.addSpacing(6)
        columna.addWidget(self.bloque_n)
        columna.addWidget(self.boton_calcular, 0, Qt.AlignmentFlag.AlignHCenter)
        columna.addStretch(3)
        columna.addWidget(self.boton_exportar, 0, Qt.AlignmentFlag.AlignLeft)
        return columna

    def _crear_columna_resultado(self):
        self.panel_resultado = PanelResultado(self.colores, self._quieto)
        self.panel_resultado.setFixedWidth(360)
        # La suma de Riemann va compacta, abajo a la derecha
        self.grafica_riemann.setFixedSize(520, 300)

        columna = QVBoxLayout()
        columna.setSpacing(0)
        columna.addStretch(2)
        columna.addWidget(self.panel_resultado, 0, Qt.AlignmentFlag.AlignRight)
        columna.addStretch(1)
        columna.addWidget(self.grafica_riemann, 0, Qt.AlignmentFlag.AlignRight)
        # Atajos a las etiquetas de resultado (los usan las pruebas)
        pr = self.panel_resultado
        self.etiqueta_perimetro = pr.etiqueta_perimetro
        self.etiqueta_control = pr.etiqueta_control
        self.etiqueta_error_abs = pr.etiqueta_error_abs
        self.etiqueta_error_rel = pr.etiqueta_error_rel
        return columna

    def _actualizar_zona_3d(self):
        """La esfera se centra en el hueco libre entre las dos columnas."""
        g = self.grafica_3d

        def en_3d(widget):
            esquina = g.mapFromGlobal(widget.mapToGlobal(widget.rect().topLeft()))
            return QRectF(esquina.x(), esquina.y(), widget.width(), widget.height())

        izquierda = max(en_3d(self.bloque_r).right(), en_3d(self.bloque_n).right())
        derecha = min(en_3d(self.panel_resultado).left(),
                      en_3d(self.grafica_riemann).left())  # fmt: skip
        arriba = en_3d(self.boton_creditos).bottom()
        abajo = g.height() - 20
        margen = 24
        g.establecer_zona(
            QRectF(
                izquierda + margen,
                arriba,
                derecha - izquierda - 2 * margen,
                abajo - arriba,
            )  # fmt: skip
        )

    def resizeEvent(self, evento):
        super().resizeEvent(evento)
        # Se espera a que los diseños terminen de acomodarse
        QTimer.singleShot(0, self._actualizar_zona_3d)

    def showEvent(self, evento):
        super().showEvent(evento)
        QTimer.singleShot(0, self._actualizar_zona_3d)

    def _conectar(self):
        self.boton_calcular.clicked.connect(self.calcular_ahora)
        self.boton_exportar.clicked.connect(self._exportar_3d)
        self.boton_creditos.clicked.connect(self.creditos.abrir)
        for caja in (self.campo_radio, self.campo_n):
            caja.returnPressed.connect(self.calcular_ahora)

        self._calculo.progreso.connect(self._al_avanzar)
        self._calculo.terminado.connect(self._al_terminar)
        self._calculo.cancelado.connect(self._ocultar_progreso)
        self._calculo.fallo.connect(self._al_fallar)

        self._temporizador_progreso = QTimer(self, singleShot=True)
        self._temporizador_progreso.setInterval(RETARDO_PROGRESO_MS)
        self._temporizador_progreso.timeout.connect(self._mostrar_progreso)
        self._progreso_visible = False

        QShortcut(QKeySequence(Qt.Key.Key_Escape), self, self._al_pulsar_escape)
        QShortcut(QKeySequence("Ctrl+S"), self, self._exportar_3d)

        # El orbe y el fondo reaccionan al cursor: se revisa su posición
        # unas 30 veces por segundo.
        self._vigia_cursor = QTimer(self)
        self._vigia_cursor.setInterval(INTERVALO_CURSOR_MS)
        self._vigia_cursor.timeout.connect(self._revisar_cursor)
        self._vigia_cursor.start()

        # Un clic en cualquier parte salta las animaciones
        QApplication.instance().installEventFilter(self)

    # =====================================================================
    # Cálculo
    # =====================================================================
    def calcular_ahora(self):
        radio = self.bloque_r.validar_y_mostrar()
        n = self.bloque_n.validar_y_mostrar()
        if radio is None or n is None:
            self.sonidos.error()
            primero = self.campo_radio if radio is None else self.campo_n
            primero.setFocus()
            primero.selectAll()
            return

        self._saltar_animaciones()
        self.sonidos.clic()
        self._calculo.lanzar(
            lambda progreso, cancelado: self._calcular(
                radio, n, METODO, progreso, cancelado
            )
        )
        self._temporizador_progreso.start()

    def _mostrar_progreso(self):
        if self._calculo.en_curso():
            self._progreso_visible = True
            self.boton_calcular.establecer_progreso(0.0)

    def _al_avanzar(self, porcentaje):
        if self._progreso_visible:
            self.boton_calcular.establecer_progreso(porcentaje / 100)

    def _ocultar_progreso(self):
        self._temporizador_progreso.stop()
        self._progreso_visible = False
        self.boton_calcular.establecer_progreso(None)

    def _al_terminar(self, resultado):
        self._ocultar_progreso()
        reducir = sistema.reducir_movimiento()
        self.panel_resultado.mostrar_resultado(resultado, animar=not reducir)
        self.sonidos.resultado()
        self.grafica_3d.mostrar(resultado.radio)
        self.grafica_riemann.mostrar_resultado(
            resultado, animar=True, reducir_movimiento=reducir
        )
        # Para encadenar cálculos: el texto del campo queda seleccionado
        foco = QApplication.focusWidget()
        if foco in (self.campo_radio, self.campo_n):
            foco.selectAll()

    def _al_fallar(self, mensaje):
        self._ocultar_progreso()
        self.panel_resultado.mostrar_error(mensaje)
        self.sonidos.error()

    # =====================================================================
    # Animaciones, teclado y mouse
    # =====================================================================
    def _hay_animacion(self):
        return (
            self.grafica_riemann.esta_animando() or self.panel_resultado.esta_animando()
        )

    def _saltar_animaciones(self):
        self.grafica_riemann.saltar_animacion()
        self.panel_resultado.saltar_animacion()

    def _al_pulsar_escape(self):
        if self.creditos.isVisible():
            self.creditos.cerrar()
        elif self._calculo.en_curso():
            self._calculo.cancelar()
        else:
            self._saltar_animaciones()

    def _revisar_cursor(self):
        fondo = self.centralWidget()
        if not self.isActiveWindow():
            fondo.mover_luz(None)
            return
        cursor = QCursor.pos()
        fondo.mover_luz(fondo.mapFromGlobal(cursor))
        self.boton_calcular.acercar(cursor)

    def eventFilter(self, objeto, evento):
        if (
            evento.type() == QEvent.Type.MouseButtonPress
            and self._hay_animacion()
            and isinstance(objeto, QWidget)
            and objeto.window() is self
        ):
            self._saltar_animaciones()  # el clic sigue haciendo lo suyo
        return False

    # =====================================================================
    # Exportar
    # =====================================================================
    def _exportar_3d(self):
        carpeta = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.PicturesLocation
        )
        sugerido = str(Path(carpeta) / self.grafica_3d.nombre_sugerido())
        ruta, _filtro = QFileDialog.getSaveFileName(
            self, "Guardar imagen", sugerido, "Imagen PNG (*.png)"
        )
        if not ruta:
            return
        try:
            self.grafica_3d.exportar(ruta)
        except Exception:  # disco lleno, sin permiso, etc.
            self._avisar_en_boton(" No se pudo guardar")
            self.sonidos.error()
            return
        self._avisar_en_boton(" Imagen guardada")
        self.sonidos.clic()

    def _avisar_en_boton(self, texto):
        """Cambia un momento el texto del botón Exportar."""
        self.boton_exportar.setText(texto)
        QTimer.singleShot(
            DURACION_AVISO_MS, lambda: self.boton_exportar.setText(" Exportar PNG")
        )

    # =====================================================================
    # Cierre
    # =====================================================================
    def closeEvent(self, evento):
        self._vigia_cursor.stop()
        QApplication.instance().removeEventFilter(self)
        self._calculo.cerrar()
        self.sonidos.cerrar()
        super().closeEvent(evento)
