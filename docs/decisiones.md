# Decisiones de arquitectura (ADR)

## ADR-001: Stack de la aplicación de escritorio

| Campo | Valor |
|---|---|
| Estado | Propuesta (pendiente de la prueba de humo de empaquetado, ver "Riesgos") |
| Fecha | 2026-11-16 |
| Rama | `feature/interfaz-grafica` |
| Alcance | Interfaz gráfica, gráficas, animación, sonido y empaquetado `.exe` |

### Convención sobre los números

- **Medido**: dato obtenido en esta máquina o en PyPI el 2026-11-16 (tamaños de wheel, versiones, errores numéricos).
- **Estimado**: juicio de ingeniería sin medición. Todo número marcado como "estimado" debe confirmarse con la prueba de humo (sección "Plan de verificación").

## 1. Contexto

- Programa de consola existente (`perimetro_viviani.py`), sin dependencias externas, con pruebas en `test_perimetro_viviani.py`. La nueva aplicación debe dar los mismos resultados.
- Entorno real: Windows 11 Home, **Python 3.15.0 de 64 bits** (compilación normal, no la `t` "free-threaded"), entorno virtual `.venv` que ya contiene numpy 2.5.5, scipy 1.18.1 y ruff 0.17.5 (medido con `pip list`).
- Entregable: un `.exe` generado con PyInstaller.
- Usuarios del código: 4 estudiantes de primer semestre que deben poder explicarlo en la sustentación.
- Video de máximo 5 minutos a 1920×1080 con voz encima: la app debe arrancar rápido, animar con fluidez y no "pelear" con la voz.

### Datos medidos en PyPI (2026-11-16)

| Paquete | Versión | Wheel para Windows x64 | Tamaño del wheel (medido) |
|---|---|---|---|
| PySide6 (metapaquete) | 6.12.0 | `cp310-abi3-win_amd64` | 0,6 MiB, **pero arrastra** Essentials + Addons + WebEngine + Pdf |
| PySide6-Essentials | 6.12.0 | `cp310-abi3-win_amd64` | 78,3 MiB |
| PySide6-Addons | 6.12.0 | `cp310-abi3-win_amd64` | 38,6 MiB |
| shiboken6 | 6.12.0 | `cp310-abi3-win_amd64` | 1,2 MiB |
| matplotlib | 3.11.2 | `cp315-cp315-win_amd64` | 9,1 MiB |
| numpy | 2.5.5 | `cp315-cp315-win_amd64` | 12,1 MiB |
| pyqtgraph | 0.14.0 | `py3-none-any` | 1,8 MiB |
| PyOpenGL (necesario para el 3D de pyqtgraph) | 3.1.10 | `py3-none-any` | 3,0 MiB |
| pyinstaller | 6.22.3 | `py3-none-win_amd64`, `requires_python <3.16,>=3.8` | 1,4 MiB |
| pyinstaller-hooks-contrib | 2026.10 | `py3-none-any` | 0,4 MiB |

Observaciones medidas:

- PySide6 6.12.0 usa wheels **abi3** (compilados para la ABI estable desde 3.10) y declara `requires_python <3.16`; no hay un wheel específico para 3.15. Funciona en 3.15 por la ABI estable, pero es menos probado que una versión con wheel propio.
- El metapaquete `PySide6==6.12.0` depende de `PySide6_WebEngine` y `PySide6_Pdf`. No los necesitamos.
- **QtMultimedia no está en PySide6-Essentials** (lista oficial de módulos en la página de PyPI de PySide6-Essentials). Está en Addons.
- La documentación de `winsound` indica que `SND_MEMORY` **no se puede combinar** con `SND_ASYNC` (lanza `RuntimeError`).

## 2. Opciones evaluadas

### Opción A: PySide6-Essentials + matplotlib incrustado (backend QtAgg)

Ventana Qt (widgets clásicos); las tres gráficas son lienzos `FigureCanvasQTAgg`; el 3D usa `mpl_toolkits.mplot3d`.

### Opción B: PySide6-Essentials + pyqtgraph (+ PyOpenGL para 3D)

Ventana Qt; gráficas 2D con `pyqtgraph.PlotWidget`; 3D con `pyqtgraph.opengl.GLViewWidget`.

### Opción C: Tkinter/ttk (stdlib) + matplotlib (backend TkAgg)

Sin Qt. Interfaz con `tkinter.ttk`; gráficas con `FigureCanvasTkAgg`.

