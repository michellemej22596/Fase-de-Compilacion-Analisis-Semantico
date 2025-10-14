"""
Extensiones de símbolos para generación de código.
Este módulo agrega información de codegen a los símbolos sin modificar el módulo semantic.
"""
from typing import Optional, Dict
from dataclasses import dataclass, field

# Diccionarios globales para almacenar información de codegen por símbolo
_symbol_codegen_info: Dict[int, 'CodegenInfo'] = {}

@dataclass
class CodegenInfo:
    """Información de generación de código asociada a un símbolo"""
    direccion: Optional[str] = None  # Dirección de memoria o nombre de temporal
    offset: int = 0  # Offset en el registro de activación
    nivel_anidamiento: int = 0  # Nivel de anidamiento de scope
    tamanio: int = 4  # Tamaño en bytes (default 4 para tipos básicos)
    es_temporal: bool = False  # Si es una variable temporal generada
    es_global: bool = False  # Si es una variable global
    es_parametro: bool = False  # Si es un parámetro de función
    posicion_parametro: int = 0  # Posición del parámetro (0, 1, 2...)
    etiqueta_inicio: Optional[str] = None  # Para funciones: etiqueta de inicio
    etiqueta_fin: Optional[str] = None  # Para funciones: etiqueta de fin
    tamanio_locals: int = 0  # Para funciones: tamaño de variables locales
    tamanio_params: int = 0  # Para funciones: tamaño de parámetros
    tamanio_temporales: int = 0  # Para funciones: tamaño de temporales
    tamanio_instancia: int = 0  # Para clases: tamaño de instancia
    vtable: Dict[str, str] = field(default_factory=dict)  # Para clases: virtual table


def get_codegen_info(symbol) -> CodegenInfo:
    """Obtiene la información de codegen para un símbolo"""
    symbol_id = id(symbol)
    if symbol_id not in _symbol_codegen_info:
        _symbol_codegen_info[symbol_id] = CodegenInfo()
    return _symbol_codegen_info[symbol_id]


def set_codegen_info(symbol, info: CodegenInfo):
    """Establece la información de codegen para un símbolo"""
    _symbol_codegen_info[id(symbol)] = info


def clear_codegen_info():
    """Limpia toda la información de codegen (útil para tests)"""
    _symbol_codegen_info.clear()


# Funciones de conveniencia para acceder a propiedades comunes

def get_direccion(symbol) -> Optional[str]:
    """Obtiene la dirección de un símbolo"""
    return get_codegen_info(symbol).direccion


def set_direccion(symbol, direccion: str):
    """Establece la dirección de un símbolo"""
    info = get_codegen_info(symbol)
    info.direccion = direccion


def get_offset(symbol) -> int:
    """Obtiene el offset de un símbolo"""
    return get_codegen_info(symbol).offset


def set_offset(symbol, offset: int):
    """Establece el offset de un símbolo"""
    info = get_codegen_info(symbol)
    info.offset = offset


def get_tamanio(symbol) -> int:
    """Obtiene el tamaño de un símbolo"""
    return get_codegen_info(symbol).tamanio


def set_tamanio(symbol, tamanio: int):
    """Establece el tamaño de un símbolo"""
    info = get_codegen_info(symbol)
    info.tamanio = tamanio


def is_temporal(symbol) -> bool:
    """Verifica si un símbolo es temporal"""
    return get_codegen_info(symbol).es_temporal


def mark_as_temporal(symbol):
    """Marca un símbolo como temporal"""
    info = get_codegen_info(symbol)
    info.es_temporal = True


def get_type_size(type_str):
    """
    Retorna el tamaño en bytes de un tipo.
    Útil para calcular offsets en registros de activación.
    """
    # Importar tipos desde semantic.types
    from semantic.types import INT, FLOAT, BOOL, STR, NULL, VOID, is_array, is_class
    
    if type_str in (INT, FLOAT, BOOL):
        return 4  # 4 bytes para tipos básicos
    elif type_str == STR:
        return 4  # 4 bytes para puntero a string
    elif is_array(type_str):
        return 4  # 4 bytes para puntero a array
    elif is_class(type_str):
        return 4  # 4 bytes para puntero a objeto
    elif type_str == NULL:
        return 4  # 4 bytes para null pointer
    elif type_str == VOID:
        return 0  # void no ocupa espacio
    else:
        return 4  # Default: 4 bytes
