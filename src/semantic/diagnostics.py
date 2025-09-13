from __future__ import annotations  # Permite la anotación de tipo en el mismo archivo antes de Python 3.10.
from dataclasses import dataclass, asdict  # Utiliza `dataclass` para crear clases con atributos fáciles de gestionar.
from typing import List, Dict, Any  # Importa tipos para manejo de listas, diccionarios y cualquier tipo.

# Clase que representa un diagnóstico de un error durante el análisis (sintáctico o semántico).
@dataclass
class Diagnostic:
    phase: str      # Fase en la que ocurrió el error: 'semantic' o 'syntax'
    code: str       # Código del error, por ejemplo, 'E001', 'E101', etc.
    message: str    # Descripción del error.
    line: int       # Línea donde ocurrió el error.
    col: int        # Columna donde ocurrió el error.
    extra: Dict[str, Any]  # Información adicional, como datos extra relacionados al error.

    # Convierte el objeto `Diagnostic` en un diccionario. Útil para la serialización.
    def to_dict(self):
        return asdict(self)

# Clase que gestiona una colección de diagnósticos (errores).
class Diagnostics:
    def __init__(self):
        self._items: List[Diagnostic] = []  # Lista que almacena todos los diagnósticos (errores).

    # Añade un nuevo diagnóstico a la lista.
    # Se le pasa como argumento la fase del error ('semantic' o 'syntax'), el código, el mensaje, y la posición del error.
    def add(self, *, phase: str, code: str, message: str, line: int, col: int, **extra):
        self._items.append(Diagnostic(phase=phase, code=code, message=message, line=line, col=col, extra=extra))

    # Extiende la lista de errores con otro objeto `Diagnostics`.
    def extend(self, ds: "Diagnostics"):
        self._items.extend(ds._items)

    # Devuelve `True` si no hay errores en la lista.
    def empty(self) -> bool:
        return not self._items  # Si la lista está vacía, retorna `True`.

    # Devuelve todos los errores como una lista de diccionarios, usando el método `to_dict` de cada diagnóstico.
    def to_list(self) -> List[dict]:
        return [d.to_dict() for d in self._items]
