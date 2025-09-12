# Tipos base como strings simples (podrías usar enums/objetos luego)
BOOL  = "boolean"
INT   = "integer"
STR   = "string"
FLOAT = "float"
NULL  = "null"

# Predicados
def is_boolean(t):
    return t == BOOL

def is_integer(t):
    return t == INT

def is_float(t):
    return t == FLOAT

def is_numeric(t):
    return t in (INT, FLOAT)

def is_string(t):
    return t == STR

def is_null(t):
    return t == NULL

# Compatibilidad de tipos (ajústala a tu semántica)
def are_compatible(expected, actual):
    # igualdad exacta
    if expected == actual:
        return True

    # numéricos compatibles entre sí (promoción implícita int<->float si quieres)
    if expected in (INT, FLOAT) and actual in (INT, FLOAT):
        return True

    # (Opcional) permitir NULL para variables de cualquier tipo de referencia.
    # Si NO quieres permitirlo, comenta estas dos líneas.
    # if actual == NULL:
    #     return True

    return False