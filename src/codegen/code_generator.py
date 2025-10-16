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
        
        # Por ahora, solo soportamos identificadores simples
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

    # ==================== EXPRESIONES NO IMPLEMENTADAS AÚN ====================
    # Estas se implementarán en fases posteriores

    def visitLeftHandSide(self, ctx: CompiscriptParser.LeftHandSideContext) -> str:
        """
        Genera código para expresiones del lado izquierdo (llamadas, índices, propiedades).
        Ahora incluye soporte para llamadas a funciones.
        """
        # Obtener el átomo primario (identificador, this, new, etc.)
        base_value = self.visit(ctx.primaryAtom())
        
        # Procesar cada operación de sufijo (llamadas, índices, propiedades)
        current_value = base_value
        
        for suffix_op in ctx.suffixOp() or []:
            # Determinar el tipo de operación de sufijo
            first_token = suffix_op.getChild(0).getText()
            
            if first_token == '(':
                # Llamada a función
                current_value = self._generate_function_call(suffix_op, current_value)
            elif first_token == '[':
                # Acceso a array (TODO: implementar en fase posterior)
                pass
            elif first_token == '.':
                # Acceso a propiedad (TODO: implementar en fase posterior)
                pass
        
        return current_value

    def visitArrayLiteral(self, ctx: CompiscriptParser.ArrayLiteralContext) -> str:
        """
        Genera código para literales de array.
        TODO: Implementar en fase posterior.
        """
        # Placeholder
        return None

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

    def _generate_function_call(self, suffix_ctx, func_name: str) -> str:
        """
        Genera código para una llamada a función.
        
        Estructura:
            func(arg1, arg2, arg3)
        
        Cuádruplos generados:
            evaluar arg1 -> temp1
            PARAM temp1
            evaluar arg2 -> temp2
            PARAM temp2
            evaluar arg3 -> temp3
            PARAM temp3
            CALL func num_args result_temp
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
        
        # Emitir cuádruplo CALL
        num_args = len(args)
        self.quads.emit(QuadOp.CALL, func_name, num_args, result)
        
        return result


def generate_code(tree, symbol_table: SymbolTable) -> QuadrupleList:
    """
    Función de fachada para generar código intermedio.
    
    Args:
        tree: Árbol de sintaxis (resultado del parser)
        symbol_table: Tabla de símbolos del análisis semántico
        
    Returns:
        Lista de cuádruplos generados
    """
    generator = CodeGeneratorVisitor(symbol_table)
    return generator.generate(tree)
