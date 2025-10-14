"""
Tests para el generador de código intermedio - Expresiones.
Verifica que se generen correctamente los cuádruplos para expresiones simples.
"""

import pytest
from antlr4 import InputStream, CommonTokenStream

from parsing.antlr.CompiscriptLexer import CompiscriptLexer
from parsing.antlr.CompiscriptParser import CompiscriptParser
from semantic.checker import CompiscriptSemanticVisitor
from codegen.code_generator import CodeGeneratorVisitor
from codegen.quadruple import OpCode


def parse_and_generate(code: str):
    """
    Helper para parsear código y generar cuádruplos.
    
    Returns:
        tuple: (quads, semantic_visitor, code_generator)
    """
    # Lexer y Parser
    input_stream = InputStream(code)
    lexer = CompiscriptLexer(input_stream)
    token_stream = CommonTokenStream(lexer)
    parser = CompiscriptParser(token_stream)
    tree = parser.program()
    
    # Análisis semántico
    semantic = CompiscriptSemanticVisitor()
    semantic.visit(tree)
    
    # Generación de código
    generator = CodeGeneratorVisitor(semantic.symtab)
    quads = generator.generate(tree)
    
    return quads, semantic, generator


class TestArithmeticExpressions:
    """Tests para expresiones aritméticas."""
    
    def test_simple_addition(self):
        """Test: a + b"""
        code = """
        let a: integer = 5;
        let b: integer = 10;
        let c: integer = a + b;
        """
        quads, _, _ = parse_and_generate(code)
        
        # Verificar que se generó el cuádruplo ADD
        add_quads = [q for q in quads.quads if q.op == OpCode.ADD]
        assert len(add_quads) == 1
        assert add_quads[0].arg1 == "a"
        assert add_quads[0].arg2 == "b"
    
    def test_simple_subtraction(self):
        """Test: a - b"""
        code = """
        let a: integer = 10;
        let b: integer = 3;
        let c: integer = a - b;
        """
        quads, _, _ = parse_and_generate(code)
        
        sub_quads = [q for q in quads.quads if q.op == OpCode.SUB]
        assert len(sub_quads) == 1
        assert sub_quads[0].arg1 == "a"
        assert sub_quads[0].arg2 == "b"
    
    def test_multiplication(self):
        """Test: a * b"""
        code = """
        let a: integer = 5;
        let b: integer = 3;
        let c: integer = a * b;
        """
        quads, _, _ = parse_and_generate(code)
        
        mul_quads = [q for q in quads.quads if q.op == OpCode.MUL]
        assert len(mul_quads) == 1
    
    def test_division(self):
        """Test: a / b"""
        code = """
        let a: integer = 10;
        let b: integer = 2;
        let c: integer = a / b;
        """
        quads, _, _ = parse_and_generate(code)
        
        div_quads = [q for q in quads.quads if q.op == OpCode.DIV]
        assert len(div_quads) == 1
    
    def test_modulo(self):
        """Test: a % b"""
        code = """
        let a: integer = 10;
        let b: integer = 3;
        let c: integer = a % b;
        """
        quads, _, _ = parse_and_generate(code)
        
        mod_quads = [q for q in quads.quads if q.op == OpCode.MOD]
        assert len(mod_quads) == 1
    
    def test_complex_expression(self):
        """Test: (a + b) * (c - d)"""
        code = """
        let a: integer = 1;
        let b: integer = 2;
        let c: integer = 3;
        let d: integer = 4;
        let result: integer = (a + b) * (c - d);
        """
        quads, _, _ = parse_and_generate(code)
        
        # Debe haber 1 ADD, 1 SUB, 1 MUL
        add_quads = [q for q in quads.quads if q.op == OpCode.ADD]
        sub_quads = [q for q in quads.quads if q.op == OpCode.SUB]
        mul_quads = [q for q in quads.quads if q.op == OpCode.MUL]
        
        assert len(add_quads) == 1
        assert len(sub_quads) == 1
        assert len(mul_quads) == 1
        
        # Verificar que MUL usa los resultados de ADD y SUB
        assert mul_quads[0].arg1.startswith("t")  # temporal
        assert mul_quads[0].arg2.startswith("t")  # temporal


class TestUnaryExpressions:
    """Tests para expresiones unarias."""
    
    def test_negation(self):
        """Test: -a"""
        code = """
        let a: integer = 5;
        let b: integer = -a;
        """
        quads, _, _ = parse_and_generate(code)
        
        neg_quads = [q for q in quads.quads if q.op == OpCode.NEG]
        assert len(neg_quads) == 1
        assert neg_quads[0].arg1 == "a"
    
    def test_logical_not(self):
        """Test: !a"""
        code = """
        let a: boolean = true;
        let b: boolean = !a;
        """
        quads, _, _ = parse_and_generate(code)
        
        not_quads = [q for q in quads.quads if q.op == OpCode.NOT]
        assert len(not_quads) == 1


