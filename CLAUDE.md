# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

University project (ESPOL, Cálculo Vectorial): a Windows desktop app that approximates the perimeter of the Viviani window with a midpoint Riemann sum and shows it with an animated 3D curve. Current version: v3 (see ADR-002 in `docs/decisiones.md`).

- Curve: r(t) = (R cos²t, R sen t cos t, R sen t), t ∈ [0, 2π]. Integrand: f(t) = R·√(1 + cos²t).
- Control value: 7.640395578·R (`RAZON_REFERENCIA`, verified with scipy).
- Everything user-facing is in Spanish, and so are identifiers, comments, commit messages and docs. Keep it that way.
- The app always uses the midpoint rule; there is no method selector.
- Numbers in the app use a dot as the decimal separator.

## Commands

Run everything from the repo root with the venv interpreter (`.venv\Scripts\python`, Python 3.15). Never install packages outside `.venv`.

```powershell
.\scripts\ejecutar.ps1                 # create .venv on first run, then launch the app (-Pruebas: tests + lint first)
.venv\Scripts\python viviani_app.py    # launch the app directly
.venv\Scripts\python -m unittest       # all tests (must run from the root: tests/__init__.py fixes sys.path)
.venv\Scripts\python -m unittest tests.test_calculo.PruebasValidacion.test_datos_invalidos   # one test
.venv\Scripts\ruff check .             # lint
.venv\Scripts\ruff format .            # format
.\scripts\construir.ps1 [-Modo onedir|onefile|ambos]   # runs the tests, then builds the .exe into dist\ (git-ignored)
.venv\Scripts\python scripts\generar_icono.py          # regenerate src/viviani/recursos/icono.png/.ico from code
```

- UI tests run headless: `tests/__init__.py` sets `QT_QPA_PLATFORM=offscreen`.
- `test_perimetro_viviani.py` in the root tests the original console program.

## Architecture

**Two layers of computation.**
- `perimetro_viviani.py` (root) is the original console program and the mathematical reference: a plain `for` loop in `suma_de_riemann` that prints with a comma decimal. It owns the shared constants (`T_INICIAL`, `T_FINAL`, `MAX_SUBINTERVALOS` = 10⁷, `RAZON_REFERENCIA`).
- `src/viviani/calculo.py` is the numpy version the app uses. It sums in blocks of `TAMANO_BLOQUE` = 10⁶, reports progress and checks cancellation between blocks.
- `calcular(radio, n, progreso, cancelado)` has no method parameter.
- It also builds the bars to draw: at most `MAX_BARRAS` = 120. Above that, subintervals are grouped and each bar shows the group's average height.
- The tests require both layers to agree within 1e-12 relative error. Keep it that way when changing either one.

**Startup** (`src/viviani/app.py`).
- `main()` shows the `PantallaCarga` splash first.
- `crear_ventana(avisar)` then imports numpy, builds the sounds, the charts and the window in stages, updating the splash (the curve traces itself as a progress bar). This keeps the first paint fast.
- Keep heavy imports lazy, inside `crear_ventana`, not at module top level. Anything the splash imports (`animacion.py`, `ui/logo.py`, `tema.py`) must stay Qt-only (no numpy). Importing `viviani.graficas` pulls numpy through its `__init__`.
- There is no matplotlib anywhere: both charts are drawn by hand with `QPainter`.

**Background computation.** `ui/trabajador.py` runs `calcular` on a QThread through a task manager where only the latest task counts. Results and errors come back to the window as signals.

**Window layout** (`ui/ventana.py`).
- The 3D chart (`graficas/curva3d.py`) fills the whole window as a background layer, and the controls are an overlay in the same grid cell.
- "Orbital" layout: four glass `Tarjeta`s in the corners around the sphere. Left column: "01 Datos" (R, n, Calcular; no n presets) and "04 Fórmula". Right column: "02 Resultado" and "03 Suma de Riemann". Header: logo, title, the r(t) equation (a `Formula`) and Créditos. Layer chips (malla, cilindro, ejes) at the bottom center.
- The window computes the free area between the columns and each card's anchor point (`Tarjeta.ancla()`). It passes both to `GraficaCurva3D.establecer_zona(zona, anclas)`: the sphere is centered in the area and the orbit ring is tied to each card with a tether. Call it again whenever the layout changes.
- Minimum size is 1100×720. Check 1536×793 (1080p at 125 %) and 1100×720 after layout changes.
- Every mouse press anywhere in the window spawns a small light pulse (`CapaPulsos`, a mouse-transparent overlay on top of everything). The app-level event filter sees a press once per widget in the propagation chain, so it dedupes by event timestamp.
- Every button plays `sonidos.clic()` (the user likes that sound).

