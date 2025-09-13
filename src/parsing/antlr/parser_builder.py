from __future__ import annotations  # Importación para usar anotaciones de tipo como cadenas (compatibilidad futura)
from dataclasses import dataclass  # Importamos el decorador para crear clases con atributos automáticamente
from typing import Optional, Tuple, Union  # Importamos tipos para anotaciones de tipo
from pathlib import Path  # Importación para trabajar con rutas de archivo

# Importaciones de ANTLR, que es la herramienta para generar analizadores sintácticos
from antlr4 import InputStream, FileStream, CommonTokenStream, ParserRuleContext

# Importación de nuestras clases personalizadas de errores y análisis léxico/sintáctico
from .error_listener import CollectingErrorListener, SyntaxDiagnostic
from .CompiscriptLexer import CompiscriptLexer  # Lexer generado por ANTLR para nuestro lenguaje
from .CompiscriptParser import CompiscriptParser  # Parser generado por ANTLR para nuestro lenguaje

# Definición de una clase para almacenar los resultados de un análisis sintáctico
@dataclass
class ParseResult:
    """Árbol, parser, tokens y errores de sintaxis."""
    tree: ParserRuleContext  # El árbol de análisis sintáctico
    parser: CompiscriptParser  # El parser usado
    tokens: CommonTokenStream  # Los tokens generados por el lexer
    errors: list[SyntaxDiagnostic]  # Errores de sintaxis (si los hay)

    # Método que devuelve True si no hay errores, False si los hay
    def ok(self) -> bool:
        return not self.errors

# Función que configura el lexer, el parser y el manejador de errores
def _configure(input_stream) -> Tuple[CompiscriptLexer, CompiscriptParser, CommonTokenStream, CollectingErrorListener]:
    lexer = CompiscriptLexer(input_stream)  # Crea el lexer a partir del flujo de entrada
    tokens = CommonTokenStream(lexer)  # Crea un flujo de tokens a partir del lexer
    parser = CompiscriptParser(tokens)  # Crea el parser a partir de los tokens generados

    err = CollectingErrorListener()  # Crea un manejador de errores personalizado
    try:
        lexer.removeErrorListeners()  # Elimina los listeners de error predeterminados del lexer
        lexer.addErrorListener(err)  # Añade nuestro listener de errores al lexer
    except Exception:
        pass  # Si ocurre un error en el lexer (por ejemplo, si no tiene listeners), lo ignoramos

    parser.removeErrorListeners()  # Elimina los listeners de error predeterminados del parser
    parser.addErrorListener(err)  # Añade nuestro listener de errores al parser

    return lexer, parser, tokens, err  # Devuelve los objetos configurados

# Función para construir el árbol de análisis sintáctico a partir de un código fuente (en texto)
def build_from_text(
    code: str,  # Código fuente como cadena de texto
    *,
    entry_rule: str = "program",  # Regla de entrada (normalmente "program")
    raise_on_error: bool = False,  # Si True, lanza una excepción si hay errores
) -> ParseResult:
    input_stream = InputStream(code)  # Crea un flujo de entrada a partir del código
    _, parser, tokens, err = _configure(input_stream)  # Configura el lexer, parser y el listener de errores

    # Verifica que la regla de entrada exista en el parser
    if not hasattr(parser, entry_rule):
        raise AttributeError(f"Entry rule '{entry_rule}' no existe en CompiscriptParser.")
    
    rule_fn = getattr(parser, entry_rule)  # Obtiene la función asociada a la regla de entrada
    tree = rule_fn()  # Llama a la función para construir el árbol de análisis sintáctico

    errors = err.errors  # Obtiene los errores de sintaxis del listener
    if raise_on_error and errors:  # Si hay errores y se ha solicitado lanzarlos
        raise SyntaxError("\n".join(str(e) for e in errors))  # Lanza una excepción con los errores

    return ParseResult(tree=tree, parser=parser, tokens=tokens, errors=errors)  # Devuelve los resultados del análisis

# Función para construir el árbol de análisis sintáctico a partir de un archivo
def build_from_file(
    path: Union[str, Path],  # Ruta al archivo de entrada (puede ser cadena o Path)
    *,
    entry_rule: str = "program",  # Regla de entrada (normalmente "program")
    encoding: Optional[str] = "utf-8",  # Codificación del archivo
    raise_on_error: bool = False,  # Si True, lanza una excepción si hay errores
) -> ParseResult:
    input_stream = FileStream(str(path), encoding=encoding)  # Crea un flujo de entrada desde el archivo
    _, parser, tokens, err = _configure(input_stream)  # Configura el lexer, parser y el listener de errores

    # Verifica que la regla de entrada exista en el parser
    if not hasattr(parser, entry_rule):
        raise AttributeError(f"Entry rule '{entry_rule}' no existe en CompiscriptParser.")
    
    rule_fn = getattr(parser, entry_rule)  # Obtiene la función asociada a la regla de entrada
    tree = rule_fn()  # Llama a la función para construir el árbol de análisis sintáctico

    errors = err.errors  # Obtiene los errores de sintaxis del listener
    if raise_on_error and errors:  # Si hay errores y se ha solicitado lanzarlos
        raise SyntaxError("\n".join(str(e) for e in errors))  # Lanza una excepción con los errores

    return ParseResult(tree=tree, parser=parser, tokens=tokens, errors=errors)  # Devuelve los resultados del análisis

# Función de alto nivel para construir el árbol de análisis sintáctico desde una cadena o archivo
def build_parse_tree(source: Union[str, Path]):
    p = Path(str(source))  # Convierte la fuente en un objeto Path
    # Si la fuente es un archivo que existe, construye el árbol desde el archivo; si no, desde el texto
    res = build_from_file(p) if p.exists() else build_from_text(str(source))
    return (res.tree, res.tokens, res.parser)  # Devuelve el árbol, los tokens y el parser

# Función para analizar el código desde un flujo de entrada
def parse_from_stream(stream: InputStream):
    _, parser, tokens, _ = _configure(stream)  # Configura el lexer, parser y tokens desde el flujo de entrada
    tree = getattr(parser, "program")()  # Llama a la regla de entrada "program" para construir el árbol
    return (tree, tokens, parser)  # Devuelve el árbol, los tokens y el parser

# Función para analizar el código desde una cadena de texto
def parse_from_string(
    code: str,
    *,
    entry_rule: str = "program",  # Regla de entrada
    raise_on_error: bool = False,  # Si True, lanza una excepción si hay errores
) -> ParsingResult:
    input_stream = InputStream(code)  # Crea un flujo de entrada a partir del código
    _, parser, tokens, error_listener = _initialize_parser(input_stream)  # Configura el lexer, parser y tokens

    # Verifica que la regla de entrada exista en el parser
    if not hasattr(parser, entry_rule):
        raise AttributeError(f"La regla de entrada '{entry_rule}' no existe en CompiscriptParser.")
    
    parse_function = getattr(parser, entry_rule)  # Obtiene la función asociada a la regla de entrada
    tree = parse_function()  # Llama a la función para construir el árbol de análisis sintáctico

    errors = error_listener.errors  # Obtiene los errores del listener
    if raise_on_error and errors:  # Si hay errores y se ha solicitado lanzarlos
        raise SyntaxError("\n".join(str(error) for error in errors))  # Lanza una excepción con los errores

    return ParseResult(tree=tree, parser=parser, tokens=tokens, errors=errors)  # Devuelve los resultados del análisis
