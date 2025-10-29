"""
Generador de código intermedio (cuádruplos) para Compiscript.
Visitor que recorre el AST y genera cuádruplos para cada construcción del lenguaje.
"""

from typing import Optional, List, Dict, Any
from antlr4 import ParserRuleContext

from parsing.antlr.CompiscriptVisitor import CompiscriptVisitor
from parsing.antlr.CompiscriptParser import CompiscriptParser

from .quadruple import Quadruple, QuadrupleList, QuadOp
from .temp_manager import TempManager, ScopedTempManager
from .label_manager import LabelManager, LoopLabelManager
from semantic.symbol_table import SymbolTable
from semantic.symbols import Symbol, VariableSymbol, FunctionSymbol, ClassSymbol


class CodeGeneratorVisitor(CompiscriptVisitor):
    """
    Visitor que genera código intermedio (cuádruplos) para Compiscript.
    Asume que el análisis semántico ya se ejecutó y la tabla de símbolos está disponible.
    """

    def __init__(self, symbol_table: SymbolTable):
        """
        Inicializa el generador de código.
        
        Args:
            symbol_table: Tabla de símbolos del análisis semántico
        """
        self.symtab = symbol_table
        self.quads = QuadrupleList()
        self.temp_manager = ScopedTempManager()
        self.label_manager = LabelManager()
        self.loop_manager = LoopLabelManager(self.label_manager)
        
        # Estado del generador
        self._current_function: Optional[FunctionSymbol] = None
        self._current_class: Optional[ClassSymbol] = None
        self._in_loop = 0

    def generate(self, tree) -> QuadrupleList:
        """
        Genera código intermedio para el árbol de sintaxis.
        
        Args:
            tree: Árbol de sintaxis (resultado del parser)
            
        Returns:
            Lista de cuádruplos generados
        """
        self.visit(tree)
        return self.quads

    # ==================== EXPRESIONES ====================

    def visitLiteralExpr(self, ctx: CompiscriptParser.LiteralExprContext) -> str:
        """
        Genera código para literales (números, strings, booleanos, null).
        Retorna el valor literal directamente (no genera cuádruplo).
        """
        if ctx.Literal():
            text = ctx.Literal().getText()
            return text
        
        if ctx.arrayLiteral():
            return self.visit(ctx.arrayLiteral())
        
        # true, false, null
        text = ctx.getText()
        if text == "true":
            return "1"  # Representamos true como 1
        if text == "false":
            return "0"  # Representamos false como 0
        if text == "null":
            return "null"
        
        return text

    def visitIdentifierExpr(self, ctx: CompiscriptParser.IdentifierExprContext) -> str:
        """
        Genera código para acceso a variables.
        Retorna el nombre de la variable (no genera cuádruplo).
        """
        name = ctx.Identifier().getText()
        return name

    def visitPrimaryExpr(self, ctx: CompiscriptParser.PrimaryExprContext) -> str:
        """
        Genera código para expresiones primarias.
        """
        if ctx.literalExpr():
            return self.visit(ctx.literalExpr())
        
        if ctx.leftHandSide():
            return self.visit(ctx.leftHandSide())
        
        # Expresión entre paréntesis
        if ctx.expression():
            return self.visit(ctx.expression())
        
        return None

    def visitUnaryExpr(self, ctx: CompiscriptParser.UnaryExprContext) -> str:
        """
        Genera código para expresiones unarias (-, !).
        """
        # Si no hay operador unario, delegar a primaryExpr
        if ctx.getChildCount() == 1:
            return self.visit(ctx.primaryExpr())
        
        # Operador unario
        op = ctx.getChild(0).getText()
        operand = self.visit(ctx.unaryExpr())
        
        # Generar temporal para el resultado
        result = self.temp_manager.new_temp()
        
        # Generar cuádruplo según el operador
        if op == '-':
            # Negación aritmética: result = -operand
            self.quads.emit(QuadOp.NEG, operand, None, result)
        elif op == '!':
            # Negación lógica: result = !operand
            self.quads.emit(QuadOp.NOT, operand, None, result)
        
        return result

    def visitMultiplicativeExpr(self, ctx: CompiscriptParser.MultiplicativeExprContext) -> str:
        """
        Genera código para expresiones multiplicativas (*, /, %).
        """
        # Si solo hay un término, delegar
        if len(ctx.unaryExpr()) == 1:
            return self.visit(ctx.unaryExpr(0))
        
        # Evaluar el primer operando
        result = self.visit(ctx.unaryExpr(0))
        
        # Procesar cada operación subsecuente
        for i in range(1, len(ctx.unaryExpr())):
            # Obtener el operador
            op_token = ctx.getChild(2 * i - 1)  # Los operadores están en posiciones impares
            op = op_token.getText()
            
            # Evaluar el operando derecho
            right = self.visit(ctx.unaryExpr(i))
            
            # Generar temporal para el resultado
            temp = self.temp_manager.new_temp()
            
            # Generar cuádruplo según el operador
            if op == '*':
                self.quads.emit(QuadOp.MUL, result, right, temp)
            elif op == '/':
                self.quads.emit(QuadOp.DIV, result, right, temp)
            elif op == '%':
                self.quads.emit(QuadOp.MOD, result, right, temp)
            
            result = temp
        
        return result

    def visitAdditiveExpr(self, ctx: CompiscriptParser.AdditiveExprContext) -> str:
        """
        Genera código para expresiones aditivas (+, -).
        """
        # Si solo hay un término, delegar
        if len(ctx.multiplicativeExpr()) == 1:
            return self.visit(ctx.multiplicativeExpr(0))
        
        # Evaluar el primer operando
        result = self.visit(ctx.multiplicativeExpr(0))
        
        # Procesar cada operación subsecuente
        for i in range(1, len(ctx.multiplicativeExpr())):
            # Obtener el operador
            op_token = ctx.getChild(2 * i - 1)
            op = op_token.getText()
            
            # Evaluar el operando derecho
            right = self.visit(ctx.multiplicativeExpr(i))
            
            # Generar temporal para el resultado
            temp = self.temp_manager.new_temp()
            
            # Generar cuádruplo según el operador
            if op == '+':
                self.quads.emit(QuadOp.ADD, result, right, temp)
            elif op == '-':
                self.quads.emit(QuadOp.SUB, result, right, temp)
            
            result = temp
        
        return result

    def visitRelationalExpr(self, ctx: CompiscriptParser.RelationalExprContext) -> str:
        """
        Genera código para expresiones relacionales (<, >, <=, >=).
        """
        # Si solo hay un término, delegar
        if len(ctx.additiveExpr()) == 1:
            return self.visit(ctx.additiveExpr(0))
        
        # Evaluar operandos
        left = self.visit(ctx.additiveExpr(0))
        right = self.visit(ctx.additiveExpr(1))
        
        # Obtener el operador
        op_token = ctx.getChild(1)
        op = op_token.getText()
        
        # Generar temporal para el resultado
        result = self.temp_manager.new_temp()
        
        # Generar cuádruplo según el operador
        if op == '<':
            self.quads.emit(QuadOp.LT, left, right, result)
        elif op == '>':
            self.quads.emit(QuadOp.GT, left, right, result)
        elif op == '<=':
            self.quads.emit(QuadOp.LE, left, right, result)
        elif op == '>=':
            self.quads.emit(QuadOp.GE, left, right, result)
        
        return result

    def visitEqualityExpr(self, ctx: CompiscriptParser.EqualityExprContext) -> str:
        """
        Genera código para expresiones de igualdad (==, !=).
        """
        # Si solo hay un término, delegar
        if len(ctx.relationalExpr()) == 1:
            return self.visit(ctx.relationalExpr(0))
        
        # Evaluar operandos
        left = self.visit(ctx.relationalExpr(0))
        right = self.visit(ctx.relationalExpr(1))
        
        # Obtener el operador
        op_token = ctx.getChild(1)
        op = op_token.getText()
        
        # Generar temporal para el resultado
        result = self.temp_manager.new_temp()
        
        # Generar cuádruplo según el operador
        if op == '==':
            self.quads.emit(QuadOp.EQ, left, right, result)
        elif op == '!=':
            self.quads.emit(QuadOp.NE, left, right, result)
        
        return result

    def visitLogicalAndExpr(self, ctx: CompiscriptParser.LogicalAndExprContext) -> str:
        """
        Genera código para expresiones lógicas AND (&&).
        Implementa evaluación en cortocircuito.
        """
        # Si solo hay un término, delegar
        if len(ctx.equalityExpr()) == 1:
            return self.visit(ctx.equalityExpr(0))
        
        # Evaluar el primer operando
        result = self.visit(ctx.equalityExpr(0))
        
        # Generar etiquetas para cortocircuito
        label_false = self.label_manager.new_label("AND_FALSE")
        label_end = self.label_manager.new_label("AND_END")
        
        # Si el primer operando es falso, saltar al final
        self.quads.emit(QuadOp.IF_FALSE, result, label_false, None)
        
        # Evaluar operandos subsecuentes
        for i in range(1, len(ctx.equalityExpr())):
            operand = self.visit(ctx.equalityExpr(i))
            
            # Si es falso, saltar al final
            self.quads.emit(QuadOp.IF_FALSE, operand, label_false, None)
            
            result = operand
        
        # Si llegamos aquí, todos fueron verdaderos
        temp = self.temp_manager.new_temp()
        self.quads.emit(QuadOp.ASSIGN, "1", None, temp)
        self.quads.emit(QuadOp.GOTO, label_end, None, None)
        
        # Etiqueta para resultado falso
        self.quads.emit(QuadOp.LABEL, label_false, None, None)
        self.quads.emit(QuadOp.ASSIGN, "0", None, temp)
        
        # Etiqueta de salida
        self.quads.emit(QuadOp.LABEL, label_end, None, None)
        
        return temp

    def visitLogicalOrExpr(self, ctx: CompiscriptParser.LogicalOrExprContext) -> str:
        """
        Genera código para expresiones lógicas OR (||).
        Implementa evaluación en cortocircuito.
        """
        # Si solo hay un término, delegar
        if len(ctx.logicalAndExpr()) == 1:
            return self.visit(ctx.logicalAndExpr(0))
        
        # Evaluar el primer operando
        result = self.visit(ctx.logicalAndExpr(0))
        
        # Generar etiquetas para cortocircuito
        label_true = self.label_manager.new_label("OR_TRUE")
        label_end = self.label_manager.new_label("OR_END")
        
        # Si el primer operando es verdadero, saltar al final
        self.quads.emit(QuadOp.IF_TRUE, result, label_true, None)
        
        # Evaluar operandos subsecuentes
        for i in range(1, len(ctx.logicalAndExpr())):
            operand = self.visit(ctx.logicalAndExpr(i))
            
            # Si es verdadero, saltar al final
            self.quads.emit(QuadOp.IF_TRUE, operand, label_true, None)
            
            result = operand
        
        # Si llegamos aquí, todos fueron falsos
        temp = self.temp_manager.new_temp()
        self.quads.emit(QuadOp.ASSIGN, "0", None, temp)
        self.quads.emit(QuadOp.GOTO, label_end, None, None)
        
        # Etiqueta para resultado verdadero
        self.quads.emit(QuadOp.LABEL, label_true, None, None)
        self.quads.emit(QuadOp.ASSIGN, "1", None, temp)
        
        # Etiqueta de salida
        self.quads.emit(QuadOp.LABEL, label_end, None, None)
        
        return temp

    def visitTernaryExpr(self, ctx: CompiscriptParser.TernaryExprContext) -> str:
        """
        Genera código para expresiones ternarias (cond ? true_expr : false_expr).
        """
        # Si no es ternario, delegar
        if ctx.getChildCount() == 1:
            return self.visit(ctx.logicalOrExpr())
        
        # Evaluar la condición
        condition = self.visit(ctx.logicalOrExpr())
        
        # Generar etiquetas
        label_false = self.label_manager.new_label("TERNARY_FALSE")
        label_end = self.label_manager.new_label("TERNARY_END")
        
        # Si la condición es falsa, saltar a la rama falsa
        self.quads.emit(QuadOp.IF_FALSE, condition, label_false, None)
        
        # Evaluar expresión verdadera
        true_val = self.visit(ctx.expression(0))
        result = self.temp_manager.new_temp()
        self.quads.emit(QuadOp.ASSIGN, true_val, None, result)
        self.quads.emit(QuadOp.GOTO, label_end, None, None)
        
        # Etiqueta para rama falsa
        self.quads.emit(QuadOp.LABEL, label_false, None, None)
        
        # Evaluar expresión falsa
        false_val = self.visit(ctx.expression(1))
        self.quads.emit(QuadOp.ASSIGN, false_val, None, result)
        
        # Etiqueta de salida
        self.quads.emit(QuadOp.LABEL, label_end, None, None)
        
        return result

    def visitAssignExpr(self, ctx: CompiscriptParser.AssignExprContext) -> str:
        """
        Genera código para asignaciones (var = expr).
        """
        # Obtener el lado izquierdo (puede ser un identificador simple o una expresión compleja)
        lhs_ctx = ctx.leftHandSide()
        
        # Por ahora, solo<bos> soportamos identificadores simples
        # TODO: Implementar acceso a propiedades y arrays en fase posterior
        if hasattr(lhs_ctx, 'Identifier') and lhs_ctx.Identifier():
            var_name = lhs_ctx.Identifier().getText()
        else:
            # Si no es un identificador simple, intentar obtenerlo del contexto
            var_name = lhs_ctx.getText()
        
        # Evaluar la expresión del lado derecho
        value = self.visit(ctx.assignmentExpr())
        
        # Generar cuádruplo de asignación
        self.quads.emit(QuadOp.ASSIGN, value, None, var_name)
        
        return var_name

    def visitLeftHandSide(self, ctx: CompiscriptParser.LeftHandSideContext) -> str:
        """
        Genera código para expresiones del lado izquierdo (llamadas, índices, propiedades).
        Soporta: llamadas a función, acceso a arrays y acceso a propiedades.
        Es tolerante a variantes de gramática (IndexExprContext sin .arguments()).
        """
        # 1) Base: identificador, this, new, literal entre paréntesis, etc.
        current_value = self.visit(ctx.primaryAtom())

        # 2) Sufijos encadenados: (), [], .campo
        for suffix_op in (ctx.suffixOp() or []):
            first_token = suffix_op.getChild(0).getText()

            if first_token == '(':
                # Llamada: f(args...) o valorRetornado(args...)
                current_value = self._generate_function_call(suffix_op, current_value)

            elif first_token == '[':
                # ------- Acceso a array: base[ index ] -------
                # La gramática puede exponer el índice de varias formas:
                #   a) suffix_op.expression()                         (IndexExprContext)
                #   b) suffix_op.indexExpr().expression()             (algunas variantes)
                #   c) suffix_op.arguments().expression()             (estilo "args")
                #   d) fallback: child 1 (entre '[' y ']')
                index_ctx = None

                # a) IndexExprContext típico
                if hasattr(suffix_op, "expression") and suffix_op.expression():
                    ex = suffix_op.expression()
                    index_ctx = ex[0] if isinstance(ex, list) else ex

                # b) Algunas gramáticas anidan indexExpr()
                elif hasattr(suffix_op, "indexExpr") and suffix_op.indexExpr():
                    ie = suffix_op.indexExpr()
                    if hasattr(ie, "expression") and ie.expression():
                        ex = ie.expression()
                        index_ctx = ex[0] if isinstance(ex, list) else ex

                # c) Variante "arguments()"
                elif hasattr(suffix_op, "arguments") and suffix_op.arguments() \
                    and hasattr(suffix_op.arguments(), "expression"):
                    ex = suffix_op.arguments().expression()
                    index_ctx = ex[0] if isinstance(ex, list) else ex

                # d) Fallback ultra defensivo
                if index_ctx is None:
                    index_ctx = suffix_op.getChild(1)

                index_val = self.visit(index_ctx)
                tmp = self.temp_manager.new_temp()
                self.quads.emit(QuadOp.ARRAY_LOAD, current_value, index_val, tmp)
                current_value = tmp

            elif first_token == '.':
                # ------- Acceso a propiedad: base.field -------
                # Puede venir como Identifier() o propertyName()
                if hasattr(suffix_op, "Identifier") and suffix_op.Identifier():
                    field_name = suffix_op.Identifier().getText()
                elif hasattr(suffix_op, "propertyName") and suffix_op.propertyName():
                    pn = suffix_op.propertyName()
                    field_name = pn.getText() if hasattr(pn, "getText") else str(pn)
                else:
                    # Fallback: token a la derecha del '.'
                    field_name = suffix_op.getChild(1).getText()

                tmp = self.temp_manager.new_temp()
                self.quads.emit(QuadOp.GET_FIELD, current_value, field_name, tmp)
                current_value = tmp

        return current_value


    def visitArrayLiteral(self, ctx: CompiscriptParser.ArrayLiteralContext) -> str:
        """
        Construye un arreglo a partir de [expr, expr, ...].
        Emite:
        ARRAY_NEW  n        -> arr_tmp
        ARRAY_STORE arr i v -> (por cada elemento)
        Retorna el temporal con el arreglo.
        """
        # 1) Intentamos obtener las expresiones con los nombres más comunes
        expr_nodes = []

        # a) ctx.expression()  (lo más habitual)
        if hasattr(ctx, "expression") and callable(getattr(ctx, "expression")):
            ex = ctx.expression()
            if isinstance(ex, list):
                expr_nodes = ex
            elif ex:
                expr_nodes = [ex]

        # b) ctx.arguments().expression()  (algunas gramáticas)
        if not expr_nodes and hasattr(ctx, "arguments") and callable(getattr(ctx, "arguments")):
            args = ctx.arguments()
            if args and hasattr(args, "expression") and callable(getattr(args, "expression")):
                ex = args.expression()
                if isinstance(ex, list):
                    expr_nodes = ex
                elif ex:
                    expr_nodes = [ex]

        # c) Fallback: recolectar hijos que parezcan expresiones
        if not expr_nodes and hasattr(ctx, "getChildCount"):
            try:
                for i in range(ctx.getChildCount()):
                    ch = ctx.getChild(i)
                    # Heurística: si el hijo tiene .accept y su nombre de clase contiene 'Expr'
                    if hasattr(ch, "accept"):
                        clsname = type(ch).__name__.lower()
                        if "expr" in clsname:
                            expr_nodes.append(ch)
            except Exception:
                pass

        # 2) Evaluar cada elemento
        values = [self.visit(n) for n in expr_nodes] if expr_nodes else []

        # 3) Crear y llenar el arreglo (aunque sea vacío)
        arr_tmp = self.temp_manager.new_temp()
        self.quads.emit(QuadOp.ARRAY_NEW, str(len(values)), None, arr_tmp)
        for i, val in enumerate(values):
            self.quads.emit(QuadOp.ARRAY_STORE, arr_tmp, i, val)

        return arr_tmp


    # ==================== STATEMENTS ====================

    def visitExpressionStatement(self, ctx: CompiscriptParser.ExpressionStatementContext):
        """
        Genera código para sentencias de expresión.
        """
        if ctx.expression():
            self.visit(ctx.expression())
        return None

    def visitVariableDeclaration(self, ctx: CompiscriptParser.VariableDeclarationContext):
        """
        Genera código para declaraciones de variables.
        TODO: Implementar completamente en fase posterior.
        """
        name = ctx.Identifier().getText()
        
        # Si hay inicializador, generar código para la asignación
        if ctx.initializer():
            value = self.visit(ctx.initializer().expression())
            self.quads.emit(QuadOp.ASSIGN, value, None, name)
        
        return None

    def visitIfStatement(self, ctx: CompiscriptParser.IfStatementContext):
        """
        Genera código para sentencias if/else.
        
        Estructura:
            if (condition) {
                // then_block
            } else {
                // else_block
            }
        
        Cuádruplos generados:
            evaluar condition -> temp
            IF_FALSE temp GOTO label_else
            código del then_block
            GOTO label_end
            LABEL label_else
            código del else_block (si existe)
            LABEL label_end
        """
        # Evaluar la condición
        condition = self.visit(ctx.expression())
        
        # Generar etiquetas
        label_else = self.label_manager.new_label("IF_ELSE")
        label_end = self.label_manager.new_label("IF_END")
        
        # Si la condición es falsa, saltar a else o al final
        has_else = len(ctx.block()) > 1
        jump_target = label_else if has_else else label_end
        self.quads.emit(QuadOp.IF_FALSE, condition, jump_target, None)
        
        # Generar código del bloque then
        self.visit(ctx.block(0))
        
        # Si hay else, saltar al final después del then
        if has_else:
            self.quads.emit(QuadOp.GOTO, label_end, None, None)
            
            # Etiqueta para el bloque else
            self.quads.emit(QuadOp.LABEL, label_else, None, None)
            
            # Generar código del bloque else
            self.visit(ctx.block(1))
        
        # Etiqueta de salida
        self.quads.emit(QuadOp.LABEL, label_end, None, None)
        
        return None

    def visitWhileStatement(self, ctx: CompiscriptParser.WhileStatementContext):
        """
        Genera código para sentencias while.
        
        Estructura:
            while (condition) {
                // body
            }
        
        Cuádruplos generados:
            LABEL label_start
            evaluar condition -> temp
            IF_FALSE temp GOTO label_end
            código del body
            GOTO label_start
            LABEL label_end
        """
        # Generar etiquetas
        label_start = self.label_manager.new_label("WHILE")
        label_end = self.label_manager.new_label("WHILE")
        
        # Registrar etiquetas para break/continue
        self._in_loop += 1
        # Push loop with start label as continue label for while loops
        self.loop_manager._loop_stack.append((label_start, label_end, label_start))
        
        # Etiqueta de inicio del loop
        self.quads.emit(QuadOp.LABEL, label_start, None, None)
        
        # Evaluar la condición
        condition = self.visit(ctx.expression())
        
        # Si la condición es falsa, salir del loop
        self.quads.emit(QuadOp.IF_FALSE, condition, label_end, None)
        
        # Generar código del cuerpo
        self.visit(ctx.block())
        
        # Saltar de vuelta al inicio
        self.quads.emit(QuadOp.GOTO, label_start, None, None)
        
        # Etiqueta de salida
        self.quads.emit(QuadOp.LABEL, label_end, None, None)
        
        # Desregistrar loop
        self.loop_manager.pop_loop()
        self._in_loop -= 1
        
        return None

    def visitDoWhileStatement(self, ctx: CompiscriptParser.DoWhileStatementContext):
        """
        Genera código para sentencias do-while.
        
        Estructura:
            do {
                // body
            } while (condition);
        
        Cuádruplos generados:
            LABEL label_start
            código del body
            evaluar condition -> temp
            IF_TRUE temp GOTO label_start
            LABEL label_end
        """
        # Generar etiquetas
        label_start = self.label_manager.new_label("DO_WHILE")
        label_end = self.label_manager.new_label("DO_WHILE")
        
        # Registrar etiquetas para break/continue
        self._in_loop += 1
        # Push loop with start label as continue label for do-while loops
        self.loop_manager._loop_stack.append((label_start, label_end, label_start))
        
        # Etiqueta de inicio del loop
        self.quads.emit(QuadOp.LABEL, label_start, None, None)
        
        # Generar código del cuerpo
        self.visit(ctx.block())
        
        # Evaluar la condición
        condition = self.visit(ctx.expression())
        
        # Si la condición es verdadera, volver al inicio
        self.quads.emit(QuadOp.IF_TRUE, condition, label_start, None)
        
        # Etiqueta de salida
        self.quads.emit(QuadOp.LABEL, label_end, None, None)
        
        # Desregistrar loop
        self.loop_manager.pop_loop()
        self._in_loop -= 1
        
        return None

    def visitForStatement(self, ctx: CompiscriptParser.ForStatementContext):
        """
        Genera código para sentencias for.
        
        Estructura:
            for (init; condition; increment) {
                // body
            }
        
        Cuádruplos generados:
            código de init
            LABEL label_start
            evaluar condition -> temp (si existe)
            IF_FALSE temp GOTO label_end (si existe condition)
            código del body
            LABEL label_continue
            código de increment (si existe)
            GOTO label_start
            LABEL label_end
        """
        # Generar código de inicialización
        if ctx.variableDeclaration():
            self.visit(ctx.variableDeclaration())
        elif ctx.assignment():
            self.visit(ctx.assignment())
        
        # Generar etiquetas
        label_start = self.label_manager.new_label("FOR_START")
        label_continue = self.label_manager.new_label("FOR_CONTINUE")
        label_end = self.label_manager.new_label("FOR_END")
        
        # Registrar etiquetas para break/continue
        self._in_loop += 1
        label_start, label_end, label_continue = self.loop_manager.push_loop("FOR")
        
        # Etiqueta de inicio del loop
        self.quads.emit(QuadOp.LABEL, label_start, None, None)
        
        # Evaluar la condición (si existe)
        if ctx.expression(0):
            condition = self.visit(ctx.expression(0))
            self.quads.emit(QuadOp.IF_FALSE, condition, label_end, None)
        
        # Generar código del cuerpo
        self.visit(ctx.block())
        
        # Etiqueta para continue
        self.quads.emit(QuadOp.LABEL, label_continue, None, None)
        
        # Generar código de incremento (si existe)
        if ctx.expression(1):
            self.visit(ctx.expression(1))
        
        # Saltar de vuelta al inicio
        self.quads.emit(QuadOp.GOTO, label_start, None, None)
        
        # Etiqueta de salida
        self.quads.emit(QuadOp.LABEL, label_end, None, None)
        
        # Desregistrar loop
        self.loop_manager.pop_loop()
        self._in_loop -= 1
        
        return None

    def visitBreakStatement(self, ctx):
        """
        Genera código para sentencias break.
        Salta a la etiqueta de salida del loop más cercano.
        """
        if self._in_loop == 0:
            # Error: break fuera de un loop (debería ser detectado en análisis semántico)
            return None
        
        # Obtener la etiqueta de salida del loop actual
        label_end = self.loop_manager.get_break_label()
        
        # Generar salto a la salida
        self.quads.emit(QuadOp.GOTO, label_end, None, None)
        
        return None

    def visitContinueStatement(self, ctx):
        """
        Genera código para sentencias continue.
        Salta a la etiqueta de continuación del loop más cercano.
        """
        if self._in_loop == 0:
            # Error: continue fuera de un loop (debería ser detectado en análisis semántico)
            return None
        
        # Obtener la etiqueta de continuación del loop actual
        label_continue = self.loop_manager.get_continue_label()
        
        # Generar salto a la continuación
        self.quads.emit(QuadOp.GOTO, label_continue, None, None)
        
        return None

    def visitBlock(self, ctx: CompiscriptParser.BlockContext):
        """
        Genera código para bloques de código.
        """
        if ctx.statement():
            for stmt in ctx.statement():
                self.visit(stmt)
        return None

    def visitProgram(self, ctx: CompiscriptParser.ProgramContext):
        """
        Genera código para el programa completo.
        """
        return self.visitChildren(ctx)

    def visitStatement(self, ctx: CompiscriptParser.StatementContext):
        """
        Genera código para sentencias.
        """
        if ctx.variableDeclaration():
            return self.visit(ctx.variableDeclaration())
        elif ctx.assignment():
            return self.visit(ctx.assignment())
        elif ctx.expressionStatement():
            return self.visit(ctx.expressionStatement())
        elif ctx.ifStatement():
            return self.visit(ctx.ifStatement())
        elif ctx.whileStatement():
            return self.visit(ctx.whileStatement())
        elif ctx.doWhileStatement():
            return self.visit(ctx.doWhileStatement())
        elif ctx.forStatement():
            return self.visit(ctx.forStatement())
        elif ctx.breakStatement():
            return self.visit(ctx.breakStatement())
        elif ctx.continueStatement():
            return self.visit(ctx.continueStatement())
        elif ctx.block():
            return self.visit(ctx.block())
        elif ctx.printStatement():
            return self.visit(ctx.printStatement())
        elif ctx.returnStatement():
            return self.visit(ctx.returnStatement())
        else:
            return self.visitChildren(ctx)

    def visitAssignment(self, ctx: CompiscriptParser.AssignmentContext):
        """
        Genera código para sentencias de asignación.
        
        Estructura:
            identifier = expression;
        o
            expression.identifier = expression;
        """
        if ctx.Identifier() and ctx.expression():
            expressions = ctx.expression()
            if len(expressions) == 1:
                # Simple assignment: identifier = expression;
                var_name = ctx.Identifier().getText()
                value = self.visit(expressions[0])
                self.quads.emit(QuadOp.ASSIGN, value, None, var_name)
            else:
                # Property assignment: expression.identifier = expression;
                # TODO: Implement in later phase
                pass
        
        return None

    def visitPrintStatement(self, ctx: CompiscriptParser.PrintStatementContext):
        """
        Genera código para sentencias de impresión.
        
        Estructura:
            print(expression);
        
        Cuádruplos generados:
            evaluar expression -> temp/var
            PRINT temp/var
        """
        if ctx.expression():
            # Evaluar la expresión a imprimir
            value = self.visit(ctx.expression())
            
            # Generar cuádruplo PRINT
            self.quads.emit(QuadOp.PRINT, value, None, None)
        
        return None

    def visitReturnStatement(self, ctx: CompiscriptParser.ReturnStatementContext):
        """
        Genera código para sentencias de retorno.
        
        Estructura:
            return expression;
        o
            return;
        
        Cuádruplos generados:
            evaluar expression -> temp (si existe)
            RETURN temp (o RETURN None si no hay expresión)
        """
        if ctx.expression():
            # Evaluar la expresión de retorno
            value = self.visit(ctx.expression())
            self.quads.emit(QuadOp.RETURN, value, None, None)
        else:
            # Return sin valor (void)
            self.quads.emit(QuadOp.RETURN, None, None, None)
        
        return None

    def visitTryCatchStatement(self, ctx: CompiscriptParser.TryCatchStatementContext):
        """
        Genera código para sentencias try-catch.
        
        Estructura:
            try {
                // try_block
            } catch (exception_var) {
                // catch_block
            }
        
        Cuádruplos generados:
            TRY label_catch
            código del try_block
            END_TRY
            GOTO label_end
            LABEL label_catch
            CATCH exception_var
            código del catch_block
            END_CATCH
            LABEL label_end
        """
        # Generar etiquetas
        label_catch = self.label_manager.new_label("CATCH")
        label_end = self.label_manager.new_label("TRY_END")
        
        # Emitir TRY con la etiqueta del manejador
        self.quads.emit(QuadOp.TRY, label_catch, None, None)
        
        # Generar código del bloque try
        self.visit(ctx.block(0))
        
        # Emitir END_TRY
        self.quads.emit(QuadOp.END_TRY, None, None, None)
        
        # Saltar al final si no hay excepción
        self.quads.emit(QuadOp.GOTO, label_end, None, None)
        
        # Etiqueta del manejador de excepciones
        self.quads.emit(QuadOp.LABEL, label_catch, None, None)
        
        # Obtener el nombre de la variable de excepción
        exception_var = ctx.Identifier().getText()
        
        # Emitir CATCH con la variable de excepción
        self.quads.emit(QuadOp.CATCH, exception_var, None, None)
        
        # Generar código del bloque catch
        self.visit(ctx.block(1))
        
        # Emitir END_CATCH
        self.quads.emit(QuadOp.END_CATCH, None, None, None)
        
        # Etiqueta de salida
        self.quads.emit(QuadOp.LABEL, label_end, None, None)
        
        return None

    def visitFunctionDeclaration(self, ctx: CompiscriptParser.FunctionDeclarationContext):
        """
        Genera código para declaraciones de funciones.
        
        Estructura:
            fun nombre(param1: tipo1, param2: tipo2): tipo_retorno {
                // body
            }
        
        Cuádruplos generados:
            BEGIN_FUNC nombre num_params
            código del body
            END_FUNC nombre
        """
        if self._current_class is not None:
            # This is a method, not a standalone function - skip for now
            # Methods will be generated when the class is instantiated
            return None
        
        # Obtener el nombre de la función
        func_name = ctx.Identifier().getText()
        
        num_params = 0
        if ctx.parameters():
            param_list = ctx.parameters().parameter()
            if param_list:
                num_params = len(param_list)
        
        # Try to get function symbol for additional info
        func_symbol = None
        if hasattr(self.symtab, 'resolve'):
            func_symbol = self.symtab.resolve(func_name)
        
        # Guardar el contexto de función actual
        prev_function = self._current_function
        if func_symbol and isinstance(func_symbol, FunctionSymbol):
            self._current_function = func_symbol
        
        # Generar etiqueta de inicio de función
        func_label = self.label_manager.new_label(f"FUNC_{func_name}")
        
        # Emitir BEGIN_FUNC con el nombre y número de parámetros
        self.quads.emit(QuadOp.LABEL, func_label, None, None)
        self.quads.emit(QuadOp.BEGIN_FUNC, func_name, num_params, None)
        
        # Crear nuevo scope de temporales para la función
        self.temp_manager.push_scope()
        
        # Generar código del cuerpo de la función
        self.visit(ctx.block())
        
        # Si la función es void y no tiene return explícito, agregar return implícito
        is_void = func_symbol and hasattr(func_symbol, 'type') and func_symbol.type == "void"
        if is_void or not func_symbol:
            # Verificar si el último cuádruplo es un RETURN
            if len(self.quads) == 0 or self.quads[-1].op != QuadOp.RETURN:
                self.quads.emit(QuadOp.RETURN, None, None, None)
        
        # Emitir END_FUNC
        self.quads.emit(QuadOp.END_FUNC, func_name, None, None)
        
        # Restaurar scope de temporales
        self.temp_manager.pop_scope()
        
        # Restaurar contexto de función
        self._current_function = prev_function
        
        return None

    def visitClassDeclaration(self, ctx: CompiscriptParser.ClassDeclarationContext):
        """
        Genera código para declaraciones de clases.
        
        Estructura:
            class NombreClase : ClaseBase {
                campo1: tipo1;
                campo2: tipo2;
                
                metodo1(params) { ... }
                metodo2(params) { ... }
            }
        
        Cuádruplos generados:
            BEGIN_CLASS nombre_clase parent_class
            // Información de campos (para layout de memoria)
            CLASS_FIELD nombre_campo tipo offset
            // Métodos
            BEGIN_METHOD clase.metodo num_params
            código del método
            END_METHOD clase.metodo
            END_CLASS nombre_clase
        """
        # Obtener el nombre de la clase
        class_name = ctx.Identifier(0).getText()
        
        # Obtener la clase padre si existe
        parent_name = None
        if ctx.Identifier(1):
            parent_name = ctx.Identifier(1).getText()
        
        # Buscar el símbolo de la clase en la tabla de símbolos
        class_symbol = None
        if hasattr(self.symtab, 'current') and hasattr(self.symtab.current, 'resolve'):
            class_symbol = self.symtab.current.resolve(class_name)
        
        parent_symbol = None
        if parent_name:
            # Try to resolve parent from current scope
            if hasattr(self.symtab, 'current') and hasattr(self.symtab.current, 'resolve'):
                parent_symbol = self.symtab.current.resolve(parent_name)
            # If not found, try global scope
            if not parent_symbol and hasattr(self.symtab, 'resolve'):
                parent_symbol = self.symtab.resolve(parent_name)
            # Verify it's actually a ClassSymbol
            if parent_symbol and not isinstance(parent_symbol, ClassSymbol):
                parent_symbol = None
        
        # Guardar el contexto de clase actual
        prev_class = self._current_class
        if class_symbol and isinstance(class_symbol, ClassSymbol):
            self._current_class = class_symbol
        
        # Emitir BEGIN_CLASS
        self.quads.emit(QuadOp.BEGIN_CLASS, class_name, parent_name, None)
        
        field_offset = 0
        all_fields = {}  # {field_name: offset}
        
        # First, collect all inherited fields from parent hierarchy
        if parent_symbol and isinstance(parent_symbol, ClassSymbol):
            # Build hierarchy from top to bottom
            class_hierarchy = []
            current_parent = parent_symbol
            while current_parent is not None:
                class_hierarchy.insert(0, current_parent)
                # Navigate to parent's parent
                if hasattr(current_parent, 'parent') and current_parent.parent:
                    # parent might be a string name, need to resolve it
                    if isinstance(current_parent.parent, str):
                        parent_name_str = current_parent.parent
                        next_parent = None
                        if hasattr(self.symtab, 'current') and hasattr(self.symtab.current, 'resolve'):
                            next_parent = self.symtab.current.resolve(parent_name_str)
                        if not next_parent and hasattr(self.symtab, 'resolve'):
                            next_parent = self.symtab.resolve(parent_name_str)
                        current_parent = next_parent if isinstance(next_parent, ClassSymbol) else None
                    else:
                        current_parent = current_parent.parent if isinstance(current_parent.parent, ClassSymbol) else None
                else:
                    current_parent = None
            
            # Emit inherited fields with correct offsets
            for ancestor_class in class_hierarchy:
                if hasattr(ancestor_class, 'fields') and ancestor_class.fields:
                    for field_name in ancestor_class.fields.keys():
                        if field_name not in all_fields:
                            # Emit CLASS_FIELD with current class name and correct offset
                            self.quads.emit(QuadOp.CLASS_FIELD, f"{class_name}.{field_name}", field_offset, None)
                            all_fields[field_name] = field_offset
                            field_offset += 1
        
        # Then, process own fields
        if ctx.classMember():
            for member in ctx.classMember():
                if member.variableDeclaration():
                    # Campo de instancia
                    var_ctx = member.variableDeclaration()
                    field_name = var_ctx.Identifier().getText()
                    
                    if field_name not in all_fields:
                        # Emitir información del campo con offset correcto
                        self.quads.emit(QuadOp.CLASS_FIELD, f"{class_name}.{field_name}", field_offset, None)
                        all_fields[field_name] = field_offset
                        field_offset += 1
                    
                elif member.constantDeclaration():
                    # Campo constante
                    const_ctx = member.constantDeclaration()
                    field_name = const_ctx.Identifier().getText()
                    
                    if field_name not in all_fields:
                        # Emitir información del campo con offset correcto
                        self.quads.emit(QuadOp.CLASS_FIELD, f"{class_name}.{field_name}", field_offset, None)
                        all_fields[field_name] = field_offset
                        field_offset += 1
                    
                elif member.functionDeclaration():
                    # Método de la clase - pass all_fields for constructor generation
                    self._generate_method(member.functionDeclaration(), class_name, all_fields)
        
        # Emitir END_CLASS
        self.quads.emit(QuadOp.END_CLASS, class_name, None, None)
        
        # Restaurar contexto de clase
        self._current_class = prev_class
        
        return None

    def _generate_method(self, func_ctx: CompiscriptParser.FunctionDeclarationContext, class_name: str, all_fields: dict = None):
        """
        Genera código para un método de clase.
        
        Args:
            func_ctx: Contexto del método (FunctionDeclaration)
            class_name: Nombre de la clase que contiene el método
            all_fields: Diccionario de todos los campos (heredados + propios) con sus offsets
        """
        # Obtener el nombre del método
        method_name = func_ctx.Identifier().getText()
        
        # Contar parámetros
        num_params = 0
        param_names = []
        if func_ctx.parameters():
            param_list = func_ctx.parameters().parameter()
            if param_list:
                num_params = len(param_list)
                for param in param_list:
                    param_names.append(param.Identifier().getText())
        
        # Generar etiqueta de inicio del método
        method_label = self.label_manager.new_label(f"METHOD_{class_name}_{method_name}")
        
        # Emitir BEGIN_METHOD con el nombre completo y número de parámetros
        self.quads.emit(QuadOp.LABEL, method_label, None, None)
        self.quads.emit(QuadOp.BEGIN_METHOD, f"{class_name}.{method_name}", num_params, None)
        
        # Crear nuevo scope de temporales para el método
        self.temp_manager.push_scope()
        
        if method_name.lower().startswith("init") and all_fields:
            # Generate SET_FIELD for each parameter that matches a field
            # Parameters are accessed as a0, a1, a2, etc.
            for i, param_name in enumerate(param_names):
                # Check if this parameter name matches any field
                if param_name in all_fields:
                    # Generate SET_FIELD: this.field = param
                    self.quads.emit(QuadOp.SET_FIELD, "this", param_name, f"a{i}")
        
        # Generar código del cuerpo del método
        self.visit(func_ctx.block())
        
        # Si el método no tiene return explícito, agregar return implícito
        if len(self.quads) == 0 or self.quads[-1].op != QuadOp.RETURN:
            self.quads.emit(QuadOp.RETURN, None, None, None)
        
        # Emitir END_METHOD
        self.quads.emit(QuadOp.END_METHOD, f"{class_name}.{method_name}", None, None)
        
        # Restaurar scope de temporales
        self.temp_manager.pop_scope()

    def visitNewExpr(self, ctx: CompiscriptParser.NewExprContext) -> str:
        """
        Genera código para instanciación de objetos.
        
        Estructura:
            new NombreClase(arg1, arg2, ...)
        
        Cuádruplos generados:
            evaluar arg1 -> temp1
            PARAM temp1
            evaluar arg2 -> temp2
            PARAM temp2
            NEW NombreClase num_args result_temp
        """
        class_name = ctx.Identifier().getText()
        
        # Obtener los argumentos del constructor
        args = []
        if ctx.arguments():
            arg_exprs = ctx.arguments().expression()
            if arg_exprs:
                for arg_expr in arg_exprs:
                    arg_value = self.visit(arg_expr)
                    args.append(arg_value)
        
        # Emitir cuádruplos PARAM para cada argumento
        for arg in args:
            self.quads.emit(QuadOp.PARAM, arg, None, None)
        
        # Generar temporal para el objeto creado
        result = self.temp_manager.new_temp()
        
        # Emitir cuádruplo NEW
        num_args = len(args)
        self.quads.emit(QuadOp.NEW, class_name, num_args, result)
        
        return result

    def visitThisExpr(self, ctx: CompiscriptParser.ThisExprContext) -> str:
        """
        Genera código para la palabra clave 'this'.
        
        'this' se refiere al objeto actual en el contexto de un método.
        Retorna el identificador especial 'this' que será resuelto en tiempo de ejecución.
        """
        # En el contexto de un método, 'this' es el primer parámetro implícito
        return "this"

    def _generate_function_call(self, suffix_ctx, func_name: str) -> str:
        """
        Genera código para una llamada a función o método.
        
        Estructura:
            func(arg1, arg2, arg3)
        o
            obj.metodo(arg1, arg2, arg3)
        
        Cuádruplos generados:
            evaluar arg1 -> temp1
            PARAM temp1
            evaluar arg2 -> temp2
            PARAM temp2
            evaluar arg3 -> temp3
            PARAM temp3
            CALL func num_args result_temp
        o
            CALL_METHOD obj metodo num_args result_temp
        """
        # Obtener los argumentos de la llamada
        args = []
        if suffix_ctx.arguments():
            arg_exprs = suffix_ctx.arguments().expression()
            if arg_exprs:
                for arg_expr in arg_exprs:
                    # Evaluar cada argumento
                    arg_value = self.visit(arg_expr)
                    args.append(arg_value)
        
        # Emitir cuádruplos PARAM para cada argumento
        for arg in args:
            self.quads.emit(QuadOp.PARAM, arg, None, None)
        
        # Generar temporal para el resultado
        result = self.temp_manager.new_temp()
        
        # If func_name is a temporary or 'this', it might be a method call
        # For now, we'll use CALL for regular functions
        # Method calls are handled in visitLeftHandSide when we see obj.method()
        
        # Emitir cuádruplo CALL
        num_args = len(args)
        self.quads.emit(QuadOp.CALL, func_name, num_args, result)
        
        return result