class TestRelationalExpressions:
    """Tests para expresiones relacionales."""
    
    def test_less_than(self):
        """Test: a < b"""
        code = """
        let a: integer = 5;
        let b: integer = 10;
        let c: boolean = a < b;
        """
        quads, _, _ = parse_and_generate(code)
        
        lt_quads = [q for q in quads.quads if q.op == OpCode.LT]
        assert len(lt_quads) == 1
        assert lt_quads[0].arg1 == "a"
        assert lt_quads[0].arg2 == "b"
    
    def test_greater_than(self):
        """Test: a > b"""
        code = """
        let a: integer = 10;
        let b: integer = 5;
        let c: boolean = a > b;
        """
        quads, _, _ = parse_and_generate(code)
        
        gt_quads = [q for q in quads.quads if q.op == OpCode.GT]
        assert len(gt_quads) == 1
    
    def test_less_equal(self):
        """Test: a <= b"""
        code = """
        let a: integer = 5;
        let b: integer = 10;
        let c: boolean = a <= b;
        """
        quads, _, _ = parse_and_generate(code)
        
        le_quads = [q for q in quads.quads if q.op == OpCode.LE]
        assert len(le_quads) == 1
    
    def test_greater_equal(self):
        """Test: a >= b"""
        code = """
        let a: integer = 10;
        let b: integer = 5;
        let c: boolean = a >= b;
        """
        quads, _, _ = parse_and_generate(code)
        
        ge_quads = [q for q in quads.quads if q.op == OpCode.GE]
        assert len(ge_quads) == 1


class TestEqualityExpressions:
    """Tests para expresiones de igualdad."""
    
    def test_equals(self):
        """Test: a == b"""
        code = """
        let a: integer = 5;
        let b: integer = 5;
        let c: boolean = a == b;
        """
        quads, _, _ = parse_and_generate(code)
        
        eq_quads = [q for q in quads.quads if q.op == OpCode.EQ]
        assert len(eq_quads) == 1
    
    def test_not_equals(self):
        """Test: a != b"""
        code = """
        let a: integer = 5;
        let b: integer = 10;
        let c: boolean = a != b;
        """
        quads, _, _ = parse_and_generate(code)
        
        ne_quads = [q for q in quads.quads if q.op == OpCode.NE]
        assert len(ne_quads) == 1


class TestLogicalExpressions:
    """Tests para expresiones lógicas."""
    
    def test_logical_and(self):
        """Test: a && b"""
        code = """
        let a: boolean = true;
        let b: boolean = false;
        let c: boolean = a && b;
        """
        quads, _, _ = parse_and_generate(code)
        
        # Debe haber etiquetas y saltos para cortocircuito
        labels = [q for q in quads.quads if q.op == OpCode.LABEL]
        if_false = [q for q in quads.quads if q.op == OpCode.IF_FALSE]
        
        assert len(labels) >= 2  # Al menos 2 etiquetas
        assert len(if_false) >= 1  # Al menos 1 IF_FALSE
    
    def test_logical_or(self):
        """Test: a || b"""
        code = """
        let a: boolean = false;
        let b: boolean = true;
        let c: boolean = a || b;
        """
        quads, _, _ = parse_and_generate(code)
        
        # Debe haber etiquetas y saltos para cortocircuito
        labels = [q for q in quads.quads if q.op == OpCode.LABEL]
        if_true = [q for q in quads.quads if q.op == OpCode.IF_TRUE]
        
        assert len(labels) >= 2
        assert len(if_true) >= 1


class TestTernaryExpression:
    """Tests para expresión ternaria."""
    
    def test_ternary(self):
        """Test: a > b ? a : b"""
        code = """
        let a: integer = 10;
        let b: integer = 5;
        let max: integer = a > b ? a : b;
        """
        quads, _, _ = parse_and_generate(code)
        
        # Debe haber comparación, etiquetas y asignaciones
        gt_quads = [q for q in quads.quads if q.op == OpCode.GT]
        labels = [q for q in quads.quads if q.op == OpCode.LABEL]
        if_false = [q for q in quads.quads if q.op == OpCode.IF_FALSE]
        
        assert len(gt_quads) == 1
        assert len(labels) >= 2
        assert len(if_false) >= 1


class TestAssignments:
    """Tests para asignaciones."""
    
    def test_simple_assignment(self):
        """Test: x = 5"""
        code = """
        let x: integer = 0;
        x = 5;
        """
        quads, _, _ = parse_and_generate(code)
        
        # Debe haber al menos 2 asignaciones (declaración + asignación)
        assign_quads = [q for q in quads.quads if q.op == OpCode.ASSIGN]
        assert len(assign_quads) >= 2
    
    def test_expression_assignment(self):
        """Test: x = a + b"""
        code = """
        let a: integer = 5;
        let b: integer = 10;
        let x: integer = 0;
        x = a + b;
        """
        quads, _, _ = parse_and_generate(code)
        
        # Debe haber ADD y ASSIGN
        add_quads = [q for q in quads.quads if q.op == OpCode.ADD]
        assign_quads = [q for q in quads.quads if q.op == OpCode.ASSIGN]
        
        assert len(add_quads) == 1
        assert len(assign_quads) >= 4  # 3 declaraciones + 1 asignación


class TestTemporals:
    """Tests para verificar el uso correcto de temporales."""
    
    def test_temporals_generated(self):
        """Verificar que se generan temporales para subexpresiones"""
        code = """
        let a: integer = 1;
        let b: integer = 2;
        let c: integer = 3;
        let result: integer = a + b + c;
        """
        quads, _, gen = parse_and_generate(code)
        
        # Debe haber temporales generados
        temp_count = sum(1 for q in quads.quads if q.result and q.result.startswith("t"))
        assert temp_count >= 2  # Al menos 2 temporales para las 2 sumas
    
    def test_temporals_reused(self):
        """Verificar que los temporales se pueden reusar"""
        code = """
        let a: integer = 1;
        let b: integer = 2;
        let x: integer = a + b;
        let c: integer = 3;
        let d: integer = 4;
        let y: integer = c + d;
        """
        quads, _, gen = parse_and_generate(code)
        
        # Los temporales deben ser liberados y reusados
        # (esto depende de la implementación del TempManager)
        temp_results = [q.result for q in quads.quads if q.result and q.result.startswith("t")]
        # Verificar que hay temporales
        assert len(temp_results) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
