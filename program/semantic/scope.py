class Scope:
    def __init__(self, parent=None, owner="<global>"):
        self.parent = parent
        self.owner = owner
        self.vars = {}

    def define_var(self, sym):
        if sym.name in self.vars:
            raise KeyError(f"Redeclaración de '{sym.name}' en {self.owner}")
        self.vars[sym.name] = sym

    def lookup_var(self, name):
        s = self
        while s:
            if name in s.vars: return s.vars[name]
            s = s.parent
        return None
