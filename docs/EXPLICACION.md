# Cómo está organizado el código

Guía para que cualquier integrante pueda explicar el programa en la
sustentación. No hace falta saber Qt ni matplotlib para seguirla.

## 1. La idea en una frase

El programa calcula la longitud de la Ventana de Viviani sumando áreas de
rectángulos (suma de Riemann) y la compara con un valor de control conocido.

    r(t) = (R cos²t, R sen t cos t, R sen t),   t ∈ [0, 2π]
    f(t) = ‖r′(t)‖ = R·√(1 + cos²t)
    L ≈ Σ f(tᵢ)·Δt,   con Δt = 2π / n
    Valor de control: L = 7,640395578·R

## 2. Dos programas, un mismo cálculo

| Programa | Cómo se ejecuta | Para qué sirve |
|---|---|---|
| Consola | `python perimetro_viviani.py` | Versión mínima, sin librerías externas. Es el **núcleo matemático**. |
| Ventana | `python viviani_app.py` (o el `.exe`) | Lo mismo, con gráficas, animación y sonido. |

La versión de ventana **no vuelve a inventar la matemática**: toma de
`perimetro_viviani.py` las constantes (el intervalo, el valor de control, los
métodos válidos) y una prueba automática exige que ambas den el mismo
resultado.

## 3. Mapa de archivos

```
perimetro_viviani.py        Núcleo: funcion_subintegral() y suma_de_riemann()
test_perimetro_viviani.py   Pruebas del núcleo
viviani_app.py              Lanzador de la ventana (4 líneas útiles)

src/viviani/
  calculo.py       La misma suma, por bloques y con numpy (rápida y cancelable)
  validacion.py    Revisa lo que el usuario escribe en R y n
  formato.py       Escribe los números con punto decimal
  tema.py          Colores y fuentes de la interfaz
  sonido.py        Fabrica y reproduce los tres sonidos
  graficas/        Las dos gráficas (curva 3D y suma de Riemann)
  ui/              La ventana y sus controles
  app.py           Une todas las piezas

tests/             Pruebas automáticas de cada pieza
docs/              Este documento, el diseño y las decisiones
scripts/           Atajos para ejecutar y para construir el .exe
```

Regla que se cumple en todo el proyecto: **las piezas de arriba no conocen a
las de abajo**. `calculo.py`, `validacion.py`, `formato.py` y `sonido.py` no
saben que existe una ventana; por eso se pueden probar solas y explicar por
separado.

## 4. Qué pasa cuando se presiona Enter

1. **`ui/ventana.py`** toma el texto de los dos campos.
2. **`validacion.py`** lo revisa. `validar_radio("7.5")` devuelve
   `(7.5, "")`; `validar_radio("abc")` devuelve
   `(None, "Escriba un número, por ejemplo 5 o 7.5.")`. Si hay un mensaje, se
   muestra bajo el campo y no se calcula.
3. **`ui/trabajador.py`** lanza el cálculo en un **hilo aparte**. Un hilo es
   una segunda "línea de ejecución": mientras ella suma, la ventana sigue
   atendiendo el mouse y el teclado, y por eso no se congela ni con
   n = 10 000 000.
4. **`calculo.py`** hace la suma y devuelve un `Resultado` (perímetro, valor
   de control, errores y los rectángulos para dibujar).
5. **`ui/resultado.py`** escribe los números con **`formato.py`** (el perímetro
   "cuenta" hasta su valor nuevo y las demás filas aparecen en cascada).
6. **`graficas/`** dibuja los rectángulos animados y actualiza el radio en la
   curva 3D (que gira sola todo el tiempo).
7. **`sonido.py`** hace sonar el aviso de "resultado listo".

## 5. Las piezas, una por una

### 5.1 `perimetro_viviani.py` (núcleo)

`suma_de_riemann(radio, n, metodo)` es un `for` que recorre los n
subintervalos, calcula el punto de muestra `t_i` y acumula `f(t_i)`. Al final
multiplica por `delta_t`. El `metodo` decide dónde cae `t_i` dentro de cada
subintervalo: 0 (izquierda), 0,5 (punto medio) o 1 (derecha).

### 5.2 `calculo.py` (la misma suma, más rápida)

Un `for` de Python con diez millones de vueltas tarda varios segundos. Aquí
se usa **numpy**, que hace la misma operación sobre un millón de valores de
una sola vez:

```python
i = np.arange(inicio, fin)  # 0, 1, 2, ... (un bloque)
t = T_INICIAL + (i + desplazamiento) * delta_t
f = radio * np.sqrt(1 + np.cos(t) ** 2)
```

Se avanza **por bloques de 1 000 000** por dos razones: no llenar la memoria
y poder, entre un bloque y otro, avisar el progreso y preguntar si el usuario
canceló. Las sumas de los bloques se juntan con `math.fsum`, que suma sin
acumular error de redondeo.

Cuando n es mayor que 120 no tiene sentido dibujar n rectángulos (no se
verían). Se dibujan 120 barras; cada una agrupa varios subintervalos y su
altura es el **promedio** de f en el grupo, de modo que el área total dibujada
es exactamente la suma calculada. La ventana lo avisa con un texto.

### 5.3 `validacion.py`

Dos funciones, `validar_radio` y `validar_subintervalos`. Devuelven siempre
una pareja `(valor, mensaje)`. Casos que cubren: campo vacío, letras, `nan`,
`inf`, cero, negativos, decimales en n (`10.5`), miles con punto (`1.000`),
n mayor que 10 000 000. En R se acepta punto o coma al escribir; los
resultados se muestran siempre con punto decimal.

### 5.4 `formato.py`

