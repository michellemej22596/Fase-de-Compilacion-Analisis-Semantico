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
        # Obtener el nombre de la variable
        var_name = ctx.Identifier().getText()
        
        # Evaluar la expresión del lado derecho
        value = self.visit(ctx.expression())
        
        # Generar cuádruplo de asignación
        self.quads.emit(QuadOp.ASSIGN, value, None, var_name)
        
        return var_name

    # ==================== EXPRESIONES NO IMPLEMENTADAS AÚN ====================
    # Estas se implementarán en fases posteriores

    def visitLeftHandSide(self, ctx: CompiscriptParser.LeftHandSideContext) -> str:
        """
        Genera código para expresiones del lado izquierdo (llamadas, índices, propiedades).
        TODO: Implementar en fase posterior.
        """
        # Por ahora, solo soportamos identificadores simples
        if hasattr(ctx, 'primaryAtom'):
            return self.visit(ctx.primaryAtom())
        return None

    def visitArrayLiteral(self, ctx: CompiscriptParser.ArrayLiteralContext) -> str:
        """
        Genera código para literales de array.
        TODO: Implementar en fase posterior.
        """
        # Placeholder
        return None

    # ==================== STATEMENTS (PLACEHOLDER) ====================
    # Se implementarán en la siguiente fase

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

    def visitProgram(self, ctx: CompiscriptParser.ProgramContext):
        """
        Genera código para el programa completo.
        """
        return self.visitChildren(ctx)

    def visitStatement(self, ctx: CompiscriptParser.StatementContext):
        """
        Genera código para sentencias.
        """
        return self.visitChildren(ctx)


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
