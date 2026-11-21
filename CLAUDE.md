# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

University project (ESPOL, Cálculo Vectorial): a Windows desktop app that approximates the perimeter of the Viviani window with a midpoint Riemann sum and shows it with an animated 3D curve.

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
- It also builds the bars to draw: at most `MAX_BARRAS` = 120. Above that, subintervals are grouped and each bar shows the group's average height.
- The tests require both layers to agree within 1e-12 relative error. Keep it that way when changing either one.

**Startup** (`src/viviani/app.py`).
- `main()` shows the `PantallaCarga` splash first.
- `crear_ventana(avisar)` then imports numpy, matplotlib (QtAgg), the charts and the window in stages, updating the splash as it goes. This keeps the first paint fast.
- Keep heavy imports lazy, inside `crear_ventana`, not at module top level.

**Background computation.** `ui/trabajador.py` runs `calcular` on a QThread through a task manager where only the latest task counts. Results and errors come back to the window as signals.

**Window layout** (`ui/ventana.py`).
- The 3D chart (`graficas/curva3d.py`) fills the whole window as a background layer, and the controls are an overlay in the same grid cell.
- The window computes the free area between the left column (inputs) and the right column (results and Riemann chart). It passes that area to `GraficaCurva3D.establecer_zona()` so the sphere is centered there. Call it again whenever the layout changes.

**3D curve.** Drawn by hand with `QPainter`, not matplotlib 3D, which was too slow.
- It is a manual projection: rotate around Z, then apply elevation, and split each segment into front or back by depth.
- It rotates on its own at 15°/s and the user cannot drag it.
- It repaints only the scene rectangle to save work.

**Riemann chart.** It uses matplotlib through `graficas/lienzo.py` (`LienzoBase`).
- The canvas is transparent. To allow that, `WA_OpaquePaintEvent` is turned off.
- `paintEvent` is overridden to always draw the full buffer. This fixes stripe artifacts at fractional display scaling (125%). Don't revert it.

**Theme.**
- `tema.py` is the single source of colors and fonts. The app has only a dark theme.
- `tema.py` and `perimetro_viviani.py` are excluded from `ruff format` because they are aligned by hand.
- Exponents in results are rendered as HTML `<sup>`, because Segoe UI Variable lacks the superscript minus.

**Credits panel** (`ui/creditos.py`).
- It is a "liquid glass" card. Every 50 ms it re-renders what lies behind the card (background plus 3D scene) at 1/6 scale, blurs it with a numpy box blur and scales it up.
- Performance matters there: about 5 ms per refresh.

**Packaging** (`viviani.spec`).
- The build mode is chosen with the env var `VIVIANI_MODO` (`onedir` or `onefile`).
- `unittest` must **not** be excluded, because pyparsing (pulled in by matplotlib) needs it at runtime.

`docs/EXPLICACION.md` explains every file for the oral defense. Update it when behavior changes. `docs/DISENO.md` and `docs/decisiones.md` hold the design spec and the decision log.

## Repo conventions

- Version 1 is preserved as tag `v1.0`, and the redesigned UI is v2 (tag `v2.0`). GitHub Releases attach the built `.exe` and onedir zip.
- Ask before pushing, touching `main` directly, rewriting history, deleting files or doing large downloads. Work on a branch.
- The user prefers lean work: no subagents unless really needed, and only minimal verification instead of extensive test or QA passes.
