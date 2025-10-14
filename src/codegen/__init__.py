"""
Módulo de generación de código intermedio (cuádruplos) para Compiscript.

Este módulo contiene las clases y utilidades necesarias para generar
código intermedio en forma de cuádruplos a partir del AST de Compiscript.
"""

from .quadruple import Quadruple, QuadrupleList
from .temp_manager import TempManager
from .label_manager import LabelManager

__all__ = [
    'Quadruple',
    'QuadrupleList',
    'TempManager',
    'LabelManager',
]
