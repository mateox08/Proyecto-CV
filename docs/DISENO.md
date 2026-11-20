# Especificación de diseño: Perímetro de la Ventana de Viviani

> **Nota (2026-11-19):** esta especificación describe el primer diseño. El
> diseño actual la reemplaza en estos puntos: tema claro único inspirado en
> tarjetas de vidrio con brillo al pasar el mouse; sin gráfica de convergencia;
> sin selector de método (siempre punto medio); sin interruptor de sonido
> (siempre activo); sin textos de ayuda bajo los campos; la curva 3D gira sola
> (dibujada con QPainter) y no se arrastra; números con punto decimal. Los
> colores y fuentes vigentes están en `src/viviani/tema.py`.

Documento para implementar la interfaz en paralelo. Stack: PySide6-Essentials + matplotlib + numpy + `winsound` (ver `docs/decisiones.md`).

Unidades: **DIP** = píxel independiente del dispositivo (píxel lógico de Qt). A 100 % de escala, 1 DIP = 1 px; a 125 %, 1 DIP = 1,25 px. **pt** = punto tipográfico (1 pt = 1,333 DIP a 96 ppp).

---

## 0. Fuentes consultadas: Human Interface Guidelines de Apple

Las HIG se usan como **principios** (jerarquía, contraste, retroalimentación, movimiento con propósito). No se usa ningún componente, fuente, icono ni recurso de Apple: la app corre en Windows con Segoe UI Variable e iconos Lucide.

La página HTML de las HIG devuelve solo el título (requiere JavaScript). El contenido se leyó desde el JSON de datos `https://developer.apple.com/tutorials/data/design/human-interface-guidelines/<sección>.json` el 2026-11-16.

| Sección | ¿Se leyó? | Qué se tomó (parafraseado) |
|---|---|---|
| accessibility | Sí (JSON; HTML vacío) | Contraste según WCAG AA (4,5:1 texto normal, 3:1 texto grande/negrita); permitir agrandar texto; con "reducir movimiento" quitar zoom/escalado y sustituir desplazamientos por fundidos; no depender solo del color; navegación completa con teclado; áreas de clic mínimas y espacio alrededor |
| color | Parcial (primer ~55 % del JSON) | Uso consistente del color con un solo significado; variantes para claro y oscuro; no depender solo del color (añadir texto o forma); el acento para la acción principal |
| typography | Parcial (primer ~35 % del JSON) | Tamaños mínimos legibles; evitar pesos finos; jerarquía con tamaño, peso y color; pocas familias; adaptar el layout al texto grande. **No** se encontró guía sobre cifras tabulares en la parte leída |
| layout | Sí | Lo importante arriba y al inicio de la lectura; agrupar con espacio; adaptar a cambios de tamaño sin cambiar la funcionalidad; apilar en vertical con texto grande |
| motion | Sí | Movimiento solo con propósito; breve y preciso; no obligar a esperar animaciones, dejar omitirlas; no transmitir información solo con movimiento |
| feedback | Sí | Estado visible en línea, cerca de lo que describe; alertas solo para lo crítico; combinar color, texto y sonido; explicar por qué falló una acción |
| dark-mode | Sí | Seguir la configuración del sistema sin ajuste propio; probar ambos modos; colores con variante clara y oscura; contraste mínimo 4,5:1 y preferible 7:1 en texto pequeño |
| charts | Sí | Ejes con rótulos cortos; leyenda cuando color o forma distinguen series; nunca solo color (añadir forma o trazo); destacar pocos datos clave; poca rejilla; los datos son lo más prominente |
| charting-data | Sí | Título o resumen que dé el mensaje principal; estilo consistente entre gráficas relacionadas; tamaño acorde al propósito |
| playing-audio | Sí | Silenciar sonidos no esenciales cuando el usuario lo pide; sonidos cortos; no transmitir nada solo con sonido |
| keyboards | Sí | No reasignar atajos estándar; atajos propios solo para lo más frecuente; acceso completo con teclado |
| entering-data | Sí | Validar en cuanto se escribe y mostrar el problema de inmediato; valores por defecto razonables; etiqueta y texto de ejemplo en el campo |
| writing | Sí | Botones con verbos; mensajes de error junto al campo, sin culpar y diciendo cómo corregir; lenguaje simple y consistente |
| progress-indicators | Sí | Preferir progreso determinado; permitir cancelar; ubicación consistente; indicador que no parezca congelado |
| buttons | Sí | Un solo botón prominente por vista; la acción principal responde a Enter (Return); etiquetas que empiezan con verbo |
| focus-and-selection | Sí | No mover el foco sin acción del usuario; anillo de foco para campos de texto |

Nada de este documento se atribuye a las HIG si no aparece en la columna "Qué se tomó". Las cifras de WCAG se verificaron además con la fórmula de luminancia relativa de WCAG 2.x.

---

## 1. Jerarquía y layout

### 1.1 Principio

Lo principal es **escribir R y n y leer el perímetro**. Por eso la columna de entrada y resultado está a la izquierda (donde empieza la lectura), arriba, con la tipografía más grande. Las gráficas acompañan a la derecha.

### 1.2 Tamaños

| Concepto | Valor |
|---|---|
| Tamaño inicial | Maximizada si la pantalla tiene ≤ 1920×1080 DIP; si no, 1600×900 DIP centrada |
| Tamaño mínimo | **1024×640 DIP** (cabe en 1280×720 a 100 % y en 1366×768 a 100 %) |
| Columna izquierda | 360 DIP de ancho fijo (mínimo 320); crece con el factor de texto hasta 480 DIP |
| Margen exterior | 24 DIP (16 DIP si el ancho < 1280) |
| Separación entre tarjetas | 16 DIP |

Nota para el video: a 1920×1080 físicos con escala de Windows al 125 %, la ventana mide 1536×864 DIP. El diseño debe verse completo en **ambos** casos (100 % y 125 %). Recomendado grabar a 125 %.

### 1.3 Esquema a 1920×1080 (ancho ≥ 1280 DIP, modo "rejilla")

```
+--------------------------------------------------------------------------------------------+
| Perímetro de la Ventana de Viviani                                     [Sonido: Activado o]|  <- barra superior 56 DIP
| Aproximación con suma de Riemann                                                           |
+--------------------------+-----------------------------------------------------------------+
| DATOS                    | CURVA EN 3D                      [↺ Restablecer] [Exportar PNG] |
| Radio de la esfera R     | +-------------------------------+ SUMA DE RIEMANN  [Exportar PNG]|
| [ 5                 cm ] | |                               | +-------------------------------+|
| Número real positivo...  | |        esfera + curva         | |  f(t) con rectángulos         ||
| Número de subintervalos n| |        (rotable)              | |                               ||
| [ 10                   ] | |                               | +-------------------------------+|
| Entero entre 1 y ...     | |                               | (aviso de muestra, si aplica)   |
| [  Calcular  ] [Cancelar]| |                               | CONVERGENCIA     [Exportar PNG] |
| ▓▓▓▓▓▓░░░ Calculando 45 %| |                               | +-------------------------------+|
+--------------------------+ |                               | |  error relativo vs n (log-log)||
| RESULTADO                | +-------------------------------+ |                               ||
| Para R = 5 cm, n = 10,   | Arrastre para rotar · Flechas    | +-------------------------------+|
| punto medio              |                                  |                                 |
| Perímetro aproximado     |                                  |                                 |
|   38,201673 cm  (28 pt)  |                                  |                                 |
| Valor de control  ...    |                                  |                                 |
| Error absoluto    ...    |                                  |                                 |
| Error relativo    ...    |                                  |                                 |
+--------------------------+                                  |                                 |
| OPCIONES                 |                                  |                                 |
| Método de la suma        |                                  |                                 |
| [Izquierda|Punto medio|Derecha]                             |                                 |
+--------------------------+-----------------------------------------------------------------+
| (barra de estado: "Imagen guardada en: ..." / avisos breves)                    28 DIP      |
+--------------------------------------------------------------------------------------------+
```

