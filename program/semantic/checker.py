# semantic/checker.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List, Tuple, Dict, Any

from antlr4 import ParserRuleContext, Token
from parsing.antlr.CompiscriptVisitor import CompiscriptVisitor  # type: ignore
from parsing.antlr.CompiscriptParser import CompiscriptParser    # type: ignore

from .types import INT, BOOL, STR, NULL, VOID, FLOAT, ArrayType, ClassType, Type  # type: ignore
from .symbols import VariableSymbol, FunctionSymbol, ClassSymbol, ParamSymbol, Symbol  # type: ignore
from .symbol_table import SymbolTable  # type: ignore
from .diagnostics import Diagnostics  # type: ignore

# -----------------------------------------------------------------------------
# Utilidades
# -----------------------------------------------------------------------------

def _pos(ctx: ParserRuleContext) -> tuple[int, int]:
    t: Optional[Token] = getattr(ctx, "start", None)
    if not t:
        return (0, 0)
    # ANTLR puede entregar None en columnas/líneas si no hay token
    return (int(getattr(t, "line", 0) or 0), int(getattr(t, "column", 0) or 0))

# Marca para cortar ejecución dentro de bloques (dead code tras return/break/continue)
_CUT = object()


# -----------------------------------------------------------------------------
# Visitor semántico principal
# -----------------------------------------------------------------------------
class CSemantic(CompiscriptVisitor):
    """
    Reglas implementadas (resumen):
      • Encadenamiento call/index/prop
      • Clases/herencia: this/new, lookup en padre
      • Comparaciones y operadores: chequeo de tipos
      • foreach: exige Array<T>; item : T
      • Dead code en bloques tras return/break/continue
      • switch: casos compatibles con el tipo base
      • const: prohíbe reasignación
      • for: analiza init/cond/inc
      • Inferencia imposible en `let x;` sin init => error
    """

    def __init__(self) -> None:
        self.diag = Diagnostics()
        self.symtab = SymbolTable()
        self._loop_depth = 0
        self._fn: Optional[FunctionSymbol] = None
        self._cls: Optional[ClassSymbol] = None
        # índice nominal de clases declaradas para resoluciones posteriores
        self._class_index: Dict[str, ClassSymbol] = {}

    # --------------- helpers de reporte/definición/resolución ---------------
    def _error(self, code: str, msg: str, ctx: ParserRuleContext, **extra: Any) -> None:
        line, col = _pos(ctx)
        self.diag.add(phase="semantic", code=code, message=msg, line=line, col=col, **extra)

    def _def_var(self, name: str, typ: Type, ctx: ParserRuleContext, *, const: bool = False) -> None:
        try:
            v = VariableSymbol(name=name, type=typ)
            if hasattr(v, "is_const"):
                v.is_const = const
            self.symtab.current.define(v)
        except KeyError:
            self._error("E001", f"Redeclaración de variable '{name}'", ctx, name=name)

    def _def_fn(self, fn: FunctionSymbol, ctx: ParserRuleContext) -> None:
        try:
            self.symtab.current.define(fn)
        except KeyError:
            self._error("E001", f"Redeclaración de función '{fn.name}'", ctx, name=fn.name)

    def _def_class(self, cs: ClassSymbol, ctx: ParserRuleContext) -> None:
        try:
            self.symtab.current.define(cs)
            self._class_index[cs.name] = cs
        except KeyError:
            self._error("E001", f"Redeclaración de clase '{cs.name}'", ctx, name=cs.name)

    def _resolve(self, name: str, ctx: ParserRuleContext) -> Optional[Symbol]:
        sym = self.symtab.current.resolve(name)
        if sym is None:
            self._error("E002", f"Símbolo no definido: '{name}'", ctx, name=name)
        return sym

    # ----------------------- pase inicial (firmas) -----------------------
    def visitProgram(self, ctx: CompiscriptParser.ProgramContext):
        # Pase 1: recolectar firmas top-level (funciones, clases y miembros)
        for st in (ctx.statement() or []):
            if st.functionDeclaration():
                self._index_function(st.functionDeclaration())
            if st.classDeclaration():
                self._index_class(st.classDeclaration())
        # Pase 2: visitar cuerpo
        return self.visitChildren(ctx)

    def _index_function(self, ctx: CompiscriptParser.FunctionDeclarationContext) -> None:
        name = ctx.Identifier().getText()
        params: List[ParamSymbol] = []
        if ctx.parameters():
            for p in ctx.parameters().parameter():
                pname = p.Identifier().getText()
                ptype = self._read_type(p.type_()) if p.type_() else None
                params.append(ParamSymbol(name=pname, type=ptype or INT))
        ret = self._read_type(ctx.type_()) if ctx.type_() else VOID
        self._def_fn(FunctionSymbol(name=name, type=ret, params=params), ctx)

    def _index_class(self, ctx: CompiscriptParser.ClassDeclarationContext) -> None:
        name = ctx.Identifier(0).getText()
        parent_name = ctx.Identifier(1).getText() if ctx.Identifier(1) else None

        cs = self._class_index.get(name)
        if not cs:
            cs = ClassSymbol(name=name, type=ClassType(name, {}))
            self._def_class(cs, ctx)

        # herencia simple
        if parent_name:
            parent_sym = self.symtab.current.resolve(parent_name)
            if isinstance(parent_sym, ClassSymbol):
                setattr(cs, "parent", parent_sym)
            else:
                self._error("E002", f"Clase base no definida: '{parent_name}'", ctx)

        # miembros
        for m in (ctx.classMember() or []):
            if m.functionDeclaration():
                f = m.functionDeclaration()
                fname = f.Identifier().getText()
                params: List[ParamSymbol] = []
                if f.parameters():
                    for p in f.parameters().parameter():
                        pname = p.Identifier().getText()
                        ptype = self._read_type(p.type_()) if p.type_() else None
                        params.append(ParamSymbol(name=pname, type=ptype or INT))
                fret = self._read_type(f.type_()) if f.type_() else VOID
                cs.methods[fname] = FunctionSymbol(name=fname, type=fret, params=params)
            elif m.variableDeclaration():
                v = m.variableDeclaration()
                vname = v.Identifier().getText()
                vtype = self._read_type(v.typeAnnotation().type_()) if v.typeAnnotation() else None
                init_t = self.visit(v.initializer().expression()) if v.initializer() else None
                declared = vtype or (init_t if isinstance(init_t, Type) else INT)
                cs.fields[vname] = VariableSymbol(name=vname, type=declared)
            elif m.constantDeclaration():
                c = m.constantDeclaration()
                cname = c.Identifier().getText()
                ctype = self._read_type(c.typeAnnotation().type_()) if c.typeAnnotation() else None
                init_t = self.visit(c.expression())
                declared = ctype or (init_t if isinstance(init_t, Type) else INT)
                vs = VariableSymbol(name=cname, type=declared)
                if hasattr(vs, "is_const"):
                    vs.is_const = True
                cs.fields[cname] = vs

    # ------------------------------ declaraciones ------------------------------
    def visitVariableDeclaration(self, ctx: CompiscriptParser.VariableDeclarationContext):
        name = ctx.Identifier().getText()
        annotated = self._read_type(ctx.typeAnnotation().type_()) if ctx.typeAnnotation() else None
        init_t = self.visit(ctx.initializer().expression()) if ctx.initializer() else None

        if annotated is None and init_t is None:
            self._error("E104", f"No es posible inferir el tipo de '{name}' sin inicializador", ctx)
            self._def_var(name, INT, ctx)  # fallback para evitar cascada
            return None

        declared = annotated or (init_t if isinstance(init_t, Type) else INT)
        self._def_var(name, declared, ctx)
        if init_t is not None and annotated is not None and init_t != annotated:
            self._error("E101", f"Tipos incompatibles en asignación: {annotated} = {init_t}", ctx)
        return None

    def visitConstantDeclaration(self, ctx: CompiscriptParser.ConstantDeclarationContext):
        name = ctx.Identifier().getText()
        annotated = self._read_type(ctx.typeAnnotation().type_()) if ctx.typeAnnotation() else None
        init_t = self.visit(ctx.expression())
        declared = annotated or (init_t if isinstance(init_t, Type) else INT)
        self._def_var(name, declared, ctx, const=True)
        if annotated is not None and init_t != annotated:
            self._error("E101", f"Tipos incompatibles en const: {annotated} = {init_t}", ctx)
        return None

    # ------------------------------ asignaciones ------------------------------
    def visitAssignment(self, ctx: CompiscriptParser.AssignmentContext):
        exprs = ctx.expression()
        if not isinstance(exprs, list):
            exprs = [exprs] if exprs is not None else []

        if len(exprs) == 1:
            # x = expr
            name = ctx.Identifier().getText()
            sym = self._resolve(name, ctx)
            rhs_t = self.visit(exprs[0])
            if isinstance(sym, VariableSymbol) and getattr(sym, "is_const", False):
                self._error("E202", f"No se puede reasignar constante '{name}'", ctx)
                return None
            if sym and rhs_t and isinstance(sym, Symbol) and sym.type != rhs_t:
                self._error("E101", f"Asignación incompatible: {sym.type} = {rhs_t}", ctx)
            return None

        if len(exprs) == 2:
            # obj.prop = valor
            obj_t = self.visit(exprs[0])
            member = ctx.Identifier().getText()
            val_t = self.visit(exprs[1])
            if isinstance(obj_t, ClassType):
                field_t = self._field_type(obj_t, member)
                if field_t is None:
                    self._error("E301", f"Miembro '{member}' no existe en {obj_t}", ctx)
                elif field_t != val_t:
                    self._error("E101", f"Asignación incompatible a miembro '{member}': {field_t} = {val_t}", ctx)
            else:
                self._error("E301", "Acceso de propiedad sobre tipo no-clase", ctx)
            return None

        self._error("E999", "Forma de asignación no soportada", ctx)
        return None

    # ------------------------------ statements ------------------------------
    def visitBlock(self, ctx: CompiscriptParser.BlockContext):
        self.symtab.push("BLOCK")
        cut = False
        for st in (ctx.statement() or []):
            if cut:
                self._error("E500", "Código inalcanzable tras return/break/continue", st)
                continue
            res = st.accept(self)
            if res is _CUT:
                cut = True
        self.symtab.pop()
        return None

    def visitIfStatement(self, ctx: CompiscriptParser.IfStatementContext):
        cond_t = self.visit(ctx.expression())
        if cond_t != BOOL:
            self._error("E101", f"La condición del if debe ser boolean, recibió {cond_t}", ctx)
        self.visit(ctx.block(0))
        if ctx.block(1):
            self.visit(ctx.block(1))
        return None

    def visitWhileStatement(self, ctx: CompiscriptParser.WhileStatementContext):
        cond_t = self.visit(ctx.expression())
        if cond_t != BOOL:
            self._error("E101", f"La condición del while debe ser boolean, recibió {cond_t}", ctx)
        self._loop_depth += 1
        self.visit(ctx.block())
        self._loop_depth -= 1
        return None

    def visitDoWhileStatement(self, ctx: CompiscriptParser.DoWhileStatementContext):
        self._loop_depth += 1
        self.visit(ctx.block())
        self._loop_depth -= 1
        cond_t = self.visit(ctx.expression())
        if cond_t != BOOL:
            self._error("E101", f"La condición del do-while debe ser boolean, recibió {cond_t}", ctx)
        return None

    def visitForStatement(self, ctx: CompiscriptParser.ForStatementContext):
        if ctx.variableDeclaration():
            self.visit(ctx.variableDeclaration())
        elif ctx.assignment():
            self.visit(ctx.assignment())
        if ctx.expression(0):  # condición
            cond_t = self.visit(ctx.expression(0))
            if cond_t != BOOL:
                self._error("E101", f"La condición del for debe ser boolean, recibió {cond_t}", ctx)
        if ctx.expression(1):  # incremento
            _ = self.visit(ctx.expression(1))
        self._loop_depth += 1
        self.visit(ctx.block())
        self._loop_depth -= 1
        return None

    def visitForeachStatement(self, ctx: CompiscriptParser.ForeachStatementContext):
        it_t = self.visit(ctx.expression())
        if not isinstance(it_t, ArrayType):
            self._error("E301", f"foreach requiere un Array, recibió {it_t}", ctx)
            elem_t = NULL
        else:
            elem_t = it_t.elem
        self.symtab.push("BLOCK")
        self._def_var(ctx.Identifier().getText(), elem_t, ctx)  # item : T
        self._loop_depth += 1
        self.visit(ctx.block())
        self._loop_depth -= 1
        self.symtab.pop()
        return None

    def visitBreakStatement(self, ctx: CompiscriptParser.BreakStatementContext):
        if self._loop_depth <= 0:
            self._error("E201", "break fuera de un bucle", ctx)
        return _CUT

    def visitContinueStatement(self, ctx: CompiscriptParser.ContinueStatementContext):
        if self._loop_depth <= 0:
            self._error("E201", "continue fuera de un bucle", ctx)
        return _CUT

    def visitReturnStatement(self, ctx: CompiscriptParser.ReturnStatementContext):
        if self._fn is None:
            self._error("E103", "return fuera de una función", ctx)
            return _CUT
        expr = ctx.expression()
        rcv = None if expr is None else self.visit(expr)
        expected = self._fn.type
        if expected == VOID and rcv is not None:
            self._error("E103", f"La función no retorna valor, pero se retornó {rcv}", ctx)
        if expected != VOID and (rcv is None or rcv != expected):
            self._error("E103", f"Tipo de retorno esperado {expected}, recibido {rcv}", ctx)
        return _CUT

    def visitSwitchStatement(self, ctx: CompiscriptParser.SwitchStatementContext):
        base_t = self.visit(ctx.expression())
        for c in (ctx.switchCase() or []):
            ct = self.visit(c.expression())
            if base_t is not None and ct is not None and base_t != ct:
                self._error("E302", f"Tipo de case incompatible: {ct} vs switch {base_t}", c)
            cut = False
            for s in (c.statement() or []):
                if cut:
                    self._error("E500", "Código inalcanzable tras return/break/continue", s)
                    continue
                if s.accept(self) is _CUT:
                    cut = True
        if ctx.defaultCase():
            cut = False
            for s in ctx.defaultCase().statement() or []:
                if cut:
                    self._error("E500", "Código inalcanzable tras return/break/continue", s)
                    continue
                if s.accept(self) is _CUT:
                    cut = True
        return None

    # ------------------------------ funciones y clases ------------------------------
    def visitFunctionDeclaration(self, ctx: CompiscriptParser.FunctionDeclarationContext):
        name = ctx.Identifier().getText()
        top_sym = self.symtab.current.resolve(name)
        method_sym = None
        if self._cls is not None:
            method_sym = self._method_symbol(self._cls.type, name)

        target: Optional[FunctionSymbol] = None
        if isinstance(top_sym, FunctionSymbol):
            target = top_sym
        elif isinstance(method_sym, FunctionSymbol):
            target = method_sym

        if target is not None:
            prev = self._fn
            self._fn = target
            label = name if self._cls is None else f"{self._cls.name}.{name}"
            self.symtab.push("FUNCTION", label)
            # parámetros
            for p in target.params:
                try:
                    self.symtab.current.define(p)
                except KeyError:
                    self._error("E001", f"Parámetro duplicado '{p.name}'", ctx)
            # cuerpo
            self.visit(ctx.block())
            self.symtab.pop()
            self._fn = prev
            return None

        # Si no encontramos firma (p.ej., casos incompletos), igual visitar el bloque
        self.visit(ctx.block())
        return None

    def visitClassDeclaration(self, ctx: CompiscriptParser.ClassDeclarationContext):
        name = ctx.Identifier(0).getText()
        cs = self._class_index.get(name)
        prev = self._cls
        self._cls = cs
        self.symtab.push("CLASS", name)
        self.visitChildren(ctx)
        self.symtab.pop()
        self._cls = prev
        return None

    # ------------------------------ expresiones ------------------------------
    def visitPrimaryExpr(self, ctx: CompiscriptParser.PrimaryExprContext):
        if ctx.literalExpr():
            return self.visit(ctx.literalExpr())
        if ctx.leftHandSide():
            return self.visit(ctx.leftHandSide())
        if ctx.expression():
            return self.visit(ctx.expression())
        return None

    def visitLeftHandSide(self, ctx):
        cur_t = self.visit(ctx.primaryAtom())
        cur_sym = None
        P = CompiscriptParser
        base = ctx.primaryAtom()
        if isinstance(base, P.IdentifierExprContext):
            ident = base.Identifier().getText()
            cur_sym = self.symtab.current.resolve(ident)
        for sop in (ctx.suffixOp() or []):
            k = sop.start.text  # '(', '[', '.'
            if k == '(':
                cur_t, cur_sym = self._apply_call(sop, cur_t, cur_sym)
            elif k == '[':
                cur_t, cur_sym = self._apply_index(sop, cur_t)
            elif k == '.':
                cur_t, cur_sym = self._apply_member(sop, cur_t)
        return cur_t

    def _apply_call(self, sop, cur_t, cur_sym=None):
        args = [self.visit(e) for e in (sop.arguments().expression() or [])] if sop.arguments() else []

        fsym = getattr(sop, "_method_symbol", None)
        if fsym is not None:
            if len(args) != len(fsym.params):
                self._error("E102", f"Número de argumentos inválido: esperaba {len(fsym.params)}, recibió {len(args)}", sop)
            else:
                for i, (at, p) in enumerate(zip(args, fsym.params)):
                    if at != p.type:
                        self._error("E102", f"Arg {i+1}: esperaba {p.type}, recibió {at}", sop)
            return fsym.type, None

        if isinstance(cur_sym, FunctionSymbol):  # función global tomada como valor
            if len(args) != len(cur_sym.params):
                self._error("E102", f"Número de argumentos inválido: esperaba {len(cur_sym.params)}, recibió {len(args)}", sop)
            else:
                for i, (at, p) in enumerate(zip(args, cur_sym.params)):
                    if at != p.type:
                        self._error("E102", f"Arg {i+1}: esperaba {p.type}, recibió {at}", sop)
            return cur_sym.type, None

        self._error("E301", "Llamada sobre un no-función", sop)
        return None, None

    def _apply_index(self, sop: CompiscriptParser.IndexExprContext, cur_t: Optional[Type]) -> Tuple[Optional[Type], Optional[Symbol]]:
        idxt = self.visit(sop.expression())
        if idxt != INT:
            self._error("E401", "El índice de un arreglo debe ser Int", sop)
        if isinstance(cur_t, ArrayType):
            return cur_t.elem, None
        self._error("E301", "Indexación sobre un tipo no indexable", sop)
        return None, None

    def _apply_member(self, sop: CompiscriptParser.PropertyAccessExprContext, cur_t: Optional[Type]) -> Tuple[Optional[Type], Optional[Symbol]]:
        member = sop.Identifier().getText()
        if isinstance(cur_t, ClassType):
            ft = self._field_type(cur_t, member)
            if ft is not None:
                return ft, None
            ms = self._method_symbol(cur_t, member)
            if ms is not None:
                setattr(sop, "_method_symbol", ms)
                return ms.type, ms
            self._error("E301", f"Miembro inexistente '{member}' en {cur_t}", sop)
            return None, None
        self._error("E301", "Acceso a miembro sobre tipo no-clase", sop)
        return None, None

    def visitIdentifierExpr(self, ctx: CompiscriptParser.IdentifierExprContext):
        name = ctx.Identifier().getText()
        sym = self._resolve(name, ctx)
        if isinstance(sym, FunctionSymbol):
            return sym.type
        return sym.type if isinstance(sym, Symbol) else None

    def visitThisExpr(self, ctx: CompiscriptParser.ThisExprContext):
        if self._cls is not None:
            return self._cls.type
        self._error("E301", "Uso de 'this' fuera del contexto de clase", ctx)
        return None

    def visitNewExpr(self, ctx: CompiscriptParser.NewExprContext):
        cname = ctx.Identifier().getText()
        sym = self._resolve(cname, ctx)
        if isinstance(sym, ClassSymbol):
            return sym.type
        return None

    # ------------------------------ literales y arrays ------------------------------
    def visitLiteralExpr(self, ctx: CompiscriptParser.LiteralExprContext):
        if ctx.Literal():
            text = (ctx.Literal().getSymbol().text or "")
            if text.startswith('"'):
                return STR
            if '.' in text:
                return FLOAT
            return INT
        if ctx.arrayLiteral():
            return self.visit(ctx.arrayLiteral())
        txt = ctx.getText()
        if txt == "null":
            return NULL
        if txt in ("true", "false"):
            return BOOL
        return None

    def visitArrayLiteral(self, ctx: CompiscriptParser.ArrayLiteralContext):
        elems = [self.visit(e) for e in (ctx.expression() or [])]
        if not elems:
            return ArrayType(NULL)
        first = elems[0]
        for e in elems[1:]:
            if e != first:
                self._error("E101", "Array con elementos de tipos distintos", ctx)
                return ArrayType(first)
        return ArrayType(first)

    # ------------------------------ operadores ------------------------------
    def _is_num(self, t: Optional[Type]) -> bool:
        return t in (INT, FLOAT)

    def _num_out(self, a: Optional[Type], b: Optional[Type]) -> Optional[Type]:
        if a == INT and b == INT:
            return INT
        if a in (INT, FLOAT) and b in (INT, FLOAT):
            return FLOAT
        return None

    def visitUnaryExpr(self, ctx: CompiscriptParser.UnaryExprContext):
        if ctx.getChildCount() == 2:
            op = ctx.getChild(0).getText()
            t = self.visit(ctx.unaryExpr())
            if op == '-':
                if not self._is_num(t):
                    self._error("E101", f"Negación numérica requiere número, recibió {t}", ctx)
                    return INT
                return t
            if op == '!':
                if t != BOOL:
                    self._error("E101", f"NOT requiere boolean, recibió {t}", ctx)
                    return BOOL
                return BOOL
            return t
        return self.visit(ctx.primaryExpr())

    def visitAdditiveExpr(self, ctx: CompiscriptParser.AdditiveExprContext):
        if len(ctx.multiplicativeExpr()) == 1:
            return self.visit(ctx.multiplicativeExpr(0))
        t = self.visit(ctx.multiplicativeExpr(0))
        for i in range(1, len(ctx.multiplicativeExpr())):
            rt = self.visit(ctx.multiplicativeExpr(i))
            nr = self._num_out(t, rt)
            if nr is not None:
                t = nr
            elif t == STR or rt == STR:
                t = STR  # concatenación con +
            else:
                self._error("E101", f"Suma/resta incompatibles: {t} y {rt}", ctx)
        return t

    def visitMultiplicativeExpr(self, ctx: CompiscriptParser.MultiplicativeExprContext):
        if len(ctx.unaryExpr()) == 1:
            return self.visit(ctx.unaryExpr(0))
        t = self.visit(ctx.unaryExpr(0))
        for i in range(1, len(ctx.unaryExpr())):
            rt = self.visit(ctx.unaryExpr(i))
            nr = self._num_out(t, rt)
            if nr is not None:
                t = nr
            else:
                self._error("E101", f"Producto/división incompatibles: {t} y {rt}", ctx)
        return t

    def visitEqualityExpr(self, ctx: CompiscriptParser.EqualityExprContext):
        if len(ctx.relationalExpr()) == 1:
            return self.visit(ctx.relationalExpr(0))
        lt = self.visit(ctx.relationalExpr(0))
        rt = self.visit(ctx.relationalExpr(1))
        if self._num_out(lt, rt) is None and lt != rt:
            self._error("E101", f"Comparación ==/!= entre tipos incompatibles: {lt} y {rt}", ctx)
        return BOOL

    def visitRelationalExpr(self, ctx: CompiscriptParser.RelationalExprContext):
        if len(ctx.additiveExpr()) == 1:
            return self.visit(ctx.additiveExpr(0))
        lt = self.visit(ctx.additiveExpr(0))
        rt = self.visit(ctx.additiveExpr(1))
        if self._num_out(lt, rt) is None:
            self._error("E101", f"Comparación relacional requiere números: {lt} y {rt}", ctx)
        return BOOL

    def visitLogicalAndExpr(self, ctx: CompiscriptParser.LogicalAndExprContext):
        if len(ctx.equalityExpr()) == 1:
            return self.visit(ctx.equalityExpr(0))
        for i in range(len(ctx.equalityExpr())):
            t = self.visit(ctx.equalityExpr(i))
            if t != BOOL:
                self._error("E101", f"AND requiere boolean, recibió {t}", ctx)
        return BOOL

    def visitLogicalOrExpr(self, ctx: CompiscriptParser.LogicalOrExprContext):
        if len(ctx.logicalAndExpr()) == 1:
            return self.visit(ctx.logicalAndExpr(0))
        for i in range(len(ctx.logicalAndExpr())):
            t = self.visit(ctx.logicalAndExpr(i))
            if t != BOOL:
                self._error("E101", f"OR requiere boolean, recibió {t}", ctx)
        return BOOL

    def visitTernaryExpr(self, ctx: CompiscriptParser.TernaryExprContext):
        if ctx.getChildCount() == 1:
            return self.visit(ctx.logicalOrExpr())
        ct = self.visit(ctx.logicalOrExpr())
        if ct != BOOL:
            self._error("E101", f"Condición del operador ternario debe ser boolean, recibió {ct}", ctx)
        then_t = self.visit(ctx.expression(0))
        _ = self.visit(ctx.expression(1))
        return then_t

    # ------------------------------ tipos ------------------------------
    def _read_type(self, tctx: Optional[CompiscriptParser.TypeContext]) -> Optional[Type]:
        if tctx is None:
            return None
        base = self._read_base(tctx.baseType())
        brackets = tctx.getText().count("[]")
        typ: Type = base or NULL
        for _ in range(brackets):
            typ = ArrayType(typ)
        return typ

    def _read_base(self, bctx: Optional[CompiscriptParser.BaseTypeContext]) -> Optional[Type]:
        if bctx is None:
            return None
        txt = bctx.getText()
        if txt == "integer":
            return INT
        if txt == "float":
            return FLOAT
        if txt == "boolean":
            return BOOL
        if txt == "string":
            return STR
        if txt == "void":
            return VOID
        # Nombre de clase (nominal)
        sym = self._resolve(txt, bctx)
        if isinstance(sym, ClassSymbol):
            return sym.type
        return ClassType(txt, {})

    # ------------------------------ lookup con herencia ------------------------------
    def _class_of(self, ct: ClassType) -> Optional[ClassSymbol]:
        return self._class_index.get(ct.class_name)

    def _field_type(self, ct: ClassType, name: str) -> Optional[Type]:
        cur = self._class_of(ct)
        while cur is not None:
            if name in cur.fields:
                return cur.fields[name].type
            cur = getattr(cur, "parent", None)
        return None

    def _method_symbol(self, ct: ClassType, name: str) -> Optional[FunctionSymbol]:
        cur = self._class_of(ct)
        while cur is not None:
            if name in cur.methods:
                return cur.methods[name]
            cur = getattr(cur, "parent", None)
        return None


# -----------------------------------------------------------------------------
# API pública
# -----------------------------------------------------------------------------

def analyze(tree) -> dict:
    """Punto de entrada estable usado por la UI.
    Devuelve un diccionario con 'symbols' y 'errors'.
    """
    v = CSemantic()
    v.visit(tree)
    return {"symbols": v.symtab.dump(), "errors": v.diag.to_list()}