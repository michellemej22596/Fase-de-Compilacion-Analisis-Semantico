from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class Symbol:
    name: str
    type: str  # Ahora usa string en lugar de Type
    kind: str = field(default="", init=False)
    
    direccion: Optional[str | int] = None  # Dirección de memoria o nombre de temporal
    offset: int = 0  # Offset en el registro de activación
    nivel_anidamiento: int = 0  # Nivel de anidamiento de scope
    tamanio: int = 4  # Tamaño en bytes (default 4 para tipos básicos)

@dataclass
class VariableSymbol(Symbol):
    is_const: bool = False
    kind: str = field(default="var", init=False)
    
    es_temporal: bool = False  # Si es una variable temporal generada
    es_global: bool = False  # Si es una variable global

@dataclass
class ParamSymbol(Symbol):
    kind: str = field(default="param", init=False)
    
    posicion_parametro: int = 0  # Posición del parámetro (0, 1, 2...)

@dataclass
class FunctionSymbol(Symbol):
    params: List[ParamSymbol] = field(default_factory=list)
    kind: str = field(default="func", init=False)
    
    etiqueta_inicio: Optional[str] = None  # Etiqueta de inicio de la función
    etiqueta_fin: Optional[str] = None  # Etiqueta de fin de la función
    tamanio_locals: int = 0  # Tamaño total de variables locales
    tamanio_params: int = 0  # Tamaño total de parámetros
    tamanio_temporales: int = 0  # Tamaño estimado de temporales

@dataclass
class ClassSymbol(Symbol):
    fields: Dict[str, Symbol] = field(default_factory=dict)
    methods: Dict[str, FunctionSymbol] = field(default_factory=dict)
    parent: Optional["ClassSymbol"] = field(default=None, repr=False)
    kind: str = field(default="class", init=False)
    
    tamanio_instancia: int = 0  # Tamaño total de una instancia de la clase
    vtable: Dict[str, str] = field(default_factory=dict)  # Virtual table para métodos
    
    def calcular_tamanio_instancia(self) -> int:
        """Calcula el tamaño total de una instancia de la clase"""
        tamanio = 0
        # Sumar tamaño de campos heredados
        if self.parent:
            tamanio = self.parent.calcular_tamanio_instancia()
        # Sumar tamaño de campos propios
        for field_sym in self.fields.values():
            tamanio += field_sym.tamanio
        self.tamanio_instancia = tamanio
        return tamanio
    
    def get_field_offset(self, field_name: str) -> Optional[int]:
        """Obtiene el offset de un campo en la instancia"""
        offset = 0
        # Primero campos heredados
        if self.parent:
            parent_offset = self.parent.get_field_offset(field_name)
            if parent_offset is not None:
                return parent_offset
            offset = self.parent.tamanio_instancia
        
        # Luego campos propios
        for fname, fsym in self.fields.items():
            if fname == field_name:
                return offset
            offset += fsym.tamanio
        
        return None