Área de gráficas (a la derecha de la columna): rejilla de 2 columnas iguales; la tarjeta 3D ocupa la columna izquierda en toda la altura; "Suma de Riemann" y "Convergencia" se reparten la columna derecha en 55 % / 45 % de altura. Esquema de nombres de tarjetas: **Curva en 3D**, **Suma de Riemann**, **Convergencia**.

### 1.4 Comportamiento al redimensionar

| Ancho disponible (DIP) | Comportamiento |
|---|---|
| ≥ 1280 | Modo rejilla (esquema anterior) |
| 1024–1279 | Modo pestañas: las tres gráficas en un `QTabWidget` con las pestañas "Curva en 3D", "Suma de Riemann", "Convergencia". Se conserva la pestaña elegida. Margen 16 DIP |
| Alto < 720 o texto ampliado ≥ 150 % | La columna izquierda va dentro de un `QScrollArea` vertical; nunca se recorta texto |

- Las gráficas se reescalan con `tight_layout` / `constrained_layout` al cambiar de tamaño (con un retardo de 100 ms para no repintar en cada píxel del arrastre).
- La funcionalidad es la misma en todos los tamaños; solo cambia cuántas gráficas se ven a la vez.
- La división columna/gráficas **no** es arrastrable (menos cosas que explicar).

---

## 2. Paleta

Valores calculados con la fórmula WCAG 2.x (luminancia relativa, sRGB) en Python stdlib. Umbrales: **4,5:1** texto normal; **3:1** texto grande y elementos gráficos o de interfaz.

### 2.1 Tokens

| Token | Claro | Oscuro | Uso |
|---|---|---|---|
| `fondo` | `#F4F6F9` | `#14171C` | Fondo de la ventana |
| `superficie` | `#FFFFFF` | `#1E2229` | Tarjetas, campos, fondo de gráficas |
| `superficie_deshab` | `#EEF0F3` | `#262B33` | Campo/botón deshabilitado |
| `texto` | `#1A1D23` | `#E8EAED` | Texto primario, línea f(t) |
| `texto_sec` | `#4A5361` | `#A9B1BC` | Ayudas, unidades, subtítulos |
| `texto_deshab` | `#5C6573` | `#8B939E` | Texto deshabilitado |
| `acento` | `#1F5FBF` | `#7AAEFF` | Botón primario, selección, interruptor activo |
| `acento_hover` | `#174C99` | `#A3C6FF` | Botón primario con el puntero encima |
| `texto_sobre_acento` | `#FFFFFF` | `#0B1220` | Texto/icono sobre `acento` |
| `error` | `#B3261E` | `#FF8A80` | Texto, icono y borde de error |
| `fondo_error` | `#FDECEA` | `#3B1A18` | Banda de error de cálculo |
| `exito` | `#1B7A3A` | `#6FD08C` | Mensaje "Imagen guardada" |
| `aviso` | `#8A5A00` | `#F2C14E` | Texto e icono de aviso |
| `fondo_aviso` | `#FFF4DB` | `#3A2E10` | Banda de aviso (muestra representativa, cancelado) |
| `borde` | `#7A8494` | `#7D8693` | Borde de campos, interruptor apagado, botón secundario |
| `separador` | `#D5DAE1` | `#3A404A` | Líneas divisorias y rejilla de gráficas (decorativo) |
| `foco` | `#0B57D0` | `#9CC3FF` | Anillo de foco |
| `tooltip_fondo` | `#2B3038` | `#E8EAED` | Fondo de tooltip |
| `tooltip_texto` | `#FFFFFF` | `#14171C` | Texto de tooltip |
| `serie_azul` | `#0072B2` | `#56B4E9` | Curva de Viviani; rectángulos; "Punto medio" en convergencia |
| `serie_naranja` | `#C24E00` | `#F28E2B` | Puntos de muestra; "Izquierda" en convergencia |
| `serie_verde` | `#00805C` | `#3CC79A` | Reservado (cilindro si se añade) |
| `serie_morado` | `#8E3B87` | `#D98CD0` | "Derecha" en convergencia |
| `punto_doble` | `#B3261E` | `#FF8A80` | Punto doble (R, 0, 0) |
| `esfera` | `#7A8494`, alfa 0,12 | `#7D8693`, alfa 0,18 | Superficie de la esfera; malla con alfa 0,35 |

Las series derivan de la paleta Okabe-Ito (apta para daltonismo), oscurecidas en modo claro para llegar a 3:1.

### 2.2 Razones de contraste calculadas

Modo claro:

| Primer plano | Fondo | Razón | Mínimo | Cumple |
|---|---|---|---|---|
| texto `#1A1D23` | fondo `#F4F6F9` | 15,59:1 | 4,5 | Sí |
| texto `#1A1D23` | superficie `#FFFFFF` | 16,88:1 | 4,5 | Sí |
| texto `#1A1D23` | fondo_aviso `#FFF4DB` | 15,45:1 | 4,5 | Sí |
| texto_sec `#4A5361` | fondo `#F4F6F9` | 7,18:1 | 4,5 | Sí |
| texto_sec `#4A5361` | superficie `#FFFFFF` | 7,77:1 | 4,5 | Sí |
| texto_sec `#4A5361` | superficie_deshab `#EEF0F3` | 6,81:1 | 4,5 | Sí |
| texto_deshab `#5C6573` | superficie_deshab `#EEF0F3` | 5,16:1 | 4,5 | Sí |
| texto_sobre_acento `#FFFFFF` | acento `#1F5FBF` | 6,09:1 | 4,5 | Sí |
| texto_sobre_acento `#FFFFFF` | acento_hover `#174C99` | 8,30:1 | 4,5 | Sí |
| acento `#1F5FBF` (texto) | superficie `#FFFFFF` | 6,09:1 | 4,5 | Sí |
| acento `#1F5FBF` (texto) | fondo `#F4F6F9` | 5,63:1 | 4,5 | Sí |
| error `#B3261E` | superficie `#FFFFFF` | 6,54:1 | 4,5 | Sí |
| error `#B3261E` | fondo `#F4F6F9` | 6,04:1 | 4,5 | Sí |
| error `#B3261E` | fondo_error `#FDECEA` | 5,72:1 | 4,5 | Sí |
| exito `#1B7A3A` | superficie `#FFFFFF` | 5,40:1 | 4,5 | Sí |
| exito `#1B7A3A` | fondo `#F4F6F9` | 4,98:1 | 4,5 | Sí |
| aviso `#8A5A00` | superficie `#FFFFFF` | 5,93:1 | 4,5 | Sí |
| aviso `#8A5A00` | fondo_aviso `#FFF4DB` | 5,42:1 | 4,5 | Sí |
| tooltip_texto `#FFFFFF` | tooltip_fondo `#2B3038` | 13,27:1 | 4,5 | Sí |
| borde `#7A8494` | superficie `#FFFFFF` | 3,78:1 | 3 | Sí |
| foco `#0B57D0` | superficie `#FFFFFF` | 6,39:1 | 3 | Sí |
| foco `#0B57D0` | fondo `#F4F6F9` | 5,90:1 | 3 | Sí |
| error (borde) `#B3261E` | superficie `#FFFFFF` | 6,54:1 | 3 | Sí |
| interruptor: pulgar `#FFFFFF` | acento `#1F5FBF` | 6,09:1 | 3 | Sí |
| serie_azul `#0072B2` | superficie `#FFFFFF` | 5,19:1 | 3 | Sí |
| serie_naranja `#C24E00` | superficie `#FFFFFF` | 4,79:1 | 3 | Sí |
| serie_verde `#00805C` | superficie `#FFFFFF` | 4,95:1 | 3 | Sí |
| serie_morado `#8E3B87` | superficie `#FFFFFF` | 6,72:1 | 3 | Sí |
| punto_doble `#B3261E` | superficie `#FFFFFF` | 6,54:1 | 3 | Sí |
| separador `#D5DAE1` | superficie `#FFFFFF` | 1,41:1 | — | Decorativo (exento) |

