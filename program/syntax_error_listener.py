# syntax_error_listener.py
from antlr4.error.ErrorListener import ErrorListener

class CollectingErrorListener(ErrorListener):
    def __init__(self):
        super().__init__()
        self.errors = []

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        # Normaliza mensaje y guarda
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
