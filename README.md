# Perímetro de la Ventana de Viviani

Proyecto de Cálculo Vectorial (ESPOL, PAO II 2026-2027). El programa aproxima el
perímetro de la Ventana de Viviani generada por una esfera de radio R (en cm),
mediante una suma de Riemann de la función subintegral de la longitud de arco.

Hay dos versiones que hacen el mismo cálculo:

- **Aplicación de escritorio** (`viviani_app.py` o el `.exe`), versión 3, con
  distribución orbital: la curva gira en 3D sobre la esfera y el cilindro que
  la generan, rodeada por un anillo al que se atan cuatro tarjetas (datos,
  fórmula, resultado y suma de Riemann). Al calcular, los rectángulos crecen
  al mismo ritmo en que aparecen los puntos r(tᵢ) sobre la curva; al pasar el
  mouse por un rectángulo se ve su vector velocidad r′(tᵢ) en 3D. El
  perímetro resalta sus cifras correctas y cada clic suelta una onda de luz.
- **Versión de consola** (`perimetro_viviani.py`): el núcleo matemático, sin
  librerías externas.

![Interfaz de la aplicación](docs/capturas/interfaz.png)

## Fundamento matemático

Parametrización de la curva (t ∈ [0, 2π]):

    r(t) = (R cos²t, R sen t cos t, R sen t)

Longitud de arco:

    L = ∫₀^{2π} ‖r′(t)‖ dt = ∫₀^{2π} R √(1 + cos²t) dt

La integral no tiene antiderivada elemental, por lo que se aproxima con

    L ≈ Σ f(tᵢ) Δt,    Δt = 2π / n,    f(t) = R √(1 + cos²t)

tomando tᵢ en el punto medio de cada subintervalo.

Valor de control: L = 4√2 · R · E(1/2) ≈ 7.640395578 · R, donde E es la
integral elíptica completa de segunda especie (verificado con scipy).

## Usar el ejecutable

No necesita Python. Descomprima `PerimetroViviani-onedir.zip` y abra
`PerimetroViviani\PerimetroViviani.exe` (o use el archivo único
`PerimetroViviani.exe`).

1. Escriba el radio R (cm) y el número de subintervalos n.
2. Presione **Enter** o **Calcular**.
3. Para encadenar otro cálculo, escriba el nuevo valor y vuelva a presionar Enter.
4. Pase el mouse sobre la gráfica de Riemann para leer cada rectángulo y ver
   su punto en la curva 3D. Los chips bajo la esfera ocultan la malla, el
   cilindro o los ejes.

| Tecla | Acción |
|---|---|
| Enter | Calcular |
| ↑ / ↓ en el campo n | Multiplicar o dividir n entre 10 |
| Esc | Cerrar los créditos, cancelar el cálculo en curso o saltar la animación |

Windows SmartScreen o el antivirus pueden avisar al abrir un `.exe` que no está
firmado (es un falso positivo frecuente con PyInstaller). Si ocurre, elija
"Más información → Ejecutar de todas formas".

## Instalar para desarrollo

Requiere Windows y Python de 64 bits. Se desarrolló y probó solo con Python 3.15.

```powershell
.\scripts\ejecutar.ps1
```

La primera vez crea el entorno virtual `.venv` e instala las dependencias de
`requirements-dev.txt` (versiones fijadas; la lista completa congelada está en
`requirements-lock.txt`). Después abre la aplicación.

Equivalente a mano:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe viviani_app.py
```

Versión de consola (no necesita nada instalado):

```powershell
python perimetro_viviani.py
```

## Probar

```powershell
.venv\Scripts\python.exe -m unittest -v
.venv\Scripts\ruff.exe check .
```

Las pruebas comprueban, entre otras cosas, que L/R = 7.640395578, que la versión
rápida (numpy) coincide con la de consola y todos los mensajes de validación.

## Construir el ejecutable

```powershell
.\scripts\construir.ps1              # los dos modos
.\scripts\construir.ps1 -Modo onedir
.\scripts\construir.ps1 -Modo onefile
```

Primero ejecuta las pruebas; si pasan, construye con PyInstaller según
`viviani.spec` y deja el resultado en `dist\` (que no se sube a git).

Medido en un portátil con Windows 11 (2026-11-21, versión 3):

| Modo | Resultado | Tamaño |
|---|---|---|
| Carpeta (`onedir`) | `dist\PerimetroViviani\` | 84.4 MB (33.6 MB en zip) |
| Archivo único (`onefile`) | `dist\PerimetroViviani.exe` | 33.5 MB |

El archivo único tarda más en mostrar algo porque primero se descomprime en
una carpeta temporal (eso ocurre antes de que el programa pueda dibujar).

El icono del `.exe` sale de `src/viviani/recursos/icono.ico`; si se cambia el
logo (`src/viviani/ui/logo.py`), se regenera con
`.venv\Scripts\python.exe scripts\generar_icono.py`.

Para grabar el video conviene el modo carpeta (abre más rápido). Para entregar
o enviar, el archivo único es más cómodo; el zip del modo carpeta suele dar
menos avisos del antivirus, porque el archivo único se descomprime en una
carpeta temporal cada vez que se abre.

## Versiones

| Versión | Dónde está | Aspecto |
|---|---|---|
| 1.0 | etiqueta `v1.0` (rama `feature/interfaz-grafica`) | Tema claro con tarjetas |
| 2.0 | etiquetas `v2.0` y `v2.1` | Tema oscuro grafito; la curva 3D ocupa el centro, resultados y Riemann juntos a la derecha, créditos con efecto vidrio, pantalla de carga e icono |
| 3.0 | etiqueta `v3.0` | Distribución orbital con tarjetas de vidrio; tema plateado; sin matplotlib (todo con QPainter); cilindro, cometa y puntos de muestra en 3D enlazados con Riemann; fórmulas bien dibujadas; cifras correctas; pulsos de luz; sonidos de marimba |

Para ver una versión anterior: `git checkout v1.0` o `git checkout v2.0`
(y `git checkout main` para regresar).

## Estructura

| Ruta | Contenido |
|---|---|
| `perimetro_viviani.py` | Núcleo matemático y versión de consola |
| `test_perimetro_viviani.py` | Pruebas del núcleo |
| `viviani_app.py` | Lanzador de la aplicación de escritorio |
| `src/viviani/` | Código de la aplicación (cálculo, gráficas, sonido, interfaz) |
| `tests/` | Pruebas de la aplicación |
| `scripts/` | `ejecutar.ps1`, `construir.ps1` y `generar_icono.py` |
| `docs/EXPLICACION.md` | Cómo está organizado el código, en lenguaje sencillo |
| `docs/decisiones.md` | Por qué se eligió PySide6 (ADR-001) y por qué la versión 3 dibuja todo con QPainter (ADR-002) |
| `viviani.spec` | Receta de PyInstaller |

## Integrantes

- Darlyn Acosta
- Juan Carrasco
- Juan Espinoza
- Mateo Saltos

Profesora: Dra. Soveny Solís