Modo oscuro:

| Primer plano | Fondo | Razón | Mínimo | Cumple |
|---|---|---|---|---|
| texto `#E8EAED` | fondo `#14171C` | 14,90:1 | 4,5 | Sí |
| texto `#E8EAED` | superficie `#1E2229` | 13,24:1 | 4,5 | Sí |
| texto `#E8EAED` | fondo_aviso `#3A2E10` | 11,04:1 | 4,5 | Sí |
| texto_sec `#A9B1BC` | fondo `#14171C` | 8,30:1 | 4,5 | Sí |
| texto_sec `#A9B1BC` | superficie `#1E2229` | 7,37:1 | 4,5 | Sí |
| texto_sec `#A9B1BC` | superficie_deshab `#262B33` | 6,57:1 | 4,5 | Sí |
| texto_deshab `#8B939E` | superficie_deshab `#262B33` | 4,58:1 | 4,5 | Sí |
| texto_sobre_acento `#0B1220` | acento `#7AAEFF` | 8,31:1 | 4,5 | Sí |
| texto_sobre_acento `#0B1220` | acento_hover `#A3C6FF` | 10,77:1 | 4,5 | Sí |
| acento `#7AAEFF` (texto) | superficie `#1E2229` | 7,09:1 | 4,5 | Sí |
| acento `#7AAEFF` (texto) | fondo `#14171C` | 7,98:1 | 4,5 | Sí |
| error `#FF8A80` | superficie `#1E2229` | 6,99:1 | 4,5 | Sí |
| error `#FF8A80` | fondo `#14171C` | 7,87:1 | 4,5 | Sí |
| error `#FF8A80` | fondo_error `#3B1A18` | 6,83:1 | 4,5 | Sí |
| exito `#6FD08C` | superficie `#1E2229` | 8,42:1 | 4,5 | Sí |
| exito `#6FD08C` | fondo `#14171C` | 9,47:1 | 4,5 | Sí |
| aviso `#F2C14E` | superficie `#1E2229` | 9,51:1 | 4,5 | Sí |
| aviso `#F2C14E` | fondo_aviso `#3A2E10` | 7,93:1 | 4,5 | Sí |
| tooltip_texto `#14171C` | tooltip_fondo `#E8EAED` | 14,90:1 | 4,5 | Sí |
| borde `#7D8693` | superficie `#1E2229` | 4,33:1 | 3 | Sí |
| foco `#9CC3FF` | superficie `#1E2229` | 8,86:1 | 3 | Sí |
| foco `#9CC3FF` | fondo `#14171C` | 9,98:1 | 3 | Sí |
| error (borde) `#FF8A80` | superficie `#1E2229` | 6,99:1 | 3 | Sí |
| interruptor: pulgar `#0B1220` | acento `#7AAEFF` | 8,31:1 | 3 | Sí |
| serie_azul `#56B4E9` | superficie `#1E2229` | 6,92:1 | 3 | Sí |
| serie_naranja `#F28E2B` | superficie `#1E2229` | 6,60:1 | 3 | Sí |
| serie_verde `#3CC79A` | superficie `#1E2229` | 7,47:1 | 3 | Sí |
| serie_morado `#D98CD0` | superficie `#1E2229` | 6,54:1 | 3 | Sí |
| punto_doble `#FF8A80` | superficie `#1E2229` | 6,99:1 | 3 | Sí |
| separador `#3A404A` | superficie `#1E2229` | 1,53:1 | — | Decorativo (exento) |

Exportación PNG (siempre fondo blanco): texto `#000000` 21,00:1; series en sus valores de modo claro (5,19; 4,79; 4,95; 6,72; punto doble 6,54), todas ≥ 3:1.

Reglas:

- El anillo de foco se dibuja **separado 2 DIP** del control, de modo que siempre queda sobre `superficie` o `fondo` (pares verificados arriba), también cuando el control es un botón `acento`.
- Los rectángulos de Riemann usan relleno `serie_azul` con alfa 0,22 **y** borde `serie_azul` opaco de 1 DIP; el borde es el que cumple 3:1.
- Modo claro/oscuro: se sigue `QGuiApplication.styleHints().colorScheme()` y se reacciona a la señal `colorSchemeChanged` en caliente (gráficas incluidas). **No** hay ajuste de tema dentro de la app.

---

## 3. Tipografía, espaciado y radios

### 3.1 Familia

- Interfaz: **Segoe UI Variable** (sistema). Pila de respaldo en Qt: `["Segoe UI Variable Text", "Segoe UI Variable", "Segoe UI", "Inter"]`. Inter (OFL) solo si se decide empaquetarla (plan B).
- Gráficas (matplotlib): `font.family = ["Segoe UI", "DejaVu Sans"]`; `mathtext.fontset = "dejavusans"`.
- Prohibido: SF Pro, SF Symbols, New York o cualquier recurso de Apple.

### 3.2 Escala (tamaños a factor de texto 100 %)

| Rol | Tamaño | Peso | Color | Notas |
|---|---|---|---|---|
| Título de la app | 16 pt | Semibold (600) | texto | Barra superior |
| Subtítulo de la app | 10,5 pt | Regular (400) | texto_sec | |
| Encabezado de tarjeta ("Datos", "Resultado", "Opciones", nombres de gráficas) | 12 pt | Semibold | texto | Mayúscula inicial, no todo en mayúsculas |
| Etiqueta de campo | 11 pt | Semibold | texto | |
| Valor dentro del campo | 14 pt | Regular | texto | Grande: se ve mientras se escribe en el video |
| Texto de ayuda / error bajo el campo | 10 pt | Regular | texto_sec / error | Mínimo absoluto de la app: 10 pt |
| Botón | 11 pt | Semibold | según estado | |
| Perímetro aproximado (resultado principal) | **28 pt** | Semibold | texto | Cifras tabulares |
| Otros resultados | 14 pt | Regular | texto | Cifras tabulares |
| Rótulos de resultados | 10,5 pt | Regular | texto_sec | |
| Tooltip / barra de estado | 10 pt | Regular | | |
| Título de gráfica (pantalla) | 12 pt | Semibold | texto | |
| Rótulo de eje (pantalla) | 10,5 pt | Regular | texto | |
| Marcas de eje y leyenda (pantalla) | 9,5 pt | Regular | texto_sec | |