## 3. Comparación

Escala: ++ muy bien, + bien, 0 aceptable, − problema, −− problema serio.

| Criterio | A: Qt + matplotlib | B: Qt + pyqtgraph | C: Tk + matplotlib |
|---|---|---|---|
| Tamaño del `.exe` (onefile) | 0. Estimado 70–100 MB | +. Estimado 55–80 MB (sin matplotlib, pero con PyOpenGL) | +. Estimado 40–60 MB |
| Riesgo de instalación en 3.15 | +. Todo tiene wheel (medido) | +. Todo tiene wheel; PyOpenGL es Python puro | +. Tk viene con Python (no medido si el instalador de 3.15 trae Tcl/Tk 9) |
| Riesgo de empaquetado en 3.15 | 0. Hooks de PyInstaller para PySide6 y matplotlib existen desde hace años; 3.15 es nuevo | −. Además: OpenGL en la máquina de destino (drivers, máquinas virtuales, escritorio remoto) | 0. Hook de Tk existe; posible cambio a Tcl/Tk 9 sin probar |
| Calidad del 3D rotable | +. `mplot3d` rota con el mouse sin código extra; sin oclusión real de profundidad | ++ visual (GPU, fluido), −− trabajo: ejes sin rótulos de texto nativos, transparencia con artefactos de orden | +. Igual que A |
| Exportación PNG de alta resolución | ++. `savefig(dpi=300)`, fondo blanco, mathtext para `√`, `π`, `Σ` | −. 2D con `ImageExporter` (escala píxeles, no tipografía); 3D solo con `renderToArray`, sin rótulos | ++. Igual que A |
| Animación de rectángulos ≤ 2 s | 0. Suficiente con blitting y ≤ 120 rectángulos (estimado 30 fps) | ++. Pensado para tiempo real | 0. Igual que A, algo más lento el repintado en Tk (estimado) |
| Modo oscuro del sistema, DPI alto, foco visible | ++. Qt 6 detecta el esquema de color (`QStyleHints.colorScheme`), escala por monitor, foco estilizable con QSS | ++. Igual que A | −−. ttk no sigue el modo oscuro de Windows; DPI y foco requieren trabajo manual |
| Lector de pantalla (Narrador) | +. Qt expone UI Automation; `setAccessibleName` | +. Igual en la interfaz; la gráfica no | −−. Tk casi no expone accesibilidad |
| Hilos y cancelación | ++. `QThread`/`QThreadPool` + señales | ++. Igual | 0. `threading` + `after()`; más fácil equivocarse |
| Facilidad para explicar (primer semestre) | +. matplotlib ya se ve en cursos y tiene mucha documentación en español; Qt requiere aprender señales y slots | 0. Dos APIs poco conocidas (pyqtgraph y OpenGL) | ++. Tk es lo más simple, pero lo que falta (oscuro, accesibilidad) habría que programarlo a mano |
| Cumple todos los requisitos sin parches grandes | **Sí** | No (3D y exportación) | No (modo oscuro, accesibilidad) |

Notas de los tamaños (todos **estimados**): el wheel de Essentials (78 MiB comprimidos) incluye módulos que no usaremos (Qml, Quick, Designer...). PyInstaller copia solo los módulos importados más sus plugins; una app de widgets suele quedar muy por debajo del tamaño del wheel. numpy aporta su biblioteca de álgebra lineal (OpenBLAS), que es la parte más pesada fuera de Qt.

## 4. Decisión

**Se elige la Opción A: PySide6-Essentials 6.12.0 + matplotlib 3.11.2 (backend QtAgg) + numpy 2.5.5.**

Razones principales:

1. Es la única opción que cumple **todos** los requisitos (3D rotable con rótulos, PNG a 300 ppp con fondo blanco, modo claro/oscuro del sistema, foco visible, DPI alto, hilo de cálculo cancelable) con APIs estándar.
2. matplotlib es la biblioteca que más probablemente el equipo ya conoce, y su código de gráficas se puede explicar línea por línea.
3. La exportación para el reporte impreso es trivial y de calidad de imprenta.

Lo que aceptamos a cambio: un `.exe` más grande (estimado 70–100 MB) y un 3D sin oclusión perfecta (ver Riesgos).

### 4.a Backend de sonido

