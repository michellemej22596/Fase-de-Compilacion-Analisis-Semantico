import sys
from antlr4 import *
from CompiscriptLexer import CompiscriptLexer
from CompiscriptParser import CompiscriptParser
from antlr4.error.ErrorListener import ErrorListener
from semantic.sema_visitor import SemaVisitor
from semantic.errors import SemanticError



class CollectingErrorListener(ErrorListener):
    def __init__(self):
        super().__init__()
        self.errors = []

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        text = getattr(offendingSymbol, 'text', '<EOF>')
        self.errors.append({
            "line": line,
            "column": column,
            "text": text,
            "msg": msg
        })

    def has_errors(self):
        return len(self.errors) > 0

    def report(self):
        return "\n".join(
            f"[Sintáctico] línea {e['line']}, col {e['column']}: cerca de '{e['text']}' → {e['msg']}"
            for e in self.errors
        )


def main(argv):
    if len(argv) < 2:
        print("Uso: python Driver.py <archivo.cps>")
        sys.exit(1)

    # Lee el archivo de entrada (UTF-8 por defecto)
    input_stream = FileStream(argv[1], encoding="utf-8")

    # Lexer y tokens
    lexer = CompiscriptLexer(input_stream)
    stream = CommonTokenStream(lexer)

    # Parser + listener de errores
    parser = CompiscriptParser(stream)
    parser.removeErrorListeners()
    err = CollectingErrorListener()
    parser.addErrorListener(err)

    # Regla inicial (ajústala si tu grammar usa otro nombre)
    tree = parser.program()  # regla de inicio

    # Reporte sintáctico
    if err.has_errors():
        print(err.report())
        sys.exit(2)  # fallo sintáctico
    else:
        print("✔ Sintaxis OK")
        sys.exit(0)

    if err.has_errors():
        print(err.report()); sys.exit(2)
    else:
        try:
            sema = SemaVisitor()
            sema.visit(tree)
            print("✔ Semántica OK")
            sys.exit(0)
        except SemanticError as e:
            print(f"Semántico: {e}")
            sys.exit(3)


if __name__ == '__main__':
    main(sys.argv)