# ---- Helpers de direccionamiento relativo y utilidades de lectura/escritura ----
def _addr_of(self, name: str):
    resolver = getattr(self.symtab, "resolve", None)
    sym = resolver(name) if callable(resolver) else None
    if isinstance(sym, VariableSymbol) and hasattr(sym, "offset"):
        storage = getattr(sym, "storage", "local")
        if storage in ("local", "param"):
            return "FP", sym.offset
        elif storage == "global":
            return "GP", sym.offset
    return None, None

def _read_var(self, name: str) -> str:
    base, off = _addr_of(self, name)
    if base is not None:
        t = self.temp_manager.new_temp()
        self.quads.emit(QuadOp.LOAD, base, off, t)
        return t
    return name

def _write_var(self, name: str, value: str):
    base, off = _addr_of(self, name)
    if base is not None:
        self.quads.emit(QuadOp.STORE, value, base, off)
    else:
        self.quads.emit(QuadOp.ASSIGN, value, None, name)

# adjuntar helpers a la clase
CodeGeneratorVisitor._addr_of = _addr_of
CodeGeneratorVisitor._read_var = _read_var
CodeGeneratorVisitor._write_var = _write_var


# ---- Override no destructivo: IdentifierExpr usa LOAD si aplica ----
_original_visitIdentifierExpr = CodeGeneratorVisitor.visitIdentifierExpr
def _visitIdentifierExpr_REL(self, ctx: CompiscriptParser.IdentifierExprContext) -> str:
    name = _original_visitIdentifierExpr(self, ctx)  # devuelve el nombre
    # si el original devuelve None por alguna razón, regresa como estaba
    if not isinstance(name, str):
        return name
    return self._read_var(name)

