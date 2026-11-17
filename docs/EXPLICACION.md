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
  formato.py       Escribe los números con coma decimal
  tema.py          Colores del modo claro y oscuro
  sonido.py        Fabrica y reproduce los tres sonidos
  graficas/        Las tres gráficas
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
2. **`validacion.py`** lo revisa. `validar_radio("7,5")` devuelve
   `(7.5, "")`; `validar_radio("abc")` devuelve
   `(None, "Escriba un número, por ejemplo 5 o 7,5.")`. Si hay un mensaje, se
   muestra bajo el campo y no se calcula.
3. **`ui/trabajador.py`** lanza el cálculo en un **hilo aparte**. Un hilo es
   una segunda "línea de ejecución": mientras ella suma, la ventana sigue
   atendiendo el mouse y el teclado, y por eso no se congela ni con
   n = 10 000 000.
4. **`calculo.py`** hace la suma y devuelve un `Resultado` (perímetro, valor
   de control, errores y los rectángulos para dibujar).
5. **`ui/resultado.py`** escribe los números con **`formato.py`**.
6. **`graficas/`** dibuja: la curva 3D, los rectángulos animados y el punto
   actual en la gráfica de convergencia.
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
n mayor que 10 000 000. Aceptan coma o punto decimal en R.

### 5.4 `formato.py`

`formatear_decimal(38.201673)` → `38,201673`.
`formatear_cientifico(0.0003049)` → `3,049 × 10⁻⁴`.
`formatear_entero(10000000)` → `10 000 000`.

### 5.5 `tema.py`

Una tabla con cada color en sus dos versiones (claro y oscuro) y la función
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
| `curva3d.py` | La esfera translúcida, la curva y el punto doble (R, 0, 0). Se rota con el mouse o con las flechas. |
| `riemann.py` | f(t) y los rectángulos, que aparecen de izquierda a derecha. |
| `convergencia.py` | El error relativo frente a n, en escala logarítmica, con el cálculo actual resaltado. |
| `lienzo.py` | Lo que las tres comparten: cambiar de tema y exportar a PNG. |
| `animacion.py` | El reloj de la animación. |
| `estilo.py` | Tamaños de letra y grosores para pantalla y para exportar. |

Cada gráfica tiene **una sola función de dibujo** que sirve tanto para la
pantalla como para el PNG del reporte (300 ppp, fondo blanco).

La animación no cuenta cuadros: en cada cuadro mira **cuánto tiempo real ha
pasado** y dibuja lo que corresponde a ese instante. Por eso dura lo mismo
(1,5 s) en un computador rápido que en uno lento, y se puede saltar con Esc.

### 5.8 `ui/`

| Archivo | Qué contiene |
|---|---|
| `ventana.py` | La ventana principal: arma las tarjetas y responde a los eventos. |
| `componentes.py` | Controles reutilizables: campo con mensaje, interruptor, selector de método. |
| `resultado.py` | La tarjeta que muestra los cuatro valores. |
| `estilos.py` | Convierte la paleta de `tema.py` en la hoja de estilos de Qt. |
| `trabajador.py` | El hilo de cálculo y su cancelación. |
| `sistema.py` | Pregunta a Windows si hay que reducir animaciones o agrandar el texto. |
| `iconos.py` | Carga los iconos (Lucide, licencia libre). |

Qt funciona con **señales**: un objeto "avisa" que algo pasó y otro "escucha".
Por ejemplo, el hilo de cálculo emite la señal `terminado` con el resultado y
la ventana, que la estaba escuchando, lo muestra.

### 5.9 `app.py`

Crea cada pieza y se las entrega a la ventana. Es el único archivo que conoce
a todas.

## 6. Dos cosas que conviene saber explicar

**¿Por qué izquierda y derecha dan lo mismo?** Porque f(0) = f(2π): la suma
por la izquierda usa f(t₀), …, f(tₙ₋₁) y la suma por la derecha usa
f(t₁), …, f(tₙ); solo cambian el primero y el último, que valen igual.

**¿Por qué el error baja tan rápido?** Porque f es una función suave y
periódica, y en ese caso la suma de Riemann con puntos equiespaciados converge
muchísimo más rápido de lo normal: con n ≈ 40 el error ya es del tamaño del
redondeo del computador (unas 16 cifras). A partir de ahí aumentar n no
mejora nada; la gráfica de convergencia lo muestra con la línea "Límite de
precisión del computador".

## 7. Cómo se comprueba que funciona

```
python -m unittest -v
```

Las pruebas revisan, entre otras cosas: que L/R sea 7,640395578; que
`calculo.py` y `suma_de_riemann` coincidan; cada mensaje de validación; el
formato de los números; el contraste de los colores; que la animación dure
menos de 2 s; y que la ventana calcule, cancele y exporte sin errores.
