"""Ventana principal: une los campos, el resultado y las dos gráficas.

La ventana NO calcula, ni dibuja gráficas, ni fabrica sonidos: recibe esas
piezas ya hechas en el constructor (ver app.py) y solo coordina:

    escribir R y n -> validar -> calcular en un hilo -> mostrar -> animar

Distribución "orbital": la esfera es el centro de todo. A su alrededor gira
un anillo, y cuatro tarjetas de vidrio flotan en las esquinas, cada una
atada al anillo con un hilo:

    [logo] Ventana de Viviani     r(t) = (R cos²t, …)             [Créditos]

    ┌ 01 DATOS ──────┐                         ┌ 02 RESULTADO ────────┐
    │ R, n,          │──●      ╭─────╮      ●──│ 38.201978 cm, cifras │
    │ Calcular       │       ╱  esfera  ╲      │ control y errores    │
    └────────────────┘      │   girando  │     └──────────────────────┘
    ┌ 04 FÓRMULA ────┐       ╲          ╱      ┌ 03 SUMA DE RIEMANN ──┐
    │ ∫, Σ, Δt, tᵢ   │──●      ╰─────╯      ●──│ rectángulos          │
    └────────────────┘  [Malla][Cilindro][Ejes] └──────────────────────┘

Las dos gráficas están enlazadas: al pasar el mouse sobre un rectángulo de
Riemann, la curva 3D señala el punto r(tᵢ) y su vector velocidad. Cada clic
en cualquier parte suelta una onda de luz (CapaPulsos).
"""

import math

from PySide6.QtCore import QEvent, QPointF, QRectF, QSize, Qt, QTimer
from PySide6.QtGui import QCursor, QFont, QKeySequence, QPainter, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QGraphicsOpacityEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from viviani import tema, validacion
from viviani.animacion import Animacion, salida_suave
from viviani.formato import formatear_entero, formatear_radio
from viviani.ui import estilos, sistema
from viviani.ui.componentes import (
    BotonCalcular,
    CampoDato,
    CapaPulsos,
    Chip,
    FondoVentana,
    Tarjeta,
    etiqueta_pequena,
    fuente,
)
from viviani.ui.creditos import PanelCreditos
from viviani.ui.formula import (
    Espacio,
    Fila,
    Formula,
    Fraccion,
    Operador,
    Raiz,
    cuadrado,
    sub,
    t,
    var,
)
from viviani.ui.logo import dibujar_logo
from viviani.ui.resultado import PanelResultado
from viviani.ui.trabajador import GestorTareas

ANCHO_IZQUIERDA = 340  # px: tarjetas de datos y fórmula
ANCHO_DERECHA = 400  # px: tarjetas de resultado y Riemann
RETARDO_PROGRESO_MS = 300  # el progreso solo aparece si el cálculo tarda más
INTERVALO_CURSOR_MS = 33  # cada cuánto se revisa dónde está el cursor
DURACION_ENTRADA_MS = 1100  # al abrir, las tarjetas aparecen una tras otra
CAPAS = [("malla", "Malla", "Ver u ocultar la malla de la esfera"),
         ("cilindro", "Cilindro", "Ver u ocultar el cilindro (x − R/2)² + y² = R²/4"),
         ("ejes", "Ejes", "Ver u ocultar los ejes X, Y, Z")]  # fmt: skip


