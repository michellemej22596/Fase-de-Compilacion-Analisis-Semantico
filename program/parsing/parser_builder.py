from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Tuple, Union
from pathlib import Path

from antlr4 import InputStream, FileStream, CommonTokenStream, ParserRuleContext

from .error_listener import CollectingErrorListener, SyntaxDiagnostic
from .CompiscriptLexer import CompiscriptLexer
from .CompiscriptParser import CompiscriptParser

@dataclass
class ParsingResult:
    """Contenedor para el árbol sintáctico, el parser, los tokens y los errores de sintaxis."""
    tree: ParserRuleContext
    parser: CompiscriptParser
    tokens: CommonTokenStream
    errors: list[SyntaxDiagnostic]

    def is_valid(self) -> bool:
        return not self.errors

def _initialize_parser(input_stream) -> Tuple[CompiscriptLexer, CompiscriptParser, CommonTokenStream, CollectingErrorListener]:
    lexer = CompiscriptLexer(input_stream)
    token_stream = CommonTokenStream(lexer)
    parser = CompiscriptParser(token_stream)

    error_listener = CollectingErrorListener()
    try:
        lexer.removeErrorListeners()
        lexer.addErrorListener(error_listener)
    except Exception:
        pass
    parser.removeErrorListeners()
    parser.addErrorListener(error_listener)

    return lexer, parser, token_stream, error_listener

def parse_from_string(
    code: str,
    *,
    entry_rule: str = "program",
    raise_on_error: bool = False,
) -> ParsingResult:
    input_stream = InputStream(code)
    _, parser, tokens, error_listener = _initialize_parser(input_stream)

    if not hasattr(parser, entry_rule):
        raise AttributeError(f"La regla de entrada '{entry_rule}' no existe en CompiscriptParser.")
    parse_function = getattr(parser, entry_rule)
    tree = parse_function()  # type: ignore[misc]

    errors = error_listener.errors
    if raise_on_error and errors:
        raise SyntaxError("\n".join(str(error) for error in errors))

    return ParsingResult(tree=tree, parser=parser, tokens=tokens, errors=errors)

def parse_from_file(
    path: Union[str, Path],
    *,
    entry_rule: str = "program",
    encoding: Optional[str] = "utf-8",
    raise_on_error: bool = False,
) -> ParsingResult:
    input_stream = FileStream(str(path), encoding=encoding)
    _, parser, tokens, error_listener = _initialize_parser(input_stream)

    if not hasattr(parser, entry_rule):
        raise AttributeError(f"La regla de entrada '{entry_rule}' no existe en CompiscriptParser.")
    parse_function = getattr(parser, entry_rule)
    tree = parse_function()  # type: ignore[misc]

    errors = error_listener.errors
    if raise_on_error and errors:
        raise SyntaxError("\n".join(str(error) for error in errors))

    return ParsingResult(tree=tree, parser=parser, tokens=tokens, errors=errors)

# Funciones opcionales que devuelven la estructura de datos que solicitaste
def get_parse_structure(source: Union[str, Path]):
    p = Path(str(source))
    result = parse_from_file(p) if p.exists() else parse_from_string(str(source))
    return result.tree, result.tokens, result.parser

def parse_from_input_stream(stream: InputStream):
    _, parser, tokens, _ = _initialize_parser(stream)
    tree = getattr(parser, "program")()
    return tree, tokens, parser