- No se usan pesos Light ni más finos.
- **Cifras tabulares:** en los valores de resultados activar la característica OpenType `tnum` (`QFont.setFeature(QFont.Tag("tnum"), 1)`, Qt ≥ 6.6). Los dígitos de Segoe UI ya son de ancho fijo por defecto; `tnum` lo garantiza. Los valores se alinean a la derecha en su columna.
- **Texto ampliado de Windows:** leer `HKCU\Software\Microsoft\Accessibility\TextScaleFactor` (100–225; si no existe, 100) y multiplicar todos los tamaños por `factor/100`. El DPI lo maneja Qt 6 (escalado por monitor activado por defecto).

### 3.3 Espaciado y radios

| Token | DIP |
|---|---|
| `esp_1` | 4 |
| `esp_2` | 8 |
| `esp_3` | 12 |
| `esp_4` | 16 |
| `esp_5` | 24 |
| `esp_6` | 32 |

- Relleno interno de tarjeta: 16 DIP (`esp_4`). Entre etiqueta y campo: 4. Entre campo y ayuda: 4. Entre grupos de campo: 16. Entre tarjetas: 16.
- Radios: controles (campos, botones, segmentos) **6 DIP**; tarjetas **10 DIP**; interruptor: pastilla (radio = alto/2); anillo de foco: radio del control + 2.
- Alturas: campo 40 DIP; botón primario 40 DIP (mín. ancho 120); botón secundario 36 DIP; botón de icono 32×32 DIP; segmento del selector 36 DIP; interruptor 24×44 DIP con área de clic que incluye su texto. Separación mínima entre controles clicables: 8 DIP.

---

## 4. Componentes, estados y textos

Todos los textos están en español y son **exactos**. Convenciones de redacción: ejes con nombre en mayúscula (eje X, eje Y, eje Z); coordenadas en minúscula (x, y, z). Se escribe "x e y", nunca "x y y". Números con coma decimal. Miles separados con espacio fino no separable (U+202F): `10 000 000`.

### 4.1 Iconos (Lucide, ISC)

| Uso | Icono Lucide |
|---|---|
| Calcular | `calculator` |
| Cancelar | `square` (detener) |
| Exportar PNG | `image-down` |
| Restablecer vista 3D | `rotate-ccw` |
| Sonido activado / desactivado | `volume-2` / `volume-x` |
| Error | `circle-alert` |
| Aviso | `triangle-alert` |
| Éxito | `circle-check` |
| Información | `info` |

Se cargan como SVG con QtSvg y se recolorean sustituyendo `currentColor` por el token correspondiente. Tamaño 16 DIP en botones con texto, 20 DIP en botones de solo icono. Copiar el `LICENSE` de Lucide a `recursos/iconos/`.

### 4.2 Textos fijos

| Elemento | Texto |
|---|---|
| Título de ventana | `Perímetro de la Ventana de Viviani` |
| Subtítulo | `Aproximación con suma de Riemann` |
| Tarjetas | `Datos`, `Resultado`, `Opciones`, `Curva en 3D`, `Suma de Riemann`, `Convergencia` |

### 4.3 Campo de texto (R y n)

| | Campo R | Campo n |
|---|---|---|
| Etiqueta | `Radio de la esfera R` | `Número de subintervalos n` |
| Sufijo dentro del campo | `cm` (texto_sec) | — |
| Marcador (placeholder) | `Ej.: 5 o 7,5` | `Ej.: 1000` |
| Ayuda (reposo) | `Número real positivo. Acepta coma o punto decimal.` | `Número entero entre 1 y 10 000 000.` |
| Valor inicial | `5` | `10` |
| Tooltip | `Radio de la esfera en centímetros` | `Cantidad de rectángulos de la suma de Riemann` |
| Nombre accesible | `Radio de la esfera R, en centímetros` | `Número de subintervalos n` |

Estados:

| Estado | Borde | Fondo | Texto | Ayuda |
|---|---|---|---|---|
| Reposo | 1 DIP `borde` | superficie | texto | texto_sec |
| Hover | 1 DIP `texto_sec` | superficie | texto | texto_sec |
| Foco | 1 DIP `borde` + anillo 2 DIP `foco` separado 2 DIP | superficie | texto | texto_sec |
| Error | **2 DIP** `error` (más el anillo si tiene foco) | superficie | texto | Se reemplaza por icono `circle-alert` + mensaje en `error` |
| Deshabilitado (durante el cálculo no se deshabilita; solo si se requiere en el futuro) | 1 DIP `borde` | superficie_deshab | texto_deshab | texto_sec |

El error se distingue sin color por tres señales: borde más grueso, icono y texto del mensaje.

**Cuándo se valida:** en cada pulsación se valida en silencio; el mensaje se **muestra** (a) al pulsar Enter o Calcular, (b) al salir del campo, o (c) tras 600 ms sin escribir. El mensaje **desaparece en cuanto** el texto pasa a ser válido. Campo vacío sin tocar no muestra error. La caja de error reserva su altura (la ayuda y el error ocupan el mismo sitio), así el layout no salta.

**Normalización antes de validar:** quitar espacios al inicio y al final; para R, reemplazar `,` por `.`; para n, quitar espacios internos (separadores de miles con espacio son válidos).

Mensajes de validación de R (se evalúan en este orden):

| Condición | Mensaje |
|---|---|
| Vacío (al calcular) | `Escriba el radio R.` |
| `nan`, `inf`, `infinity` o su versión con signo (cualquier mayúscula), o el número es infinito al convertir (p. ej. `1e999`) | `R debe ser un número finito.` |
| No se puede convertir a número (letras, dos separadores, etc.) | `Escriba un número, por ejemplo 5 o 7,5.` |
| R ≤ 0 | `R debe ser mayor que cero.` |

Mensajes de validación de n (en este orden):

| Condición | Mensaje |
|---|---|
| Vacío (al calcular) | `Escriba el número de subintervalos n.` |
| `nan`, `inf`, `infinity` (con o sin signo) | `n debe ser un número finito.` |
| Coincide con `^\d{1,3}([.,]\d{3})+$` (p. ej. `1.000`, `10,000`) | `Escriba n sin puntos ni comas, por ejemplo 1000.` |
| Contiene `.` o `,` en otro patrón, o notación `e` (p. ej. `2,5`, `1e6`) | `n debe ser un número entero, sin decimales.` |
| No coincide con `^[+-]?\d+$` | `Escriba solo dígitos, por ejemplo 1000.` |
| n ≤ 0 | `n debe ser mayor que cero.` |
| n > 10 000 000 | `n no debe superar 10 000 000.` |

Al calcular con datos inválidos: no se calcula, se muestran los mensajes de ambos campos, el foco va al **primer** campo con error, se reproduce el sonido de error. No hay cuadros modales.

### 4.4 Botón primario "Calcular"

| Atributo | Valor |
|---|---|
| Texto | `Calcular` con icono `calculator` a la izquierda |
| Tooltip | `Calcular el perímetro (Enter)` |
| Reposo | Fondo `acento`, texto `texto_sobre_acento` |
| Hover | Fondo `acento_hover` |
| Presionado | Fondo `acento_hover`, contenido desplazado 1 DIP hacia abajo (sin animación) |
| Foco | Anillo `foco` 2 DIP separado 2 DIP |
| Durante el cálculo | Sigue habilitado: pulsarlo (o Enter) **reinicia** el cálculo con los datos actuales |
| Deshabilitado | No se usa (si se llegara a usar: superficie_deshab + texto_deshab + borde) |

