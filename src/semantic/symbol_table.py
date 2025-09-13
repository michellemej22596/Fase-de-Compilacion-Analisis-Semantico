from __future__ import annotations  # Permite las anotaciones de tipo en el mismo archivo antes de Python 3.10.
from dataclasses import dataclass, field  # Utiliza `dataclass` para crear clases fáciles de gestionar.
from typing import Dict, Optional, List  # Importa tipos de datos como diccionarios, listas y opcionales.
from .symbols import Symbol  # Importa la clase `Symbol`, que se utiliza para representar los símbolos en la tabla.

# Define el tipo de un alcance (scope), que puede ser 'GLOBAL', 'FUNCTION', 'CLASS', o 'BLOCK'.
ScopeKind = str

# Clase que representa un alcance (scope) en la tabla de símbolos.
@dataclass
class Scope:
    kind: ScopeKind  # El tipo de alcance (ej. 'GLOBAL', 'FUNCTION', etc.)
    name: str = ""   # Nombre del alcance (puede ser vacío, como en el caso del global)
    parent: Optional["Scope"] = None  # El alcance padre, si lo hay. Esto permite crear jerarquías de scopes.
    symbols: Dict[str, Symbol] = field(default_factory=dict)  # Diccionario de símbolos definidos en este alcance.

    # Define un nuevo símbolo en este alcance.
    def define(self, sym: Symbol):
        if sym.name in self.symbols:
            # Si el símbolo ya está definido, lanza un error.
            raise KeyError(f"Symbol '{sym.name}' already defined in this scope")
        # Si no está definido, lo añade al diccionario de símbolos.
        self.symbols[sym.name] = sym

    # Resuelve un nombre de símbolo en el alcance actual y sus padres.
    def resolve(self, name: str) -> Optional[Symbol]:
        cur: Optional[Scope] = self
        # Recorre los scopes desde el actual hasta el global (si existe).
        while cur:
            if name in cur.symbols:
                # Si encuentra el símbolo, lo devuelve.
                return cur.symbols[name]
            cur = cur.parent  # Si no lo encuentra, sube al scope padre.
        return None  # Si no encuentra el símbolo en ninguno de los scopes, devuelve None.

# Clase que representa la tabla de símbolos global de todo el programa.
class SymbolTable:
    def __init__(self):
        # Comienza con un solo scope global.
        self._stack: List[Scope] = [Scope(kind="GLOBAL", name="__global__")]

    # Propiedad que devuelve el scope actual (el último en el stack).
    @property
    def current(self) -> Scope:
        return self._stack[-1]

    # Crea un nuevo scope y lo agrega al stack de scopes.
    def push(self, kind: ScopeKind, name: str = "") -> Scope:
        # Crea un nuevo scope con el tipo y nombre especificados, y lo añade al stack.
        scope = Scope(kind=kind, name=name, parent=self.current)
        self._stack.append(scope)
        return scope

    # Elimina el último scope del stack (excepto el global).
    def pop(self) -> Scope:
        if len(self._stack) == 1:
            # Si solo queda el scope global, no se puede hacer pop.
            raise RuntimeError("Cannot pop global scope")
        return self._stack.pop()  # Elimina el último scope y lo devuelve.

    # Devuelve una representación de la tabla de símbolos para ser mostrada, como un listado de scopes.
    def dump(self) -> list:
        out = []
        for s in self._stack:
            # Para cada scope en el stack, genera un diccionario con su tipo, nombre y sus símbolos.
            out.append({
                "scope": f"{s.kind} {s.name}".strip(),
                "entries": [
                    {"name": k, "kind": v.kind, "type": str(v.type)}
                    for k, v in s.symbols.items()
                ],
            })
        return out
