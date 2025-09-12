# src/cli.py
import sys
from antlr4 import FileStream, CommonTokenStream
from parsing.antlr.CompiscriptLexer import CompiscriptLexer
from parsing.antlr.CompiscriptParser import CompiscriptParser
from semantic.checker import analyze

def build_syntax_tree(file_path: str):
    """Genera el árbol sintáctico a partir de un archivo .cps"""
    input_stream = FileStream(file_path, encoding="utf-8")
    lexer = CompiscriptLexer(input_stream)
    token_stream = CommonTokenStream(lexer)
    parser = CompiscriptParser(token_stream)
    tree = parser.program()   # Usa la regla inicial del parser
    return tree

def execute_cli():
    if len(sys.argv) < 2:
        print("Error: Se necesita un archivo .cps como argumento.")
        print("Uso: python -m cli <ruta_del_archivo.cps>")
        sys.exit(1)

    file_path = sys.argv[1]
    print(f"Iniciando compilación del archivo: {file_path}...\n")

    syntax_tree = build_syntax_tree(file_path)
    analysis_result = analyze(syntax_tree)

    print("=== Símbolos encontrados ===")
    for symbol in analysis_result["symbols"]:
        print(symbol)

    print("\n=== Errores detectados ===")
    if not analysis_result["errors"]:
        print("No se encontraron errores ✅")
    else:
        for error in analysis_result["errors"]:
            print(f"{error['line']}:{error['col']} {error['code']}: {error['message']}")

if __name__ == "__main__":
    execute_cli()
