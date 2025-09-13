from __future__ import annotations
from typing import Optional, List, Tuple, Dict
from dataclasses import dataclass

from antlr4 import ParserRuleContext, Token
from parsing.antlr.CompiscriptVisitor import CompiscriptVisitor
from parsing.antlr.CompiscriptParser import CompiscriptParser

from .types import is_numeric, is_boolean, are_compatible, get_array_element_type, create_array_type
from .symbols import VariableSymbol, FunctionSymbol, ClassSymbol, ParamSymbol, Symbol
from .symbol_table import SymbolTable
from .diagnostics import Diagnostics

# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def where(ctx: ParserRuleContext) -> tuple[int, int]:
    t: Optional[Token] = getattr(ctx, "start", None)
    return ((t.line or 0), (t.column or 0)) if t else (0, 0)

TERMINATED = object()  # marca de corte para dead-code en bloques

# ---------------------------------------------------------------------
# Visitor semántico
# ---------------------------------------------------------------------

class CompiscriptSemanticVisitor(CompiscriptVisitor):
    """
    Visitor semántico para Compiscript.g4 con sistema de tipos simplificado usando strings.
    """

    def __init__(self):
        self.diag = Diagnostics()
        self.symtab = SymbolTable()
        self._in_loop = 0
        self._current_function: Optional[FunctionSymbol] = None
        self._current_class: Optional[ClassSymbol] = None
        self.classes: Dict[str, ClassSymbol] = {}  # nombre -> ClassSymbol

    # -------------------- utilidades --------------------

    def error(self, code: str, msg: str, ctx: ParserRuleContext, **extra):
        line, col = where(ctx)
        self.diag.add(phase="semantic", code=code, message=msg, line=line, col=col, **extra)

    def define_var(self, name: str, typ: str, ctx: ParserRuleContext, *, is_const: bool = False):
        try:
            v = VariableSymbol(name=name, type=typ)
            if hasattr(v, "is_const"):
                v.is_const = is_const
            self.symtab.current.define(v)
        except KeyError:
            self.error("E001", f"Redeclaración de '{name}'", ctx, name=name)

    def define_func(self, func: FunctionSymbol, ctx: ParserRuleContext):
        try:
            self.symtab.current.define(func)
        except KeyError:
            self.error("E001", f"Redeclaración de función '{func.name}'", ctx, name=func.name)

    def define_class(self, cls: ClassSymbol, ctx: ParserRuleContext):
        try:
            self.symtab.current.define(cls)
            self.classes[cls.name] = cls
        except KeyError:
            self.error("E001", f"Redeclaración de clase '{cls.name}'", ctx, name=cls.name)

    def resolve(self, name: str, ctx: ParserRuleContext) -> Optional[Symbol]:
        sym = self.symtab.current.resolve(name)
        if sym is None:
            self.error("E002", f"Símbolo no definido '{name}'", ctx, name=name)
        return sym

    # -------------------- programa & firmas --------------------

    def visitProgram(self, ctx: CompiscriptParser.ProgramContext):
        # Pase 1: recolecta firmas de funciones y clases (y miembros de clase)
        for st in ctx.statement() or []:
            if st.functionDeclaration():
                self._collect_function_signature(st.functionDeclaration())
            if st.classDeclaration():
                self._collect_class_signature(st.classDeclaration())
        # Pase 2: visita todo
        return self.visitChildren(ctx)

    def _collect_function_signature(self, ctx: CompiscriptParser.FunctionDeclarationContext):
        name = ctx.Identifier().getText()
        params: List[ParamSymbol] = []
        if ctx.parameters():
            for p in ctx.parameters().parameter():
                pname = p.Identifier().getText()
                ptype = self._read_type(p.type_()) if p.type_() else None
                params.append(ParamSymbol(name=pname, type=ptype or "integer"))
        ret = self._read_type(ctx.type_()) if ctx.type_() else "void"
        self.define_func(FunctionSymbol(name=name, type=ret, params=params), ctx)

    def _collect_class_signature(self, ctx: CompiscriptParser.ClassDeclarationContext):
        # classDeclaration: 'class' Identifier (':' Identifier)? '{' classMember* '}';
        name = ctx.Identifier(0).getText()
        parent_name = ctx.Identifier(1).getText() if ctx.Identifier(1) else None

        cls = self.classes.get(name)
        if not cls:
            cls = ClassSymbol(name=name, type=name)
            self.define_class(cls, ctx)

        # Herencia simple
        if parent_name:
            parent_sym = self.symtab.current.resolve(parent_name)
            if isinstance(parent_sym, ClassSymbol):
                setattr(cls, "parent", parent_sym)
            else:
                self.error("E002", f"Clase base '{parent_name}' no definida", ctx)

        # Recolectar miembros (campos y métodos)
        for m in ctx.classMember() or []:
            if m.functionDeclaration():
                f = m.functionDeclaration()
                fname = f.Identifier().getText()
                fparams: List[ParamSymbol] = []
                if f.parameters():
                    for p in f.parameters().parameter():
                        pname = p.Identifier().getText()
                        ptype = self._read_type(p.type_()) if p.type_() else None
                        fparams.append(ParamSymbol(name=pname, type=ptype or "integer"))
                fret = self._read_type(f.type_()) if f.type_() else "void"
                fsym = FunctionSymbol(name=fname, type=fret, params=fparams)
                cls.methods[fname] = fsym
            elif m.variableDeclaration():
                v = m.variableDeclaration()
                vname = v.Identifier().getText()
                vtype = self._read_type(v.typeAnnotation().type_()) if v.typeAnnotation() else None
                init_t = self.visit(v.initializer().expression()) if v.initializer() else None
                typ = vtype or (init_t if isinstance(init_t, str) else "integer")
                cls.fields[vname] = VariableSymbol(name=vname, type=typ)
            elif m.constantDeclaration():
                c = m.constantDeclaration()
                cname = c.Identifier().getText()
                ctype = self._read_type(c.typeAnnotation().type_()) if c.typeAnnotation() else None
                init_t = self.visit(c.expression())
                typ = ctype or (init_t if isinstance(init_t, str) else "integer")
                vs = VariableSymbol(name=cname, type=typ)
                if hasattr(vs, "is_const"):
                    vs.is_const = True
                cls.fields[cname] = vs

    # -------------------- declaraciones --------------------

    def visitVariableDeclaration(self, ctx: CompiscriptParser.VariableDeclarationContext):
        name = ctx.Identifier().getText()
        annotated = self._read_type(ctx.typeAnnotation().type_()) if ctx.typeAnnotation() else None
        init_t = self.visit(ctx.initializer().expression()) if ctx.initializer() else None

        if annotated is None and init_t is None:
            self.error("E104", f"No se puede inferir tipo de '{name}' sin inicializador", ctx)
            self.define_var(name, "integer", ctx)  # fallback para no cascada
            return None

        vtype = annotated or (init_t if isinstance(init_t, str) else "integer")
        self.define_var(name, vtype, ctx)
        if init_t is not None and annotated is not None and not are_compatible(annotated, init_t):
            self.error("E101", f"Asignación incompatible: {annotated} = {init_t}", ctx)
        return None

    def visitConstantDeclaration(self, ctx: CompiscriptParser.ConstantDeclarationContext):
        name = ctx.Identifier().getText()
        annotated = self._read_type(ctx.typeAnnotation().type_()) if ctx.typeAnnotation() else None
        init_t = self.visit(ctx.expression())
        vtype = annotated or (init_t if isinstance(init_t, str) else "integer")
        self.define_var(name, vtype, ctx, is_const=True)
        if annotated is not None and not are_compatible(annotated, init_t):
            self.error("E101", f"Asignación incompatible: const {annotated} = {init_t}", ctx)
        return None

    # -------------------- asignaciones --------------------

    def visitAssignment(self, ctx: CompiscriptParser.AssignmentContext):
        # 1) Identifier '=' expression ';'
        # 2) expression '.' Identifier '=' expression ';'
        exprs = ctx.expression()
        if not isinstance(exprs, list):
            exprs = [exprs] if exprs is not None else []

        if len(exprs) == 1:
            # var = expr
            name = ctx.Identifier().getText()
            sym = self.resolve(name, ctx)
            et = self.visit(exprs[0])
            if isinstance(sym, VariableSymbol) and getattr(sym, "is_const", False):
                self.error("E202", f"No se puede reasignar const '{name}'", ctx)
                return None
            if sym and et and isinstance(sym, Symbol) and not are_compatible(sym.type, et):
                self.error("E101", f"Asignación incompatible: {sym.type} = {et}", ctx)
            return None

        elif len(exprs) == 2:
            # obj.prop = valor
            obj_t = self.visit(exprs[0])
            prop_name = ctx.Identifier().getText()
            val_t = self.visit(exprs[1])
            if isinstance(obj_t, str) and obj_t.startswith("class:"):
                field_type = self._lookup_field_type(obj_t, prop_name)
                if field_type is None:
                    self.error("E301", f"Miembro '{prop_name}' no existe en {obj_t}", ctx)
                else:
                    if not are_compatible(field_type, val_t):
                        self.error("E101", f"Asignación incompatible a miembro '{prop_name}': {field_type} = {val_t}", ctx)
            else:
                self.error("E301", "Asignación de propiedad sobre tipo no-clase", ctx)
            return None

        self.error("E999", "Forma de asignación no reconocida", ctx)
        return None

    # -------------------- statements --------------------

    def visitBlock(self, ctx: CompiscriptParser.BlockContext):
        self.symtab.push("BLOCK")
        terminated = False
        for st in (ctx.statement() or []):
            if terminated:
                self.error("E500", "Código inalcanzable después de return/break/continue", st)
                continue
            res = st.accept(self)
            if res is TERMINATED:
                terminated = True
        self.symtab.pop()
        return None

    def visitIfStatement(self, ctx: CompiscriptParser.IfStatementContext):
        ct = self.visit(ctx.expression())
        if not is_boolean(ct):
            self.error("E101", f"La condición del if debe ser Bool, recibió {ct}", ctx)
        self.visit(ctx.block(0))
        if ctx.block(1):
            self.visit(ctx.block(1))
        return None

    def visitWhileStatement(self, ctx: CompiscriptParser.WhileStatementContext):
        ct = self.visit(ctx.expression())
        if not is_boolean(ct):
            self.error("E101", f"La condición del while debe ser Bool, recibió {ct}", ctx)
        self._in_loop += 1
        self.visit(ctx.block())
        self._in_loop -= 1
        return None

    def visitDoWhileStatement(self, ctx: CompiscriptParser.DoWhileStatementContext):
        self._in_loop += 1
        self.visit(ctx.block())
        self._in_loop -= 1
        ct = self.visit(ctx.expression())
        if not is_boolean(ct):
            self.error("E101", f"La condición del do-while debe ser Bool, recibió {ct}", ctx)
        return None

    def visitForStatement(self, ctx: CompiscriptParser.ForStatementContext):
        # init
        if ctx.variableDeclaration():
            self.visit(ctx.variableDeclaration())
        elif ctx.assignment():
            self.visit(ctx.assignment())
        # condición
        if ctx.expression(0):
            ct = self.visit(ctx.expression(0))
            if not is_boolean(ct):
                self.error("E101", f"La condición del for debe ser Bool, recibió {ct}", ctx)
        # increment
        if ctx.expression(1):
            _ = self.visit(ctx.expression(1))
        self._in_loop += 1
        self.visit(ctx.block())
        self._in_loop -= 1
        return None

    def visitForeachStatement(self, ctx: CompiscriptParser.ForeachStatementContext):
        iter_t = self.visit(ctx.expression())
        elem_t = get_array_element_type(iter_t)
        if elem_t is None:
            self.error("E301", f"foreach requiere Array, recibió {iter_t}", ctx)
            elem_t = "null"
        self.symtab.push("BLOCK")
        self.define_var(ctx.Identifier().getText(), elem_t, ctx)  # item : T
        self._in_loop += 1
        self.visit(ctx.block())
        self._in_loop -= 1
        self.symtab.pop()
        return None

    def visitBreakStatement(self, ctx: CompiscriptParser.BreakStatementContext):
        if self._in_loop <= 0:
            self.error("E201", "break fuera de un bucle", ctx)
        return TERMINATED

    def visitContinueStatement(self, ctx: CompiscriptParser.ContinueStatementContext):
        if self._in_loop <= 0:
            self.error("E201", "continue fuera de un bucle", ctx)
        return TERMINATED

    def visitReturnStatement(self, ctx: CompiscriptParser.ReturnStatementContext):
        if self._current_function is None:
            self.error("E103", "return fuera de una función", ctx)
            return TERMINATED
        expr = ctx.expression()
        rt = None if expr is None else self.visit(expr)
        expected = self._current_function.type
        if expected == "void" and rt is not None:
            self.error("E103", f"La función no retorna valor, pero se retornó {rt}", ctx)
        if expected != "void" and (rt is None or not are_compatible(expected, rt)):
            self.error("E103", f"Tipo de retorno esperado {expected}, recibido {rt}", ctx)
        return TERMINATED

    def visitSwitchStatement(self, ctx: CompiscriptParser.SwitchStatementContext):
        st = self.visit(ctx.expression())
        for c in ctx.switchCase() or []:
            ct = self.visit(c.expression())
            if st is not None and ct is not None and not are_compatible(st, ct):
                self.error("E302", f"Tipo de 'case' incompatible: {ct} con switch {st}", c)
            terminated = False
            for s in c.statement() or []:
                if terminated:
                    self.error("E500", "Código inalcanzable después de return/break/continue", s)
                    continue
                res = s.accept(self)
                if res is TERMINATED:
                    terminated = True
        if ctx.defaultCase():
            dc = ctx.defaultCase()
            terminated = False
            for s in dc.statement() or []:
                if terminated:
                    self.error("E500", "Código inalcanzable después de return/break/continue", s)
                    continue
                res = s.accept(self)
                if res is TERMINATED:
                    terminated = True
        return None

    # -------------------- funciones & clases --------------------

    def visitFunctionDeclaration(self, ctx: CompiscriptParser.FunctionDeclarationContext):
        name = ctx.Identifier().getText()
        sym = self.symtab.current.resolve(name)

        method_sym = None
        if self._current_class is not None:
            method_sym = self._lookup_method_symbol(self._current_class.type, name)


        if isinstance(sym, FunctionSymbol):
            prev_fn = self._current_function
            self._current_function = sym
            self.symtab.push("FUNCTION", name)
            for p in sym.params:
                try:
                    self.symtab.current.define(p)
                except KeyError:
                    self.error("E001", f"Parámetro duplicado '{p.name}'", ctx)
            self.visit(ctx.block())
            self.symtab.pop()
            self._current_function = prev_fn
            return None
        if isinstance(method_sym, FunctionSymbol):
            prev_fn = self._current_function
            self._current_function = method_sym
            self.symtab.push("FUNCTION", f"{self._current_class.name}.{name}")
            # define parámetros del método en el scope
            for p in method_sym.params:
                try:
                    self.symtab.current.define(p)
                except KeyError:
                    self.error("E001", f"Parámetro duplicado '{p.name}'", ctx)
            # cuerpo
            self.visit(ctx.block())
            self.symtab.pop()
            self._current_function = prev_fn
            return None

        
        self.visit(ctx.block())
        return None


    def visitClassDeclaration(self, ctx: CompiscriptParser.ClassDeclarationContext):
        name = ctx.Identifier(0).getText()
        cls = self.classes.get(name)
        prev_cls = self._current_class
        self._current_class = cls
        self.symtab.push("CLASS", name)
        self.visitChildren(ctx)
        self.symtab.pop()
        self._current_class = prev_cls
        return None

    # -------------------- expresiones / chaining --------------------

    def visitPrimaryExpr(self, ctx: CompiscriptParser.PrimaryExprContext):
        if ctx.literalExpr():
            return self.visit(ctx.literalExpr())
        if ctx.leftHandSide():
            return self.visit(ctx.leftHandSide())
        if ctx.expression():
            return self.visit(ctx.expression())
        return None

    def visitLeftHandSide(self, ctx):
        cur_type = self.visit(ctx.primaryAtom())
        cur_sym = None
        from parsing.antlr.CompiscriptParser import CompiscriptParser as P
        base = ctx.primaryAtom()
        if isinstance(base, P.IdentifierExprContext):
            name = base.Identifier().getText()
            cur_sym = self.symtab.current.resolve(name)

        for sop in ctx.suffixOp() or []:
            k = sop.start.text  # '(', '[', '.'
            if k == '(':
                cur_type, cur_sym = self._apply_call(ctx, sop, cur_type, cur_sym)
            elif k == '[':
                cur_type, cur_sym = self._apply_index(ctx, sop, cur_type)
            elif k == '.':
                cur_type, cur_sym = self._apply_member(ctx, sop, cur_type)
        return cur_type

    def _apply_call(self, parent_ctx, sop, cur_type, cur_sym=None):
        args = [self.visit(e) for e in (sop.arguments().expression() or [])] if sop.arguments() else []

        fsym = getattr(sop, "_method_symbol", None)
        if fsym is not None:
            if len(args) != len(fsym.params):
                self.error("E102", f"Argumentos incompatibles: esperaba {len(fsym.params)}, recibió {len(args)}", sop)
            else:
                for i, (at, p) in enumerate(zip(args, fsym.params)):
                    if at != p.type:
                        self.error("E102", f"Parametro {i+1}: esperaba {p.type}, recibió {at}", sop)
            return fsym.type, None

        # funciones globales
        if isinstance(cur_sym, FunctionSymbol):
            if len(args) != len(cur_sym.params):
                self.error("E102", f"Argumentos incompatibles: esperaba {len(cur_sym.params)}, recibió {len(args)}", sop)
            else:
                for i, (at, p) in enumerate(zip(args, cur_sym.params)):
                    if at != p.type:
                        self.error("E102", f"Parametro {i+1}: esperaba {p.type}, recibió {at}", sop)
            return cur_sym.type, None

        self.error("E301", "Llamada sobre un no-función", sop)
        return None, None


    def _apply_index(self, parent_ctx, sop: CompiscriptParser.IndexExprContext,
                     cur_type: Optional[str]) -> Tuple[Optional[str], Optional[Symbol]]:
        idxt = self.visit(sop.expression())
        if idxt != "integer":
            self.error("E401", "Índice de arreglo debe ser Int", sop)
        
        elem_t = get_array_element_type(cur_type)
        if elem_t is not None:
            return elem_t, None
        self.error("E301", "Indexación sobre un tipo no indexable", sop)
        return None, None

    def _apply_member(self, parent_ctx, sop: CompiscriptParser.PropertyAccessExprContext,
                      cur_type: Optional[str]) -> Tuple[Optional[str], Optional[Symbol]]:
        member = sop.Identifier().getText()
        if isinstance(cur_type, str) and cur_type.startswith("class:"):
            ft = self._lookup_field_type(cur_type, member)
            if ft is not None:
                return ft, None
            ms = self._lookup_method_symbol(cur_type, member)
            if ms is not None:
                setattr(sop, "_method_symbol", ms)
                return ms.type, ms
            self.error("E301", f"Miembro '{member}' no existe en {cur_type}", sop)
            return None, None
        self.error("E301", "Acceso a miembro sobre un tipo no-clase", sop)
        return None, None

    def visitIdentifierExpr(self, ctx: CompiscriptParser.IdentifierExprContext):
        name = ctx.Identifier().getText()
        sym = self.resolve(name, ctx)
        if isinstance(sym, FunctionSymbol):
            return sym.type
        return sym.type if isinstance(sym, Symbol) else None

    def visitThisExpr(self, ctx: CompiscriptParser.ThisExprContext):
        if self._current_class is not None:
            return f"class:{self._current_class.name}"
        self.error("E301", "Uso de 'this' fuera de clase", ctx)
        return None

    def visitNewExpr(self, ctx: CompiscriptParser.NewExprContext):
        cname = ctx.Identifier().getText()
        sym = self.resolve(cname, ctx)
        if isinstance(sym, ClassSymbol):
            return f"class:{sym.name}"
        return None

    # -------------------- literales / arrays --------------------

    def visitLiteralExpr(self, ctx: CompiscriptParser.LiteralExprContext):
        if ctx.Literal():
            text = (ctx.Literal().getSymbol().text or "")
            if text.startswith('"'):
                return "string"
            if '.' in text:     # si agregaste FloatLiteral, esto seguirá funcionando bien
                return "float"
            return "integer"
        if ctx.arrayLiteral():
            return self.visit(ctx.arrayLiteral())
        txt = ctx.getText()
        if txt == "null":
            return "null"
        if txt == "true" or txt == "false":
            return "boolean"
        return None

    def visitArrayLiteral(self, ctx: CompiscriptParser.ArrayLiteralContext):
        exprs = ctx.expression()
        elems = [self.visit(e) for e in (exprs or [])]
        if not elems:
            return create_array_type("null")
        first = elems[0]
        for e in elems[1:]:
            if not are_compatible(e, first):
                self.error("E101", "Array con tipos heterogéneos", ctx)
                return create_array_type(first)
        return create_array_type(first)

    # -------------------- helpers numéricos --------------------

    def _is_numeric(self, t: Optional[str]) -> bool:
        return t in ("integer", "float")

    def _num_result(self, a: Optional[str], b: Optional[str]) -> Optional[str]:
        # Int op Int -> Int; cualquier mezcla con Float -> Float; otros -> None
        if a == "integer" and b == "integer":
            return "integer"
        if a in ("integer", "float") and b in ("integer", "float"):
            return "float"
        return None

    # -------------------- unarios / binarios / lógicos / condicional --------------------

    def visitUnaryExpr(self, ctx: CompiscriptParser.UnaryExprContext):
        if ctx.getChildCount() == 2:
            op = ctx.getChild(0).getText()
            t = self.visit(ctx.unaryExpr())
            if op == '-':
                if not is_numeric(t):
                    self.error("E101", f"Negación requiere número, recibió {t}", ctx)
                    return "integer"
                return t
            if op == '!':
                if not is_boolean(t):
                    self.error("E101", f"NOT requiere Bool, recibió {t}", ctx)
                    return "boolean"
                return "boolean"
            return t
        return self.visit(ctx.primaryExpr())

    def visitAdditiveExpr(self, ctx: CompiscriptParser.AdditiveExprContext):
        if len(ctx.multiplicativeExpr()) == 1:
            return self.visit(ctx.multiplicativeExpr(0))
        t = self.visit(ctx.multiplicativeExpr(0))
        for i in range(1, len(ctx.multiplicativeExpr())):
            rt = self.visit(ctx.multiplicativeExpr(i))
            if is_numeric(t) and is_numeric(rt):
                # Int op Int -> Int; cualquier mezcla con Float -> Float
                if t == "integer" and rt == "integer":
                    t = "integer"
                else:
                    t = "float"
            elif t == "string" or rt == "string":
                t = "string"  # concatenación con +
            else:
                self.error("E101", f"Operación aditiva incompatible: {t} y {rt}", ctx)
        return t

    def visitMultiplicativeExpr(self, ctx: CompiscriptParser.MultiplicativeExprContext):
        if len(ctx.unaryExpr()) == 1:
            return self.visit(ctx.unaryExpr(0))
        t = self.visit(ctx.unaryExpr(0))
        for i in range(1, len(ctx.unaryExpr())):
            rt = self.visit(ctx.unaryExpr(i))
            if is_numeric(t) and is_numeric(rt):
                # Int op Int -> Int; cualquier mezcla con Float -> Float
                if t == "integer" and rt == "integer":
                    t = "integer"
                else:
                    t = "float"
            else:
                self.error("E101", f"Operación multiplicativa incompatible: {t} y {rt}", ctx)
        return t

    def visitEqualityExpr(self, ctx: CompiscriptParser.EqualityExprContext):
        n = len(ctx.relationalExpr())
        if n == 1:
            return self.visit(ctx.relationalExpr(0))
        lt = self.visit(ctx.relationalExpr(0))
        rt = self.visit(ctx.relationalExpr(1))
        if not are_compatible(lt, rt):
            self.error("E101", f"Comparación ==/!= entre tipos incompatibles: {lt} y {rt}", ctx)
        return "boolean"

    def visitRelationalExpr(self, ctx: CompiscriptParser.RelationalExprContext):
        n = len(ctx.additiveExpr())
        if n == 1:
            return self.visit(ctx.additiveExpr(0))
        lt = self.visit(ctx.additiveExpr(0))
        rt = self.visit(ctx.additiveExpr(1))
        if not (is_numeric(lt) and is_numeric(rt)):
            self.error("E101", f"Comparación relacional requiere números, recibió {lt} y {rt}", ctx)
        return "boolean"

    def visitLogicalAndExpr(self, ctx: CompiscriptParser.LogicalAndExprContext):
        n = len(ctx.equalityExpr())
        if n == 1:
            return self.visit(ctx.equalityExpr(0))
        for i in range(n):
            t = self.visit(ctx.equalityExpr(i))
            if not is_boolean(t):
                self.error("E101", f"AND requiere Bool, recibió {t}", ctx)
        return "boolean"

    def visitLogicalOrExpr(self, ctx: CompiscriptParser.LogicalOrExprContext):
        n = len(ctx.logicalAndExpr())
        if n == 1:
            return self.visit(ctx.logicalAndExpr(0))
        for i in range(n):
            t = self.visit(ctx.logicalAndExpr(i))
            if not is_boolean(t):
                self.error("E101", f"OR requiere Bool, recibido {t}", ctx)
        return "boolean"

    def visitTernaryExpr(self, ctx: CompiscriptParser.TernaryExprContext):
        if ctx.getChildCount() == 1:
            return self.visit(ctx.logicalOrExpr())
        ct = self.visit(ctx.logicalOrExpr())
        if not is_boolean(ct):
            self.error("E101", f"Condición del operador ternario debe ser Bool, recibió {ct}", ctx)
        tt = self.visit(ctx.expression(0))
        _ = self.visit(ctx.expression(1))
        return tt

    # -------------------- tipos --------------------

    def _read_type(self, tctx: Optional[CompiscriptParser.TypeContext]) -> Optional[str]:
        if tctx is None:
            return None
        base = self._read_base_type(tctx.baseType())
        txt = tctx.getText()
        brackets = txt.count("[]")
        typ: str = base or "null"
        for _ in range(brackets):
            typ = create_array_type(typ)
        return typ

    def _read_base_type(self, bctx: Optional[CompiscriptParser.BaseTypeContext]) -> Optional[str]:
        if bctx is None:
            return None
        txt = bctx.getText()
        if txt == "integer":
            return "integer"
        if txt == "float":
            return "float"
        if txt == "boolean":
            return "boolean"
        if txt == "string":
            return "string"
        if txt == "void":
            return "void"
        # Identificador de clase (nominal)
        sym = self.resolve(txt, bctx)
        if isinstance(sym, ClassSymbol):
            return f"class:{sym.name}"
        return f"class:{txt}"

    # -------------------- lookup de clases (fields/methods con herencia) --------------------

    def _lookup_class_symbol(self, ct: str) -> Optional[ClassSymbol]:
        if ct.startswith("class:"):
            class_name = ct[6:]  # quitar "class:" prefix
            return self.classes.get(class_name)
        return None

    def _lookup_field_type(self, ct: str, name: str) -> Optional[str]:
        cs = self._lookup_class_symbol(ct)
        cur = cs
        while cur is not None:
            if name in cur.fields:
                return cur.fields[name].type
            cur = getattr(cur, "parent", None)
        return None

    def _lookup_method_symbol(self, ct: str, name: str) -> Optional[FunctionSymbol]:
        cs = self._lookup_class_symbol(ct)
        cur = cs
        while cur is not None:
            if name in cur.methods:
                return cur.methods[name]
            cur = getattr(cur, "parent", None)
        return None


# ---------------------------------------------------------------------
# Facade
# ---------------------------------------------------------------------

def analyze(tree) -> dict:
    checker = CompiscriptSemanticVisitor()
    checker.visit(tree)
    return {"symbols": checker.symtab.dump(), "errors": checker.diag.to_list()}