CodeGeneratorVisitor.visitIdentifierExpr = _visitIdentifierExpr_REL


# ---- Arrays: literal [ ... ] -> ARRAY_NEW + ARRAY_STORE ----
_original_visitArrayLiteral = CodeGeneratorVisitor.visitArrayLiteral
def _visitArrayLiteral_IMPL(self, ctx: CompiscriptParser.ArrayLiteralContext) -> str:
    # si tu gramática no tiene argumentos, esto cae en el return None original
    try:
        values = []
        if ctx.arguments() and ctx.arguments().expression():
            for ex in ctx.arguments().expression():
                values.append(self.visit(ex))
        res = self.temp_manager.new_temp()
        self.quads.emit(QuadOp.ARRAY_NEW, len(values), None, res)
        for i, v in enumerate(values):
            self.quads.emit(QuadOp.ARRAY_STORE, res, i, v)
        return res
    except Exception:
        # fallback al placeholder original si algo no matchea
        return _original_visitArrayLiteral(self, ctx)

CodeGeneratorVisitor.visitArrayLiteral = _visitArrayLiteral_IMPL


# ---- LeftHandSide robusto: indexación y propiedades (ARRAY_LOAD / GET_FIELD) ----
def _visitLeftHandSide_EXT(self, ctx: CompiscriptParser.LeftHandSideContext) -> str:
    current_value = self.visit(ctx.primaryAtom())
    
    # Track if we're accessing a method (for proper CALL_METHOD generation)
    is_method_call = False
    method_object = None
    method_name = None

    for i, suffix_op in enumerate(ctx.suffixOp() or []):
        tok0 = suffix_op.getChild(0).getText()

        if tok0 == '(':
            if is_method_call and method_object is not None and method_name is not None:
                # This is a method call: obj.method(args)
                args = []
                if suffix_op.arguments():
                    arg_exprs = suffix_op.arguments().expression()
                    if arg_exprs:
                        for arg_expr in arg_exprs:
                            arg_value = self.visit(arg_expr)
                            args.append(arg_value)
                
                # Emitir PARAM para cada argumento
                for arg in args:
                    self.quads.emit(QuadOp.PARAM, arg, None, None)
                
                # Generar temporal para el resultado
                result = self.temp_manager.new_temp()
                
                # Emitir CALL_METHOD
                num_args = len(args)
                self.quads.emit(QuadOp.CALL_METHOD, method_object, method_name, result)
                # The number of arguments for CALL_METHOD needs to be passed explicitly
                # to the runtime, often as a separate parameter or encoded.
                # For simplicity here, let's assume it's handled by the runtime based on context
                # or potentially via a temporary parameter.
                # A common approach is to push the argument count before the call.
                # For now, let's use the 'PARAM' quad for argument count as a placeholder.
                # This might need adjustment based on the actual runtime implementation.
                self.quads.emit(QuadOp.PARAM, num_args, None, None)  
                
                current_value = result
                is_method_call = False
                method_object = None
                method_name = None
            else:
                # Regular function call
                current_value = self._generate_function_call(suffix_op, current_value)

        elif tok0 == '[':
            # Acceso a array: base[ index ]
            index_ctx = None

            # a) IndexExprContext: suffix_op.expression()
            if hasattr(suffix_op, "expression") and callable(getattr(suffix_op, "expression")):
                ex = suffix_op.expression()
                if ex:
                    index_ctx = ex[0] if isinstance(ex, list) else ex

            # b) Variante con indexExpr(): suffix_op.indexExpr().expression()
            if index_ctx is None and hasattr(suffix_op, "indexExpr") and callable(getattr(suffix_op, "indexExpr")):
                ie = suffix_op.indexExpr()
                if ie and hasattr(ie, "expression") and callable(getattr(ie, "expression")):
                    ex = ie.expression()
                    if ex:
                        index_ctx = ex[0] if isinstance(ex, list) else ex

            # c) Variante "arguments()": suffix_op.arguments().expression()
            if index_ctx is None and hasattr(suffix_op, "arguments") and callable(getattr(suffix_op, "arguments")):
                args = suffix_op.arguments()
                if args and hasattr(args, "expression") and callable(getattr(args, "expression")):
                    ex = args.expression()
                    if ex:
                        index_ctx = ex[0] if isinstance(ex, list) else ex

            # d) Fallback seguro
            if index_ctx is None:
                try:
                    index_ctx = suffix_op.getChild(1)
                except Exception:
                    index_ctx = None

            index_val = self.visit(index_ctx)
            tmp = self.temp_manager.new_temp()
            self.quads.emit(QuadOp.ARRAY_LOAD, current_value, index_val, tmp)
            current_value = tmp
            
            # Reset method call tracking
            is_method_call = False

        elif tok0 == '.':
            # Acceso a propiedad: base.field
            if hasattr(suffix_op, "Identifier") and callable(getattr(suffix_op, "Identifier")) and suffix_op.Identifier():
                field_name = suffix_op.Identifier().getText()
            elif hasattr(suffix_op, "propertyName") and callable(getattr(suffix_op, "propertyName")) and suffix_op.propertyName():
                pn = suffix_op.propertyName()
                field_name = pn.getText() if hasattr(pn, "getText") else str(pn)
            else:
                field_name = suffix_op.getChild(1).getText()

            next_is_call = False
            if i + 1 < len(ctx.suffixOp()):
                next_suffix = ctx.suffixOp()[i + 1]
                if next_suffix.getChild(0).getText() == '(':
                    next_is_call = True
            
            if next_is_call:
                # This is a method access, prepare for method call
                is_method_call = True
                method_object = current_value
                method_name = field_name
                # Don't generate GET_FIELD yet, wait for the call
                current_value = field_name  # Placeholder, will be replaced by the actual method call result
            else:
                # Regular field access
                tmp = self.temp_manager.new_temp()
                self.quads.emit(QuadOp.GET_FIELD, current_value, field_name, tmp)
                current_value = tmp
                is_method_call = False

    return current_value