def paso_de_n(n, sentido):
    """↑ multiplica n por 10 y ↓ lo divide (sin bajar de 1)."""
    return str(n * 10 if sentido > 0 else max(1, n // 10))


def ecuacion_curva():
    """r(t) = (R cos²t, R sen t cos t, R sen t),  0 ≤ t ≤ 2π"""
    return Fila(
        var("r", "valor"), t("("), var("t"), t(") = ("), var("R"), t(" "),
        cuadrado(t("cos")), var("t"), t(", "), var("R"), t(" sen "), var("t"),
        t(" cos "), var("t"), t(", "), var("R"), t(" sen "), var("t"), t(")"),
        Espacio(1.0), t("0 ≤ ", "suave"), var("t", "suave"), t(" ≤ 2π", "suave"),
    )  # fmt: skip


def formula_perimetro(n, radio):
    """Las cuatro filas de la tarjeta Fórmula, con Δt y R actuales."""
    dt = (t("Δ"), var("t"))
    delta = t(f"{2 * math.pi / n:.6f}", "valor") if n else t("—", "suave")
    valor_r = t(formatear_radio(radio), "valor") if radio else t("—", "suave")
    return (
        Fila(var("L"), t(" = "), Operador("∫", t("2π"), t("0"), apilado=False),
             var("R"), Espacio(0.12),
             Raiz(Fila(t("1 + "), cuadrado(t("cos")), var("t"))),
             Espacio(0.2), t("d"), var("t")),
        Fila(Espacio(0.9), t("≈ "),
             Operador("Σ", var("n"), Fila(var("i"), t(" = 1")), apilado=True),
             Espacio(0.15), var("f"), t("("), sub(var("t"), var("i")), t(") "), *dt),
        Fila(*dt, t(" = "), Fraccion(t("2π"), var("n")), t(" = "), delta),
        Fila(sub(var("t"), var("i")), t(" = ("), var("i"), t(" − "),
             Fraccion(t("1"), t("2"), chica=True), t(") "), *dt,
             Espacio(0.9), var("R"), t(" = "), valor_r, t(" cm")),
    )  # fmt: skip


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
        self.setMinimumSize(1100, 720)
        self.colores = tema.paleta()
        self.setStyleSheet(estilos.hoja_de_estilos(self.colores))

        self.grafica_3d = grafica_3d
        self.grafica_riemann = grafica_riemann
        self.sonidos = sonidos
        self._calcular = calcular
        self._calculo = GestorTareas(self)
        self._quieto = sistema.reducir_movimiento()
        self._entrada = None  # animación de entrada (se hace una sola vez)
        self._ultimo_clic = None  # para soltar una sola onda por clic

        self._construir_interfaz()
        self._conectar()

        self.grafica_riemann.mostrar_funcion(5.0)
        self._actualizar_formula()
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
        raiz.setContentsMargins(40, 16, 40, 18)
        raiz.setSpacing(0)
        raiz.addLayout(self._crear_encabezado())
        cuerpo = QHBoxLayout()
        cuerpo.setSpacing(0)
        self._columna_izquierda = self._crear_columna_izquierda()
        self._columna_derecha = self._crear_columna_derecha()
        cuerpo.addWidget(self._columna_izquierda)
        cuerpo.addLayout(self._crear_centro(), 1)  # el centro queda para la esfera
        cuerpo.addWidget(self._columna_derecha)
        raiz.addLayout(cuerpo, 1)

        self.creditos = PanelCreditos(fondo, self.sonidos)
        self.pulsos = CapaPulsos(fondo)

    def _crear_encabezado(self):
        titulo = QLabel("Ventana de Viviani")
        titulo.setFont(fuente(tema.FAMILIAS_INTERFAZ, 11, QFont.Weight.DemiBold))

        self.ecuacion = Formula(tam=17, centrada=True)
        self.ecuacion.establecer(ecuacion_curva())

        self.boton_creditos = QPushButton("Créditos")
        self.boton_creditos.setObjectName("enlace")
        self.boton_creditos.setCursor(Qt.CursorShape.PointingHandCursor)
        self.boton_creditos.setToolTip("Integrantes del grupo")

        encabezado = QHBoxLayout()
        encabezado.setSpacing(10)
        encabezado.addWidget(Logo(30))
        encabezado.addWidget(titulo)
        encabezado.addWidget(self.ecuacion, 1)
        encabezado.addWidget(self.boton_creditos, 0, Qt.AlignmentFlag.AlignVCenter)
        return encabezado

    def _crear_columna_izquierda(self):
        # --- Tarjeta de datos
        self.tarjeta_datos = Tarjeta("01", "Datos", "izquierda")
        self.bloque_r = CampoDato(
            self.colores, "Radio de la esfera R", validacion.validar_radio,
            "5", "Ej.: 7.5", unidad="cm",
        )  # fmt: skip
        self.bloque_n = CampoDato(
            self.colores, "Número de subintervalos n",
            validacion.validar_subintervalos, "100", "Ej.: 1000", paso=paso_de_n,
        )  # fmt: skip
        self.campo_radio, self.campo_n = self.bloque_r.caja, self.bloque_n.caja
        self.campo_n.setToolTip("↑ multiplica n por 10, ↓ lo divide entre 10")

        # El botón trae un margen para su halo: la píldora queda un poco
        # más angosta que los campos, centrada bajo ellos
        ancho_boton = ANCHO_IZQUIERDA - 2 * Tarjeta.MARGEN - 2 * BotonCalcular.MARGEN
        self.boton_calcular = BotonCalcular(self.colores, ancho_boton)
        self.boton_calcular.setToolTip("Calcular el perímetro (Enter)")

        contenido = self.tarjeta_datos.contenido
        contenido.addWidget(self.bloque_r)
        contenido.addWidget(self.bloque_n)
        contenido.addWidget(self.boton_calcular)

        # --- Tarjeta de la fórmula
        self.tarjeta_formula = Tarjeta("04", "Fórmula", "izquierda")
        self.formula = Formula(tam=17, separacion=12)
        self.tarjeta_formula.contenido.addWidget(self.formula)

        return self._columna(self.tarjeta_datos, self.tarjeta_formula, ANCHO_IZQUIERDA)

    def _crear_centro(self):
        """Debajo de la esfera, los chips de las capas."""
        chips = QHBoxLayout()
        chips.setSpacing(6)
        chips.addStretch(1)
        self.capas = {}
        for clave, texto, descripcion in CAPAS:
            chip = Chip(texto, marcable=True, descripcion=descripcion)
            chip.toggled.connect(
                lambda visible, k=clave: self._cambiar_capa(k, visible)
            )
            chips.addWidget(chip)
            self.capas[clave] = chip
        chips.addStretch(1)

        centro = QVBoxLayout()
        centro.addStretch(1)
        centro.addLayout(chips)
        return centro

    def _crear_columna_derecha(self):
        self.tarjeta_resultado = Tarjeta("02", "Resultado", "derecha")
        self.panel_resultado = PanelResultado(self.colores, self._quieto)
        self.tarjeta_resultado.contenido.addWidget(self.panel_resultado)

        self.detalle_riemann = etiqueta_pequena("")
        self.tarjeta_riemann = Tarjeta(
            "03", "Suma de Riemann", "derecha", extra=self.detalle_riemann
        )
        self.grafica_riemann.setFixedHeight(236)
        self.grafica_riemann.setToolTip(
            "Pase el mouse sobre un rectángulo para leerlo y verlo en la curva 3D"
        )
        self.tarjeta_riemann.contenido.addWidget(self.grafica_riemann)
        return self._columna(
            self.tarjeta_resultado, self.tarjeta_riemann, ANCHO_DERECHA
        )

    @staticmethod
    def _columna(arriba, abajo, ancho):
        columna = QVBoxLayout()
        columna.setContentsMargins(0, 12, 0, 0)
        columna.setSpacing(14)
        columna.addStretch(1)
        columna.addWidget(arriba)
        columna.addWidget(abajo)
        columna.addStretch(1)
        contenedor = QWidget()
        contenedor.setLayout(columna)
        contenedor.setFixedWidth(ancho)
        return contenedor

    def _tarjetas(self):
        return (self.tarjeta_datos, self.tarjeta_formula,
                self.tarjeta_resultado, self.tarjeta_riemann)  # fmt: skip

    def _actualizar_zona_3d(self):
        """La esfera se centra en el hueco libre entre las dos columnas, y los
        hilos de la órbita se atan al borde de cada tarjeta."""
        g = self.grafica_3d

        def en_3d(widget):
            esquina = g.mapFromGlobal(widget.mapToGlobal(widget.rect().topLeft()))
            return QRectF(esquina.x(), esquina.y(), widget.width(), widget.height())

        izquierda = en_3d(self._columna_izquierda).right()
        derecha = en_3d(self._columna_derecha).left()
        arriba = en_3d(self.boton_creditos).bottom() + 8
        abajo = en_3d(self.capas["malla"]).top() - 8
        margen = 16
        zona = QRectF(izquierda + margen, arriba,
                      derecha - izquierda - 2 * margen, abajo - arriba)  # fmt: skip
        anclas = []
        for tarjeta in self._tarjetas():
            punto = tarjeta.mapToGlobal(tarjeta.ancla().toPoint())
            anclas.append((QPointF(g.mapFromGlobal(punto)), tarjeta.lado))
        g.establecer_zona(zona, anclas)

    def resizeEvent(self, evento):
        super().resizeEvent(evento)
        self.pulsos.setGeometry(self.centralWidget().rect())
        # Se espera a que los diseños terminen de acomodarse
        QTimer.singleShot(0, self._actualizar_zona_3d)

    def showEvent(self, evento):
        super().showEvent(evento)
        QTimer.singleShot(0, self._actualizar_zona_3d)
        if not self._quieto and self._entrada is None:
            self._animar_entrada()

    def _animar_entrada(self):
        """Al abrir, las tarjetas aparecen una tras otra, en el orden del cálculo."""
        orden = (self.tarjeta_datos, self.tarjeta_resultado,
                 self.tarjeta_riemann, self.tarjeta_formula)  # fmt: skip
        efectos = []
        for tarjeta in orden:
            efecto = QGraphicsOpacityEffect(tarjeta)
            efecto.setOpacity(0.0)
            tarjeta.setGraphicsEffect(efecto)
            efectos.append(efecto)

        def al_cuadro(ms):
            for k, efecto in enumerate(efectos):
                efecto.setOpacity(salida_suave((ms - 200 - 160 * k) / 450))

        def al_terminar():
            for tarjeta in orden:
                tarjeta.setGraphicsEffect(None)  # sin efecto se pinta más rápido

        self._entrada = Animacion(self, al_cuadro, al_terminar)
        self._entrada.iniciar(DURACION_ENTRADA_MS)

    def _conectar(self):
        self.boton_calcular.clicked.connect(self.calcular_ahora)
        self.boton_creditos.clicked.connect(self.sonidos.clic)
        self.boton_creditos.clicked.connect(self.creditos.abrir)
        for caja in (self.campo_radio, self.campo_n):
            caja.returnPressed.connect(self.calcular_ahora)
            caja.textChanged.connect(self._actualizar_formula)
        self.grafica_riemann.t_resaltado.connect(self.grafica_3d.resaltar)

        self._calculo.progreso.connect(self._al_avanzar)
        self._calculo.terminado.connect(self._al_terminar)
        self._calculo.cancelado.connect(self._ocultar_progreso)
        self._calculo.fallo.connect(self._al_fallar)

        self._temporizador_progreso = QTimer(self, singleShot=True)
        self._temporizador_progreso.setInterval(RETARDO_PROGRESO_MS)
        self._temporizador_progreso.timeout.connect(self._mostrar_progreso)
        self._progreso_visible = False

        QShortcut(QKeySequence(Qt.Key.Key_Escape), self, self._al_pulsar_escape)

        # El botón y el fondo reaccionan al cursor: se revisa su posición
        # unas 30 veces por segundo.
        self._vigia_cursor = QTimer(self)
        self._vigia_cursor.setInterval(INTERVALO_CURSOR_MS)
        self._vigia_cursor.timeout.connect(self._revisar_cursor)
        self._vigia_cursor.start()

        # Cada clic suelta una onda de luz y salta las animaciones
        QApplication.instance().installEventFilter(self)

    def _cambiar_capa(self, clave, visible):
        self.sonidos.clic()
        self.grafica_3d.establecer_capa(clave, visible)

    def _actualizar_formula(self):
        """La fórmula con los números actuales: Δt cambia con n."""
        n, radio = self.bloque_n.valor(), self.bloque_r.valor()
        self.formula.establecer(*formula_perimetro(n, radio))

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
        self.grafica_3d.enviar(entrante=True)
        self._calculo.lanzar(
            lambda progreso, cancelado: self._calcular(radio, n, progreso, cancelado)
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
        animar = not sistema.reducir_movimiento()
        self.panel_resultado.mostrar_resultado(resultado, animar=animar)
        self.sonidos.resultado()
        self.grafica_3d.mostrar(resultado.radio)
        self.grafica_3d.enviar(entrante=False)
        self.grafica_3d.barrer(resultado.barras_inicio + resultado.barras_ancho / 2)
        detalle = f"n = {formatear_entero(resultado.n)}"
        if resultado.agrupado:
            detalle += f"  ·  {len(resultado.barras_altura)} barras"
        self.detalle_riemann.setText(detalle)
        self.grafica_riemann.mostrar_resultado(resultado, animar=animar)
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
    def _animables(self):
        return (self.grafica_riemann, self.panel_resultado, self.grafica_3d)

    def _hay_animacion(self):
        return any(pieza.esta_animando() for pieza in self._animables())

    def _saltar_animaciones(self):
        for pieza in self._animables():
            pieza.saltar_animacion()

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
            and isinstance(objeto, QWidget)
            and objeto.window() is self
        ):
            # Si el widget no usa el clic, Qt se lo pasa a su padre y este
            # filtro lo vuelve a ver: con la hora del clic se suelta una sola onda.
            if evento.timestamp() != self._ultimo_clic:
                self._ultimo_clic = evento.timestamp()
                if not self._quieto:
                    posicion = evento.globalPosition().toPoint()
                    self.pulsos.pulsar(self.centralWidget().mapFromGlobal(posicion))
                if self._hay_animacion():
                    self._saltar_animaciones()  # el clic sigue haciendo lo suyo
        return False

    # =====================================================================
    # Cierre
    # =====================================================================
    def closeEvent(self, evento):
        self._vigia_cursor.stop()
        QApplication.instance().removeEventFilter(self)
        self._calculo.cerrar()
        self.sonidos.cerrar()
        super().closeEvent(evento)
