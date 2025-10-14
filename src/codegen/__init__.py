"""
Módulo de generación de código intermedio (cuádruplos) para Compiscript.

Este módulo contiene las clases y utilidades necesarias para generar
código intermedio en forma de cuádruplos a partir del AST de Compiscript.
"""

from .quadruple import Quadruple, QuadrupleList
from .temp_manager import TempManager, ScopedTempManager
from .label_manager import LabelManager, LoopLabelManager
from .activation_record import ActivationRecord, ActivationRecordManager
from .code_generator import CodeGeneratorVisitor, generate_code

__all__ = [
    'Quadruple',
    'QuadrupleList',
    'TempManager',
    'ScopedTempManager',
    'LabelManager',
    'LoopLabelManager',
    'ActivationRecord',
    'ActivationRecordManager',
    'CodeGeneratorVisitor',
    'generate_code',
]
