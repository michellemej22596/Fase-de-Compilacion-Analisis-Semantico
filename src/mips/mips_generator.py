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
    - Usa $fp (frame pointer) y $sp (stack pointer) para funciones
    """
    
    def __init__(self):
        self.register_manager = RegisterManager()
        self.code: List[str] = []
        self.data_section: List[str] = []
        self.string_literals: Dict[str, str] = {}
        self.string_counter = 0
        self.param_count = 0  # Contador de parámetros para llamadas a funciones
        self.in_function = False  # Flag para saber si estamos dentro de una función
        self.global_vars: Dict[str, any] = {}  # Track global variable declarations

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
        self.global_vars.clear()
        self.string_counter = 0
        self.param_count = 0  # Reiniciar contador de parámetros
        self.in_function = False  # No estamos dentro de una función al inicio
    
    def _generate_data_section(self):
        """Genera la sección .data con variables globales y strings."""
        self.data_section.append(".data")
        self.data_section.append("newline: .asciiz \"\\n\"")  # Línea nueva predeterminada
        
        for var_name, value in self.global_vars.items():
            if isinstance(value, str) and value.startswith('"') and value.endswith('"'):
                # String literal
                self.data_section.append(f"{var_name}: .asciiz {value}")
            else:
                # Integer or other numeric value
                self.data_section.append(f"{var_name}: .word {value}")
        
        # for label, value in self.string_literals.items():
        #     self.data_section.append(f"{label}: .asciiz \"{value}\"")

    def _generate_text_section(self, quadruples: QuadrupleList):
        """Genera la sección .text con el código principal."""
        self.code.append(".text")
        self.code.append(".globl main")
        self.code.append("")
        
        if self.global_vars:
            self.code.append("# Initialize global variables")
            self.code.append("_init:")
            for var_name in self.global_vars.keys():
                reg = self.register_manager.allocate_saved(var_name)
                self.code.append(f"lw {reg}, {var_name}")
            self.code.append("")
        
        # Traducir cada cuádruplo
        for quad in quadruples:
            self._translate_quadruple(quad)
        
        if not self.in_function:
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
        elif quad.op == QuadOp.BEGIN_FUNC:
            self._translate_begin_func(quad)
        elif quad.op == QuadOp.END_FUNC:
            self._translate_end_func(quad)
        elif quad.op == QuadOp.PARAM:
            self._translate_param(quad)
        elif quad.op == QuadOp.CALL:
            self._translate_call(quad)
        elif quad.op == QuadOp.RETURN:
            self._translate_return(quad)
        else:
            self.code.append(f"# TODO: Implementar {quad.op}")
        
        self.code.append("")
    
    def _translate_assign(self, quad: Quadruple):
        """Traduce ASSIGN: asignación de variable."""
        if not self.in_function and isinstance(quad.arg1, (int, float, str)):
            # This is a global variable declaration
            self.global_vars[quad.result] = quad.arg1
            return
        
        # Load source value
        src = self._load_operand(quad.arg1)
        
        # Get destination register
        dest = self._get_or_allocate_register(quad.result)
        
        # Move value to destination
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
        """Traduce LABEL: etiqueta de salto."""
        label = quad.arg1
        if not label.startswith("L_FUNC_"):
            self.code.append(f"{label}:")
    
    def _translate_begin_func(self, quad: Quadruple):
        """
        Traduce BEGIN_FUNC: inicio de función.
        
        Genera el prólogo de la función que:
        1. Guarda el frame pointer anterior
        2. Guarda la dirección de retorno
        3. Establece el nuevo frame pointer
        4. Reserva espacio para variables locales
        """
        func_name = quad.arg1
        num_locals = quad.arg2 or 0
        
        self.in_function = True
        
        if func_name == "main" and self.global_vars:
            self.code.append("# Initialize global variables before main")
            for var_name in self.global_vars.keys():
                reg = self.register_manager.allocate_saved(var_name)
                self.code.append(f"lw {reg}, {var_name}")
            self.code.append("")
        
        self.code.append(f"# Function: {func_name}")
        self.code.append(f"{func_name}:")
        self.code.append("# Function prologue")
        self.code.append("addi $sp, $sp, -8")    # Space for $ra and $fp
        self.code.append("sw $ra, 4($sp)")       # Save return address
        self.code.append("sw $fp, 0($sp)")       # Save frame pointer
        self.code.append("move $fp, $sp")        # New frame pointer
        
        # Reservar espacio para variables locales
        if num_locals > 0:
            space = num_locals * 4
            self.code.append(f"addi $sp, $sp, -{space}")

    def _translate_end_func(self, quad: Quadruple):
        """
        Traduce END_FUNC: fin de función.
        
        Solo genera epílogo si no hubo un RETURN explícito antes.
        """
        if self.in_function:
            func_name = quad.arg1
            
            self.code.append(f"# End function: {func_name}")
            self.code.append("# Function epilogue")
            self.code.append("move $sp, $fp")      # Restore stack pointer
            self.code.append("lw $fp, 0($sp)")     # Restore previous frame pointer
            self.code.append("lw $ra, 4($sp)")     # Restore return address
            self.code.append("addi $sp, $sp, 8")   # Free frame space
            self.code.append("jr $ra")             # Return
            
            self.in_function = False

    def _load_operand(self, operand):
        """
        Carga un operando en un registro o devuelve el registro donde está.
        
        Args:
            operand: Operando a cargar (puede ser constante, variable o registro)
            
        Returns:
            Registro donde está el operando
        """
        if operand is None:
            return None
        
        # Si es una constante numérica
        if isinstance(operand, (int, float)):
            reg = self.register_manager.allocate_temp()
            self.code.append(f"li {reg}, {operand}")
            return reg
        
        # Si es un string (literal o variable)
        if isinstance(operand, str):
            if operand in self.global_vars:
                # Load from global variable
                reg = self.register_manager.allocate_temp()
                self.code.append(f"lw {reg}, {operand}")
                return reg
            
            # Si es una constante string
            if operand.startswith('"') and operand.endswith('"'):
                label = self._add_string_literal(operand)
                reg = self.register_manager.allocate_temp()
                self.code.append(f"la {reg}, {label}")
                return reg
            
            # Si es un temporal o variable
            if operand.startswith('t') or operand.startswith('_'):
                # Es un temporal, buscar su registro
                reg = self.register_manager.get_register(operand)
                if reg is None:
                    # No está en registro, asignar uno
                    reg = self._get_or_allocate_register(operand)
                return reg
            
            # Cualquier otra variable
            return self._get_or_allocate_register(operand)
        
        return None
    
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

    def _translate_foo(self):
        # Proceso de la función foo, similar al ejemplo anterior, con variables y su cálculo
        self.code.append("# Generando código para foo")
        
        # Reservar espacio para las variables de foo
        self.code.append("addi $sp, $sp, -16")  # Por ejemplo, espacio para 2 variables locales
        self.code.append("sw $a0, 0($sp)")      # Guardar el primer parámetro 'a'
        self.code.append("sw $a1, 4($sp)")      # Guardar el segundo parámetro 'b'
        
        # Llamada a bar
        self.code.append("# Llamada a bar")
        self.code.append("jal bar")  # Llamar a la función bar
        
        # Después de la llamada a bar, guardar el valor de retorno en una variable de foo
        self.code.append("move $t0, $v0")  # Guardar el valor de retorno de bar
        self.code.append("addi $sp, $sp, 16")  # Limpiar el espacio de la función foo
        
        self.code.append("jr $ra")  # Retornar de foo

    def _translate_bar(self):
        # Proceso de la función bar
        self.code.append("# Generando código para bar")
        
        # Reservar espacio para las variables de bar
        self.code.append("addi $sp, $sp, -8")  # Reservar espacio para las variables locales de bar
        self.code.append("sw $a0, 0($sp)")      # Guardar 'f'
        self.code.append("sw $a1, 4($sp)")      # Guardar 'g'
        
        # Sumar f + g y guardarlo en x
        self.code.append("lw $t0, 0($sp)")  # Cargar 'f' en $t0
        self.code.append("lw $t1, 4($sp)")  # Cargar 'g' en $t1
        self.code.append("add $t2, $t0, $t1")  # x = f + g
        
        self.code.append("move $v0, $t2")  # Retornar el valor de x
        
        # Limpiar el espacio reservado para bar
        self.code.append("addi $sp, $sp, 8")
        self.code.append("jr $ra")  # Retornar de bar

    def _translate_main(self):
        # Definir las variables globales c y d
        self.code.append("# Script principal")
        self.code.append("li $t0, 2")  # c = 2
        self.code.append("li $t1, 3")  # d = 3
        self.code.append("move $a0, $t0")  # Argumento c para foo
        self.code.append("move $a1, $t1")  # Argumento d para foo
        
        # Llamada a foo
        self.code.append("jal foo")
        
        # Guardar el resultado de foo en x
        self.code.append("move $t2, $v0")  # x = valor retornado de foo
        self.code.append("li $v0, 10")  # Código de salida
        self.code.append("syscall")

    def _add_string_literal(self, value: str) -> str:
        """
        Añade un string literal a la sección de datos.
        
        Args:
            value: String literal (con comillas)
            
        Returns:
            Etiqueta para el string
        """
        if value in self.string_literals:
            return self.string_literals[value]
        
        label = f"str_{self.string_counter}"
        self.string_counter += 1
        self.string_literals[value] = label
        
        return label
