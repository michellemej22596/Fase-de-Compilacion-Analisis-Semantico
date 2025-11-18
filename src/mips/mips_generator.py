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
        self.param_count = 0  # Reiniciar contador de parámetros
        self.in_function = False  # No estamos dentro de una función al inicio
    
    def _generate_data_section(self):
        """Genera la sección .data con variables globales y strings."""
        self.data_section.append(".data")
        self.data_section.append("newline: .asciiz \"\\n\"")  # Línea nueva predeterminada
        
        # Añadir constantes a la sección de datos
        for var_name, value in self.string_literals.items():
            self.data_section.append(f"{var_name}: .word {value}")
        
        # También incluir las literales de cadenas, si las tienes
        for label, value in self.string_literals.items():
            self.data_section.append(f"{label}: .asciiz \"{value}\"")

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
        """Traduce ASSIGN: result = arg1"""
        if quad.arg1.isdigit():  # Verificar si es un valor literal (constante)
            # Si es una constante, agregarla a la sección de datos
            const_name = f"const_{self.string_counter}"
            self.string_literals[const_name] = quad.arg1
            self.string_counter += 1
            self.code.append(f"li {quad.result}, {quad.arg1}")  # Cargar constante en el registro
        else:
            # Si no es una constante, seguir el procedimiento normal
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
        """Traduce PRINT: imprime un valor o una cadena."""
        value = self._load_operand(quad.arg1)
        
        if value.startswith('"') and value.endswith('"'):
            # Es un string literal
            label = self._add_string_literal(value)
            self.code.append(f"la $a0, {label}")
            self.code.append("li $v0, 4")  # syscall 4 = print_string
            self.code.append("syscall")
        else:
            # Si no es un literal de cadena, se trata de un número entero
            self.code.append(f"move $a0, {value}")
            self.code.append("li $v0, 1")  # syscall 1 = print_int
            self.code.append("syscall")
        
        # Imprimir newline
        self.code.append("la $a0, newline")
        self.code.append("li $v0, 4")  # syscall 4 = print_string
        self.code.append("syscall")

    def _translate_begin_func(self, quad: Quadruple):
        func_name = quad.arg1
        num_params = quad.arg2 if quad.arg2 else 0
        
        self.in_function = True
        self.code.append(f"# Function: {func_name}")
        
        # Función anidada, comenzamos el prólogo de la función
        self.code.append("# Function prologue")
        self.code.append("addi $sp, $sp, -8")  # Reservar espacio para $ra y $fp
        self.code.append("sw $ra, 4($sp)")     # Guardar return address
        self.code.append("sw $fp, 0($sp)")     # Guardar frame pointer anterior
        self.code.append("move $fp, $sp")      # Establecer nuevo frame pointer
        
        # Reservar espacio para variables locales (puedes ajustarlo según el número de variables)
        self.code.append("addi $sp, $sp, -32")  # Por ejemplo, 32 bytes para variables locales

    def _translate_end_func(self, quad: Quadruple):
        """
        Traduce END_FUNC: fin de función.
        
        Epílogo de la función:
        - Restaurar $sp
        - Restaurar $fp
        - Restaurar $ra
        - Retornar
        """
        func_name = quad.arg1
        
        self.code.append(f"# End function: {func_name}")
        self.code.append("# Function epilogue")
        self.code.append("move $sp, $fp")      # Restaurar stack pointer
        self.code.append("lw $fp, 0($sp)")     # Restaurar frame pointer anterior
        self.code.append("lw $ra, 4($sp)")     # Restaurar return address
        self.code.append("addi $sp, $sp, 8")   # Liberar espacio del frame
        self.code.append("jr $ra")             # Retornar
        
        self.in_function = False
        

    def _translate_end_func(self, quad: Quadruple):
        """
        Traduce END_FUNC: fin de función.
        
        Epílogo de la función:
        - Restaurar $sp
        - Restaurar $fp
        - Restaurar $ra
        - Retornar
        """
        func_name = quad.arg1
        
        self.code.append(f"# End function: {func_name}")
        self.code.append("# Function epilogue")
        self.code.append("move $sp, $fp")      # Restaurar stack pointer
        self.code.append("lw $fp, 0($sp)")     # Restaurar frame pointer anterior
        self.code.append("lw $ra, 4($sp)")     # Restaurar return address
        self.code.append("addi $sp, $sp, 8")   # Liberar espacio del frame
        self.code.append("jr $ra")             # Retornar
        
        self.in_function = False
    
    def _translate_param(self, quad: Quadruple):
        """
        Traduce PARAM: pasar parámetro a función.
        
        Los primeros 4 parámetros van en $a0-$a3.
        Los siguientes van en el stack.
        """
        param_value = self._load_operand(quad.arg1)
        
        if self.param_count < 4:
            # Usar registros $a0-$a3
            arg_reg = f"$a{self.param_count}"
            self.code.append(f"move {arg_reg}, {param_value}")
        else:
            # Usar stack para parámetros adicionales
            offset = (self.param_count - 4) * 4
            self.code.append(f"sw {param_value}, {offset}($sp)")
        
        self.param_count += 1
    
    def _translate_call(self, quad: Quadruple):
        """
        Traduce CALL: llamada a función.
        
        Formato: CALL func_name num_args result
        """
        func_name = quad.arg1
        num_args = quad.arg2 if quad.arg2 else 0
        result_var = quad.result
        
        # Llamar a la función
        self.code.append(f"jal {func_name}")
        
        # Resetear contador de parámetros
        self.param_count = 0
        
        # Si hay resultado, guardarlo
        if result_var:
            dest = self._get_or_allocate_register(result_var)
            self.code.append(f"move {dest}, $v0")
    
    def _translate_return(self, quad: Quadruple):
        """
        Traduce RETURN: retornar de función.
        
        Si hay valor de retorno, ponerlo en $v0.
        Luego saltar al epílogo de la función.
        """
        if quad.arg1:
            # Hay valor de retorno
            return_value = self._load_operand(quad.arg1)
            self.code.append(f"move $v0, {return_value}")
        
        # Si estamos en una función, hacer el epílogo
        if self.in_function:
            self.code.append("# Early return")
            self.code.append("move $sp, $fp")
            self.code.append("lw $fp, 0($sp)")
            self.code.append("lw $ra, 4($sp)")
            self.code.append("addi $sp, $sp, 8")
            self.code.append("jr $ra")

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
        if self.register_manager.is_temp_var(operand):
            return self.register_manager.allocate_temp(operand)
        else:
            return self.register_manager.allocate_saved(operand)
    
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