| Criterio | `winsound` (stdlib) + WAV sintetizado en memoria | QtMultimedia (`QSoundEffect`) |
|---|---|---|
| Disponible con Essentials | Sí (stdlib) | **No**: requiere PySide6-Addons (+38,6 MiB de wheel, medido) |
| Tamaño en el `.exe` | ~0 | Estimado +15–30 MB (Addons + plugins de FFmpeg) |
| Riesgo de empaquetado | Muy bajo | Medio (plugins multimedia) |
| Volumen | Se fija en la amplitud de las muestras (no hay control de volumen) | `setVolume()` |
| Asincronía | `SND_MEMORY` no admite `SND_ASYNC` (documentado) → reproducir en un hilo propio | Nativa |
| Facilidad de explicar | Alta: se generan las muestras con `math.sin` y el módulo `wave` | Media |

**Decisión: `winsound`.** Los tres WAV se sintetizan al arrancar con `math`, `array` y `wave` en un `io.BytesIO` (16 bits, mono, 44 100 Hz) con la amplitud ya baja. Se reproducen con `winsound.PlaySound(datos, winsound.SND_MEMORY | winsound.SND_NODEFAULT)` dentro de **un único hilo demonio** que lee de una `queue.Queue(maxsize=1)`; si la cola está llena, el sonido nuevo se descarta (nunca se acumulan sonidos). Alternativa aceptada si el hilo da problemas: escribir los tres WAV en `tempfile.gettempdir()` al arrancar y usar `SND_FILENAME | SND_ASYNC | SND_NODEFAULT`.

### 4.b PySide6-Essentials frente al metapaquete PySide6

**Decisión: instalar `PySide6-Essentials==6.12.0` (que trae `shiboken6==6.12.0`), no el metapaquete.** Solo usamos QtCore, QtGui, QtWidgets y QtSvg (iconos Lucide), todos en Essentials (medido en la lista oficial). El metapaquete añadiría Addons, WebEngine y Pdf: más descarga, más tiempo de instalación y más superficie para errores de PyInstaller. Importante: en el código se importa igual, `from PySide6.QtWidgets import ...`; matplotlib detecta PySide6 por el nombre del módulo, no del paquete.

### 4.c Decisiones derivadas

- **Cálculo numérico en la app:** numpy vectorizado por bloques (por ejemplo, de 1 000 000 de subintervalos) para poder informar progreso y cancelar entre bloques, acumulando con `math.fsum` (suma con redondeo correcto). Dato medido: la convergencia es exponencial (f es periódica y suave); con punto medio el error relativo baja a ~10⁻¹⁶ hacia n ≈ 40, y a partir de ahí lo que se ve es **error de redondeo**: el bucle de la consola acumula hasta 1,1 × 10⁻¹³ (R = 1, n = 100 000). Por eso la app y la consola coinciden en los 6 decimales del perímetro, pero el **error absoluto** puede diferir para n grande (el de la app es más exacto). Se recomienda cambiar también la consola a `math.fsum` para que ambas den exactamente lo mismo; la función `suma_de_riemann` sigue siendo la referencia y las pruebas comparan ambas.
- **Hilo:** `QThread` con un objeto trabajador y señales `progreso(int)`, `terminado(float)`, `fallo(str)`; la cancelación es una bandera revisada entre bloques.
- **Empaquetado:** PyInstaller en modo `--onefile --windowed` para el entregable, con `--exclude-module tkinter` y exclusión de módulos Qt no usados. Para grabar el video se recomienda la versión `--onedir` (arranca más rápido; el onefile se descomprime en cada arranque, estimado 3–8 s).
- **Fuentes:** Segoe UI Variable del sistema (presente en `C:\Windows\Fonts\SegUIVar.ttf`, medido). No se empaqueta Inter salvo que la prueba de humo muestre un problema. En matplotlib se usa "Segoe UI" (`segoeui.ttf`, presente) con respaldo DejaVu Sans, porque matplotlib maneja mal las fuentes variables (estimado; verificar).
- **Iconos:** SVG de Lucide (licencia ISC) copiados a `recursos/iconos/` junto con su archivo `LICENSE`, cargados con QtSvg. No se usa ningún recurso de Apple.

## 5. Dependencias con versiones fijadas

### `requirements.txt` (ejecución, lo que va dentro del `.exe`)

```
PySide6-Essentials==6.12.0
shiboken6==6.12.0
matplotlib==3.11.2
numpy==2.5.5
# Dependencias transitivas de matplotlib (versiones vigentes en PyPI el 2026-11-16):
contourpy==1.4.0
cycler==0.12.1
fonttools==4.68.0
kiwisolver==1.5.1
packaging==26.3
pillow==13.0.0
pyparsing==3.3.3
python-dateutil==4.0.0
six==1.17.0
```

