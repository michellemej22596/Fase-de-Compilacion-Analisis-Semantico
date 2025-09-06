from dataclasses import dataclass

@dataclass
class VarSymbol:
    name: str
    typ: str
    is_const: bool = False
    initialized: bool = False
