# src/cli.py
import sys
from antlr4 import InputStream, FileStream, CommonTokenStream
from parsing.antlr.CompiscriptLexer import CompiscriptLexer
from parsing.antlr.CompiscriptParser import CompiscriptParser
from semantic.checker import analyze

def generate_syntax_tree(path: str):
    """Construye el árbol sintáctico desde un archivo .cps"""
    input_stream = FileStream(path, encoding="utf-8")
    lexer = CompiscriptLexer(input_stream)
    token_stream = CommonTokenStream(lexer)
    parser = CompiscriptParser(token_stream)
    tree = parser.program()   # Regla inicial de tu gramática
    return tree

def execute_cli():
    if len(sys.argv) < 2:
        print("Uso: python -m cli <archivo.cps>")
        sys.exit(1)

    file_path = sys.argv[1]
    print(f"Procesando archivo {file_path}...\n")

    # Crear árbol sintáctico a partir del archivo
    tree = generate_syntax_tree(file_path)
    analysis_result = analyze(tree)  # Realiza el análisis semántico

    # Mostrar símbolos
    print("=== Tabla de Símbolos ===")
    for symbol in analysis_result["symbols"]:
        print(symbol)

    # Mostrar errores
    print("\n=== Errores detectados ===")
    if not analysis_result["errors"]:
        print("No se encontraron errores ✅")
    else:
        for error in analysis_result["errors"]:
            print(f"{error['line']}:{error['col']} {error['code']}: {error['message']}")

if __name__ == "__main__":
    execute_cli()
