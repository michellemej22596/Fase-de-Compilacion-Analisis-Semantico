"""
Generador de código MIPS a partir de cuádruplos.

Este módulo traduce código intermedio (cuádruplos) a código assembler MIPS32.
"""

from .mips_generator import MIPSGenerator
from .register_manager import RegisterManager

__all__ = ['MIPSGenerator', 'RegisterManager']