`formatear_decimal(38.2016729)` → `38.201673`.
`formatear_cientifico(0.0003049)` → `3.049 × 10⁻⁴`.
`formatear_entero(10000000)` → `10 000 000`.

### 5.5 `tema.py`

Una tabla con cada color (un solo tema oscuro tipo grafito con acento verde
menta), las fuentes y la función
`razon_de_contraste`, que aplica la fórmula de accesibilidad WCAG. Una prueba
automática comprueba que todo texto tenga contraste suficiente (4,5 a 1).

### 5.6 `sonido.py`

Un sonido digital es una lista de números. Cada sonido se fabrica con
`math.sin` (una onda), se le da forma con una **envolvente** (sube rápido,
baja suave, para que no haga "clic" al cortarse) y se guarda como WAV en
memoria. Se reproduce con `winsound`, que ya viene con Python en Windows, en
un hilo propio para no detener la ventana.

### 5.7 `graficas/`

| Archivo | Qué dibuja |
|---|---|
| `curva3d.py` | La esfera translúcida, la curva y el punto doble (R, 0, 0), girando sola. Se dibuja con QPainter, no con matplotlib (ver abajo). |
| `riemann.py` | f(t) y los rectángulos, que aparecen de izquierda a derecha. |
| `lienzo.py` | Base de la gráfica de Riemann: dibujo y animación. |
| `animacion.py` | El reloj de la animación. |
| `estilo.py` | Tamaños de letra, grosores y colores de matplotlib. |


La animación no cuenta cuadros: en cada cuadro mira **cuánto tiempo real ha
pasado** y dibuja lo que corresponde a ese instante. Por eso dura lo mismo
(1,5 s) en un computador rápido que en uno lento, y se puede saltar con Esc.

### 5.8 `ui/`

| Archivo | Qué contiene |
|---|---|
| `ventana.py` | La ventana principal: arma las tarjetas y responde a los eventos. |
| `componentes.py` | Piezas visuales: fondo de puntos con auroras que se enciende alrededor del cursor, campos con una línea que se ilumina, y el botón Calcular (brilla al acercar el cursor y se llena para mostrar el progreso). |
| `resultado.py` | El panel que muestra los cuatro valores. |
| `estilos.py` | Convierte la paleta de `tema.py` en la hoja de estilos de Qt. |
| `trabajador.py` | El hilo de cálculo y su cancelación. |
| `sistema.py` | Pregunta a Windows si hay que reducir animaciones o agrandar el texto. |
| `logo.py` | Dibuja el logo (la curva vista de frente, un "8"). Lo usan la pantalla de carga, el encabezado y el icono del `.exe`. |
| `carga.py` | La pantalla de carga que aparece mientras se preparan numpy y matplotlib. |
| `creditos.py` | El panel de créditos con efecto de vidrio: toma una foto de la ventana, la desenfoca y la muestra a través de la tarjeta. Los nombres están en las listas al inicio del archivo. |

Qt funciona con **señales**: un objeto "avisa" que algo pasó y otro "escucha".
Por ejemplo, el hilo de cálculo emite la señal `terminado` con el resultado y
la ventana, que la estaba escuchando, lo muestra.

### 5.9 `app.py`

Crea cada pieza y se las entrega a la ventana. Es el único archivo que conoce
a todas.

Arranca por etapas: primero muestra la pantalla de carga (que solo necesita
Qt, así aparece en medio segundo) y después importa las librerías pesadas
(numpy y matplotlib), avisando cada paso en esa pantalla. Por eso esos
`import` están dentro de la función `crear_ventana` y no al principio del
archivo.

## 6. Dos cosas que conviene saber explicar

**¿Por qué izquierda y derecha dan lo mismo?** Porque f(0) = f(2π): la suma
por la izquierda usa f(t₀), …, f(tₙ₋₁) y la suma por la derecha usa
f(t₁), …, f(tₙ); solo cambian el primero y el último, que valen igual.

**¿Por qué el error baja tan rápido?** Porque f es una función suave y
periódica, y en ese caso la suma de Riemann con puntos equiespaciados converge
muchísimo más rápido de lo normal: con n ≈ 40 el error ya es del tamaño del
redondeo del computador (unas 16 cifras). A partir de ahí aumentar n no
mejora nada: por eso el error absoluto llega a mostrarse como 0 o como
números del orden de 10⁻¹⁵.

**¿Cómo se dibuja la curva 3D que gira?** En cada cuadro (unas 60 veces por
segundo) `curva3d.py` hace tres cosas con cada punto (x, y, z) de la curva y de
la esfera:

1. Lo gira un ángulo φ alrededor del eje Z (matriz de rotación):
   x₁ = x cos φ − y sen φ,  y₁ = x sen φ + y cos φ.
2. Inclina la vista un ángulo fijo hacia la cámara y se queda con dos
   coordenadas para la pantalla (proyección ortogonal).
3. Usa la tercera coordenada, la profundidad, para saber si el punto está
   delante o detrás de la esfera: lo de atrás se dibuja tenue.

El ángulo φ sale del tiempo transcurrido, así que gira a la misma velocidad
en cualquier computador. Si Windows tiene las animaciones desactivadas, la
curva se queda quieta.

**¿Por qué solo punto medio?** El núcleo acepta izquierda, derecha y punto
medio, pero la ventana usa siempre punto medio: en esta curva los tres dan
prácticamente lo mismo (izquierda y derecha, exactamente lo mismo).

## 7. Cómo se comprueba que funciona

```
python -m unittest -v
```

Las pruebas revisan, entre otras cosas: que L/R sea 7,640395578; que
`calculo.py` y `suma_de_riemann` coincidan; cada mensaje de validación; el
formato de los números; el contraste de los colores; que la animación dure
menos de 2 s; y que la curva 3D y la gráfica de Riemann se dibujen sin errores.
