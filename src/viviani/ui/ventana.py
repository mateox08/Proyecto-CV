"""Ventana principal: une los campos, el resultado y las tres gráficas.

La ventana NO calcula ni dibuja gráficas ni suena: recibe esas piezas ya
hechas en el constructor (ver app.py) y solo coordina:

    escribir R y n -> validar -> calcular en un hilo -> mostrar -> animar

Diseño y textos: docs/DISENO.md (secciones 1, 3, 4, 5 y 6).
"""

from pathlib import Path

from PySide6.QtCore import QEvent, QSettings, QStandardPaths, Qt, QTimer
from PySide6.QtGui import QGuiApplication, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QAbstractButton,
    QApplication,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from viviani import NOMBRE_APP, tema, validacion
from viviani.formato import formatear_entero
from viviani.ui import estilos, iconos, sistema
from viviani.ui.componentes import (
    Banda,
    BotonSecundario,
    CampoNumerico,
    ConAnillo,
    Interruptor,
    SelectorMetodo,
    Tarjeta,
    TarjetaGrafica,
    etiqueta,
    repulir,
)
from viviani.ui.resultado import TarjetaResultado
from viviani.ui.trabajador import GestorTareas

ANCHO_REJILLA = 1280  # desde este ancho (DIP) las tres gráficas se ven a la vez
RETARDO_PROGRESO_MS = 300  # la barra de progreso solo aparece si tarda más
DURACION_EXITO_MS = 6000  # cuánto se ve "Imagen guardada en: ..."
SANGRIA_PROGRESO = 4  # alinea la barra con los bordes de los campos
RECTANGULOS_MAXIMOS = 120  # lo que dibuja la gráfica de Riemann (DISENO 6.3)

ESTADOS_ICONO = {"exito": "circle-check", "error": "circle-alert"}


