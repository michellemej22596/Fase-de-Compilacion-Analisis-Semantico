from CompiscriptVisitor import CompiscriptVisitor
from CompiscriptParser import CompiscriptParser as P
from .scope import Scope
from .symbols import VarSymbol
from .types import *
from .errors import throw


class SemaVisitor(CompiscriptVisitor):
    def __init__(self):
        self.scope = Scope(owner="<global>")

    # =========================
    # STATEMENTS
    # =========================

    def visitVariableDeclaration(self, ctx: P.VariableDeclarationContext):
        name = ctx.Identifier().getText()
        declared = ctx.typeAnnotation().type_().getText() if ctx.typeAnnotation() else None

        if name in self.scope.vars:
            throw(f"Redeclaración de '{name}' en el mismo ámbito", ctx)

        sym = VarSymbol(name, declared or NULL)

        if ctx.initializer():
            expr_t = self.visit(ctx.initializer().expression())
            if declared and not are_compatible(declared, expr_t):
                throw(f"Asignación incompatible: {declared} = {expr_t}", ctx)
            sym.typ = declared or expr_t
            sym.initialized = True

        self.scope.define_var(sym)
        return None

    def visitConstantDeclaration(self, ctx: P.ConstantDeclarationContext):
        name = ctx.Identifier().getText()
        declared = ctx.typeAnnotation().type_().getText() if ctx.typeAnnotation() else None

        if name in self.scope.vars:
            throw(f"Redeclaración de '{name}' en el mismo ámbito", ctx)

        expr_t = self.visit(ctx.expression())
        if declared and not are_compatible(declared, expr_t):
            throw(f"Asignación incompatible a const: {declared} = {expr_t}", ctx)

        sym = VarSymbol(name, declared or expr_t, is_const=True, initialized=True)
        self.scope.define_var(sym)
        return None

    # assignment:
    #   Identifier '=' expression ';'
    # | expression '.' Identifier '=' expression ';'
    def visitAssignment(self, ctx: P.AssignmentContext):
        if ctx.getChildCount() >= 4 and ctx.getChild(1).getText() == '=':
            name = ctx.getChild(0).getText()
            var = self.scope.lookup_var(name)
            if not var:
                throw(f"Variable '{name}' no declarada", ctx)
            if var.is_const:
                throw(f"No se puede asignar a constante '{name}'", ctx)
            expr_t = self.visit(ctx.expression(0))
            if not are_compatible(var.typ, expr_t):
                throw(f"Asignación incompatible: {var.typ} = {expr_t}", ctx)
            var.initialized = True
            return None

        for e in ctx.expression() or []:
            _ = self.visit(e)
        return None

    # =========================
    # EXPRESIONES (PUENTES)
    # =========================

    def visitExpression(self, ctx: P.ExpressionContext):
        return self.visit(ctx.assignmentExpr())

    def visitAssignExpr(self, ctx: P.AssignExprContext):
        return self.visit(ctx.assignmentExpr())

    def visitPropertyAssignExpr(self, ctx: P.PropertyAssignExprContext):
        return self.visit(ctx.assignmentExpr())

    def visitExprNoAssign(self, ctx: P.ExprNoAssignContext):
        return self.visit(ctx.conditionalExpr())

    # Nota: por el label #TernaryExpr, ANTLR llamará a este método
    def visitTernaryExpr(self, ctx: P.TernaryExprContext):
    # En esta alternativa etiquetada (#TernaryExpr), el ('?' expr ':' expr) es OPCIONAL.
    # Si NO hay parte ternaria, simplemente delegamos a logicalOrExpr sin exigir boolean.
        if ctx.expression() is None or len(ctx.expression()) == 0:
         return self.visit(ctx.logicalOrExpr())

        # Con parte ternaria presente: la condición SÍ debe ser booleana.
        cond_t = self.visit(ctx.logicalOrExpr())
        if not is_boolean(cond_t):
            throw(f"?: condición debe ser boolean", ctx)

        # (Opcional) visitar ramas y/o chequear compatibilidad entre ellas.
        for e in ctx.expression():
            _ = self.visit(e)
        return NULL

    # Si ANTLR llega a usar el método de la regla base (sin label),
    # deja un pass-through seguro:
    def visitConditionalExpr(self, ctx: P.ConditionalExprContext):
        # Normalmente ANTLR llamará a visitTernaryExpr por el label, pero por seguridad:
        return self.visitChildren(ctx)


    # =========================
    # EXPRESIONES (OPERADORES)
    # =========================

    # logicalOrExpr: logicalAndExpr ( '||' logicalAndExpr )*
    def visitLogicalOrExpr(self, ctx: P.LogicalOrExprContext):
        n = len(ctx.logicalAndExpr())
        if n == 1:
            return self.visit(ctx.logicalAndExpr(0))
        t0 = self.visit(ctx.logicalAndExpr(0))
        if not is_boolean(t0):
            throw(f"|| requiere booleanos: {t0}, ...", ctx)
        for i in range(1, n):
            ti = self.visit(ctx.logicalAndExpr(i))
            if not is_boolean(ti):
                throw(f"|| requiere booleanos: ..., {ti}", ctx)
        return BOOL

    # logicalAndExpr: equalityExpr ( '&&' equalityExpr )*
    def visitLogicalAndExpr(self, ctx: P.LogicalAndExprContext):
        n = len(ctx.equalityExpr())
        if n == 1:
            return self.visit(ctx.equalityExpr(0))
        t0 = self.visit(ctx.equalityExpr(0))
        if not is_boolean(t0):
            throw(f"&& requiere booleanos: {t0}, ...", ctx)
        for i in range(1, n):
            ti = self.visit(ctx.equalityExpr(i))
            if not is_boolean(ti):
                throw(f"&& requiere booleanos: ..., {ti}", ctx)
        return BOOL

    def visitEqualityExpr(self, ctx: P.EqualityExprContext):
        n = len(ctx.relationalExpr())
        # Sin '==' ni '!=' -> delega al hijo
        if n == 1:
            return self.visit(ctx.relationalExpr(0))
        # Con operadores de igualdad -> resultado booleano (y verifica compatibilidad)
        t = self.visit(ctx.relationalExpr(0))
        for i in range(1, n):
            rt = self.visit(ctx.relationalExpr(i))
            if not are_compatible(t, rt):
                throw(f"Igualdad incompatible: {t} vs {rt}", ctx)
        return BOOL

    def visitRelationalExpr(self, ctx: P.RelationalExprContext):
        n = len(ctx.additiveExpr())
        # Sin <, <=, >, >= -> delega al hijo
        if n == 1:
            return self.visit(ctx.additiveExpr(0))
        # Con operadores relacionales -> resultado booleano (y verifica compatibilidad)
        t = self.visit(ctx.additiveExpr(0))
        for i in range(1, n):
            rt = self.visit(ctx.additiveExpr(i))
            if not are_compatible(t, rt):
                throw(f"Comparación incompatible: {t} vs {rt}", ctx)
        return BOOL


    def visitAdditiveExpr(self, ctx: P.AdditiveExprContext):
        t = self.visit(ctx.multiplicativeExpr(0))
        for i in range(1, len(ctx.multiplicativeExpr())):
            rt = self.visit(ctx.multiplicativeExpr(i))
            if not (is_numeric(t) and is_numeric(rt)):
                throw(f"Operación aritmética requiere numéricos: {t}, {rt}", ctx)
            t = FLOAT if FLOAT in (t, rt) else INT
        return t

    def visitMultiplicativeExpr(self, ctx: P.MultiplicativeExprContext):
        t = self.visit(ctx.unaryExpr(0))
        for i in range(1, len(ctx.unaryExpr())):
            rt = self.visit(ctx.unaryExpr(i))
            if not (is_numeric(t) and is_numeric(rt)):
                throw(f"Operación aritmética requiere numéricos: {t}, {rt}", ctx)
            t = FLOAT if FLOAT in (t, rt) else INT
        return t

    def visitUnaryExpr(self, ctx: P.UnaryExprContext):
        if ctx.getChildCount() == 2:
            op = ctx.getChild(0).getText()
            t  = self.visit(ctx.unaryExpr())
            if op == '!':
                if not is_boolean(t):
                    throw(f"! requiere booleano, no {t}", ctx)
                return BOOL
            if op == '-':
                if not is_numeric(t):
                    throw(f"Negación requiere numérico, no {t}", ctx)
                return t
            return self.visitChildren(ctx)
        return self.visitChildren(ctx)

    # =========================
    # PRIMARIAS / LITERALES / LHS
    # =========================

    def visitPrimaryExpr(self, ctx: P.PrimaryExprContext):
        if ctx.expression():
            return self.visit(ctx.expression())
        if ctx.literalExpr():
            return self.visit(ctx.literalExpr())
        if ctx.leftHandSide():
            return self.visit(ctx.leftHandSide())
        return NULL

    # literalExpr: Literal | arrayLiteral | 'null' | 'true' | 'false'
    def visitLiteralExpr(self, ctx: P.LiteralExprContext):
        txt = ctx.getText()
        if txt == "true" or txt == "false":
            return BOOL
        if txt == "null":
            return NULL
        if ctx.arrayLiteral():
            return NULL
        if len(txt) >= 2 and txt[0] == '"' and txt[-1] == '"':
            return STR
        if txt.isdigit():
            return INT
        return NULL

    # leftHandSide: primaryAtom (suffixOp)*
    def visitLeftHandSide(self, ctx: P.LeftHandSideContext):
        t = self.visit(ctx.primaryAtom())
        for _ in ctx.suffixOp() or []:
            pass
        return t

    # primaryAtom labels
    def visitIdentifierExpr(self, ctx: P.IdentifierExprContext):
        name = ctx.Identifier().getText()
        v = self.scope.lookup_var(name)
        if not v:
            throw(f"Variable '{name}' no declarada", ctx)
        return v.typ

    def visitNewExpr(self, ctx: P.NewExprContext):
        return ctx.Identifier().getText()

    def visitThisExpr(self, ctx: P.ThisExprContext):
        return NULL

    # suffixOp labels
    def visitCallExpr(self, ctx: P.CallExprContext):
        parent = ctx.parentCtx
        if hasattr(parent, "arguments") and parent.arguments():
            for arg in parent.arguments().expression():
                _ = self.visit(arg)
        return NULL

    def visitIndexExpr(self, ctx: P.IndexExprContext):
        _ = self.visit(ctx.expression())
        return NULL

    def visitPropertyAccessExpr(self, ctx: P.PropertyAccessExprContext):
        return NULL
