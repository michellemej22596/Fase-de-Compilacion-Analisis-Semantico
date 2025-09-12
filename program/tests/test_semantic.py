import os
from antlr4 import FileStream, CommonTokenStream
from parsing.antlr.CompiscriptLexer import CompiscriptLexer
from parsing.antlr.CompiscriptParser import CompiscriptParser
from semantic.checker import analyze

BASE = os.path.dirname(__file__)  # mismo directorio (src/tests)


# 1. SISTEMA DE TIPOS - Tests que DEBEN PASAR
TIPOS_OK = [
    "tipos_01_aritmetica_integer.cps",      # Operaciones +,-,*,/ con integer
    "tipos_02_aritmetica_float.cps",        # Operaciones +,-,*,/ con float  
    "tipos_03_logicas_boolean.cps",         # Operaciones &&,||,! con boolean
    "tipos_04_comparaciones_mismo_tipo.cps", # Comparaciones ==,!=,<,> mismo tipo
    "tipos_05_asignacion_correcta.cps",     # Asignación tipo correcto
    "tipos_06_const_inicializada.cps"       # Constante inicializada
]

# 2. MANEJO DE ÁMBITO - Tests que DEBEN PASAR  
AMBITO_OK = [
    "ambito_01_resolucion_local_global.cps", # Resolución ámbito local/global
    "ambito_02_acceso_bloques_anidados.cps", # Acceso en bloques anidados
    "ambito_03_entornos_funcion.cps",        # Entornos de función
    "ambito_04_entornos_clase.cps",          # Entornos de clase
    "ambito_05_entornos_bloque.cps"          # Entornos de bloque
]

# 3. FUNCIONES Y PROCEDIMIENTOS - Tests que DEBEN PASAR
FUNCIONES_OK = [
    "func_01_argumentos_correctos.cps",      # Número y tipo de argumentos
    "func_02_tipo_retorno_correcto.cps",     # Tipo de retorno correcto
    "func_03_recursion.cps",                 # Función recursiva
    "func_04_anidadas_closures.cps",         # Funciones anidadas y closures
]

# 4. CONTROL DE FLUJO - Tests que DEBEN PASAR
CONTROL_OK = [
    "control_01_condiciones_boolean.cps",    # Condiciones boolean en if/while/for
    "control_02_break_continue_en_loop.cps", # break/continue dentro de loops
    "control_03_return_en_funcion.cps"       # return dentro de función
]

# 5. CLASES Y OBJETOS - Tests que DEBEN PASAR
CLASES_OK = [
    "clases_01_atributos_metodos.cps",       # Atributos y métodos válidos
    "clases_02_constructor.cps",             # Constructor correcto
    "clases_03_this_correcto.cps"            # this en ámbito correcto
]

# 6. LISTAS Y ESTRUCTURAS - Tests que DEBEN PASAR
LISTAS_OK = [
    "listas_01_tipo_elementos.cps",          # Tipo correcto de elementos
    "listas_02_indices_validos.cps"          # Índices válidos
]

# 7. GENERALES - Tests que DEBEN PASAR
GENERALES_OK = [
    "general_01_sin_codigo_muerto.cps",      # Sin código muerto
    "general_02_expresiones_validas.cps"     # Expresiones con sentido semántico
]

# TESTS DE ERRORES - Tests que DEBEN FALLAR
ERRORES = [
    # Sistema de Tipos - Errores
    "error_tipos_01_aritmetica_string.cps",     # Aritmética con string
    "error_tipos_02_logica_integer.cps",        # Lógica con integer
    "error_tipos_03_comparacion_tipos_diff.cps", # Comparación tipos diferentes
    "error_tipos_04_asignacion_incorrecta.cps", # Asignación tipo incorrecto
    "error_tipos_05_const_sin_inicializar.cps", # Constante sin inicializar
    
    # Manejo de Ámbito - Errores
    "error_ambito_01_variable_no_declarada.cps", # Variable no declarada
    "error_ambito_02_redeclaracion.cps",         # Redeclaración mismo ámbito
    
    # Funciones - Errores
    "error_func_01_argumentos_incorrectos.cps",  # Número/tipo argumentos incorrecto
    "error_func_02_tipo_retorno_incorrecto.cps", # Tipo retorno incorrecto
    "error_func_03_declaracion_duplicada.cps",   # Declaración duplicada
    
    # Control de Flujo - Errores
    "error_control_01_condicion_no_boolean.cps", # Condición no boolean
    "error_control_02_break_fuera_loop.cps",     # break fuera de loop
    "error_control_03_return_fuera_funcion.cps", # return fuera de función
    
    # Clases - Errores
    "error_clases_01_atributo_inexistente.cps",  # Atributo inexistente
    "error_clases_02_this_fuera_clase.cps",      # this fuera de clase
    
    # Listas - Errores
    "error_listas_01_tipo_incorrecto.cps",       # Tipo elemento incorrecto
    
    # Generales - Errores
    "error_general_01_codigo_muerto.cps",        # Código muerto
    "error_general_02_expresion_invalida.cps"    # Expresión inválida
]

def compile_file(path):
    input_stream = FileStream(path, encoding="utf-8")
    lexer = CompiscriptLexer(input_stream)
    stream = CommonTokenStream(lexer)
    parser = CompiscriptParser(stream)
    tree = parser.program()
    return analyze(tree)

def test_tipos_ok():
    for fname in TIPOS_OK:
        path = os.path.join(BASE, fname)
        assert os.path.exists(path), f"No existe {path}"
        res = compile_file(path)
        assert res["errors"] == [], f"{fname} no debería dar errores, obtuvo: {res['errors']}"

def test_ambito_ok():
    for fname in AMBITO_OK:
        path = os.path.join(BASE, fname)
        assert os.path.exists(path), f"No existe {path}"
        res = compile_file(path)
        assert res["errors"] == [], f"{fname} no debería dar errores, obtuvo: {res['errors']}"

def test_funciones_ok():
    for fname in FUNCIONES_OK:
        path = os.path.join(BASE, fname)
        assert os.path.exists(path), f"No existe {path}"
        res = compile_file(path)
        assert res["errors"] == [], f"{fname} no debería dar errores, obtuvo: {res['errors']}"

def test_control_ok():
    for fname in CONTROL_OK:
        path = os.path.join(BASE, fname)
        assert os.path.exists(path), f"No existe {path}"
        res = compile_file(path)
        assert res["errors"] == [], f"{fname} no debería dar errores, obtuvo: {res['errors']}"

def test_clases_ok():
    for fname in CLASES_OK:
        path = os.path.join(BASE, fname)
        assert os.path.exists(path), f"No existe {path}"
        res = compile_file(path)
        assert res["errors"] == [], f"{fname} no debería dar errores, obtuvo: {res['errors']}"

def test_listas_ok():
    for fname in LISTAS_OK:
        path = os.path.join(BASE, fname)
        assert os.path.exists(path), f"No existe {path}"
        res = compile_file(path)
        assert res["errors"] == [], f"{fname} no debería dar errores, obtuvo: {res['errors']}"

def test_generales_ok():
    for fname in GENERALES_OK:
        path = os.path.join(BASE, fname)
        assert os.path.exists(path), f"No existe {path}"
        res = compile_file(path)
        assert res["errors"] == [], f"{fname} no debería dar errores, obtuvo: {res['errors']}"

def test_errores():
    for fname in ERRORES:
        path = os.path.join(BASE, fname)
        assert os.path.exists(path), f"No existe {path}"
        res = compile_file(path)
        assert res["errors"], f"{fname} debería dar errores semánticos"
