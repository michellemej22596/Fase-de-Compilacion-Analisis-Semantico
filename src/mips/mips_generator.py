"""
Generador de código MIPS a partir de cuádruplos.

Traduce código intermedio (cuádruplos) a código assembler MIPS32.
"""

from typing import List, Dict, Optional
from codegen.quadruple import Quadruple, QuadOp, QuadrupleList
from mips.register_manager import RegisterManager


class MIPSGenerator:
    """
    Genera código MIPS a partir de una lista de cuádruplos.
    
    El código generado sigue las convenciones de MIPS32:
    - Usa registros $t0-$t9 para temporales
    - Usa registros $s0-$s7 para variables
    - Usa $v0 para syscalls y valores de retorno
    - Usa $a0-$a3 para argumentos
    """
    
    def __init__(self):
        self.register_manager = RegisterManager()
        self.code: List[str] = []
        self.data_section: List[str] = []
        self.string_literals: Dict[str, str] = {}
        self.string_counter = 0
    
    def generate(self, quadruples: QuadrupleList) -> str:
        """
        Genera código MIPS completo a partir de cuádruplos.
        
        Args:
            quadruples: Lista de cuádruplos a traducir
            
        Returns:
            Código MIPS completo como string
        """
        self.reset()
        
        # Generar sección de datos
        self._generate_data_section()
        
        # Generar sección de código
        self._generate_text_section(quadruples)
        
        # Ensamblar el programa completo
        return self._assemble_program()
    
    def reset(self):
        """Reinicia el generador."""
        self.register_manager.reset()
        self.code.clear()
        self.data_section.clear()
        self.string_literals.clear()
        self.string_counter = 0
    
    def _generate_data_section(self):
        """Genera la sección .data con variables globales y strings."""
        self.data_section.append(".data")
        self.data_section.append("newline: .asciiz \"\\n\"")
        # Los string literals se agregarán dinámicamente
    
    def _generate_text_section(self, quadruples: QuadrupleList):
        """Genera la sección .text con el código principal."""
        self.code.append(".text")
        self.code.append(".globl main")
        self.code.append("")
        self.code.append("main:")
        
        # Traducir cada cuádruplo
        for quad in quadruples:
            self._translate_quadruple(quad)
        
        # Agregar código de salida
        self.code.append("")
        self.code.append("# Exit program")
        self.code.append("li $v0, 10")
        self.code.append("syscall")
    
    def _translate_quadruple(self, quad: Quadruple):
        """
        Traduce un cuádruplo individual a código MIPS.
        
        Args:
            quad: Cuádruplo a traducir
        """
        # Agregar comentario con el cuádruplo original
        self.code.append(f"# {quad}")
        
        # Despachar según el operador
        if quad.op == QuadOp.ASSIGN:
            self._translate_assign(quad)
        elif quad.op == QuadOp.ADD:
            self._translate_add(quad)
        elif quad.op == QuadOp.SUB:
            self._translate_sub(quad)
        elif quad.op == QuadOp.MUL:
            self._translate_mul(quad)
        elif quad.op == QuadOp.DIV:
            self._translate_div(quad)
        elif quad.op == QuadOp.MOD:
            self._translate_mod(quad)
        elif quad.op == QuadOp.NEG:
            self._translate_neg(quad)
        elif quad.op == QuadOp.AND:
            self._translate_and(quad)
        elif quad.op == QuadOp.OR:
            self._translate_or(quad)
        elif quad.op == QuadOp.NOT:
            self._translate_not(quad)
        elif quad.op == QuadOp.LABEL:
            self._translate_label(quad)
        elif quad.op == QuadOp.GOTO:
            self._translate_goto(quad)
        elif quad.op == QuadOp.IF_TRUE:
            self._translate_if_true(quad)
        elif quad.op == QuadOp.IF_FALSE:
            self._translate_if_false(quad)
        elif quad.op == QuadOp.LT:
            self._translate_lt(quad)
        elif quad.op == QuadOp.LE:
            self._translate_le(quad)
        elif quad.op == QuadOp.GT:
            self._translate_gt(quad)
        elif quad.op == QuadOp.GE:
            self._translate_ge(quad)
        elif quad.op == QuadOp.EQ:
            self._translate_eq(quad)
        elif quad.op == QuadOp.NE:
            self._translate_ne(quad)
        elif quad.op == QuadOp.PRINT:
            self._translate_print(quad)
        else:
            self.code.append(f"# TODO: Implementar {quad.op}")
        
        self.code.append("")
    
    def _translate_assign(self, quad: Quadruple):
        """Traduce ASSIGN: result = arg1"""
        # (ASSIGN, valor, None, variable)
        src = self._load_operand(quad.arg1)
        dest = self._get_or_allocate_register(quad.result)
        
        if src != dest:
            self.code.append(f"move {dest}, {src}")
    
    def _translate_add(self, quad: Quadruple):
        """Traduce ADD: result = arg1 + arg2"""
        src1 = self._load_operand(quad.arg1)
        src2 = self._load_operand(quad.arg2)
        dest = self._get_or_allocate_register(quad.result)
        
        self.code.append(f"add {dest}, {src1}, {src2}")
    
    def _translate_sub(self, quad: Quadruple):
        """Traduce SUB: result = arg1 - arg2"""
        src1 = self._load_operand(quad.arg1)
        src2 = self._load_operand(quad.arg2)
        dest = self._get_or_allocate_register(quad.result)
        
        self.code.append(f"sub {dest}, {src1}, {src2}")
    
    def _translate_mul(self, quad: Quadruple):
        """Traduce MUL: result = arg1 * arg2"""
        src1 = self._load_operand(quad.arg1)
        src2 = self._load_operand(quad.arg2)
        dest = self._get_or_allocate_register(quad.result)
        
        self.code.append(f"mul {dest}, {src1}, {src2}")
    
    def _translate_div(self, quad: Quadruple):
        """Traduce DIV: result = arg1 / arg2"""
        src1 = self._load_operand(quad.arg1)
        src2 = self._load_operand(quad.arg2)
        dest = self._get_or_allocate_register(quad.result)
        
        self.code.append(f"div {dest}, {src1}, {src2}")
    
    def _translate_mod(self, quad: Quadruple):
        """Traduce MOD: result = arg1 % arg2"""
        src1 = self._load_operand(quad.arg1)
        src2 = self._load_operand(quad.arg2)
        dest = self._get_or_allocate_register(quad.result)
        
        # MIPS usa div y luego mfhi para obtener el resto
        self.code.append(f"div {src1}, {src2}")
        self.code.append(f"mfhi {dest}")
    
    def _translate_neg(self, quad: Quadruple):
        """Traduce NEG: result = -arg1"""
        src = self._load_operand(quad.arg1)
        dest = self._get_or_allocate_register(quad.result)
        
        self.code.append(f"neg {dest}, {src}")
    
    def _translate_and(self, quad: Quadruple):
        """Traduce AND: result = arg1 && arg2"""
        src1 = self._load_operand(quad.arg1)
        src2 = self._load_operand(quad.arg2)
        dest = self._get_or_allocate_register(quad.result)
        
        # AND lógico: ambos deben ser != 0
        # Convertir a booleano (0 o 1) y hacer AND bitwise
        temp1 = self.register_manager.allocate_temp()
        temp2 = self.register_manager.allocate_temp()
        
        self.code.append(f"sne {temp1}, {src1}, $zero")  # temp1 = (src1 != 0)
        self.code.append(f"sne {temp2}, {src2}, $zero")  # temp2 = (src2 != 0)
        self.code.append(f"and {dest}, {temp1}, {temp2}")  # dest = temp1 & temp2
        
        self.register_manager.free_temp(temp1)
        self.register_manager.free_temp(temp2)
    
    def _translate_or(self, quad: Quadruple):
        """Traduce OR: result = arg1 || arg2"""
        src1 = self._load_operand(quad.arg1)
        src2 = self._load_operand(quad.arg2)
        dest = self._get_or_allocate_register(quad.result)
        
        # OR lógico: al menos uno debe ser != 0
        # Convertir a booleano (0 o 1) y hacer OR bitwise
        temp1 = self.register_manager.allocate_temp()
        temp2 = self.register_manager.allocate_temp()
        
        self.code.append(f"sne {temp1}, {src1}, $zero")  # temp1 = (src1 != 0)
        self.code.append(f"sne {temp2}, {src2}, $zero")  # temp2 = (src2 != 0)
        self.code.append(f"or {dest}, {temp1}, {temp2}")  # dest = temp1 | temp2
        
        self.register_manager.free_temp(temp1)
        self.register_manager.free_temp(temp2)
    
    def _translate_not(self, quad: Quadruple):
        """Traduce NOT: result = !arg1"""
        src = self._load_operand(quad.arg1)
        dest = self._get_or_allocate_register(quad.result)
        
        # NOT lógico: 0 -> 1, cualquier otro -> 0
        self.code.append(f"seq {dest}, {src}, $zero")  # dest = (src == 0)
    
    def _translate_label(self, quad: Quadruple):
        """Traduce LABEL: etiqueta"""
        self.code.append(f"{quad.arg1}:")
    
    def _translate_goto(self, quad: Quadruple):
        """Traduce GOTO: salto incondicional"""
        self.code.append(f"j {quad.arg1}")
    
    def _translate_if_true(self, quad: Quadruple):
        """Traduce IF_TRUE: if arg1 goto arg2"""
        cond = self._load_operand(quad.arg1)
        label = quad.arg2
        
        self.code.append(f"bnez {cond}, {label}")
    
    def _translate_if_false(self, quad: Quadruple):
        """Traduce IF_FALSE: if not arg1 goto arg2"""
        cond = self._load_operand(quad.arg1)
        label = quad.arg2
        
        self.code.append(f"beqz {cond}, {label}")
    
    def _translate_lt(self, quad: Quadruple):
        """Traduce LT: result = arg1 < arg2"""
        src1 = self._load_operand(quad.arg1)
        src2 = self._load_operand(quad.arg2)
        dest = self._get_or_allocate_register(quad.result)
        
        self.code.append(f"slt {dest}, {src1}, {src2}")
    
    def _translate_le(self, quad: Quadruple):
        """Traduce LE: result = arg1 <= arg2"""
        src1 = self._load_operand(quad.arg1)
        src2 = self._load_operand(quad.arg2)
        dest = self._get_or_allocate_register(quad.result)
        
        # a <= b es equivalente a !(a > b)
        self.code.append(f"sgt {dest}, {src1}, {src2}")
        self.code.append(f"xori {dest}, {dest}, 1")
    
    def _translate_gt(self, quad: Quadruple):
        """Traduce GT: result = arg1 > arg2"""
        src1 = self._load_operand(quad.arg1)
        src2 = self._load_operand(quad.arg2)
        dest = self._get_or_allocate_register(quad.result)
        
        # a > b es equivalente a b < a
        self.code.append(f"slt {dest}, {src2}, {src1}")
    
    def _translate_ge(self, quad: Quadruple):
        """Traduce GE: result = arg1 >= arg2"""
        src1 = self._load_operand(quad.arg1)
        src2 = self._load_operand(quad.arg2)
        dest = self._get_or_allocate_register(quad.result)
        
        # a >= b es equivalente a !(a < b)
        self.code.append(f"slt {dest}, {src1}, {src2}")
        self.code.append(f"xori {dest}, {dest}, 1")
    
    def _translate_eq(self, quad: Quadruple):
        """Traduce EQ: result = arg1 == arg2"""
        src1 = self._load_operand(quad.arg1)
        src2 = self._load_operand(quad.arg2)
        dest = self._get_or_allocate_register(quad.result)
        
        # a == b: restar y verificar si es 0
        self.code.append(f"sub {dest}, {src1}, {src2}")
        self.code.append(f"seq {dest}, {dest}, $zero")
    
    def _translate_ne(self, quad: Quadruple):
        """Traduce NE: result = arg1 != arg2"""
        src1 = self._load_operand(quad.arg1)
        src2 = self._load_operand(quad.arg2)
        dest = self._get_or_allocate_register(quad.result)
        
        # a != b: restar y verificar si no es 0
        self.code.append(f"sub {dest}, {src1}, {src2}")
        self.code.append(f"sne {dest}, {dest}, $zero")
    
    def _translate_print(self, quad: Quadruple):
        """Traduce PRINT: imprime un valor"""
        value = self._load_operand(quad.arg1)
        
        # Imprimir el valor (asumiendo entero)
        self.code.append(f"move $a0, {value}")
        self.code.append("li $v0, 1")  # syscall 1 = print_int
        self.code.append("syscall")
        
        # Imprimir newline
        self.code.append("la $a0, newline")
        self.code.append("li $v0, 4")  # syscall 4 = print_string
        self.code.append("syscall")
    
    def _load_operand(self, operand: str) -> str:
        """
        Carga un operando en un registro.
        
        Args:
            operand: Puede ser un número, variable, o temporal
            
        Returns:
            Nombre del registro que contiene el valor
        """
        # Si es un registro, retornarlo directamente
        if self.register_manager.is_register(operand):
            return operand
        
        # Si es un número literal
        if operand.lstrip('-').isdigit():
            reg = self.register_manager.allocate_temp()
            self.code.append(f"li {reg}, {operand}")
            return reg
        
        # Si es una variable o temporal
        reg = self.register_manager.get_register(operand)
        if reg:
            return reg
        
        # Asignar un nuevo registro
        reg = self.register_manager.allocate_temp(operand)
        return reg
    
    def _get_or_allocate_register(self, var_name: str) -> str:
        """Obtiene o asigna un registro para una variable."""
        reg = self.register_manager.get_register(var_name)
        if reg:
            return reg
        
        # Asignar nuevo registro
        if self.register_manager.is_temp_var(var_name):
            return self.register_manager.allocate_temp(var_name)
        else:
            return self.register_manager.allocate_saved(var_name)
    
    def _assemble_program(self) -> str:
        """Ensambla el programa completo con secciones .data y .text."""
        program = []
        
        # Agregar sección de datos
        program.extend(self.data_section)
        
        # Agregar string literals si hay
        for label, value in self.string_literals.items():
            program.append(f"{label}: .asciiz {value}")
        
        program.append("")
        
        # Agregar sección de código
        program.extend(self.code)
        
        return "\n".join(program)