**3D curve.** Drawn by hand with `QPainter`. Sphere radius is 0.33 of the free area's side so the orbit ring (`ORBITA` = 1.45 R) fits.
- Orbit: ring with rotating instrument ticks, a satellite, tethers to the cards and a flash that travels along them (`enviar(entrante)`); while that flash runs the partial repaint region also covers the tethers.
- It is a manual projection: rotate around Z, then apply elevation. Mesh and cylinder split front/back by depth; the curve is split into 6 depth levels (`NIVELES`).
- It shows the sphere mesh, the cylinder generatrices (from one branch of the curve to the other), a comet along the curve, the double point, axes with cm ticks, the sample points r(tᵢ) after a result and, while the mouse is over the Riemann chart, r(t) with its velocity vector r′(t).
- It rotates on its own at 15°/s and the user cannot drag it. With "reduce motion" there is no rotation, intro, comet or sweep.
- It repaints only the scene rectangle to save work, and it keeps its last frame in a pixmap (`_cuadro`): the scene is recomputed only for regions marked dirty via `_invalidar()` (once per tick); any other repaint (click pulses, the credits fade, the spinning logo above it) just blits the pixmap. Always call `_invalidar()` instead of `update()` in that widget.

**Riemann chart** (`graficas/riemann.py`). Drawn by hand with `QPainter` on a transparent widget (no buffer, so no fractional-scaling stripes). Hovering shows a readout card and emits `t_resaltado(t | None)`, which the window connects to `GraficaCurva3D.resaltar`.

**Sweep.** After each result both charts animate for `DURACION_BARRIDO_MS` using `graficas/barrido.py` (`inicios_escalonados`): bars grow one after another and the matching 3D sample points appear at the same moment. All animations use `animacion.Animacion` (real-time clock; the last frame always receives the full duration so skipping lands on the final state).

**Theme.**
- `tema.py` is the single source of colors and fonts. There is ONE theme: dark silver (white → silver gradient as accent, signal orange for sample points, digits not yet correct and the cylinder). The user tried gold, green and cyan/purple palettes and rejected them, and asked to drop the palette selector: don't bring them back.
- `tema.con_alfa` is the shared color-with-alpha helper.
- Math formulas are drawn by `ui/formula.py` (a tiny box-layout engine: `Fila`, `Indices`, `Fraccion`, `Operador`, `Raiz`), not with HTML labels, which clipped exponents and could not stack limits. Its accessible name comes from `texto()`. Italic variables get side margins (`Texto.MARGEN_CURSIVA`) so slanted letters don't touch parentheses, and `Indices` pulls subscripts back under that margin.
- `tema.py` and `perimetro_viviani.py` are excluded from `ruff format` because they are aligned by hand.
- Exponents in results are rendered as HTML `<sup>`, because Segoe UI Variable lacks the superscript minus.

**Credits panel** (`ui/creditos.py`).
- A solid card with a static logo (no glass, no blur, no veil, no spinning: the user asked to remove them). An invisible full-window layer only catches the click outside the card to close it.
- The card content lives in an opaque `_Cuerpo` (`WA_OpaquePaintEvent`), so the spinning logo repaints without forcing Qt to repaint the 3D scene underneath.
- Open/close fade: the card is snapshotted (`_Tarjeta.fotografiar`) and drawn as one pixmap with opacity and 96→100 % scale; only the card rect repaints. Don't use a `QGraphicsOpacityEffect` on a full-window panel, and when drawing pixmaps with a source rect remember it is in device pixels (that bug enlarged everything at 125 %).

**Sounds** (`sonido.py`). Four marimba-like sounds (clic, resultado, error, creditos with an air pad) synthesized with numpy at startup and played by `winsound` on one daemon thread. Always on: there is no toggle.

**Packaging** (`viviani.spec`).
- The build mode is chosen with the env var `VIVIANI_MODO` (`onedir` or `onefile`).
- matplotlib, PIL and scipy are explicitly excluded (they are installed in `.venv` for history, the icon script and the control-value check, but the app does not use them).

`docs/EXPLICACION.md` explains every file for the oral defense. Update it when behavior changes. `docs/DISENO.md` and `docs/decisiones.md` hold the design spec and the decision log.

## Repo conventions

- Version 1 is preserved as tag `v1.0`, the redesigned dark UI is v2 (tags `v2.0`, `v2.1`), and the current version is v3 (tag `v3.0`). GitHub Releases attach the built `.exe` and onedir zip.
- Ask before pushing, touching `main` directly, rewriting history, deleting files or doing large downloads. Work on a branch.
- The user prefers lean work: no subagents unless really needed, and only minimal verification instead of extensive test or QA passes.
