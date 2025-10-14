"""
Módulo de análisis semántico para Compiscript.
Exporta la función principal 'analyze' y las clases de símbolos y tipos.
"""

from .checker import analyze, CompiscriptSemanticVisitor
from .symbols import Symbol, VariableSymbol, FunctionSymbol, ClassSymbol, ParamSymbol
from .symbol_table import SymbolTable, Scope
from .types import (
    is_numeric,
    is_boolean,
    are_compatible,
    get_array_element_type,
    create_array_type,
    get_type_size
)
from .diagnostics import Diagnostics

__all__ = [
    # Función principal
    'analyze',
    
    # Visitor
    'CompiscriptSemanticVisitor',
    
    # Símbolos
    'Symbol',
    'VariableSymbol',
    'FunctionSymbol',
    'ClassSymbol',
    'ParamSymbol',
    
    # Tabla de símbolos
    'SymbolTable',
    'Scope',
    
    # Tipos
    'is_numeric',
    'is_boolean',
    'are_compatible',
    'get_array_element_type',
    'create_array_type',
    'get_type_size',
    
    # Diagnósticos
    'Diagnostics',
]
