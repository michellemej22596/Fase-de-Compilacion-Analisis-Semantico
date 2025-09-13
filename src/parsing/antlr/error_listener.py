from antlr4.error.ErrorListener import ErrorListener  # Importamos la clase base ErrorListener de ANTLR
from dataclasses import dataclass  # Importamos decorador dataclass para crear clases con características simples

# Definición de la clase CollectingErrorListener, que maneja los errores sintácticos
class CollectingErrorListener(ErrorListener):
    def __init__(self):
        super().__init__()  # Llamamos al constructor de la clase base ErrorListener
        self.errors = []  # Lista para almacenar los errores detectados

    # Método sobrescrito para capturar los errores de sintaxis
    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        # 'offendingSymbol' es el símbolo que causó el error, 'line' y 'column' indican donde ocurrió
        # 'msg' es el mensaje de error, 'e' es la excepción que se generó (puede no ser usada aquí)
        text = getattr(offendingSymbol, 'text', '<EOF>')  # Obtenemos el texto del símbolo que causó el error
        # Agregamos un objeto 'SyntaxDiagnostic' a la lista de errores, con los detalles del error
        self.errors.append(SyntaxDiagnostic(line, column, text, msg))

    # Método para verificar si hay errores
    def has_errors(self):
        return len(self.errors) > 0  # Retorna True si la lista de errores tiene elementos

    # Método para generar un reporte de los errores de sintaxis
    def report(self):
        # Iteramos sobre todos los errores almacenados y los formateamos como una cadena
        return "\n".join(
            f"[Sintáctico] línea {e.line}, col {e.column}: cerca de '{e.text}' → {e.msg}"
            for e in self.errors  # Cada error es un objeto 'SyntaxDiagnostic'
        )

# Clase que define la estructura de un error de sintaxis
@dataclass
class SyntaxDiagnostic:
    """Contenedor para los detalles de un error de sintaxis."""
    line: int  # Línea donde ocurrió el error
    column: int  # Columna donde ocurrió el error
    text: str  # El texto del símbolo que causó el error
    msg: str  # El mensaje de error

    def __str__(self):
        # Método especial para imprimir el error de forma legible
        return f"[Sintáctico] línea {self.line}, col {self.column}: cerca de '{self.text}' → {self.msg}"
