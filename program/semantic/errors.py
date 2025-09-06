class SemanticError(Exception):
    def __init__(self, msg, line=None, col=None):
        where = f" (línea {line}, col {col})" if line is not None else ""
        super().__init__(msg + where)

def throw(msg, ctx):
    t = getattr(ctx, "start", None)
    line = getattr(t, "line", None) if t else None
    col  = getattr(t, "column", None) if t else None
    raise SemanticError(msg, line, col)