# Enlazar el monkey-patch
CodeGeneratorVisitor.visitLeftHandSide = _visitLeftHandSide_EXT


# ---- Asignaciones: x=e | a[i]=e | obj.f=e (usa STORE/ARRAY_STORE/SET_FIELD) ----
_original_visitAssignExpr = CodeGeneratorVisitor.visitAssignExpr
def _visitAssignExpr_EXT(self, ctx: CompiscriptParser.AssignExprContext) -> str:
    lhs_ctx = ctx.leftHandSide()
    rhs = self.visit(ctx.assignmentExpr())

    # identificador simple
    if hasattr(lhs_ctx, 'Identifier') and lhs_ctx.Identifier() and lhs_ctx.getChildCount() == 1:
        name = lhs_ctx.Identifier().getText()
        self._write_var(name, rhs)
        return name

    # desenrollar base + sufijos
    # The base needs to be evaluated, but we don't generate LOADs until the end.
    # We need to track the chain of accesses.
    base = lhs_ctx.primaryAtom()
    suffixes = list(lhs_ctx.suffixOp() or [])

    # If there are no suffixes, it's a simple assignment already handled above.
    if not suffixes:
        return _original_visitAssignExpr(self, ctx)

    # Generate quads for the final assignment operation.
    if suffixes[-1].getChild(0).getText() == '[':
        # Array assignment: base[index] = rhs
        # Re-evaluate the context for the base of the array access
        array_ref = self.visit(base)
        
        # Resolve the index expression
        index_ctx = None
        last_suffix = suffixes[-1]
        # This needs to be more robust to match the logic in visitLeftHandSide
        if hasattr(last_suffix, "arguments") and callable(getattr(last_suffix, "arguments")):
            args = last_suffix.arguments()
            if args and hasattr(args, "expression") and callable(getattr(args, "expression")):
                ex = args.expression()
                if ex:
                    index_ctx = ex[0] if isinstance(ex, list) else ex
        elif hasattr(last_suffix, "expression") and callable(getattr(last_suffix, "expression")):
             ex = last_suffix.expression()
             if ex:
                 index_ctx = ex[0] if isinstance(ex, list) else ex

        if index_ctx:
            index_val = self.visit(index_ctx)
            self.quads.emit(QuadOp.ARRAY_STORE, array_ref, index_val, rhs)
        else:
            # Error handling for missing index
            pass

    elif suffixes[-1].getChild(0).getText() == '.':
        # Field assignment: base.field = rhs
        # Re-evaluate the context for the base of the field access
        object_ref = self.visit(base)
        
        # Resolve the field name
        field_name = None
        last_suffix = suffixes[-1]
        if hasattr(last_suffix, "Identifier") and callable(getattr(last_suffix, "Identifier")):
            field_name = last_suffix.Identifier().getText()
        elif hasattr(last_suffix, "propertyName") and callable(getattr(last_suffix, "propertyName")):
            pn = last_suffix.propertyName()
            field_name = pn.getText() if hasattr(pn, "getText") else str(pn)
        
        if field_name:
            self.quads.emit(QuadOp.SET_FIELD, object_ref, field_name, rhs)
        else:
            # Error handling for missing field name
            pass
    else:
        # Fallback for non-assignable LHS or unsupported structures
        return _original_visitAssignExpr(self, ctx)

    # Return the LHS value for chained assignments like a = b = c, though this might need refinement
    # For now, we focus on generating the assignment quads.
    return None # Or potentially the value that was assigned

CodeGeneratorVisitor.visitAssignExpr = _visitAssignExpr_EXT
