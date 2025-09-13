from __future__ import annotations  # Permite las anotaciones de tipo para evitar problemas con las referencias circulares (anotaciones tipo-string).
from dataclasses import dataclass, field  # Usamos `dataclass` para definir clases simples que se gestionan automáticamente.
from typing import List, Dict, Optional  # Importa tipos como listas, diccionarios y opcionales.
from .types import Type  # Importa el tipo `Type` desde otro archivo, el cual probablemente define los tipos posibles como `int`, `str`, etc.

# Definición de la clase base para representar cualquier tipo de símbolo (variable, función, clase, etc.).
@dataclass
class Symbol:
    name: str  # Nombre del símbolo (ej. 'x' para una variable, 'foo' para una función).
    type: Type  # Tipo del símbolo (puede ser `int`, `float`, `string`, etc.).
    kind: str = field(default="", init=False)  # Tipo de símbolo (por ejemplo, 'var' para variable, 'func' para función).

# Clase para representar un símbolo de variable, que hereda de `Symbol`.
@dataclass
class VariableSymbol(Symbol):
    is_const: bool = False  # Indica si la variable es constante.
    kind: str = field(default="var", init=False)  # El tipo de símbolo es 'var' para variables.

# Clase para representar un símbolo de parámetro de función, que también hereda de `Symbol`.
@dataclass
class ParamSymbol(Symbol):
    kind: str = field(default="param", init=False)  # El tipo de símbolo es 'param' para parámetros de funciones.

# Clase para representar un símbolo de función, que hereda de `Symbol`.
@dataclass
class FunctionSymbol(Symbol):
    params: List[ParamSymbol] = field(default_factory=list)  # Lista de parámetros de la función.
    kind: str = field(default="func", init=False)  # El tipo de símbolo es 'func' para funciones.

# Clase para representar un símbolo de clase, que hereda de `Symbol`.
@dataclass
class ClassSymbol(Symbol):
    fields: Dict[str, Symbol] = field(default_factory=dict)  # Diccionario de campos (variables) de la clase.
    methods: Dict[str, FunctionSymbol] = field(default_factory=dict)  # Diccionario de métodos (funciones) de la clase.
    parent: Optional["ClassSymbol"] = field(default=None, repr=False)  # Clase base de la cual hereda, si la tiene.
    kind: str = field(default="class", init=False)  # El tipo de símbolo es 'class' para clases.

