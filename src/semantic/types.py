BOOL  = "boolean"
INT   = "integer"
STR   = "string"
FLOAT = "float"
NULL  = "null"
VOID  = "void"

def get_type_size(type_str: str) -> int:
    """
    Retorna el tamaño en bytes de un tipo.
    Útil para calcular offsets en registros de activación.
    """
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

# Predicados para verificación de tipos
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

def is_void(t):
    return t == VOID

# Compatibilidad de tipos
def are_compatible(expected, actual):
    # Igualdad exacta
    if expected == actual:
        return True

    # Numéricos compatibles entre sí (promoción implícita int<->float)
    if expected in (INT, FLOAT) and actual in (INT, FLOAT):
        return True

    # NULL compatible con cualquier tipo (opcional)
    if actual == NULL:
        return True

    return False

# Función para crear tipos de array (mantenemos funcionalidad existente)
def array_type(elem_type):
    return f"array<{elem_type}>"

def is_array(t):
    return isinstance(t, str) and t.startswith("array<")

def get_array_element_type(array_type_str):
    if is_array(array_type_str):
        return array_type_str[6:-1]  # Extrae el tipo entre "array<" y ">"
    return None

# Función para crear tipos de clase
def class_type(class_name):
    return f"class<{class_name}>"

def is_class(t):
    return isinstance(t, str) and t.startswith("class<")

def get_class_name(class_type_str):
    if is_class(class_type_str):
        return class_type_str[6:-1]  # Extrae el nombre entre "class<" y ">"
    return None