Es el **único** botón prominente de la ventana.

### 4.5 Botón secundario (Exportar PNG, Restablecer vista)

| Atributo | Valor |
|---|---|
| Reposo | Fondo transparente, borde 1 DIP `borde`, texto e icono `texto` |
| Hover | Fondo `superficie_deshab` |
| Presionado | Fondo `separador` |
| Foco | Anillo `foco` |
| Deshabilitado | Texto `texto_deshab`, borde `separador` (Exportar solo se deshabilita mientras se guarda) |
| Textos | `Exportar PNG` (icono `image-down`); `Restablecer vista` (icono `rotate-ccw`) |
| Tooltips | 3D: `Guardar esta gráfica como imagen PNG de alta resolución (Ctrl+Mayús+1)`; Riemann: `... (Ctrl+Mayús+2)`; Convergencia: `... (Ctrl+Mayús+3)`; Restablecer: `Volver al ángulo de vista inicial (Ctrl+0)` |

En modo pestañas o si el ancho de la cabecera de la tarjeta < 320 DIP, los botones muestran solo el icono (32×32) y el texto pasa al tooltip y al nombre accesible.

### 4.6 Botón "Cancelar" y progreso

- Oculto en reposo. Aparece a la derecha de "Calcular" solo si el cálculo dura más de **300 ms** (así los cálculos rápidos no hacen parpadear la interfaz).
- Estilo secundario (no rojo: cancelar no destruye datos). Icono `square`. Texto `Cancelar`. Tooltip `Detener el cálculo (Esc)`.
- Debajo de los botones: barra de progreso determinada (alto 6 DIP, relleno `acento`, pista `separador`, radio 3) y el texto `Calculando… 45 %` (10 pt, texto_sec). El porcentaje se actualiza por bloques de 1 000 000 de subintervalos.
- Al cancelar: desaparecen barra y botón; en la tarjeta Resultado aparece una banda `fondo_aviso` con icono `info` y el texto `Cálculo cancelado. Se mantienen los resultados anteriores.` (o `Cálculo cancelado.` si no había resultados). La banda se quita con el siguiente cálculo. Sin sonido de error (cancelar no es un error).

### 4.7 Tarjeta Resultado

| Estado | Contenido |
|---|---|
| Vacía (al abrir) | Icono `info` + `Aún no hay resultados. Escriba R y n y presione Enter.` |
| Con resultado | Encabezado contextual: `Para R = 5 cm, n = 10, punto medio` (texto_sec). Luego las cuatro filas |
| Error de cálculo | Banda `fondo_error`, icono `circle-alert`: `No se pudo calcular: el resultado es demasiado grande para representarse. Pruebe con un radio menor.` |

Filas (rótulo a la izquierda, valor a la derecha, cifras tabulares):

| Rótulo | Formato del valor | Ejemplo (R = 5, n = 10, punto medio) |
|---|---|---|
| `Perímetro aproximado` | 6 decimales + ` cm` | `38,201673 cm` |
| `Valor de control` | 6 decimales + ` cm`; ayuda debajo `7,640395578 · R` | `38,201978 cm` |
| `Error absoluto` | Científica 4 cifras + ` cm` | `3,049 × 10⁻⁴ cm` |
| `Error relativo` | Científica 4 cifras + ` %` | `7,982 × 10⁻⁴ %` |

- Científica: mantisa con coma, `×` (U+00D7), exponente en superíndices Unicode (`⁻⁰¹²³⁴⁵⁶⁷⁸⁹`). Si el exponente está entre −2 y 3, se escribe en decimal normal con 4 cifras significativas.
- Si el error es exactamente 0: `0 cm` y debajo, en texto_sec, `Coincide con el valor de control dentro de la precisión del computador.`
- R grandes (≥ 10⁶) o pequeños (< 10⁻³): perímetro y control también en científica con 7 cifras significativas.
- Nombre accesible de la tarjeta tras calcular (los superíndices se escriben en palabras para el Narrador): `Perímetro aproximado 38,201673 centímetros. Error relativo 7,982 por 10 a la menos 4 por ciento.`

### 4.8 Interruptor de sonido (barra superior, derecha)

| Estado | Pista | Pulgar | Icono | Texto visible |
|---|---|---|---|---|
| Activado | `acento` | `texto_sobre_acento`, a la derecha | `volume-2` | `Sonido: activado` |
| Desactivado | Transparente, borde 1 DIP `borde` | `borde`, a la izquierda | `volume-x` | `Sonido: desactivado` |
| Foco | + anillo `foco` alrededor de pista y texto | | | |

El estado se lee por la posición del pulgar, el icono y el texto, no solo por el color. Tooltip: `Activar o desactivar los sonidos (M)`. Valor por defecto: activado. Se recuerda con `QSettings("ESPOL", "PerimetroViviani")`, clave `sonido/activado`. Al activarlo suena el clic (confirma que hay sonido); al desactivarlo no suena nada.

### 4.9 Selector de método (tarjeta Opciones)

- Etiqueta: `Método de la suma`.
- Control segmentado de 3 botones exclusivos, en este orden: `&Izquierda`, `&Punto medio`, `&Derecha` (la letra subrayada es el atajo Alt). Por defecto: **Punto medio**.
- Seleccionado: fondo `acento`, texto `texto_sobre_acento`, semibold. No seleccionado: fondo transparente, borde `borde`, texto `texto`, regular. Hover en no seleccionado: fondo `superficie_deshab`. Diferencia sin color: relleno sólido frente a contorno, y cambio de peso.
- Tooltips: `Evalúa f en el extremo izquierdo de cada subintervalo (Alt+I)`; `Evalúa f en el punto medio de cada subintervalo (Alt+P)`; `Evalúa f en el extremo derecho de cada subintervalo (Alt+D)`.
- Ayuda bajo el control (texto_sec, 10 pt): `En esta curva, izquierda y derecha dan el mismo resultado porque f(0) = f(2π).`
- Al cambiar de método: si ya hay un resultado y los datos son válidos, se recalcula de inmediato (con animación). Si no, solo cambia la selección.

### 4.10 Avisos y barra de estado

| Situación | Dónde | Texto |
|---|---|---|
| n > 120 (muestra representativa) | Banda `fondo_aviso` bajo la gráfica "Suma de Riemann", icono `triangle-alert` | `Se dibujan 120 de los {n} rectángulos: cada barra agrupa unos {n/120 redondeado} subintervalos y su altura es el promedio de f en el grupo. El área total es la misma.` |
| Imagen exportada | Barra de estado, `exito`, icono `circle-check`, 6 s | `Imagen guardada en: {ruta}` |
| Error al exportar | Barra de estado, `error`, icono `circle-alert`, hasta la siguiente acción | `No se pudo guardar la imagen: {motivo}.` |
| Sugerencia 3D | Debajo de la gráfica 3D, texto_sec 10 pt | `Arrastre para rotar · Con la gráfica enfocada, use las flechas.` |

---

## 5. Teclado

### 5.1 Orden de tabulación

1. Campo R
2. Campo n
3. Botón Calcular
4. Botón Cancelar (solo si está visible)
5. Selector de método (un solo tope de tabulación; ← y → cambian de opción)
6. Interruptor de sonido
7. Gráfica "Curva en 3D" (lienzo enfocable)
8. Restablecer vista
9. Exportar PNG (3D)
10. Gráfica "Suma de Riemann"
11. Exportar PNG (Riemann)
12. Gráfica "Convergencia"
13. Exportar PNG (Convergencia)

