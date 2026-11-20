"""Ventana principal: une los campos, el resultado y las dos gráficas.

La ventana NO calcula, ni dibuja gráficas, ni fabrica sonidos: recibe esas
piezas ya hechas en el constructor (ver app.py) y solo coordina:

    escribir R y n -> validar -> calcular en un hilo -> mostrar -> animar

Distribución (sin recuadros: todo flota sobre el fondo de puntos):

    [logo] Ventana de Viviani                         L = 7.640395578 · R
           PERÍMETRO · SUMA DE RIEMANN

    RADIO R            .-""-.                     PERÍMETRO APROXIMADO
    ____40______ cm   (  3D  )  girando            305.615823 cm
    SUBINTERVALOS n    '-..-'                      ───────────────
    ____10______                                   VALOR DE CONTROL ...
       ( ∫ )  orbe "Calcular"         [PNG]        ERROR ABSOLUTO   ...
    ──────────────────────── línea ────────────────────────
    gráfica de la suma de Riemann, a todo lo ancho
"""

from pathlib import Path

from PySide6.QtCore import QEvent, QRectF, QSize, QStandardPaths, Qt, QTimer
from PySide6.QtGui import QCursor, QKeySequence, QPainter, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
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
    Separador,
    fuente,
)
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
        raiz = QVBoxLayout(fondo)
        raiz.setContentsMargins(40, 22, 40, 14)
        raiz.setSpacing(10)

        raiz.addLayout(self._crear_encabezado())
        cuerpo = QHBoxLayout()
        cuerpo.setSpacing(28)
        cuerpo.addLayout(self._crear_columna_datos())
        cuerpo.addLayout(self._crear_centro(), 1)
        cuerpo.addWidget(self._crear_columna_resultado())
        raiz.addLayout(cuerpo, 12)
        raiz.addWidget(Separador())
        raiz.addWidget(self.grafica_riemann, 7)

    def _crear_encabezado(self):
        titulo = QLabel(TITULO)
        titulo.setFont(fuente(tema.FAMILIAS_TITULO, 22))
        subtitulo = QLabel("PERÍMETRO  ·  SUMA DE RIEMANN")
        subtitulo.setFont(fuente(tema.FAMILIAS_MONO, 8.5, espaciado=3))
        subtitulo.setProperty("rol", "etiqueta")
        textos = QVBoxLayout()
        textos.setSpacing(0)
        textos.addWidget(titulo)
        textos.addWidget(subtitulo)

        chip = QLabel("L = 4√2 · R · E(½) ≈ 7.640395578 · R")
        chip.setObjectName("chip")
        chip.setFont(fuente(tema.FAMILIAS_MONO, 9))
        chip.setToolTip("Valor de control del perímetro")

        encabezado = QHBoxLayout()
        encabezado.setSpacing(14)
        encabezado.addWidget(Logo())
        encabezado.addLayout(textos)
        encabezado.addStretch(1)
        encabezado.addWidget(chip, 0, Qt.AlignmentFlag.AlignVCenter)
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

        columna = QVBoxLayout()
        columna.setSpacing(8)
        columna.addStretch(1)
        columna.addWidget(self.bloque_r)
        columna.addSpacing(6)
        columna.addWidget(self.bloque_n)
        columna.addWidget(self.boton_calcular, 0, Qt.AlignmentFlag.AlignHCenter)
        columna.addStretch(1)
        return columna

    def _crear_centro(self):
        self.boton_exportar = QPushButton(" Exportar PNG")
        self.boton_exportar.setObjectName("fantasma")
        self.boton_exportar.setIcon(
            iconos.icono("image-down", self.colores["texto_sec"], 16)
        )
        self.boton_exportar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.boton_exportar.setToolTip("Guardar la curva 3D como imagen PNG (Ctrl+S)")

        pie = QHBoxLayout()
        pie.addStretch(1)
        pie.addWidget(self.boton_exportar)
        centro = QVBoxLayout()
        centro.setSpacing(0)
        centro.addWidget(self.grafica_3d, 1)
        centro.addLayout(pie)
        return centro

    def _crear_columna_resultado(self):
        self.panel_resultado = PanelResultado(self.colores, self._quieto)
        self.panel_resultado.setFixedWidth(360)
        contenedor = QWidget()
        diseno = QVBoxLayout(contenedor)
        diseno.setContentsMargins(0, 0, 0, 0)
        diseno.addStretch(1)
        diseno.addWidget(self.panel_resultado)
        diseno.addStretch(1)
        # Atajos a las etiquetas de resultado (los usan las pruebas)
        pr = self.panel_resultado
        self.etiqueta_perimetro = pr.etiqueta_perimetro
        self.etiqueta_control = pr.etiqueta_control
        self.etiqueta_error_abs = pr.etiqueta_error_abs
        self.etiqueta_error_rel = pr.etiqueta_error_rel
        return contenedor

    def _conectar(self):
        self.boton_calcular.clicked.connect(self.calcular_ahora)
        self.boton_exportar.clicked.connect(self._exportar_3d)
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
        if self._calculo.en_curso():
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
