# Cómo está organizado el código

Guía para que cualquier integrante pueda explicar el programa en la
sustentación. No hace falta saber Qt para seguirla.

## 1. La idea en una frase

El programa calcula la longitud de la Ventana de Viviani sumando áreas de
rectángulos (suma de Riemann) y la compara con un valor de control conocido.

    r(t) = (R cos²t, R sen t cos t, R sen t),   t ∈ [0, 2π]
    f(t) = ‖r′(t)‖ = R·√(1 + cos²t)
    L ≈ Σ f(tᵢ)·Δt,   con Δt = 2π / n  y  tᵢ = (i − ½)·Δt
    Valor de control: L = 7.640395578·R

## 2. Dos programas, un mismo cálculo

| Programa | Cómo se ejecuta | Para qué sirve |
|---|---|---|
| Consola | `python perimetro_viviani.py` | Versión mínima, sin librerías externas. Es el **núcleo matemático**. |
| Ventana | `python viviani_app.py` (o el `.exe`) | Lo mismo, con gráficas, animación y sonido. |

La versión de ventana **no vuelve a inventar la matemática**: toma de
`perimetro_viviani.py` las constantes (el intervalo, el máximo de n y el valor
de control) y una prueba automática exige que ambas den el mismo resultado.

## 3. Mapa de archivos