En modo pestañas, los pasos 7–13 se sustituyen por: barra de pestañas (← → cambian de pestaña) y los elementos de la pestaña visible. Mayús+Tab recorre al revés. Al abrir la app, el foco está en el campo R con su texto seleccionado.

### 5.2 Teclas y atajos

| Tecla | Acción | Dónde funciona |
|---|---|---|
| Enter / Intro del teclado numérico | Calcular | En toda la ventana, salvo cuando el foco está en un botón (entonces activa ese botón) |
| Esc | 1) Si hay cálculo en curso: cancelarlo. 2) Si hay animación: saltar al estado final. 3) Si no: nada | Toda la ventana |
| Clic izquierdo en cualquier parte de la ventana durante la animación | Saltar al estado final (el clic también hace su acción normal) | Toda la ventana |
| M | Activar/desactivar sonido | Cuando el foco **no** está en un campo de texto |
| Ctrl+M | Activar/desactivar sonido | En toda la ventana (incluido dentro de los campos) |
| Alt+I / Alt+P / Alt+D | Método izquierda / punto medio / derecha | Toda la ventana |
| Ctrl+Mayús+1 / 2 / 3 | Exportar PNG de Curva en 3D / Suma de Riemann / Convergencia | Toda la ventana |
| Ctrl+0 | Restablecer la vista 3D | Toda la ventana |
| Flechas ← → | Rotar acimut ±10° | Con la gráfica 3D enfocada |
| Flechas ↑ ↓ | Rotar elevación ±10° (limitada a −90°…90°) | Con la gráfica 3D enfocada |
| Ctrl+1 / 2 / 3 | Mostrar pestaña 1 / 2 / 3 | Solo en modo pestañas |
| Alt+F4 | Cerrar (estándar de Windows) | |

No se redefinen atajos estándar (Ctrl+C, Ctrl+V, Ctrl+Z, Ctrl+A funcionan normalmente en los campos).

**Encadenar cálculos:** tras calcular, el foco se queda en el campo donde estaba y su texto queda seleccionado, de modo que se puede escribir el nuevo valor y pulsar Enter de inmediato. Si se pulsa Enter durante la animación, la animación salta al final y empieza el cálculo nuevo.

### 5.3 Cómo se ve el foco

- Anillo de 2 DIP en `foco`, separado 2 DIP del borde del control, con radio = radio del control + 2.
- Gráficas: el anillo rodea la tarjeta completa de la gráfica.
- Selector de método: el anillo rodea solo el segmento activo.
- El foco se muestra siempre que se navegue con teclado; con el mouse, los campos de texto también lo muestran (los botones pueden ocultarlo tras un clic).
- Nunca se mueve el foco automáticamente, salvo al primer campo con error tras pulsar Calcular.

---

## 6. Movimiento

### 6.1 Principios

Duraciones de 150–300 ms por elemento, curva de salida suave; nada decorativo; todo se puede saltar; nada se mueve mientras el expositor habla si no lo pidió con una acción.

Curvas (`QEasingCurve`): **OutCubic** para entradas; **InOutCubic** para desplazamientos; **Linear** solo para la barra de progreso.

### 6.2 Línea de tiempo tras recibir el resultado (presupuesto total: 1 800 ms ≤ 2 000 ms)

| Inicio | Duración | Qué se anima | Curva |
|---|---|---|---|
| 0 ms | 200 ms | Valores de la tarjeta Resultado: opacidad 0 → 1 (los números aparecen ya completos, **sin** contadores que suben) | OutCubic |
| 0 ms | 1 500 ms | Rectángulos de Riemann, de izquierda a derecha: cada uno crece desde el eje (altura 0 → f) en 250 ms; inicio del rectángulo k: `k · (1500 − 250) / (m − 1)` ms (con m = 1, empieza en 0) | OutCubic por rectángulo |
| 0 ms | 1 500 ms | Puntos de muestra (n ≤ 120): cada punto aparece (opacidad) cuando su rectángulo termina de crecer | — |
| 1 500 ms | 300 ms | Punto actual en Convergencia: opacidad 0 → 1 y anillo de 2 DIP | OutCubic |

- **No se animan**: la gráfica 3D (se redibuja una vez al inicio con la escala del nuevo R), los cambios de tamaño de la ventana, los mensajes de validación (aparecen y desaparecen sin transición), la barra de estado.
- Botón presionado: cambio instantáneo (sin animación).
- Frecuencia objetivo: 30 fps con blitting de una única `PolyCollection` (estimado; ver ADR, R3).

### 6.3 Cuántos rectángulos y cómo se elige la muestra

- Máximo dibujado: **m = 120** rectángulos.
- Si n ≤ 120: se dibujan los n rectángulos reales, con un punto en (tᵢ, f(tᵢ)) que muestra dónde se evalúa f según el método.
- Si n > 120: se dibujan 120 **barras agrupadas**. La barra k (k = 0…119) cubre los subintervalos de `i_ini = ⌊k·n/120⌋` a `i_fin = ⌊(k+1)·n/120⌋ − 1`; su ancho es `(i_fin − i_ini + 1)·Δt` y su altura es el **promedio** de f(tᵢ) en ese grupo. Así la suma de áreas de las barras es exactamente la suma de Riemann calculada. No se dibujan puntos de muestra. Se muestra el aviso de 4.10. El promedio por grupo se obtiene en el mismo hilo de cálculo, sin coste extra relevante.

### 6.4 Cómo se omite

Esc, clic en cualquier parte de la ventana, Enter (nuevo cálculo) o cambio de método: se detienen todos los temporizadores y se dibuja el estado final en un solo repintado.

### 6.5 "Reducir movimiento"

Se lee al arrancar y en cada cálculo con `SystemParametersInfoW(SPI_GETCLIENTAREAANIMATION = 0x1042)` vía `ctypes` (corresponde a Configuración > Accesibilidad > Efectos visuales > Efectos de animación). Si está **desactivado** en Windows:

- Rectángulos, puntos y punto actual: aparecen **todos a la vez** con un único fundido de opacidad de 150 ms (OutCubic). Sin crecimiento ni escalonado.
- Tarjeta Resultado: los valores aparecen sin transición.
- La barra de progreso sí se muestra (es información, no decoración).
- Nada más cambia: mismos sonidos, mismos textos.

---

## 7. Sonido

Generación: `math.sin` + `array("h")` + `wave` a 44 100 Hz, 16 bits, mono, en memoria. Reproducción con `winsound` en un hilo (ADR 4.a). Nivel en dBFS de pico (0 dBFS = 32 767). Todas las notas con ataque lineal y caída exponencial; fundido final de 5 ms a cero para evitar chasquidos.

Pensado para no competir con la voz: muy cortos (≤ 280 ms), pico entre −24 y −20 dBFS, ondas sin armónicos agudos agresivos, sin reverberación, nunca en bucle.

