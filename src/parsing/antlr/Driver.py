import sys  # Importamos el módulo sys para manejar argumentos de línea de comandos
from antlr4 import *  # Importamos las clases de antlr4 para el procesamiento de gramáticas
from CompiscriptLexer import CompiscriptLexer  # Importamos el lexer generado por ANTLR para la gramática
from CompiscriptParser import CompiscriptParser  # Importamos el parser generado por ANTLR para la gramática
from antlr4.error.ErrorListener import ErrorListener  # Importamos la clase ErrorListener para manejar errores
from semantic.sema_visitor import SemaVisitor  # Importamos el visitante semántico que analizará el árbol
from semantic.errors import SemanticError  # Importamos la clase de errores semánticos que se pueden generar


# Definimos una clase para recopilar los errores sintácticos
class CollectingErrorListener(ErrorListener):
    def __init__(self):
        super().__init__()  # Llamamos al constructor de la clase base ErrorListener
        self.errors = []  # Lista para almacenar los errores

    # Método sobrescrito para capturar los errores de sintaxis
    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        text = getattr(offendingSymbol, 'text', '<EOF>')  # Obtenemos el texto del símbolo que causó el error (si no tiene, usamos <EOF>)
        # Almacenamos la información del error en la lista
        self.errors.append({
            "line": line,  # Línea donde ocurrió el error
            "column": column,  # Columna donde ocurrió el error
            "text": text,  # El texto del símbolo que causó el error
            "msg": msg  # El mensaje del error
        })

    # Verifica si existen errores
    def has_errors(self):
        return len(self.errors) > 0  # Retorna True si hay errores

    # Método para generar un reporte de los errores
    def report(self):
        return "\n".join(
            f"[Sintáctico] línea {e['line']}, col {e['column']}: cerca de '{e['text']}' → {e['msg']}"
            for e in self.errors  # Por cada error, generamos un mensaje detallado
        )


# Función principal que maneja el flujo del programa
def main(argv):
    # Verificamos si el número de argumentos es menor que 2
    if len(argv) < 2:
        print("Uso: python Driver.py <archivo.cps>")  # Si no se pasa el archivo, mostramos el mensaje de uso
        sys.exit(1)  # Salimos del programa con código de error 1

    input_stream = FileStream(argv[1], encoding="utf-8")  # Leemos el archivo de entrada (en formato cps)

    lexer = CompiscriptLexer(input_stream)  # Creamos el lexer (analizador léxico) para tokenizar el archivo
    tokens = CommonTokenStream(lexer)  # Generamos un flujo de tokens a partir del lexer

    parser = CompiscriptParser(tokens)  # Creamos el parser (analizador sintáctico) para generar el árbol de análisis
    parser.removeErrorListeners()  # Eliminamos cualquier listener de error por defecto
    err = CollectingErrorListener()  # Creamos nuestro listener personalizado para recopilar los errores
    parser.addErrorListener(err)  # Agregamos nuestro listener al parser

    tree = parser.program()  # Comenzamos el análisis sintáctico, generando el árbol de sintaxis

    # --- Sintaxis ---
    if err.has_errors():  # Si hubo errores sintácticos
        print(err.report())  # Imprimimos el reporte de los errores
        sys.exit(2)  # Salimos con código de error 2 (error de sintaxis)
    else:
        print("✔ Sintaxis OK")  # Si no hubo errores, informamos que la sintaxis está correcta

    # --- Semántica ---
    try:
        sema = SemaVisitor()  # Creamos un visitante semántico
        sema.visit(tree)  # Visitamos el árbol de sintaxis para analizar semánticamente el código
        print("✔ Semántica OK")  # Si no hay errores semánticos, informamos que la semántica es correcta
        sys.exit(0)  # Salimos con código 0 (sin errores)
    except SemanticError as e:  # Si ocurre un error semántico
        print(f"Semántico: {e}")  # Imprimimos el error semántico
        sys.exit(3)  # Salimos con código de error 3 (error semántico)


# Punto de entrada principal del programa
if __name__ == '__main__':
    main(sys.argv)  # Llamamos a la función main pasando los argumentos de la línea de comandos
