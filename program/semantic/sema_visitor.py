from CompiscriptVisitor import CompiscriptVisitor
from CompiscriptParser import CompiscriptParser as P
from .scope import Scope
from .symbols import VarSymbol
from .types import *
from .errors import throw

class SemaVisitor(CompiscriptVisitor):
    def __init__(self):
        self.scope = Scope(owner="<global>")

    # ==============
    # STATEMENTS
    # ==============

    # variableDeclaration: ('let' | 'var') Identifier typeAnnotation? initializer? ';'
    def visitVariableDeclaration(self, ctx: P.VariableDeclarationContext):
        name = ctx.Identifier().getText()
        declared = ctx.typeAnnotation().type_().getText() if ctx.typeAnnotation() else None
        if name in self.scope.vars:
            throw(f"Redeclaración de '{name}' en el mismo ámbito", ctx)

        sym = VarSymbol(name, declared or NULL)
        if ctx.initializer():
            t = self.visit(ctx.initializer().expression())
            if declared and not are_compatible(declared, t):
                throw(f"Asignación incompatible: {declared} = {t}", ctx)
            sym.typ = declared or t
            sym.initialized = True

        self.scope.define_var(sym)
        return None

    # constantDeclaration: 'const' Identifier typeAnnotation? '=' expression ';'
    def visitConstantDeclaration(self, ctx: P.ConstantDeclarationContext):
        name = ctx.Identifier().getText()
        declared = ctx.typeAnnotation().type_().getText() if ctx.typeAnnotation() else None
        if name in self.scope.vars:
            throw(f"Redeclaración de '{name}' en el mismo ámbito", ctx)

        t = self.visit(ctx.expression())
        if declared and not are_compatible(declared, t):
            throw(f"Asignación incompatible a const: {declared} = {t}", ctx)

        sym = VarSymbol(name, declared or t, is_const=True, initialized=True)
        self.scope.define_var(sym)
        return None

    # assignment: Identifier '=' expression ';' | expression '.' Identifier '=' expression ';'
    def visitAssignment(self, ctx: P.AssignmentContext):
        # Caso simple: ID = expr ;
        if ctx.Identifier():
            # En esta regla hay un Identifier() a la izquierda; hay que distinguir:
            # grammar: (Identifier '=' expression ';')  OR  (expression '.' Identifier '=' expression ';')
            # Si hay dos Identifier(), el de la izquierda no es "lvalue simple". Usamos la forma simple si no hay '.'
            if ctx.getChildCount() >= 4 and ctx.getChild(1).getText() == '=':
                name = ctx.getChild(0).getText()
                var = self.scope.lookup_var(name)
                if not var: throw(f"Variable '{name}' no declarada", ctx)
                if var.is_const: throw(f"No se puede asignar a constante '{name}'", ctx)
                t = self.visit(ctx.expression(0))
                if not are_compatible(var.typ, t):
                    throw(f"Asignación incompatible: {var.typ} = {t}", ctx)
                var.initialized = True
                return None

        # Caso propiedad: expr '.' ID '=' expr ;
        # (Para esta fase podemos omitir validación de propiedad si aún no modelas clases/objetos)
        _ = [self.visit(e) for e in ctx.expression()]  # visitamos para forzar chequeo básico
        return None

    # Otros statements (opcional por ahora):
    # printStatement, ifStatement, whileStatement, etc.,
    # puedes añadirlos después cuando valides boolean en condiciones, break/continue, etc.

    # ==============
    # EXPRESIONES
    # ==============

    # Literales
    def visitLiteralExpr(self, ctx: P.LiteralExprContext):
        tok = ctx.getText()
        if tok == "true" or tok == "false": return BOOL
        if tok == "null": return NULL
        # Literal → IntegerLiteral | StringLiteral
        if ctx.Literal():
            if ctx.IntegerLiteral(): return INT
            if ctx.StringLiteral():  return STR
        return NULL  # fallback seguro

    # IdentifierExpr: primaryAtom: Identifier # IdentifierExpr
    def visitIdentifierExpr(self, ctx: P.IdentifierExprContext):
        name = ctx.Identifier().getText()
        v = self.scope.lookup_var(name)
        if not v: throw(f"Variable '{name}' no declarada", ctx)
        return v.typ

    # ThisExpr / NewExpr / CallExpr / IndexExpr / PropertyAccessExpr:
    # Por ahora devolvemos tipos genéricos o delegamos a subexpresiones para que no bloquee.
    def visitThisExpr(self, ctx: P.ThisExprContext):
        # Si aún no modelas clases/this, marca NULL o lanza si se usa fuera de clase
        return NULL

    def visitNewExpr(self, ctx: P.NewExprContext):
        # 'new' Identifier '(' arguments? ')'
        # Sin modelar clases aún, devuelve NULL o el nombre del "tipo" instanciado
        return ctx.Identifier().getText()  # opcional

    def visitCallExpr(self, ctx: P.CallExprContext):
        # suffixOp '(' arguments? ')'
        # Primero visita el "callee" (base de la llamada) para forzar validaciones de id/propiedad
        # y luego cada argumento
        # Nota: cuando modeles funciones, valida número/tipos.
        base_t = self.visit(ctx.parentCtx.leftHandSide()) if hasattr(ctx, "parentCtx") else NULL
        if ctx.arguments():
            for arg in ctx.arguments().expression():
                _ = self.visit(arg)
        return NULL

    def visitIndexExpr(self, ctx: P.IndexExprContext):
        # '[' expression ']'
        _ = self.visit(ctx.expression())
        return NULL

    def visitPropertyAccessExpr(self, ctx: P.PropertyAccessExprContext):
        # '.' Identifier
        return NULL

    # Paréntesis: '(' expression ')'
    def visitPrimaryExpr(self, ctx: P.PrimaryExprContext):
        if ctx.expression():
            return self.visit(ctx.expression())
        return self.visitChildren(ctx)

    # Operadores unarios: ('-' | '!') unaryExpr | primaryExpr
    def visitUnaryExpr(self, ctx: P.UnaryExprContext):
        if ctx.getChildCount() == 2:
            op = ctx.getChild(0).getText()
            t  = self.visit(ctx.unaryExpr())
            if op == '!':
                if not is_boolean(t): throw(f"! requiere booleano, no {t}", ctx)
                return BOOL
            elif op == '-':
                if not is_numeric(t): throw(f"Negación requiere numérico, no {t}", ctx)
                return t
        # primaryExpr
        return self.visitChildren(ctx)

    # multiplicativeExpr: unaryExpr (('*'|'/'|'%') unaryExpr)*
    def visitMultiplicativeExpr(self, ctx: P.MultiplicativeExprContext):
        t = self.visit(ctx.unaryExpr(0))
        for i in range(1, len(ctx.unaryExpr())):
            rt = self.visit(ctx.unaryExpr(i))
            if not (is_numeric(t) and is_numeric(rt)):
                throw(f"Operación aritmética requiere numéricos: {t}, {rt}", ctx)
            t = FLOAT if FLOAT in (t, rt) else INT
        return t

    # additiveExpr: multiplicativeExpr (('+'|'-') multiplicativeExpr)*
    def visitAdditiveExpr(self, ctx: P.AdditiveExprContext):
        t = self.visit(ctx.multiplicativeExpr(0))
        for i in range(1, len(ctx.multiplicativeExpr())):
            rt = self.visit(ctx.multiplicativeExpr(i))
            if not (is_numeric(t) and is_numeric(rt)):
                throw(f"Operación aritmética requiere numéricos: {t}, {rt}", ctx)
            t = FLOAT if FLOAT in (t, rt) else INT
        return t

    # relationalExpr: additiveExpr (('<'|'<='|'>'|'>=') additiveExpr)*
    def visitRelationalExpr(self, ctx: P.RelationalExprContext):
        l = self.visit(ctx.additiveExpr(0))
        for i in range(1, len(ctx.additiveExpr())):
            r = self.visit(ctx.additiveExpr(i))
            if not are_compatible(l, r):
                throw(f"Comparación incompatible: {l} vs {r}", ctx)
        return BOOL

    # equalityExpr: relationalExpr (('=='|'!=') relationalExpr)*
    def visitEqualityExpr(self, ctx: P.EqualityExprContext):
        l = self.visit(ctx.relationalExpr(0))
        for i in range(1, len(ctx.relationalExpr())):
            r = self.visit(ctx.relationalExpr(i))
            if not are_compatible(l, r):
                throw(f"Igualdad incompatible: {l} vs {r}", ctx)
        return BOOL

    # logicalAndExpr: equalityExpr ('&&' equalityExpr)*
    def visitLogicalAndExpr(self, ctx: P.LogicalAndExprContext):
        l = self.visit(ctx.equalityExpr(0))
        if not is_boolean(l):
            throw(f"&& requiere booleanos: {l}, ...", ctx)
        for i in range(1, len(ctx.equalityExpr())):
            r = self.visit(ctx.equalityExpr(i))
            if not is_boolean(r):
                throw(f"&& requiere booleanos: ..., {r}", ctx)
        return BOOL

    # logicalOrExpr: logicalAndExpr ('||' logicalAndExpr)*
    def visitLogicalOrExpr(self, ctx: P.LogicalOrExprContext):
        l = self.visit(ctx.logicalAndExpr(0))
        if not is_boolean(l):
            throw(f"|| requiere booleanos: {l}, ...", ctx)
        for i in range(1, len(ctx.logicalAndExpr())):
            r = self.visit(ctx.logicalAndExpr(i))
            if not is_boolean(r):
                throw(f"|| requiere booleanos: ..., {r}", ctx)
        return BOOL

    # conditionalExpr: logicalOrExpr ('?' expression ':' expression)?
    def visitTernaryExpr(self, ctx: P.TernaryExprContext):
        # label aplicado en tu gramática
        cond_t = self.visit(ctx.logicalOrExpr())
        if not is_boolean(cond_t):
            throw(f"?: condición debe ser boolean", ctx)
        if ctx.expression():  # cuando existe el ternario
            _ = [self.visit(e) for e in ctx.expression()]
        return NULL

    # assignmentExpr: (labels) AssignExpr | PropertyAssignExpr | ExprNoAssign
    def visitAssignExpr(self, ctx: P.AssignExprContext):
        # lvalue es leftHandSide; pero en tu gramática tienes también 'assignment' como statement
        # Aquí solo devolvemos el tipo de la RHS (y que las validaciones se hagan en statement "assignment")
        return self.visit(ctx.assignmentExpr())

    def visitPropertyAssignExpr(self, ctx: P.PropertyAssignExprContext):
        # similar: forzamos visita de RHS para validar subexpresiones
        return self.visit(ctx.assignmentExpr())

    def visitExprNoAssign(self, ctx: P.ExprNoAssignContext):
        return self.visit(ctx.conditionalExpr())
