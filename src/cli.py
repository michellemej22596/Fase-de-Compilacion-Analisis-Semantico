# src/cli.py
import sys
from antlr4 import InputStream, FileStream, CommonTokenStream
from parsing.antlr.CompiscriptLexer import CompiscriptLexer
from parsing.antlr.CompiscriptParser import CompiscriptParser
from semantic.checker import analyze

def generate_syntax_tree(path: str):
    """
    Genera un árbol sintáctico a partir de un archivo fuente .cps.
    
    El archivo .cps debe estar escrito en el lenguaje definido por la gramática Compiscript.
    El proceso consiste en:
    1. Leer el archivo de entrada.
    2. Tokenizar el contenido utilizando el lexer de ANTLR.
    3. Analizar los tokens con el parser y construir el árbol sintáctico.
    
    Args:
        path (str): Ruta al archivo .cps que se va a procesar.

    Returns:
        tree: Árbol sintáctico generado por el parser.
    """
    input_stream = FileStream(path, encoding="utf-8")  # Leer el archivo en formato UTF-8
    lexer = CompiscriptLexer(input_stream)  # Tokenizar el contenido del archivo
    token_stream = CommonTokenStream(lexer)  # Crear un flujo de tokens
    parser = CompiscriptParser(token_stream)  # Crear el parser que usará los tokens
    tree = parser.program()  # Procesar la regla inicial de la gramática (programa)
    return tree

def execute_cli():
    """
    Función principal que ejecuta la interfaz de línea de comandos (CLI) para procesar un archivo .cps.
    
    Esta función maneja la ejecución del programa en la terminal y realiza lo siguiente:
    1. Verificar que se haya proporcionado un archivo como argumento.
    2. Llamar a la función generate_syntax_tree() para obtener el árbol sintáctico.
    3. Realizar el análisis semántico utilizando la función 'analyze' del módulo 'semantic.checker'.
    4. Mostrar la tabla de símbolos extraída del análisis semántico.
    5. Mostrar los errores detectados durante el análisis semántico.
    """
    if len(sys.argv) < 2:
        print("Uso: python -m cli <archivo.cps>")  # Mensaje de uso si no se proporciona el archivo
        sys.exit(1)  # Salir si no se pasa el archivo como argumento

    file_path = sys.argv[1]  # Obtener la ruta del archivo desde los argumentos de la línea de comandos
    print(f"Procesando archivo {file_path}...\n")  # Imprimir el archivo que se está procesando

    # Crear el árbol sintáctico a partir del archivo proporcionado
    tree = generate_syntax_tree(file_path)
    analysis_result = analyze(tree)  # Realizar el análisis semántico sobre el árbol sintáctico

    # Mostrar la tabla de símbolos extraída del análisis semántico
    print("=== Tabla de Símbolos ===")
    for symbol in analysis_result["symbols"]:
        print(symbol)

    # Mostrar los errores detectados durante el análisis semántico
    print("\n=== Errores detectados ===")
    if not analysis_result["errors"]:
        print("No se encontraron errores ✅")  # Si no hay errores, mostrar mensaje de éxito
    else:
        for error in analysis_result["errors"]:
            # Imprimir cada error con su línea, columna, código y mensaje
            print(f"{error['line']}:{error['col']} {error['code']}: {error['message']}")

if __name__ == "__main__":
    execute_cli()  # Ejecutar la función principal cuando se ejecuta el archivo
