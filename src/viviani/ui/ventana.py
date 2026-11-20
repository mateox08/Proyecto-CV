"""Ventana principal: une los campos, el resultado y las dos gráficas.

La ventana NO calcula, ni dibuja gráficas, ni fabrica sonidos: recibe esas
piezas ya hechas en el constructor (ver app.py) y solo coordina:

    escribir R y n -> validar -> calcular en un hilo -> mostrar -> animar

Distribución:

    +------------------------------------------------------------------+
    | Ventana de Viviani                                               |
    | PERÍMETRO · SUMA DE RIEMANN                                      |
    +-------------+-------------------------+--------------------------+
    | DATOS       | CURVA EN 3D  [Exportar] | SUMA DE RIEMANN          |
    |  R  [   ]   |                         |                          |
    |  n  [   ]   |   esfera girando        |   f(t) y rectángulos     |
    | [Calcular]  |                         |                          |
    +-------------+                         |                          |
    | RESULTADO   |                         |                          |
    +-------------+-------------------------+--------------------------+
"""

from pathlib import Path

from PySide6.QtCore import QEvent, QStandardPaths, Qt, QTimer
from PySide6.QtGui import QCursor, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from viviani import tema, validacion
from viviani.ui import estilos, sistema
from viviani.ui.componentes import (
    BotonBrillante,
    CampoNumerico,
    FondoVentana,
    Tarjeta,
    fuente,
)
from viviani.ui.resultado import TarjetaResultado
from viviani.ui.trabajador import GestorTareas

TITULO = "Ventana de Viviani"
RETARDO_PROGRESO_MS = 300  # la barra de progreso solo aparece si tarda más
INTERVALO_CURSOR_MS = 33  # cada cuánto se revisa dónde está el cursor
DURACION_AVISO_MS = 2500  # "Imagen guardada"
METODO = "punto_medio"  # en esta curva los tres métodos coinciden en la práctica