| Sonido | Cuándo | Forma de onda | Notas y frecuencias | Duración total | Envolvente | Nivel de pico |
|---|---|---|---|---|---|---|
| **Clic / confirmación** | Al pulsar Calcular con datos válidos; al exportar una imagen con éxito; al activar el sonido | Senoidal pura | Una nota: 1 760 Hz | 45 ms | Ataque 2 ms; caída exponencial τ = 12 ms; fundido final 5 ms | −24 dBFS (amplitud 2 067) |
| **Resultado listo** | Cuando aparecen los valores (instante 0 ms de la animación) | Senoidal + 2.º armónico a −18 dB | Dos notas ascendentes: 880 Hz (90 ms), silencio 20 ms, 1 318,5 Hz (140 ms) | 250 ms | Cada nota: ataque 5 ms; caída exponencial τ = 60 ms; fundido final 5 ms | −20 dBFS (amplitud 3 277) |
| **Error suave** | Al pulsar Calcular con datos inválidos; al fallar un cálculo o una exportación | Senoidal + 3.er armónico a −19 dB (timbre "triangular" suave) | Dos notas descendentes: 523,25 Hz (110 ms), silencio 20 ms, 392 Hz (150 ms) | 280 ms | Cada nota: ataque 8 ms; caída exponencial τ = 70 ms; fundido final 5 ms | −22 dBFS (amplitud 2 603) |

Reglas:

- El sonido **nunca** es el único canal: cada sonido acompaña a un cambio visible (valores, mensaje de error, barra de estado).
- No suena al validar mientras se escribe ni al cancelar.
- Antirrepetición: no se reproduce el mismo sonido dos veces en menos de 150 ms; si llega otro mientras uno suena, se descarta.
- Interruptor + M/Ctrl+M silencian todo; la preferencia se recuerda (4.8).

---

## 8. Gráficas

### 8.1 Estilo común

- Fondo del área de dibujo y de la figura: `superficie`. Textos: `texto`; marcas de eje: `texto_sec`. Ejes (spines) solo izquierdo e inferior en 2D, 1 DIP `borde`.
- Rejilla: solo mayor, 0,8 DIP, `separador`, detrás de los datos.
- Al cambiar el tema del sistema se reconstruye el estilo y se redibuja.
- Los títulos de la gráfica en pantalla van dentro de la figura (no repetir el nombre de la tarjeta): son el mensaje principal.

### 8.2 Gráfica 1: Curva en 3D

| Elemento | Especificación |
|---|---|
| Título | `Ventana de Viviani sobre la esfera de radio R = 5 cm` |
| Ejes | `X (cm)`, `Y (cm)`, `Z (cm)`; límites [−R, R] en los tres; `set_box_aspect((1, 1, 1))` |
| Esfera | Superficie 24×48 con color `esfera` (alfa 0,12/0,18) + malla de 12 meridianos y 6 paralelos, 0,6 DIP, alfa 0,35 |
| Curva | r(t) con 600 puntos, `serie_azul`, trazo continuo 2,5 DIP, `zorder` alto |
| Punto doble | Marcador círculo relleno `punto_doble` de 9 DIP con borde `superficie` de 1,5 DIP, en (R, 0, 0); rótulo de texto al lado: `Punto doble (R, 0, 0)` |
| Leyenda (abajo a la izquierda) | `Curva de Viviani` (línea continua) · `Esfera x² + y² + z² = R²` (parche gris) · `Punto doble (R, 0, 0)` (círculo) |
| Vista inicial | elevación 22°, acimut 35° (ajustable tras la prueba en pantalla; debe verse el cruce en (R, 0, 0)) |
| Interacción | Arrastrar con el botón izquierdo rota; rueda acerca/aleja; teclado según 5.2 |
| Nombre accesible | `Gráfica 3D de la Ventana de Viviani sobre una esfera de radio 5 centímetros. Punto doble en (5, 0, 0).` |

Las series se distinguen sin color: la curva es una línea, la esfera es una superficie, el punto doble es un marcador con rótulo de texto.

### 8.3 Gráfica 2: Suma de Riemann

| Elemento | Especificación |
|---|---|
| Título | `Suma de Riemann con n = 10 (punto medio)` — el método en minúsculas: `izquierda`, `punto medio`, `derecha` |
| Eje horizontal | `t (rad)`; marcas en 0, π/2, π, 3π/2, 2π, rotuladas `0`, `π/2`, `π`, `3π/2`, `2π`; límites [0, 2π] |
| Eje vertical | `f(t) (cm/rad)`; límites fijos [0; 1,5·R] para que la altura sea comparable entre cálculos |
| f(t) | 400 puntos, `texto`, línea continua 2 DIP |
| Rectángulos | Relleno `serie_azul` alfa 0,22; borde `serie_azul` 1 DIP |
| Puntos de muestra (n ≤ 120) | Círculos de 5 DIP, `serie_naranja`, sin borde |
| Anotación (arriba a la derecha, dentro del eje) | `Σ f(tᵢ)·Δt = 38,201673 cm` |
| Leyenda (arriba a la izquierda) | `f(t) = R√(1 + cos²t)` (línea) · `Rectángulos` (parche con borde) · `Puntos de muestra` (círculo; solo si n ≤ 120) |
| Estado antes del primer cálculo | Solo f(t) para el R del campo (si es válido) y el título `f(t) = R√(1 + cos²t) con R = 5 cm` |
| Nombre accesible | `Suma de Riemann con 10 rectángulos, método punto medio. Suma igual a 38,201673 centímetros.` |

Distinción sin color: la curva es una línea, los rectángulos son áreas con borde, los puntos son círculos.

### 8.4 Gráfica 3: Convergencia

Dato medido (R = 1, punto medio): el error cae de forma **exponencial** (≈ 6 × 10⁻⁵ con n = 10; ≈ 3 × 10⁻⁹ con n = 20) y llega al nivel de redondeo (~10⁻¹⁶) hacia n ≈ 40. La gráfica debe mostrarlo honestamente: no es una recta en log-log.

| Elemento | Especificación |
|---|---|
| Título | `Convergencia del error relativo según n` |
| Eje horizontal | `Número de subintervalos n` — escala log, [1, 10⁷] |
| Eje vertical | `Error relativo (%)` — escala log, [10⁻¹⁵, 10²] |
| Datos | Error relativo (independiente de R) para n = 1…64 (todos) y 24 valores logarítmicos entre 80 y 10⁷. Se calculan una sola vez al arrancar, en el hilo de trabajo, para los tres métodos |
| Errores iguales a 0 o < 10⁻¹⁵ % | Se dibujan sobre la línea inferior con marcador hueco |
| Línea de referencia | Recta horizontal discontinua `texto_sec` en el nivel de redondeo (≈ 1 × 10⁻¹⁴ %), con rótulo `Límite de precisión del computador` |
| Punto medio | `serie_azul`, línea continua 1,5 DIP, marcador círculo ● 4 DIP |
| Izquierda | `serie_naranja`, línea discontinua (6, 3) 1,5 DIP, marcador triángulo ▲ 5 DIP |
| Derecha | `serie_morado`, línea punteada (1, 2) 1,5 DIP, marcador triángulo ▽ hueco 6 DIP |
| Punto actual | Rombo ◆ 10 DIP relleno `texto`, con anillo de 2 DIP `acento` y rótulo `n = 10 (actual)`; solo del método elegido |
| Leyenda (abajo a la izquierda) | `Punto medio` · `Izquierda` · `Derecha` · `Cálculo actual` y nota debajo en texto_sec: `Izquierda y derecha coinciden.` |
| Nombre accesible | `Convergencia: con n = 10 y punto medio, el error relativo es 7,982 por 10 a la menos 4 por ciento.` |

Izquierda y derecha coinciden en esta curva; por eso usan trazos y marcadores distintos (lleno ▲ y hueco ▽) que siguen leyéndose aunque se superpongan.

