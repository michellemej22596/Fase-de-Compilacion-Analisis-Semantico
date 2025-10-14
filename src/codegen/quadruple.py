"""
Definición de la estructura de cuádruplos para código intermedio.

Un cuádruplo representa una operación de tres direcciones:
    (operador, arg1, arg2, resultado)

Ejemplo:
    (ADD, a, b, t0)  →  t0 = a + b
    (IF_FALSE, t0, L1, None)  →  if not t0 goto L1
"""

from dataclasses import dataclass
from typing import Optional, List
from enum import Enum


class QuadOp(str, Enum):
    """Operadores soportados en cuádruplos."""
    
    # Operadores aritméticos
    ADD = "ADD"
    SUB = "SUB"
    MUL = "MUL"
    DIV = "DIV"
    MOD = "MOD"
    NEG = "NEG"  # Negación unaria
    
    # Operadores relacionales
    EQ = "EQ"   # ==
    NE = "NE"   # !=
    LT = "LT"   # <
    LE = "LE"   # <=
    GT = "GT"   # >
    GE = "GE"   # >=
    
    # Operadores lógicos
    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    
    # Asignación
    ASSIGN = "ASSIGN"
    
    # Control de flujo
    GOTO = "GOTO"
    IF_TRUE = "IF_TRUE"
    IF_FALSE = "IF_FALSE"
    LABEL = "LABEL"
    
    # Funciones
    BEGIN_FUNC = "BEGIN_FUNC"
    END_FUNC = "END_FUNC"
    PARAM = "PARAM"
    CALL = "CALL"
    RETURN = "RETURN"
    
    # Arrays
    ARRAY_NEW = "ARRAY_NEW"
    ARRAY_LOAD = "ARRAY_LOAD"
    ARRAY_STORE = "ARRAY_STORE"
    ARRAY_LEN = "ARRAY_LEN"
    
    # Objetos y clases
    NEW = "NEW"
    GET_FIELD = "GET_FIELD"
    SET_FIELD = "SET_FIELD"
    CALL_METHOD = "CALL_METHOD"
    
    # Conversión de tipos
    CAST = "CAST"
    
    # I/O
    PRINT = "PRINT"
    READ = "READ"


@dataclass
class Quadruple:
    """
    Representa un cuádruplo de código intermedio.
    
    Attributes:
        op: Operador del cuádruplo
        arg1: Primer argumento (puede ser None)
        arg2: Segundo argumento (puede ser None)
        result: Resultado de la operación
        line: Número de línea en el código fuente (para debugging)
    """
    op: QuadOp
    arg1: Optional[str] = None
    arg2: Optional[str] = None
    result: Optional[str] = None
    line: Optional[int] = None
    
    def __str__(self) -> str:
        """Representación en string del cuádruplo."""
        args = []
        if self.arg1 is not None:
            args.append(str(self.arg1))
        if self.arg2 is not None:
            args.append(str(self.arg2))
        if self.result is not None:
            args.append(str(self.result))
        
        return f"({self.op}, {', '.join(args)})"
    
    def to_tuple(self) -> tuple:
        """Convierte el cuádruplo a tupla para compatibilidad."""
        return (self.op, self.arg1, self.arg2, self.result)
    
    def is_label(self) -> bool:
        """Verifica si el cuádruplo es una etiqueta."""
        return self.op == QuadOp.LABEL
    
    def is_jump(self) -> bool:
        """Verifica si el cuádruplo es un salto."""
        return self.op in (QuadOp.GOTO, QuadOp.IF_TRUE, QuadOp.IF_FALSE)
    
    def is_function_boundary(self) -> bool:
        """Verifica si el cuádruplo marca inicio/fin de función."""
        return self.op in (QuadOp.BEGIN_FUNC, QuadOp.END_FUNC)


class QuadrupleList:
    """
    Lista de cuádruplos con utilidades para generación de código.
    
    Mantiene una lista ordenada de cuádruplos y proporciona métodos
    para agregar, modificar y consultar cuádruplos.
    """
    
    def __init__(self):
        self._quads: List[Quadruple] = []
    
    def emit(self, op: QuadOp, arg1=None, arg2=None, result=None, line=None) -> int:
        """
        Emite un nuevo cuádruplo y retorna su índice.
        
        Args:
            op: Operador del cuádruplo
            arg1: Primer argumento
            arg2: Segundo argumento
            result: Resultado
            line: Número de línea en el código fuente
            
        Returns:
            Índice del cuádruplo emitido
        """
        quad = Quadruple(op, arg1, arg2, result, line)
        self._quads.append(quad)
        return len(self._quads) - 1
    
    def get(self, index: int) -> Quadruple:
        """Obtiene un cuádruplo por su índice."""
        return self._quads[index]
    
    def patch(self, index: int, arg1=None, arg2=None, result=None):
        """
        Modifica un cuádruplo existente (backpatching).
        
        Útil para completar saltos condicionales y etiquetas
        que no se conocen en el momento de emisión.
        """
        quad = self._quads[index]
        if arg1 is not None:
            quad.arg1 = arg1
        if arg2 is not None:
            quad.arg2 = arg2
        if result is not None:
            quad.result = result
    
    def next_index(self) -> int:
        """Retorna el índice del próximo cuádruplo a emitir."""
        return len(self._quads)
    
    def __len__(self) -> int:
        """Retorna la cantidad de cuádruplos."""
        return len(self._quads)
    
    def __iter__(self):
        """Permite iterar sobre los cuádruplos."""
        return iter(self._quads)
    
    def __getitem__(self, index: int) -> Quadruple:
        """Permite acceso por índice."""
        return self._quads[index]
    
    def to_list(self) -> List[Quadruple]:
        """Retorna una copia de la lista de cuádruplos."""
        return self._quads.copy()
    
    def dump(self) -> str:
        """
        Genera una representación en texto de todos los cuádruplos.
        
        Útil para debugging y visualización en el IDE.
        """
        lines = []
        for i, quad in enumerate(self._quads):
            lines.append(f"{i:4d}: {quad}")
        return "\n".join(lines)
    
    def dump_table(self) -> List[dict]:
        """
        Genera una representación tabular de los cuádruplos.
        
        Útil para el IDE y visualización estructurada.
        """
        table = []
        for i, quad in enumerate(self._quads):
            table.append({
                "index": i,
                "op": quad.op,
                "arg1": quad.arg1 if quad.arg1 is not None else "",
                "arg2": quad.arg2 if quad.arg2 is not None else "",
                "result": quad.result if quad.result is not None else "",
                "line": quad.line if quad.line is not None else ""
            })
        return table
    
    def clear(self):
        """Limpia todos los cuádruplos."""
        self._quads.clear()