class VentanaPrincipal(QMainWindow):
    def __init__(self, grafica_3d, grafica_riemann, sonidos, calcular):
        super().__init__()
        self.setWindowTitle("Perímetro de la Ventana de Viviani")
        self.setMinimumSize(1024, 640)
        self.colores = tema.paleta()
        self.setStyleSheet(estilos.hoja_de_estilos(self.colores))

        self.grafica_3d = grafica_3d
        self.grafica_riemann = grafica_riemann
        self.sonidos = sonidos
        self._calcular = calcular
        self._calculo = GestorTareas(self)

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
        raiz = QVBoxLayout(fondo)
        raiz.setContentsMargins(22, 16, 22, 16)
        raiz.setSpacing(6)

        raiz.addLayout(self._crear_encabezado())
        cuerpo = QHBoxLayout()
        cuerpo.setSpacing(0)  # las tarjetas ya traen su margen para el halo
        cuerpo.addLayout(self._crear_columna_izquierda())
        cuerpo.addWidget(self._crear_tarjeta_3d(), 6)
        cuerpo.addWidget(self._crear_tarjeta_riemann(), 5)
        raiz.addLayout(cuerpo, 1)

    def _crear_encabezado(self):
        titulo = QLabel(TITULO)
        titulo.setFont(fuente(tema.FAMILIAS_TITULO, 26))
        subtitulo = QLabel("PERÍMETRO  ·  SUMA DE RIEMANN")
        subtitulo.setFont(fuente(tema.FAMILIAS_MONO, 9, espaciado=3))
        subtitulo.setProperty("rol", "etiqueta")
        encabezado = QVBoxLayout()
        encabezado.setContentsMargins(12, 0, 0, 4)
        encabezado.setSpacing(0)
        encabezado.addWidget(titulo)
        encabezado.addWidget(subtitulo)
        return encabezado

    def _crear_columna_izquierda(self):
        columna = QVBoxLayout()
        columna.setSpacing(0)
        columna.addWidget(self._crear_tarjeta_datos())
        self.tarjeta_resultado = TarjetaResultado(self.colores)
        columna.addWidget(self.tarjeta_resultado, 1)
        # Atajos a las etiquetas de resultado (los usan las pruebas)
        tr = self.tarjeta_resultado
        self.etiqueta_perimetro = tr.etiqueta_perimetro
        self.etiqueta_control = tr.etiqueta_control
        self.etiqueta_error_abs = tr.etiqueta_error_abs
        self.etiqueta_error_rel = tr.etiqueta_error_rel
        return columna

    def _crear_tarjeta_datos(self):
        tarjeta = Tarjeta(self.colores, "Datos")
        tarjeta.setFixedWidth(380)

        self.bloque_r = CampoNumerico(
            self.colores, "Radio de la esfera R", validacion.validar_radio,
            "5", "Ej.: 7.5", unidad="cm",
        )  # fmt: skip
        self.bloque_n = CampoNumerico(
            self.colores, "Número de subintervalos n",
            validacion.validar_subintervalos, "10", "Ej.: 1000",
        )  # fmt: skip
        self.campo_radio, self.mensaje_radio = self.bloque_r.caja, self.bloque_r.mensaje
        self.campo_n, self.mensaje_n = self.bloque_n.caja, self.bloque_n.mensaje
        tarjeta.contenido.addWidget(self.bloque_r)
        tarjeta.contenido.addWidget(self.bloque_n)

        self.boton_calcular = BotonBrillante(self.colores, "Calcular", "calculator")
        self.boton_calcular.setToolTip("Calcular el perímetro (Enter)")
        tarjeta.contenido.addWidget(self.boton_calcular)

        # Progreso: fila de altura fija para que nada se mueva al aparecer
        fila = QWidget()
        fila.setFixedHeight(24)
        diseno = QHBoxLayout(fila)
        diseno.setContentsMargins(12, 0, 12, 0)
        self.barra_progreso = QProgressBar()
        self.barra_progreso.setTextVisible(False)
        self.boton_cancelar = QPushButton("Cancelar")
        self.boton_cancelar.setObjectName("enlace")
        self.boton_cancelar.setFont(fuente(tema.FAMILIAS_MONO, 9))
        self.boton_cancelar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.boton_cancelar.setToolTip("Detener el cálculo (Esc)")
        diseno.addWidget(self.barra_progreso, 1)
        diseno.addWidget(self.boton_cancelar)
        self._mostrar_progreso(False)
        tarjeta.contenido.addWidget(fila)
        return tarjeta

    def _crear_tarjeta_3d(self):
        tarjeta = Tarjeta(self.colores, "Curva en 3D")
        self.boton_exportar = BotonBrillante(
            self.colores, "Exportar PNG", "image-down", variante="secundario"
        )
        self.boton_exportar.setToolTip("Guardar la curva como imagen PNG (Ctrl+S)")
        tarjeta.cabecera.addWidget(self.boton_exportar)
        tarjeta.contenido.addWidget(self.grafica_3d, 1)
        return tarjeta

    def _crear_tarjeta_riemann(self):
        tarjeta = Tarjeta(self.colores, "Suma de Riemann")
        tarjeta.contenido.addWidget(self.grafica_riemann, 1)
        return tarjeta

    def _conectar(self):
        self.boton_calcular.clicked.connect(self.calcular_ahora)
        self.boton_cancelar.clicked.connect(self._calculo.cancelar)
        self.boton_exportar.clicked.connect(self._exportar_3d)
        for caja in (self.campo_radio, self.campo_n):
            caja.returnPressed.connect(self.calcular_ahora)

        self._calculo.progreso.connect(self.barra_progreso.setValue)
        self._calculo.terminado.connect(self._al_terminar)
        self._calculo.cancelado.connect(lambda: self._mostrar_progreso(False))
        self._calculo.fallo.connect(self._al_fallar)

        self._temporizador_progreso = QTimer(self, singleShot=True)
        self._temporizador_progreso.setInterval(RETARDO_PROGRESO_MS)
        self._temporizador_progreso.timeout.connect(
            lambda: self._mostrar_progreso(self._calculo.en_curso())
        )

        QShortcut(QKeySequence(Qt.Key.Key_Escape), self, self._al_pulsar_escape)
        QShortcut(QKeySequence("Ctrl+S"), self, self._exportar_3d)

        # Los botones brillan según la distancia al cursor: se revisa la
        # posición del cursor unas 30 veces por segundo.
        self._botones = [self.boton_calcular, self.boton_exportar]
        self._vigia_cursor = QTimer(self)
        self._vigia_cursor.setInterval(INTERVALO_CURSOR_MS)
        self._vigia_cursor.timeout.connect(self._revisar_cursor)
        self._vigia_cursor.start()

        # Un clic en cualquier parte salta la animación de los rectángulos
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
        self.barra_progreso.setValue(0)
        self._calculo.lanzar(
            lambda progreso, cancelado: self._calcular(
                radio, n, METODO, progreso, cancelado
            )
        )
        self._temporizador_progreso.start()

    def _al_terminar(self, resultado):
        self._mostrar_progreso(False)
        reducir = sistema.reducir_movimiento()
        self.tarjeta_resultado.mostrar_resultado(resultado, animar=not reducir)
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
        self._mostrar_progreso(False)
        self.tarjeta_resultado.mostrar_error(mensaje)
        self.sonidos.error()

    def _mostrar_progreso(self, visible):
        self.barra_progreso.setVisible(visible)
        self.boton_cancelar.setVisible(visible)

    # =====================================================================
    # Animaciones, teclado y mouse
    # =====================================================================
    def _hay_animacion(self):
        return (
            self.grafica_riemann.esta_animando()
            or self.tarjeta_resultado.esta_animando()
        )

    def _saltar_animaciones(self):
        self.grafica_riemann.saltar_animacion()
        self.tarjeta_resultado.saltar_animacion()

    def _al_pulsar_escape(self):
        if self._calculo.en_curso():
            self._calculo.cancelar()
        else:
            self._saltar_animaciones()

    def _revisar_cursor(self):
        if not self.isActiveWindow():
            return
        cursor = QCursor.pos()
        for boton in self._botones:
            boton.acercar(cursor)

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
            self._avisar_en_boton("No se pudo guardar")
            self.sonidos.error()
            return
        self._avisar_en_boton("Imagen guardada")
        self.sonidos.clic()

    def _avisar_en_boton(self, texto):
        """Cambia un momento el texto del botón Exportar."""
        self.boton_exportar.setText(texto)
        self.boton_exportar.updateGeometry()
        QTimer.singleShot(DURACION_AVISO_MS, self._restaurar_boton_exportar)

    def _restaurar_boton_exportar(self):
        self.boton_exportar.setText("Exportar PNG")
        self.boton_exportar.updateGeometry()

    # =====================================================================
    # Cierre
    # =====================================================================
    def closeEvent(self, evento):
        self._vigia_cursor.stop()
        QApplication.instance().removeEventFilter(self)
        self._calculo.cerrar()
        self.sonidos.cerrar()
        super().closeEvent(evento)
