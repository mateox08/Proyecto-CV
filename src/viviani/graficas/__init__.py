"""Gráficas de matplotlib incrustables en Qt (curva 3D, Riemann, convergencia)."""

import logging

from viviani.graficas.convergencia import GraficaConvergencia
from viviani.graficas.curva3d import GraficaCurva3D
from viviani.graficas.riemann import GraficaRiemann

# Segoe UI no tiene todos los pesos de DejaVu Sans (la fuente de respaldo) y
# matplotlib avisaría en consola sin que importe: se silencia ese aviso.
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

__all__ = ["GraficaConvergencia", "GraficaCurva3D", "GraficaRiemann"]
