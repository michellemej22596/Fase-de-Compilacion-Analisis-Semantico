INT, STR, BOOL, FLOAT, NULL, VOID = "integer","string","boolean","float","null","void"

def is_numeric(t): return t in (INT, FLOAT)
def is_boolean(t): return t == BOOL
def are_compatible(a,b):
    if a == b: return True
    if is_numeric(a) and is_numeric(b): return True
    return False
