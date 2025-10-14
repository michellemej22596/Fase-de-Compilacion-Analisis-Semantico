"""
Módulo para gestionar registros de activación (stack frames) de funciones.
Calcula offsets de variables locales, parámetros y temporales.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

try:
    from semantic.symbols import Symbol, FunctionSymbol, ParamSymbol, VariableSymbol
except ImportError:
    from ..semantic.symbols import Symbol, FunctionSymbol, ParamSymbol, VariableSymbol

try:
    from codegen.symbol_extensions import get_type_size
except ImportError:
    from .symbol_extensions import get_type_size


@dataclass
class ActivationRecord:
    """
    Representa un registro de activación (stack frame) para una función.
    
    Estructura típica del stack frame:
    
    +------------------+  <- Frame Pointer (FP)
    | Return Address   |  offset: 0
    +------------------+
    | Saved FP         |  offset: 4
    +------------------+
    | Param N          |  offset: 8 + (N-1)*4
    | ...              |
    | Param 1          |  offset: 8 + 0*4
    +------------------+
    | Local 1          |  offset: 8 + params_size
    | Local 2          |
    | ...              |
    | Local M          |
    +------------------+
    | Temp 1           |  offset: 8 + params_size + locals_size
    | Temp 2           |
    | ...              |
    +------------------+  <- Stack Pointer (SP)
    """
    
    nombre_funcion: str
    parametros: List[ParamSymbol] = field(default_factory=list)
    variables_locales: List[VariableSymbol] = field(default_factory=list)
    temporales: List[str] = field(default_factory=list)
    
    # Offsets calculados
    offset_parametros: Dict[str, int] = field(default_factory=dict)
    offset_locales: Dict[str, int] = field(default_factory=dict)
    offset_temporales: Dict[str, int] = field(default_factory=dict)
    
    # Tamaños
    tamanio_parametros: int = 0
    tamanio_locales: int = 0
    tamanio_temporales: int = 0
    tamanio_total: int = 0
    
    def calcular_offsets(self):
        """Calcula los offsets de todos los elementos del registro de activación"""
        # Offset base después de return address y saved FP
        base_offset = 8
        
        # 1. Calcular offsets de parámetros
        current_offset = base_offset
        for param in self.parametros:
            self.offset_parametros[param.name] = current_offset
            param_size = get_type_size(param.type)
            current_offset += param_size
        self.tamanio_parametros = current_offset - base_offset
        
        # 2. Calcular offsets de variables locales
        for var in self.variables_locales:
            self.offset_locales[var.name] = current_offset
            var_size = get_type_size(var.type)
            current_offset += var_size
        self.tamanio_locales = current_offset - base_offset - self.tamanio_parametros
        
        # 3. Calcular offsets de temporales
        for temp in self.temporales:
            self.offset_temporales[temp] = current_offset
            current_offset += 4  # Temporales siempre ocupan 4 bytes
        self.tamanio_temporales = current_offset - base_offset - self.tamanio_parametros - self.tamanio_locales
        
        # Tamaño total del frame
        self.tamanio_total = current_offset - base_offset
    
    def get_offset(self, name: str) -> Optional[int]:
        """Obtiene el offset de una variable, parámetro o temporal"""
        if name in self.offset_parametros:
            return self.offset_parametros[name]
        if name in self.offset_locales:
            return self.offset_locales[name]
        if name in self.offset_temporales:
            return self.offset_temporales[name]
        return None
    
    def agregar_temporal(self, temp_name: str):
        """Agrega un temporal al registro de activación"""
        if temp_name not in self.temporales:
            self.temporales.append(temp_name)
            # Recalcular offsets
            self.calcular_offsets()
    
    def __str__(self) -> str:
        """Representación legible del registro de activación"""
        lines = [
            f"Activation Record: {self.nombre_funcion}",
            f"  Total Size: {self.tamanio_total} bytes",
            f"  Parameters ({self.tamanio_parametros} bytes):"
        ]
        for param in self.parametros:
            offset = self.offset_parametros.get(param.name, 0)
            size = get_type_size(param.type)
            lines.append(f"    {param.name}: offset {offset}, size {size}")
        
        lines.append(f"  Local Variables ({self.tamanio_locales} bytes):")
        for var in self.variables_locales:
            offset = self.offset_locales.get(var.name, 0)
            size = get_type_size(var.type)
            lines.append(f"    {var.name}: offset {offset}, size {size}")
        
        if self.temporales:
            lines.append(f"  Temporals ({self.tamanio_temporales} bytes):")
            for temp in self.temporales:
                offset = self.offset_temporales.get(temp, 0)
                lines.append(f"    {temp}: offset {offset}, size 4")
        
        return "\n".join(lines)


class ActivationRecordManager:
    """
    Gestiona los registros de activación de todas las funciones del programa.
    """
    
    def __init__(self):
        self.records: Dict[str, ActivationRecord] = {}
        self.current_function: Optional[str] = None
    
    def crear_record(self, func_symbol: FunctionSymbol) -> ActivationRecord:
        """Crea un registro de activación para una función"""
        record = ActivationRecord(
            nombre_funcion=func_symbol.name,
            parametros=func_symbol.params.copy() if func_symbol.params else []
        )
        self.records[func_symbol.name] = record
        return record
    
    def get_record(self, func_name: str) -> Optional[ActivationRecord]:
        """Obtiene el registro de activación de una función"""
        return self.records.get(func_name)
    
    def agregar_variable_local(self, func_name: str, var_symbol: VariableSymbol):
        """Agrega una variable local al registro de activación de una función"""
        if func_name in self.records:
            self.records[func_name].variables_locales.append(var_symbol)
            self.records[func_name].calcular_offsets()
    
    def agregar_temporal(self, func_name: str, temp_name: str):
        """Agrega un temporal al registro de activación de una función"""
        if func_name in self.records:
            self.records[func_name].agregar_temporal(temp_name)
    
    def finalizar_record(self, func_name: str):
        """Finaliza el registro de activación calculando todos los offsets"""
        if func_name in self.records:
            record = self.records[func_name]
            record.calcular_offsets()
            return record
    
    def dump(self) -> str:
        """Genera un reporte de todos los registros de activación"""
        lines = ["=" * 60, "ACTIVATION RECORDS", "=" * 60]
        for func_name, record in self.records.items():
            lines.append("")
            lines.append(str(record))
        lines.append("=" * 60)
        return "\n".join(lines)