class VentanaPrincipal(QMainWindow):
    def __init__(self, grafica_3d, grafica_riemann, grafica_convergencia, sonidos,
                 calcular, datos_convergencia, ajustes=None):  # fmt: skip
        super().__init__()
        self.setWindowTitle(NOMBRE_APP)
        self.setMinimumSize(1024, 640)

        self.grafica_3d = grafica_3d
        self.grafica_riemann = grafica_riemann
        self.grafica_convergencia = grafica_convergencia
        self.sonidos = sonidos
        self._calcular = calcular
        self._datos_convergencia = datos_convergencia
        self._ajustes = ajustes or QSettings("ESPOL", "PerimetroViviani")

        self._escala = sistema.factor_de_texto()
        self._colores = tema.paleta(False)
        self._oscuro = False
        self._ultimo = None  # último Resultado mostrado (None si no hay)
        self._pendiente_convergencia = None  # (resultado, reducir_movimiento)
        self._modo_pestanas = None
        self._tematizables = []  # piezas que repintan sus iconos al cambiar de tema

        self._calculo = GestorTareas(self)
        self._datos = GestorTareas(self)
        self._temporizador_progreso = QTimer(self)
        self._temporizador_progreso.setSingleShot(True)
        self._temporizador_progreso.setInterval(RETARDO_PROGRESO_MS)
        self._temporizador_estado = QTimer(self)
        self._temporizador_estado.setSingleShot(True)

        self._construir_interfaz()
        self._crear_atajos()
        self._conectar_senales()
        self._adaptar_a_ancho(ANCHO_REJILLA)  # empieza en rejilla; resizeEvent ajusta
        self._recordar_sonido()

        esquema = QGuiApplication.styleHints().colorScheme()
        self.aplicar_modo(esquema == Qt.ColorScheme.Dark)
        self._mostrar_vista_previa()
        self._pedir_datos_de_convergencia()

        # Filtro de toda la aplicación: Enter, y clic para saltar animaciones.
        QApplication.instance().installEventFilter(self)
        self.campo_radio.setFocus()
        self.campo_radio.selectAll()

    # =====================================================================
    # Construcción
    # =====================================================================
    def _construir_interfaz(self):
        raiz = QWidget()
        raiz.setObjectName("raiz")
        self.setCentralWidget(raiz)
        self._diseno_raiz = QVBoxLayout(raiz)
        self._diseno_raiz.setContentsMargins(0, 0, 0, 0)
        self._diseno_raiz.setSpacing(0)

        self._diseno_raiz.addWidget(self._crear_barra_superior())
        self._diseno_cuerpo = QHBoxLayout()
        self._diseno_cuerpo.setSpacing(0)  # 12 de la columna + 4 de anillo = 16 DIP
        self._diseno_cuerpo.addWidget(self._crear_columna_izquierda())
        self._diseno_cuerpo.addWidget(self._crear_zona_graficas(), 1)
        self._diseno_raiz.addLayout(self._diseno_cuerpo, 1)

        self._crear_barra_de_estado()
        self._aplicar_margen(24)

    def _crear_barra_superior(self):
        barra = QWidget()
        barra.setMinimumHeight(56)
        self._diseno_barra = QHBoxLayout(barra)
        textos = QVBoxLayout()
        textos.setSpacing(0)
        textos.addWidget(etiqueta(NOMBRE_APP, "titulo_app", sangria=False))
        textos.addWidget(
            etiqueta("Aproximación con suma de Riemann", "subtitulo", sangria=False)
        )
        self._diseno_barra.addLayout(textos, 1)

        self.interruptor_sonido = Interruptor()
        self.interruptor_sonido.setText("Sonido: activado")
        self.interruptor_sonido.setAccessibleName("Sonido")
        self.interruptor_sonido.setToolTip("Activar o desactivar los sonidos (M)")
        self._tematizables.append(self.interruptor_sonido)
        self._diseno_barra.addWidget(
            ConAnillo(self.interruptor_sonido, solo_teclado=True)
        )
        return barra

    # --- columna izquierda ------------------------------------------------
    def _crear_columna_izquierda(self):
        contenido = QWidget()
        diseno = QVBoxLayout(contenido)
        diseno.setContentsMargins(0, 4, 0, 4)  # 4 DIP: lo que añade el anillo arriba
        diseno.setSpacing(12)
        diseno.addWidget(self._crear_tarjeta_datos())
        self.tarjeta_resultado = TarjetaResultado(self._escala)
        self._tematizables.append(self.tarjeta_resultado)
        self.etiqueta_perimetro = self.tarjeta_resultado.etiqueta_perimetro
        self.etiqueta_control = self.tarjeta_resultado.etiqueta_control
        self.etiqueta_error_abs = self.tarjeta_resultado.etiqueta_error_abs
        self.etiqueta_error_rel = self.tarjeta_resultado.etiqueta_error_rel
        diseno.addWidget(self.tarjeta_resultado)
        diseno.addWidget(self._crear_tarjeta_opciones())
        diseno.addStretch(1)

        desplazable = QScrollArea()
        desplazable.setWidgetResizable(True)
        desplazable.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        desplazable.setFrameShape(QScrollArea.Shape.NoFrame)
        # El marco desplazable no es una parada de Tab; al enfocar un control
        # interior, QScrollArea lo desplaza hasta dejarlo visible.
        desplazable.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        desplazable.setWidget(contenido)
        # El fondo transparente deja ver el color de la ventana.
        desplazable.viewport().setAutoFillBackground(False)
        contenido.setAutoFillBackground(False)
        ancho = min(480, max(360, round(360 * self._escala)))
        # 12 DIP extra: ahí cae la barra de desplazamiento cuando hace falta, así
        # el ancho útil de las tarjetas no cambia (y el texto no se re-acomoda).
        desplazable.setFixedWidth(ancho + 12)
        contenido.setMaximumWidth(ancho)
        desplazable.setAccessibleName("Datos, resultado y opciones")
        self.columna_izquierda = desplazable
        return desplazable

    def _crear_tarjeta_datos(self):
        tarjeta = Tarjeta("Datos")
        tarjeta.diseno.setSpacing(6)
        self.bloque_r = CampoNumerico(
            "Radio de la esfera R", validacion.validar_radio, "5", "Ej.: 5 o 7,5",
            "Número real positivo. Acepta coma o punto decimal.",
            "Radio de la esfera en centímetros",
            "Radio de la esfera R, en centímetros", sufijo="cm",
        )  # fmt: skip
        self.bloque_n = CampoNumerico(
            "Número de subintervalos n", validacion.validar_subintervalos, "10",
            "Ej.: 1000", "Número entero entre 1 y 10 000 000.",
            "Cantidad de rectángulos de la suma de Riemann",
            "Número de subintervalos n",
        )  # fmt: skip
        self.campo_radio = self.bloque_r.entrada
        self.campo_n = self.bloque_n.entrada
        self.mensaje_radio = self.bloque_r.mensaje
        self.mensaje_n = self.bloque_n.mensaje
        self._tematizables += [self.bloque_r, self.bloque_n]
        tarjeta.diseno.addWidget(self.bloque_r)
        tarjeta.diseno.addWidget(self.bloque_n)

        self.boton_calcular = QPushButton("Calcular")
        self.boton_calcular.setObjectName("primario")
        self.boton_calcular.setToolTip("Calcular el perímetro (Enter)")
        self.boton_calcular.setAccessibleName("Calcular")
        self.boton_calcular.setCursor(Qt.CursorShape.PointingHandCursor)
        self.boton_cancelar = BotonSecundario(
            "Cancelar", "square", "Detener el cálculo (Esc)"
        )
        self._tematizables.append(self.boton_cancelar)
        self._anillo_cancelar = ConAnillo(self.boton_cancelar, solo_teclado=True)

        fila = QHBoxLayout()
        fila.setSpacing(0)
        fila.addWidget(ConAnillo(self.boton_calcular, solo_teclado=True))
        fila.addWidget(self._anillo_cancelar)
        fila.addStretch(1)
        tarjeta.diseno.addLayout(fila)

        self.barra_progreso = QProgressBar()
        self.barra_progreso.setRange(0, 100)
        self.barra_progreso.setTextVisible(False)
        self.etiqueta_progreso = etiqueta("Calculando… 0 %", "progreso", sangria=False)
        # Ancho fijo para que la barra no "baile" al pasar de 9 % a 100 %.
        self.etiqueta_progreso.setMinimumWidth(
            self.etiqueta_progreso.fontMetrics().horizontalAdvance("Calculando… 100 %")
        )
        self.panel_progreso = QWidget()
        interior = QHBoxLayout(self.panel_progreso)
        interior.setContentsMargins(SANGRIA_PROGRESO, 0, SANGRIA_PROGRESO, 0)
        interior.setSpacing(12)
        interior.addWidget(self.barra_progreso, 1)
        interior.addWidget(self.etiqueta_progreso)
        politica = self.panel_progreso.sizePolicy()
        politica.setRetainSizeWhenHidden(True)  # no empuja el resto al aparecer
        self.panel_progreso.setSizePolicy(politica)
        tarjeta.diseno.addWidget(self.panel_progreso)
        self._mostrar_progreso(False)
        return tarjeta

    def _crear_tarjeta_opciones(self):
        tarjeta = Tarjeta("Opciones")
        tarjeta.diseno.addWidget(etiqueta("Método de la suma", "etiqueta_campo"))
        self.selector_metodo = SelectorMetodo()
        tarjeta.diseno.addWidget(self.selector_metodo)
        tarjeta.diseno.addWidget(
            etiqueta(
                "En esta curva, izquierda y derecha dan el mismo resultado "
                "porque f(0) = f(2π).",
                "ayuda",
                palabras=True,
            )  # fmt: skip
        )
        return tarjeta

    # --- gráficas -----------------------------------------------------------
    def _crear_zona_graficas(self):
        self._boton_restablecer = BotonSecundario(
            "Restablecer vista", "rotate-ccw",
            "Volver al ángulo de vista inicial (Ctrl+0)",
        )  # fmt: skip
        self._botones_exportar = [
            BotonSecundario(
                "Exportar PNG",
                "image-down",
                f"Guardar esta gráfica como imagen PNG de alta resolución "
                f"(Ctrl+Mayús+{numero})",
            )  # fmt: skip
            for numero in (1, 2, 3)
        ]
        self._tematizables += [self._boton_restablecer, *self._botones_exportar]

        self.tarjeta_3d = TarjetaGrafica(
            "Curva en 3D", self.grafica_3d,
            [self._boton_restablecer, self._botones_exportar[0]],
        )  # fmt: skip
        self.tarjeta_riemann = TarjetaGrafica(
            "Suma de Riemann", self.grafica_riemann, [self._botones_exportar[1]]
        )
        self.tarjeta_convergencia = TarjetaGrafica(
            "Convergencia", self.grafica_convergencia, [self._botones_exportar[2]]
        )
        self._tarjetas = [
            self.tarjeta_3d,
            self.tarjeta_riemann,
            self.tarjeta_convergencia,
        ]
        self._nombres_pestanas = ["Curva en 3D", "Suma de Riemann", "Convergencia"]

        self.tarjeta_3d.agregar_pie(
            etiqueta(
                "Arrastre para rotar · Con la gráfica enfocada, use las flechas.",
                "sugerencia",
                sangria=False,
            )  # fmt: skip
        )
        self.banda_muestra = Banda("aviso", "triangle-alert", "aviso")
        self.banda_muestra.setVisible(False)
        self.tarjeta_riemann.agregar_pie(self.banda_muestra)
        self._tematizables.append(self.banda_muestra)

        # Dos presentaciones de las mismas tres tarjetas: rejilla o pestañas.
        self._rejilla = QWidget()
        self._diseno_rejilla = QGridLayout(self._rejilla)
        self._diseno_rejilla.setContentsMargins(0, 0, 0, 0)
        self._diseno_rejilla.setSpacing(8)  # + 8 de anillos = 16 DIP visibles
        self._diseno_rejilla.setColumnStretch(0, 1)
        self._diseno_rejilla.setColumnStretch(1, 1)
        self._diseno_rejilla.setRowStretch(0, 55)
        self._diseno_rejilla.setRowStretch(1, 45)
        self._pestanas = QTabWidget()
        self._pestanas.setDocumentMode(True)
        self._pestanas.setAccessibleName("Gráficas")

        self._zona = QStackedWidget()
        self._zona.addWidget(self._rejilla)
        self._zona.addWidget(self._pestanas)
        return self._zona

    def _crear_barra_de_estado(self):
        self.icono_estado = QLabel()
        self.icono_estado.setFixedSize(16, 16)
        self.etiqueta_estado = etiqueta("", "estado_normal", sangria=False)
        barra = self.statusBar()
        barra.setSizeGripEnabled(False)
        barra.addWidget(self.icono_estado)
        barra.addWidget(self.etiqueta_estado, 1)
        self.icono_estado.setVisible(False)

    # =====================================================================
    # Atajos y señales
    # =====================================================================
    def _crear_atajos(self):
        def atajo(secuencia, accion):
            QShortcut(QKeySequence(secuencia), self, activated=accion)

        atajo("Esc", self._al_pulsar_escape)
        # M solo actúa fuera de los campos de texto: ahí la tecla escribe "m".
        atajo("M", self.interruptor_sonido.click)
        atajo("Ctrl+M", self.interruptor_sonido.click)
        atajo("Ctrl+0", self.grafica_3d.restablecer_vista)
        for indice in range(3):
            atajo(f"Ctrl+Shift+{indice + 1}", lambda i=indice: self._exportar(i))
            atajo(f"Ctrl+{indice + 1}", lambda i=indice: self._mostrar_pestana(i))

    def _conectar_senales(self):
        self.boton_calcular.clicked.connect(self.calcular_ahora)
        self.boton_cancelar.clicked.connect(self._cancelar_calculo)
        self.selector_metodo.metodo_cambiado.connect(self._al_cambiar_metodo)
        self.interruptor_sonido.toggled.connect(self._al_alternar_sonido)
        self._boton_restablecer.clicked.connect(self.grafica_3d.restablecer_vista)
        for indice, boton in enumerate(self._botones_exportar):
            boton.clicked.connect(lambda _=False, i=indice: self._exportar(i))

        self.bloque_r.pausa_al_escribir.connect(self._mostrar_vista_previa_si_vacia)
        self._temporizador_progreso.timeout.connect(self._mostrar_progreso_si_tarda)
        self._temporizador_estado.timeout.connect(self._limpiar_estado)

        self._calculo.progreso.connect(self._al_avanzar)
        self._calculo.terminado.connect(self._al_terminar)
        self._calculo.cancelado.connect(self._al_cancelar)
        self._calculo.fallo.connect(self._al_fallar)
        self._datos.terminado.connect(self._al_llegar_datos_de_convergencia)
        self._datos.fallo.connect(self._al_fallar_datos_de_convergencia)

        self.grafica_riemann.animacion_terminada.connect(self._al_terminar_animacion)
        QGuiApplication.styleHints().colorSchemeChanged.connect(
            self._al_cambiar_esquema
        )

    def _ordenar_tabulacion(self):
        """Orden de DISENO 5.1: datos, calcular, método, sonido y gráficas."""
        activo = self.selector_metodo.botones[self.selector_metodo.metodo()]
        cadena = [self.campo_radio, self.campo_n, self.boton_calcular,
                  self.boton_cancelar, activo, self.interruptor_sonido]  # fmt: skip
        if self._modo_pestanas:
            cadena.append(self._pestanas.tabBar())
        cadena += [
            self.grafica_3d, self._boton_restablecer, self._botones_exportar[0],
            self.grafica_riemann, self._botones_exportar[1],
            self.grafica_convergencia, self._botones_exportar[2],
        ]  # fmt: skip
        for anterior, siguiente in zip(cadena, cadena[1:], strict=False):
            QWidget.setTabOrder(anterior, siguiente)

    # =====================================================================
    # Cálculo
    # =====================================================================
    def calcular_ahora(self, con_clic=True):
        """Valida R y n y, si son correctos, lanza el cálculo. Devuelve si lo lanzó."""
        self._saltar_animacion()
        radio, _mensaje = self.bloque_r.validar_y_mostrar()
        n, _mensaje = self.bloque_n.validar_y_mostrar()
        if radio is None or n is None:
            # El foco va al primer campo con error (la única vez que se mueve solo).
            primero = self.campo_radio if radio is None else self.campo_n
            primero.setFocus(Qt.FocusReason.OtherFocusReason)
            self.sonidos.error()
            return False

        if con_clic:
            self.sonidos.clic()
        # Tras calcular el foco se queda donde estaba, con el texto
        # seleccionado, para escribir el valor siguiente y pulsar Enter.
        foco = self.focusWidget()
        if foco in (self.campo_radio, self.campo_n):
            foco.selectAll()

        metodo = self.selector_metodo.metodo()
        self.tarjeta_resultado.ocultar_avisos()
        self._barra_a(0)
        self._mostrar_progreso(False)

        def tarea(progreso, cancelado):
            return self._calcular(
                radio, n, metodo, progreso=progreso, cancelado=cancelado
            )

        self._calculo.lanzar(tarea)
        self._temporizador_progreso.start()
        return True

    def _cancelar_calculo(self):
        self._calculo.cancelar()

    def _al_cambiar_metodo(self, _metodo):
        self._ordenar_tabulacion()
        if self._ultimo is None:
            return
        # Solo se recalcula si los datos actuales son válidos.
        if (
            self.bloque_r.validar()[0] is not None
            and self.bloque_n.validar()[0] is not None
        ):
            self.calcular_ahora(con_clic=False)

    def _al_avanzar(self, porcentaje):
        self._barra_a(porcentaje)

    def _al_terminar(self, r):
        self._fin_de_calculo()
        self._ultimo = r
        reducir = sistema.reducir_movimiento()
        self.tarjeta_resultado.mostrar_resultado(r, animar=not reducir)
        self.sonidos.resultado()
        self.grafica_3d.mostrar(r.radio)
        self._pendiente_convergencia = (r, reducir)
        self.grafica_riemann.mostrar_resultado(
            r, animar=True, reducir_movimiento=reducir
        )
        self._mostrar_aviso_de_muestra(r)
        self._actualizar_nombres_accesibles()

    def _al_cancelar(self):
        self._fin_de_calculo()
        # Cancelar no es un error: sin sonido.
        self.tarjeta_resultado.mostrar_cancelado(self._ultimo is not None)

    def _al_fallar(self, mensaje):
        self._fin_de_calculo()
        self._ultimo = None
        self.tarjeta_resultado.mostrar_error(mensaje)
        self.sonidos.error()

    def _fin_de_calculo(self):
        self._temporizador_progreso.stop()
        self._mostrar_progreso(False)

    def _mostrar_aviso_de_muestra(self, r):
        """Aviso bajo la gráfica de Riemann cuando n > 120 (DISENO 4.10)."""
        if not r.agrupado:
            self.banda_muestra.setVisible(False)
            return
        por_barra = formatear_entero(round(r.n / RECTANGULOS_MAXIMOS))
        self.banda_muestra.mostrar(
            f"Se dibujan {RECTANGULOS_MAXIMOS} de los {formatear_entero(r.n)} "
            f"rectángulos: cada barra agrupa unos {por_barra} subintervalos y su "
            "altura es el promedio de f en el grupo. El área total es la misma."
        )

    # --- progreso -----------------------------------------------------------
    def _barra_a(self, porcentaje):
        self.barra_progreso.setValue(porcentaje)
        self.etiqueta_progreso.setText(f"Calculando… {porcentaje} %")

    def _mostrar_progreso(self, visible):
        self.panel_progreso.setVisible(visible)
        self._anillo_cancelar.setVisible(visible)
        self.boton_cancelar.setVisible(visible)

    def _mostrar_progreso_si_tarda(self):
        if self._calculo.en_curso():
            self._mostrar_progreso(True)

    # =====================================================================
    # Animaciones y vista previa
    # =====================================================================
    def _hay_animacion(self):
        return (
            self.tarjeta_resultado.esta_animando()
            or self.grafica_riemann.esta_animando()
            or self.grafica_convergencia.esta_animando()
            or self._pendiente_convergencia is not None
        )

    def _saltar_animacion(self):
        """Muestra de inmediato el estado final de todas las animaciones."""
        self.tarjeta_resultado.saltar_animacion()
        if self.grafica_riemann.esta_animando():
            self.grafica_riemann.saltar_animacion()
        if self.grafica_convergencia.esta_animando():
            self.grafica_convergencia.saltar_animacion()
        self._poner_punto_actual(animar=False)

    def _al_terminar_animacion(self):
        self._poner_punto_actual(animar=True)

    def _poner_punto_actual(self, animar):
        """Marca el cálculo actual en la gráfica de convergencia (una sola vez)."""
        if self._pendiente_convergencia is None:
            return
        resultado, reducir = self._pendiente_convergencia
        self._pendiente_convergencia = None
        self.grafica_convergencia.marcar_actual(
            resultado, animar=animar, reducir_movimiento=reducir
        )

    def _al_pulsar_escape(self):
        if self._calculo.en_curso():
            self._calculo.cancelar()
        elif self._hay_animacion():
            self._saltar_animacion()

    def _mostrar_vista_previa(self):
        """Antes del primer cálculo: f(t) y la esfera para el R escrito."""
        radio, mensaje = self.bloque_r.validar()
        if mensaje == "":
            self.grafica_3d.mostrar(radio)
            self.grafica_riemann.mostrar_funcion(radio)
            self._actualizar_nombres_accesibles()

    def _mostrar_vista_previa_si_vacia(self):
        if self._ultimo is None:
            self._mostrar_vista_previa()

    def _actualizar_nombres_accesibles(self):
        for grafica in (
            self.grafica_3d,
            self.grafica_riemann,
            self.grafica_convergencia,
        ):
            grafica.setAccessibleName(grafica.descripcion_accesible())

    # --- datos de la gráfica de convergencia -------------------------------
    def _pedir_datos_de_convergencia(self):
        if self._datos_convergencia is None:
            return

        def tarea(_progreso, cancelado):
            return self._datos_convergencia(cancelado=cancelado)

        self._datos.lanzar(tarea)

    def _al_llegar_datos_de_convergencia(self, datos):
        self.grafica_convergencia.establecer_datos(datos)
        self._actualizar_nombres_accesibles()

    def _al_fallar_datos_de_convergencia(self, mensaje):
        self._mostrar_estado(
            f"No se pudo preparar la gráfica de convergencia: {mensaje}", "error"
        )

    # =====================================================================
    # Sonido
    # =====================================================================
    def _recordar_sonido(self):
        """Lee la preferencia guardada y deja interruptor y sonidos de acuerdo."""
        activado = self._ajustes.value("sonido/activado", True, type=bool)
        self.interruptor_sonido.blockSignals(True)
        self.interruptor_sonido.setChecked(activado)
        self.interruptor_sonido.blockSignals(False)
        self._actualizar_texto_sonido(activado)
        self.sonidos.establecer_activado(activado)

    def _actualizar_texto_sonido(self, activado):
        texto = "Sonido: activado" if activado else "Sonido: desactivado"
        self.interruptor_sonido.setText(texto)
        self.interruptor_sonido.updateGeometry()

    def _al_alternar_sonido(self, activado):
        self._actualizar_texto_sonido(activado)
        self.sonidos.establecer_activado(activado)
        self._ajustes.setValue("sonido/activado", activado)
        if activado:
            self.sonidos.clic()  # confirma que ahora sí hay sonido

    # =====================================================================
    # Exportar
    # =====================================================================
    def _exportar(self, indice):
        """Pide un archivo con el diálogo del sistema y guarda la gráfica."""
        grafica = (self.grafica_3d, self.grafica_riemann, self.grafica_convergencia)[
            indice
        ]
        boton = self._botones_exportar[indice]
        carpeta = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.PicturesLocation
        )
        sugerida = str(Path(carpeta) / grafica.nombre_sugerido())
        ruta, _filtro = QFileDialog.getSaveFileName(
            self, "Exportar imagen", sugerida, "Imagen PNG (*.png)"
        )
        if not ruta:
            return  # el usuario cerró el diálogo
        if not ruta.lower().endswith(".png"):
            ruta += ".png"

        boton.setEnabled(False)  # solo mientras se guarda
        try:
            grafica.exportar(ruta)
        except Exception as error:
            motivo = str(error).strip().rstrip(".") or type(error).__name__
            self._mostrar_estado(f"No se pudo guardar la imagen: {motivo}.", "error")
            self.sonidos.error()
        else:
            self._mostrar_estado(
                f"Imagen guardada en: {ruta}", "exito", DURACION_EXITO_MS
            )
            self.sonidos.clic()
        finally:
            boton.setEnabled(True)

    def _mostrar_estado(self, texto, tipo, duracion_ms=0):
        """Mensaje en la barra de estado: éxito (con tiempo) o error (se queda)."""
        self._tipo_estado = tipo
        self.etiqueta_estado.setProperty("rol", f"estado_{tipo}")
        repulir(self.etiqueta_estado)
        self.etiqueta_estado.setText(texto)
        self._pintar_icono_estado()
        self.icono_estado.setVisible(True)
        self._temporizador_estado.stop()
        if duracion_ms:
            self._temporizador_estado.start(duracion_ms)

    def _limpiar_estado(self):
        self.etiqueta_estado.setText("")
        self.icono_estado.setVisible(False)

    def _pintar_icono_estado(self):
        tipo = getattr(self, "_tipo_estado", None)
        if tipo in ESTADOS_ICONO:
            self.icono_estado.setPixmap(
                iconos.pixmap(ESTADOS_ICONO[tipo], self._colores[tipo], 16)
            )

    # =====================================================================
    # Tema claro / oscuro
    # =====================================================================
    def _al_cambiar_esquema(self, esquema):
        self.aplicar_modo(esquema == Qt.ColorScheme.Dark)

    def aplicar_modo(self, oscuro):
        """Cambia entre modo claro y oscuro (también las tres gráficas)."""
        self._oscuro = bool(oscuro)
        self._colores = tema.paleta(self._oscuro)
        self.setStyleSheet(estilos.generar(self._colores, self._escala))

        for pieza in self._tematizables:
            pieza.aplicar_colores(self._colores)
        self.boton_calcular.setIcon(
            iconos.icono("calculator", self._colores["texto_sobre_acento"], 16)
        )
        self._pintar_icono_estado()
        for grafica in (
            self.grafica_3d,
            self.grafica_riemann,
            self.grafica_convergencia,
        ):
            grafica.aplicar_tema(self._colores)

    # =====================================================================
    # Tamaño: rejilla o pestañas
    # =====================================================================
    def resizeEvent(self, evento):
        super().resizeEvent(evento)
        self._adaptar_a_ancho(self.width())

    def _adaptar_a_ancho(self, ancho):
        self._aplicar_margen(24 if ancho >= ANCHO_REJILLA else 16)
        pestanas = ancho < ANCHO_REJILLA
        if pestanas == self._modo_pestanas:
            return
        elegida = self._pestanas.currentIndex()
        if pestanas:
            for tarjeta in self._tarjetas:
                self._diseno_rejilla.removeWidget(tarjeta)
            for tarjeta, nombre in zip(
                self._tarjetas, self._nombres_pestanas, strict=True
            ):
                self._pestanas.addTab(tarjeta, nombre)
            self._pestanas.setCurrentIndex(max(elegida, 0))
        else:
            while self._pestanas.count():
                self._pestanas.removeTab(0)
            self._diseno_rejilla.addWidget(self.tarjeta_3d, 0, 0, 2, 1)
            self._diseno_rejilla.addWidget(self.tarjeta_riemann, 0, 1)
            self._diseno_rejilla.addWidget(self.tarjeta_convergencia, 1, 1)
            for tarjeta in self._tarjetas:
                tarjeta.setVisible(True)  # las pestañas ocultan las que no ve
        for tarjeta in self._tarjetas:
            tarjeta.forzar_compacto(pestanas)
        self._modo_pestanas = pestanas
        self._zona.setCurrentIndex(1 if pestanas else 0)
        self._ordenar_tabulacion()

    def _aplicar_margen(self, margen):
        # Los anillos de las tarjetas añaden 4 DIP por lado, de ahí el "- 4".
        # Arriba y abajo se quita algo más (la barra superior ya tiene aire):
        # sin eso la columna izquierda no cabe en 864 DIP de alto.
        self._diseno_cuerpo.setContentsMargins(
            margen, margen - 12, margen - 4, margen - 8
        )
        self._diseno_barra.setContentsMargins(margen, 4, margen, 4)

    def _mostrar_pestana(self, indice):
        """Ctrl+1/2/3: solo tiene efecto en el modo de pestañas."""
        if self._modo_pestanas:
            self._pestanas.setCurrentIndex(indice)

    # =====================================================================
    # Teclado y ratón de toda la ventana
    # =====================================================================
    def _es_de_esta_ventana(self, objeto):
        return isinstance(objeto, QWidget) and objeto.window() is self

    def eventFilter(self, objeto, evento):
        tipo = evento.type()
        if tipo == QEvent.Type.MouseButtonPress:
            # Un clic salta la animación, pero el clic sigue su camino normal.
            if (
                evento.button() == Qt.MouseButton.LeftButton
                and self._es_de_esta_ventana(objeto)
                and self._hay_animacion()
            ):
                self._saltar_animacion()
        elif tipo == QEvent.Type.KeyPress and self._es_de_esta_ventana(objeto):
            if evento.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                return self._al_pulsar_enter(objeto, evento)
        return False

    def _al_pulsar_enter(self, objeto, evento):
        """Enter calcula, salvo si el foco está en un botón: entonces lo pulsa."""
        if evento.isAutoRepeat():
            return True
        if isinstance(objeto, QAbstractButton):
            objeto.click()
        else:
            self.calcular_ahora()
        return True

    # =====================================================================
    # Cierre
    # =====================================================================
    def closeEvent(self, evento):
        QApplication.instance().removeEventFilter(self)
        try:
            QGuiApplication.styleHints().colorSchemeChanged.disconnect(
                self._al_cambiar_esquema
            )
        except (RuntimeError, TypeError):
            pass
        self._temporizador_progreso.stop()
        self._calculo.cerrar()
        self._datos.cerrar()
        self._saltar_animacion()
        self.sonidos.cerrar()
        super().closeEvent(evento)
