"""Gráficas de la aplicación: la curva 3D (dibujada con QPainter) y la suma
de Riemann (matplotlib incrustado en Qt)."""

import logging

from viviani.graficas.curva3d import GraficaCurva3D
from viviani.graficas.riemann import GraficaRiemann

# Segoe UI no tiene todos los pesos de DejaVu Sans (la fuente de respaldo) y
# matplotlib avisaría en consola sin que importe: se silencia ese aviso.
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

__all__ = ["GraficaCurva3D", "GraficaRiemann"]