### 8.5 Exportación PNG (para el reporte impreso)

- Siempre **fondo blanco** y paleta de modo claro con texto `#000000`, aunque la app esté en modo oscuro. Se dibuja en una figura nueva con `matplotlib.rc_context` (no se toca la de pantalla) y en estado final (sin animación).
- Resolución: **300 ppp**. Tamaños: 3D 12 × 12 cm (1 417 × 1 417 px); Riemann y Convergencia 16 × 10 cm (1 890 × 1 181 px).
- Tipografía de exportación: títulos 10 pt semibold, rótulos de eje 9 pt, marcas y leyenda 8 pt; líneas 1,2 pt; marcadores 4 pt.
- `bbox_inches="tight"`, `pad_inches=0.05`, metadatos `{"Title": ..., "Software": "Perímetro de la Ventana de Viviani"}`.
- Diálogo de guardar del sistema (`QFileDialog.getSaveFileName`), carpeta inicial `Imágenes` del usuario, filtro `Imagen PNG (*.png)`. Nombres sugeridos:
  - `viviani_3d_R5cm.png`
  - `riemann_R5cm_n10_punto_medio.png`
  - `convergencia_n10_punto_medio.png`
  (la coma decimal de R se escribe como `-`: `R7-5cm`).
- La vista 3D exportada usa el ángulo actual de la pantalla.

---

## 9. Lista de verificación de accesibilidad

Marcar cada punto antes de grabar el video.

- [ ] Todos los pares texto/fondo de la sección 2 se usan tal como están (≥ 4,5:1) y los elementos gráficos ≥ 3:1, en claro y oscuro.
- [ ] La app sigue el modo claro/oscuro de Windows y cambia en caliente.
- [ ] Ningún dato depende solo del color: errores con icono + texto + borde grueso; series con trazo y marcador distintos; selector con relleno/contorno; interruptor con posición, icono y texto.
- [ ] Todo se puede hacer sin mouse (sección 5), incluida la rotación 3D y la exportación.
- [ ] El anillo de foco es visible en todos los elementos enfocables y nunca queda tapado.
- [ ] Orden de tabulación según 5.1.
- [ ] Áreas de clic ≥ 32×32 DIP y separación ≥ 8 DIP.
- [ ] Con texto ampliado al 150 % y 200 % (Configuración > Accesibilidad > Tamaño del texto) no hay texto recortado; la columna izquierda se desplaza si hace falta.
- [ ] A 100 %, 125 % y 150 % de escala de pantalla todo se ve nítido.
- [ ] Ventana redimensionable hasta 1024×640 DIP sin perder funciones.
- [ ] Con "Efectos de animación" desactivado en Windows se cumple 6.5.
- [ ] Toda animación se omite con Esc o clic y nunca dura más de 2 s.
- [ ] Los mensajes de error están junto al campo, en español, dicen cómo corregir y no usan cuadros modales.
- [ ] Cada sonido tiene un equivalente visible; el sonido se puede silenciar con el interruptor, M y Ctrl+M; la preferencia se recuerda.
- [ ] El Narrador de Windows lee el nombre de cada campo, botón, selector, interruptor y gráfica (nombres accesibles de las secciones 4 y 8).
- [ ] El cálculo con n = 10 000 000 no congela la ventana y se puede cancelar.
- [ ] Textos: ejes en mayúscula (X, Y, Z), coordenadas en minúscula (x, y, z), "x e y", coma decimal.
- [ ] No se usa ningún recurso de Apple (fuentes, iconos, imágenes).

---

## 10. Decisiones y principios HIG que las justifican

| Decisión | Principio HIG (sección leída) |
|---|---|
| Entrada y resultado arriba a la izquierda; gráficas a la derecha | Lo importante arriba y al inicio de la lectura (layout) |
| Tarjetas "Datos", "Resultado", "Opciones" separadas por espacio | Agrupar elementos relacionados con espacio o contenedores (layout) |
| Rejilla ≥ 1280 DIP y pestañas por debajo, sin quitar funciones | Adaptarse al tamaño sin cambiar la funcionalidad (layout) |
| Columna con desplazamiento y nada recortado con texto ampliado | Permitir texto más grande y apilar en vertical (accessibility, layout, typography) |
| Paleta con contraste ≥ 4,5:1 / 3:1 verificado en ambos modos | Contraste según WCAG AA en claro y oscuro (accessibility, dark-mode) |
| Seguir el tema del sistema, sin ajuste propio | Respetar la apariencia elegida por el sistema (dark-mode) |
| Error = icono + texto + borde, series = trazo + marcador | No depender solo del color (accessibility, color, charts) |
| El acento solo para la acción principal y la selección | Color con significado consistente (color) |
| Un solo botón prominente, "Calcular", que responde a Enter | Un botón principal; la acción por defecto responde a Return (buttons) |
| Etiquetas de botón con verbo ("Calcular", "Exportar PNG", "Cancelar") | Botones que empiezan con verbo (buttons, writing) |
| Validación inmediata con mensajes junto al campo, sin modales | Validar al escribir y mostrar el problema enseguida; errores junto al campo y con la corrección (entering-data, writing) |
| Valores por defecto R = 5, n = 10 y ejemplos en el marcador | Valores por defecto razonables y texto de ejemplo (entering-data) |
| Estado (cancelado, muestra representativa, imagen guardada) en línea, no en alertas | Estado cerca de lo que describe; alertas solo para lo crítico (feedback) |
| Mensaje de error de cálculo que explica la causa | Explicar por qué falló un comando (feedback) |
| Barra de progreso determinada + Cancelar en lugar fijo | Progreso determinado, cancelable y en ubicación consistente (progress-indicators) |
| Animación de ≤ 1,8 s, solo donde enseña (rectángulos), omitible | Movimiento con propósito, breve; no obligar a esperar (motion) |
| "Reducir movimiento": fundido único de 150 ms | Con reducir movimiento, cambiar desplazamientos por fundidos (accessibility) |
| Sonidos cortos, bajos, silenciables y siempre con equivalente visual | Silenciar lo no esencial; no transmitir solo con sonido (playing-audio, feedback) |
| Atajos solo para acciones frecuentes; no se tocan Ctrl+C/V/Z/A | No reasignar atajos estándar; pocos atajos propios (keyboards) |
| Navegación completa con teclado, incluida la rotación 3D | Acceso completo con teclado (accessibility, keyboards) |
| Anillo de foco en campos y controles; el foco no se mueve solo | Anillo para campos; no mover el foco sin acción del usuario (focus-and-selection) |
| Títulos de gráfica que dicen el mensaje; leyendas; poca rejilla | Título o resumen con el mensaje; leyenda cuando hay series; datos más prominentes que la rejilla (charts, charting-data) |
| Mismo estilo de color y trazo en las tres gráficas | Consistencia entre gráficas relacionadas (charting-data) |
| Nombres accesibles de gráficas con valores reales | Etiquetas accesibles que describen los datos con valores concretos (charts) |
| Pesos Regular/Semibold, nunca Light; mínimo 10 pt | Evitar pesos finos; tamaños mínimos legibles (typography) |
| Cifras tabulares en resultados | **Sin respaldo en las HIG leídas** (decisión propia de legibilidad para comparar valores) |
| Paleta Okabe-Ito para daltonismo | Cuidar combinaciones difíciles para daltónicos (color, accessibility); la paleta concreta es decisión propia |