### `requirements-dev.txt` (desarrollo y construcción, no va en el `.exe`)

```
-r requirements.txt
pyinstaller==6.22.3
pyinstaller-hooks-contrib==2026.10
altgraph==0.17.5
pefile==2024.8.26
pywin32-ctypes==0.2.3
setuptools==84.2.1
scipy==1.18.1      # solo para verificar el valor de control 7,640395578·R
ruff==0.17.5
```

Las versiones transitivas se tomaron de PyPI (última versión publicada). Si `pip` resuelve otras por restricciones de matplotlib, se acepta lo que resuelva y se congela con `pip freeze > requirements-lock.txt`, que pasa a ser la referencia para construir el `.exe`.

No se usan: pyqtgraph, PyOpenGL, PySide6-Addons, el metapaquete PySide6, Inter (salvo plan B), scipy en tiempo de ejecución.

## 6. Consecuencias

Positivas:

- Un único modelo mental para la interfaz (Qt) y uno para las gráficas (matplotlib).
- Exportación a PNG de 300 ppp con el mismo código que dibuja en pantalla.
- El sonido no añade dependencias.

Negativas:

- `.exe` grande (estimado 70–100 MB en onefile).
- El 3D de matplotlib no hace oclusión real: la curva puede verse "por delante" de la esfera aunque esté detrás. Mitigación: esfera muy translúcida (alfa 0,12) con malla de meridianos, curva con `zorder` alto; es aceptable porque la esfera es solo contexto.
- La rotación 3D con el mouse repinta toda la escena; con malla moderada se estima 20–30 fps (estimado).
- Qt exige explicar señales y slots; se mitigará con comentarios en español y un diagrama en el README.

## 7. Riesgos abiertos

| # | Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|---|
| R1 | PyInstaller 6.22.3 + Python 3.15 + PySide6 abi3 falla al construir o al ejecutar el `.exe` (hooks, DLL, `importlib`) | Media (estimado) | Alto: no hay entregable | Prueba de humo el primer día (ver abajo). Plan B: instalar un Python anterior de python.org solo para construir (requiere aprobación del grupo; hoy solo hay 3.15). Plan C: `--onedir` comprimido en `.zip` |
| R2 | Antivirus (Defender) marca el onefile como sospechoso | Media (estimado) | Medio | Probar en dos PCs; entregar también el onedir; no usar UPX |
| R3 | matplotlib no anima a ≥ 24 fps a 1920×1080 | Baja-media (estimado) | Medio: animación entrecortada en el video | Blitting de una sola colección de rectángulos; tope de 120 rectángulos; si no alcanza, bajar a 60 rectángulos |
| R4 | `winsound` con el hilo demonio bloquea al cerrar la app | Baja | Bajo | `PlaySound(None, 0)` al cerrar; hilo demonio |
| R5 | La suma con numpy por bloques difiere de la consola en el último dígito | Baja (con `math.fsum`) | Bajo | Prueba automática que compare con `suma_de_riemann` para varios n |
| R6 | Escalado de texto de Windows (Configuración > Accesibilidad > Tamaño del texto) no se refleja en Qt | Media (estimado) | Medio | Leer `HKCU\Software\Microsoft\Accessibility\TextScaleFactor` y multiplicar los tamaños base (ver `DISENO.md`) |
| R7 | Se instala por error la variante `python3.15t` (free-threaded); PyPI tiene wheels `cp315t` (medido) | Baja | Medio | Usar siempre `.venv\Scripts\python.exe`; comprobar que `sys._is_gil_enabled()` sea `True` en la prueba de humo |

### Plan de verificación (prueba de humo, día 1)

1. `pip install -r requirements-dev.txt` en `.venv`.
2. Script mínimo: ventana Qt con un `FigureCanvasQTAgg` 2D y otro 3D, un `QThread` que sume 10 000 000 de términos, y un sonido con `winsound`.
3. `pyinstaller --onefile --windowed` y `--onedir`; ejecutar ambos en esta PC y en la de otro integrante sin Python.
4. Anotar en este archivo, reemplazando "estimado" por "medido": tamaño del `.exe`, tiempo de arranque, fps de la animación y tiempo del cálculo con n = 10 000 000.
5. Si falla el paso 3, activar el Plan B de R1 antes de escribir más código de interfaz.