```
perimetro_viviani.py        Núcleo: funcion_subintegral() y suma_de_riemann()
test_perimetro_viviani.py   Pruebas del núcleo
viviani_app.py              Lanzador de la ventana (4 líneas útiles)

src/viviani/
  calculo.py       La misma suma, por bloques y con numpy (rápida y cancelable)
  validacion.py    Revisa lo que el usuario escribe en R y n
  formato.py       Escribe los números (punto decimal, 10⁻⁴, cifras correctas)
  tema.py          Los colores (un solo tema, plateado) y las fuentes
  sonido.py        Fabrica y reproduce los cuatro sonidos
  animacion.py     El reloj de todas las animaciones
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
   muestra bajo el campo (que se pone rojo) y no se calcula.
3. **`ui/trabajador.py`** lanza el cálculo en un **hilo aparte**. Un hilo es
   una segunda "línea de ejecución": mientras ella suma, la ventana sigue
   atendiendo el mouse y el teclado, y por eso no se congela ni con
   n = 10 000 000.
4. **`calculo.py`** hace la suma y devuelve un `Resultado` (perímetro, valor
   de control, errores y los rectángulos para dibujar).
5. **`ui/resultado.py`** escribe los números con **`formato.py`**: el perímetro
   "cuenta" hasta su valor nuevo, sus cifras correctas quedan en el color del
   texto y las que aún no coinciden en un color de aviso, y el medidor de cifras se llena.
6. **`graficas/`** hace el **barrido**: en la gráfica de Riemann los
   rectángulos crecen uno tras otro y, al mismo ritmo, en la curva 3D aparecen
   los puntos r(tᵢ) con un cometa que los va recorriendo.
7. **`sonido.py`** hace sonar el acorde de marimba de "resultado listo".

Mientras tanto, en la órbita alrededor de la esfera, un destello viaja por
los hilos: de la tarjeta de datos a la esfera al calcular, y de la esfera a
las tarjetas de resultado al terminar.

## 5. Las piezas, una por una

### 5.1 `perimetro_viviani.py` (núcleo)

`suma_de_riemann(radio, n, metodo)` es un `for` que recorre los n
subintervalos, calcula el punto de muestra `t_i` y acumula `f(t_i)`. Al final
multiplica por `delta_t`. El `metodo` decide dónde cae `t_i` dentro de cada
subintervalo: 0 (izquierda), 0.5 (punto medio) o 1 (derecha). La ventana usa
siempre el punto medio.

### 5.2 `calculo.py` (la misma suma, más rápida)

Un `for` de Python con diez millones de vueltas tarda varios segundos. Aquí
se usa **numpy**, que hace la misma operación sobre un millón de valores de
una sola vez:

```python
i = np.arange(inicio, fin)  # 0, 1, 2, ... (un bloque)
f = radio * np.sqrt(1 + np.cos(T_INICIAL + (i + 0.5) * delta_t) ** 2)
suma += float(np.sum(f))
```

Se avanza **por bloques de 1 000 000** por dos razones: no llenar la memoria
y poder, entre un bloque y otro, avisar el progreso y preguntar si el usuario
canceló (con Esc).

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

- `formatear_decimal(38.2016729)` → `38.201673`.
- `formatear_cientifico(0.0003049)` → `3.049 × 10⁻⁴`, y `con_exponente`
  lo convierte a `3.049 × 10<sup>−4</sup>` para mostrarlo en la ventana (la
  fuente de Windows no tiene el signo menos en superíndice).
- `formatear_entero(10000000)` → `10 000 000`.
- `cifras_correctas(error_relativo)`: si el error relativo es 10⁻⁵, son 5
  cifras correctas. Con error 0 son 16, todo lo que cabe en un `float`.
- `prefijo_comun("38.201673", "38.201978")` → 6: cuántos caracteres coinciden
  al inicio. Con eso se pinta distinta la parte correcta del perímetro.

### 5.5 `tema.py`

Una tabla con cada color: un solo tema oscuro y plateado (fondo casi negro
con estrellas, texto blanco, un degradado de blanco a plata como sello) y un
naranja de señal para lo que hay que mirar (puntos de muestra, cifras que
aún no son correctas). También están las fuentes, `con_alfa` (un color con
transparencia para dibujar) y `razon_de_contraste`, la fórmula de
accesibilidad WCAG. Una prueba automática comprueba que todo texto tenga
contraste suficiente (4.5 a 1).

### 5.6 `sonido.py`

Un sonido digital es una lista de números. Cada nota es una suma de senos
(con numpy) a la que se le da forma con una **envolvente** (sube rápido, baja
como e^(−t/τ), y se apaga al final para que no haga "clic"). Una barra de
marimba vibra con parciales 1, 3.93 y 9.2 veces la nota, y los agudos se
apagan antes: por eso suena a **madera**. Hay cuatro sonidos:

| Sonido | Qué es |
|---|---|
| Clic | Un golpe corto de madera al pulsar cualquier botón (Calcular, Créditos, Cerrar, las capas). |
| Resultado | Acorde mayor de marimba que sube (do-mi-sol-do). |
| Error | Dos golpes graves que bajan (fa-re). |
| Créditos | Un "colchón" de aire (acorde la mayor con notas desafinadas 1.5 Hz, que respira) con un arpegio encima. |

Se guardan como WAV en memoria y se reproducen con `winsound` (viene con
Python en Windows) en un hilo propio para no detener la ventana.

### 5.7 `animacion.py` y `graficas/`

`animacion.py` tiene el reloj de **todas** las animaciones. No cuenta
cuadros: en cada cuadro mira **cuánto tiempo real ha pasado** y dibuja lo que
corresponde a ese instante. Por eso dura lo mismo en un computador rápido que
en uno lento, y se puede saltar (con Esc o con un clic).

| Archivo | Qué dibuja |
|---|---|
| `curva3d.py` | La esfera, el cilindro, la curva con un cometa que la recorre, el punto doble (R, 0, 0) y, tras calcular, los puntos r(tᵢ). Gira sola. |
| `riemann.py` | f(t), los rectángulos que crecen uno tras otro y la ficha con los valores de la barra bajo el mouse. |
| `barrido.py` | El ritmo común: cuándo empieza a crecer cada rectángulo (las dos gráficas lo usan para ir sincronizadas). |

Las dos gráficas se dibujan **a mano con QPainter** (líneas, rectángulos,
degradados), sin matplotlib: así arrancan más rápido, se animan a 60 cuadros
por segundo y el `.exe` pesa menos.

### 5.8 `ui/`

| Archivo | Qué contiene |
|---|---|
| `ventana.py` | La ventana principal: arma la distribución orbital (cuatro tarjetas alrededor de la esfera), conecta las dos gráficas y responde a los eventos. |
| `componentes.py` | Piezas visuales: el cielo con estrellas que se encienden alrededor del cursor, las tarjetas de vidrio, las cajas de los datos, los chips, el botón Calcular (brilla y lo cruza un reflejo al acercar el cursor; se llena con el progreso) y la capa de pulsos (cada clic suelta una onda de luz). |
| `formula.py` | Dibuja fórmulas matemáticas: integrales y sumas con sus límites, fracciones con raya, raíces y exponentes, cada pieza con el espacio que necesita (ver abajo). |
| `resultado.py` | El panel del perímetro, el medidor de cifras correctas y los errores. |
| `estilos.py` | Convierte la paleta de `tema.py` en la hoja de estilos de Qt. |
| `trabajador.py` | El hilo de cálculo y su cancelación. |
| `sistema.py` | Pregunta a Windows si hay que reducir animaciones o agrandar el texto. |
| `logo.py` | Dibuja el logo (la curva vista de frente, un "8"). Lo usan la pantalla de carga, el encabezado, los créditos y el icono del `.exe`. |
| `carga.py` | La pantalla de carga: la curva se va trazando de t = 0 a t = 2π a medida que avanza la carga. |
| `creditos.py` | La tarjeta de créditos: sólida, con el logo girando. Al abrir y cerrar se anima como una sola imagen (aparece y crece un poco), así solo se repinta su rectángulo. Los nombres están en las listas al inicio del archivo. |

Qt funciona con **señales**: un objeto "avisa" que algo pasó y otro "escucha".
Por ejemplo, el hilo de cálculo emite la señal `terminado` con el resultado y
la ventana, que la estaba escuchando, lo muestra. Igual con las gráficas: la
de Riemann emite `t_resaltado(t)` al mover el mouse y la curva 3D, que la
escucha, señala ese punto.

### 5.9 `app.py`

Crea cada pieza y se las entrega a la ventana. Es el único archivo que conoce
a todas.

Arranca por etapas: primero muestra la pantalla de carga (que solo necesita
Qt, así aparece de inmediato) y después importa numpy, fabrica los sonidos y
arma las gráficas, avisando cada paso en esa pantalla. Por eso esos `import`
están dentro de la función `crear_ventana` y no al principio del archivo.

## 6. Cosas que conviene saber explicar

**¿Por qué el error baja tan rápido?** Porque f es una función suave y
periódica, y en ese caso la suma de Riemann con puntos equiespaciados converge
muchísimo más rápido de lo normal: con n = 4 hay 2 cifras correctas, con
n = 10 hay 5, con n = 20 hay 9 y con n ≈ 40 el error ya es del tamaño del
redondeo del computador (unas 16 cifras). A partir de ahí aumentar n no
mejora nada: por eso el error llega a mostrarse como 0 o como números del
orden de 10⁻¹⁵. Con ↑ en el campo n (multiplica n por 10) se ve en vivo.

**¿Qué tiene que ver el cilindro?** La Ventana de Viviani es la
intersección de la esfera x² + y² + z² = R² con el cilindro
(x − R/2)² + y² = (R/2)². Sobre el cilindro x² + y² = R·x, así que la esfera
deja z² ≤ R² − R·x: cada línea vertical del cilindro dibujada en la escena va
de una rama de la curva a la otra.

**¿Qué es la flecha que aparece al pasar el mouse por Riemann?** Es el
vector velocidad r′(t) = R(−sen 2t, cos 2t, cos t) en el punto r(t). Su
longitud es ‖r′(t)‖ = R√(1 + cos²t) = f(t): **la altura de cada rectángulo es
la rapidez con que se recorre la curva**. Donde la flecha es larga, el
rectángulo es alto.

**¿Cómo se dibujan las fórmulas?** Un texto con HTML no sabe poner los
límites de una suma arriba y abajo, y recorta los exponentes. `formula.py`
trata cada pieza como una **caja** que sabe medirse (ancho, cuánto sube y
cuánto baja de la línea base) y dibujarse. Con esas medidas, una fracción
pone el numerador justo encima de la raya y el denominador justo debajo; la
suma pone n arriba de la Σ e i = 1 abajo; la raíz estira su raya sobre todo lo
que contiene. Así nada se recorta ni se encima.

**¿Cómo se dibuja la curva 3D que gira?** En cada cuadro (unas 60 veces por
segundo) `curva3d.py` hace tres cosas con cada punto (x, y, z) de la curva, la
esfera y el cilindro:

1. Lo gira un ángulo φ alrededor del eje Z (matriz de rotación):
   x₁ = x cos φ − y sen φ,  y₁ = x sen φ + y cos φ.
2. Inclina la vista un ángulo fijo hacia la cámara y se queda con dos
   coordenadas para la pantalla (proyección ortogonal).
3. Usa la tercera coordenada, la profundidad, para decidir cómo se ve: la
   curva se reparte en 6 niveles de profundidad; lo más lejano es tenue y
   delgado y lo más cercano brillante y grueso.

Cada cuadro de la escena se guarda en una imagen: si otra cosa pide
repintar encima (la onda de un clic, los créditos), se copia esa imagen en
vez de volver a calcular la escena. Así nunca se dibuja dos veces en el mismo
cuadro y la animación no da tirones.

El ángulo φ sale del tiempo transcurrido, así que gira a la misma velocidad
en cualquier computador. Si Windows tiene las animaciones desactivadas, la
curva se queda quieta y no hay cometa ni barrido.

**¿Por qué solo punto medio?** El núcleo acepta izquierda, derecha y punto
medio, pero la ventana usa siempre punto medio: en esta curva los tres dan
prácticamente lo mismo (izquierda y derecha, exactamente lo mismo, porque
f(0) = f(2π)).

## 7. Cómo se comprueba que funciona

```
python -m unittest -v
```

Las pruebas revisan, entre otras cosas: que L/R sea 7.640395578; que
`calculo.py` y `suma_de_riemann` coincidan; cada mensaje de validación; el
formato de los números y las cifras correctas; el contraste de los colores;
que la curva esté sobre la esfera y el cilindro y que ‖r′(t)‖ = f(t)/R; los
sonidos (duración y volumen); y que la ventana completa calcule y muestre un
resultado sin errores.

## 8. Teclado

| Tecla | Acción |
|---|---|
| Enter | Calcular |
| ↑ / ↓ en el campo n | Multiplicar o dividir n entre 10 |
| Esc | Cerrar los créditos, cancelar el cálculo en curso o saltar la animación |
