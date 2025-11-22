from typing import List, Dict, Optional

class QuadOp:
    """Operaciones de cuádruplos"""
    ASSIGN = "ASSIGN"
    ADD = "ADD"
    SUB = "SUB"
    MUL = "MUL"
    DIV = "DIV"
    MOD = "MOD"
    NEG = "NEG"
    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    LABEL = "LABEL"
    GOTO = "GOTO"
    IF_TRUE = "IF_TRUE"
    IF_FALSE = "IF_FALSE"
    LT = "LT"
    LE = "LE"
    GT = "GT"
    GE = "GE"
    EQ = "EQ"
    NE = "NE"
    PRINT = "PRINT"
    BEGIN_FUNC = "BEGIN_FUNC"
    END_FUNC = "END_FUNC"
    PARAM = "PARAM"
    CALL = "CALL"
    RETURN = "RETURN"
    ARRAY_ACCESS = "ARRAY_ACCESS"
    ARRAY_ASSIGN = "ARRAY_ASSIGN"

class Quadruple:
    """Representación de un cuádruplo"""
    def __init__(self, op, arg1=None, arg2=None, result=None):
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2
        self.result = result
    
    def __str__(self):
        return f"({self.op}, {self.arg1}, {self.arg2}, {self.result})"

class QuadrupleList:
    """Lista de cuádruplos"""
    def __init__(self):
        self.quads = []
    
    def __iter__(self):
        return iter(self.quads)
    
    def add(self, op, arg1=None, arg2=None, result=None):
        self.quads.append(Quadruple(op, arg1, arg2, result))

class RegisterManager:
    """Gestor de registros MIPS"""
    def __init__(self):
        self.temp_regs = [f"$t{i}" for i in range(10)]  # $t0-$t9
        self.saved_regs = [f"$s{i}" for i in range(8)]  # $s0-$s7
        self.arg_regs = [f"$a{i}" for i in range(4)]    # $a0-$a3
        
        self.temp_pool = self.temp_regs.copy()
        self.saved_pool = self.saved_regs.copy()
        
        self.var_to_reg = {}
        self.temp_count = 0
    
    def reset(self):
        """Reinicia el gestor"""
        self.temp_pool = self.temp_regs.copy()
        self.saved_pool = self.saved_regs.copy()
        self.var_to_reg.clear()
        self.temp_count = 0
    
    def allocate_temp(self, var_name=None):
        """Asigna un registro temporal"""
        if var_name and var_name in self.var_to_reg:
            return self.var_to_reg[var_name]
        
        if not self.temp_pool:
            # Si no hay registros disponibles, reusar
            reg = self.temp_regs[self.temp_count % len(self.temp_regs)]
            self.temp_count += 1
        else:
            reg = self.temp_pool.pop(0)
        
        if var_name:
            self.var_to_reg[var_name] = reg
        
        return reg
    
    def allocate_saved(self, var_name):
        """Asigna un registro guardado"""
        if var_name in self.var_to_reg:
            return self.var_to_reg[var_name]
        
        if not self.saved_pool:
            # Si no hay registros disponibles, usar temporales
            return self.allocate_temp(var_name)
        
        reg = self.saved_pool.pop(0)
        self.var_to_reg[var_name] = reg
        return reg
    
    def get_register(self, var_name):
        """Obtiene el registro asignado a una variable"""
        return self.var_to_reg.get(var_name)
    
    def free_temp(self, reg):
        """Libera un registro temporal"""
        if reg in self.temp_regs and reg not in self.temp_pool:
            self.temp_pool.append(reg)
    
    def is_register(self, operand):
        """Verifica si es un registro"""
        return operand.startswith('$')
    
    def is_temp_var(self, var_name):
        """Verifica si es una variable temporal"""
        return var_name.startswith('t') or var_name.startswith('_t')

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
        self.variables: Dict[str, int] = {}
        self.string_counter = 0
        self.param_count = 0
        self.in_function = False
        self.current_function = None
        self.label_counter = 0

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
        self.variables.clear()
        self.string_counter = 0
        self.param_count = 0
        self.in_function = False
        self.current_function = None
        self.label_counter = 0
    
    def _generate_data_section(self):
        """Genera la sección .data con variables globales y strings."""
        self.data_section.append(".data")
        self.data_section.append("newline: .asciiz \"\\n\"")

    def _generate_text_section(self, quadruples: QuadrupleList):
        """Genera la sección .text con el código principal."""
        self.code.append(".text")
        self.code.append(".globl main")
        self.code.append("")
        self.code.append("main:")
        
        # Traducir cada cuádruplo
        for quad in quadruples:
            self._translate_quadruple(quad)
        
        # Agregar código de salida si no estamos en una función
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
        elif quad.op == QuadOp.ARRAY_ACCESS:
            self._translate_array_access(quad)
        elif quad.op == QuadOp.ARRAY_ASSIGN:
            self._translate_array_assign(quad)
        else:
            self.code.append(f"# TODO: Implementar {quad.op}")
        
        self.code.append("")
    
    def _translate_assign(self, quad: Quadruple):
        """Traduce ASSIGN: result = arg1"""
        if quad.arg1 and str(quad.arg1).lstrip('-').isdigit():
            # Es una constante numérica
            dest = self._get_or_allocate_register(quad.result)
            self.code.append(f"li {dest}, {quad.arg1}")
        else:
            # Es una variable o temporal
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
        temp1 = self.register_manager.allocate_temp()
        temp2 = self.register_manager.allocate_temp()
        
        self.code.append(f"sne {temp1}, {src1}, $zero")
        self.code.append(f"sne {temp2}, {src2}, $zero")
        self.code.append(f"and {dest}, {temp1}, {temp2}")
        
        self.register_manager.free_temp(temp1)
        self.register_manager.free_temp(temp2)
    
    def _translate_or(self, quad: Quadruple):
        """Traduce OR: result = arg1 || arg2"""
        src1 = self._load_operand(quad.arg1)
        src2 = self._load_operand(quad.arg2)
        dest = self._get_or_allocate_register(quad.result)
        
        # OR lógico: al menos uno debe ser != 0
        temp1 = self.register_manager.allocate_temp()
        temp2 = self.register_manager.allocate_temp()
        
        self.code.append(f"sne {temp1}, {src1}, $zero")
        self.code.append(f"sne {temp2}, {src2}, $zero")
        self.code.append(f"or {dest}, {temp1}, {temp2}")
        
        self.register_manager.free_temp(temp1)
        self.register_manager.free_temp(temp2)
    
    def _translate_not(self, quad: Quadruple):
        """Traduce NOT: result = !arg1"""
        src = self._load_operand(quad.arg1)
        dest = self._get_or_allocate_register(quad.result)
        
        # NOT lógico: 0 -> 1, cualquier otro -> 0
        self.code.append(f"seq {dest}, {src}, $zero")
    
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
        temp = self.register_manager.allocate_temp()
        self.code.append(f"slt {temp}, {src2}, {src1}")  # temp = (b < a) = (a > b)
        self.code.append(f"xori {dest}, {temp}, 1")       # dest = !(a > b)
        self.register_manager.free_temp(temp)
    
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
        
        # a == b
        temp = self.register_manager.allocate_temp()
        self.code.append(f"sub {temp}, {src1}, {src2}")
        self.code.append(f"seq {dest}, {temp}, $zero")
        self.register_manager.free_temp(temp)
    
    def _translate_ne(self, quad: Quadruple):
        """Traduce NE: result = arg1 != arg2"""
        src1 = self._load_operand(quad.arg1)
        src2 = self._load_operand(quad.arg2)
        dest = self._get_or_allocate_register(quad.result)
        
        # a != b
        temp = self.register_manager.allocate_temp()
        self.code.append(f"sub {temp}, {src1}, {src2}")
        self.code.append(f"sne {dest}, {temp}, $zero")
        self.register_manager.free_temp(temp)
    
    def _translate_print(self, quad: Quadruple):
        """Traduce PRINT: imprime un valor o una cadena."""
        arg = str(quad.arg1)
        
        if arg.startswith('"') and arg.endswith('"'):
            # Es un string literal
            label = self._add_string_literal(arg)
            self.code.append(f"la $a0, {label}")
            self.code.append("li $v0, 4")  # syscall 4 = print_string
            self.code.append("syscall")
        else:
            # Es un número o variable
            value = self._load_operand(quad.arg1)
            self.code.append(f"move $a0, {value}")
            self.code.append("li $v0, 1")  # syscall 1 = print_int
            self.code.append("syscall")
        
        # Imprimir newline
        self.code.append("la $a0, newline")
        self.code.append("li $v0, 4")
        self.code.append("syscall")
    
    def _translate_begin_func(self, quad: Quadruple):
        """Traduce BEGIN_FUNC: inicio de una función"""
        func_name = quad.arg1
        self.in_function = True
        self.current_function = func_name
        
        self.code.append(f"{func_name}:")
        self.code.append("# Prólogo de función")
        self.code.append("addi $sp, $sp, -8")  # Espacio para $ra y $fp
        self.code.append("sw $ra, 4($sp)")     # Guardar dirección de retorno
        self.code.append("sw $fp, 0($sp)")     # Guardar frame pointer anterior
        self.code.append("move $fp, $sp")      # Nuevo frame pointer
    
    def _translate_end_func(self, quad: Quadruple):
        """Traduce END_FUNC: fin de una función"""
        self.code.append("# Epílogo de función")
        self.code.append("move $sp, $fp")      # Restaurar stack pointer
        self.code.append("lw $fp, 0($sp)")     # Restaurar frame pointer
        self.code.append("lw $ra, 4($sp)")     # Restaurar dirección de retorno
        self.code.append("addi $sp, $sp, 8")   # Liberar espacio
        self.code.append("jr $ra")             # Retornar
        
        self.in_function = False
        self.current_function = None
        self.param_count = 0
    
    def _translate_param(self, quad: Quadruple):
        """Traduce PARAM: pasar parámetro a función"""
        param_value = self._load_operand(quad.arg1)
        
        if self.param_count < 4:
            # Primeros 4 parámetros en $a0-$a3
            arg_reg = f"$a{self.param_count}"
            self.code.append(f"move {arg_reg}, {param_value}")
        else:
            # Parámetros adicionales en el stack
            self.code.append(f"addi $sp, $sp, -4")
            self.code.append(f"sw {param_value}, 0($sp)")
        
        self.param_count += 1
    
    def _translate_call(self, quad: Quadruple):
        """Traduce CALL: llamada a función"""
        func_name = quad.arg1
        result = quad.result
        
        self.code.append(f"jal {func_name}")
        
        # Si hay un resultado, guardarlo desde $v0
        if result:
            dest = self._get_or_allocate_register(result)
            self.code.append(f"move {dest}, $v0")
        
        # Limpiar parámetros del stack si hay más de 4
        if self.param_count > 4:
            extra_params = self.param_count - 4
            self.code.append(f"addi $sp, $sp, {extra_params * 4}")
        
        self.param_count = 0
    
    def _translate_return(self, quad: Quadruple):
        """Traduce RETURN: retorno de función"""
        if quad.arg1:
            # Hay un valor de retorno
            ret_value = self._load_operand(quad.arg1)
            self.code.append(f"move $v0, {ret_value}")
        
        # Saltar al epílogo (END_FUNC se encargará del resto)
        if self.current_function:
            self.code.append(f"j {self.current_function}_end")
    
    def _translate_array_access(self, quad: Quadruple):
        """Traduce ARRAY_ACCESS: result = array[index]"""
        array_base = quad.arg1  # Dirección base del arreglo
        index = self._load_operand(quad.arg2)
        dest = self._get_or_allocate_register(quad.result)
        
        # Calcular dirección: base + index * 4
        temp = self.register_manager.allocate_temp()
        self.code.append(f"sll {temp}, {index}, 2")  # temp = index * 4
        
        # Cargar la dirección base del arreglo
        base_reg = self._get_or_allocate_register(array_base)
        self.code.append(f"add {temp}, {base_reg}, {temp}")  # temp = base + offset
        self.code.append(f"lw {dest}, 0({temp})")  # dest = memory[temp]
        
        self.register_manager.free_temp(temp)
    
    def _translate_array_assign(self, quad: Quadruple):
        """Traduce ARRAY_ASSIGN: array[index] = value"""
        array_base = quad.result  # Dirección base del arreglo
        index = self._load_operand(quad.arg1)
        value = self._load_operand(quad.arg2)
        
        # Calcular dirección: base + index * 4
        temp = self.register_manager.allocate_temp()
        self.code.append(f"sll {temp}, {index}, 2")  # temp = index * 4
        
        # Cargar la dirección base del arreglo
        base_reg = self._get_or_allocate_register(array_base)
        self.code.append(f"add {temp}, {base_reg}, {temp}")  # temp = base + offset
        self.code.append(f"sw {value}, 0({temp})")  # memory[temp] = value
        
        self.register_manager.free_temp(temp)
    
    def _load_operand(self, operand: str) -> str:
        """
        Carga un operando en un registro.
        
        Args:
            operand: Puede ser un número, variable, o temporal
            
        Returns:
            Nombre del registro que contiene el valor
        """
        if not operand:
            return "$zero"
        
        operand = str(operand)
        
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
        if not var_name:
            return "$zero"
        
        var_name = str(var_name)
        
        reg = self.register_manager.get_register(var_name)
        if reg:
            return reg
        
        # Asignar nuevo registro
        if self.register_manager.is_temp_var(var_name):
            return self.register_manager.allocate_temp(var_name)
        else:
            return self.register_manager.allocate_saved(var_name)
    
    def _add_string_literal(self, string_value: str) -> str:
        """
        Agrega un literal de cadena a la sección .data y retorna su etiqueta.
        
        Args:
            string_value: String literal con comillas
            
        Returns:
            Etiqueta del string en la sección .data
        """
        # Remover comillas
        clean_string = string_value.strip('"')
        
        if not clean_string.endswith('\\n'):
            clean_string += '\\n'
        
        # Verificar si ya existe
        for label, value in self.string_literals.items():
            if value == clean_string:
                return label
        
        # Crear nueva etiqueta
        label = f"str_{self.string_counter}"
        self.string_counter += 1
        
        # Guardar el string
        self.string_literals[label] = clean_string
        
        # Agregar a la sección .data inmediatamente
        self.data_section.append(f'{label}: .asciiz "{clean_string}"')
        
        return label
    
    def _assemble_program(self) -> str:
        """Ensambla el programa completo con secciones .data y .text."""
        program = []
        
        # Agregar sección de datos
        program.extend(self.data_section)
        
        # Agregar variables globales
        for var_name, value in self.variables.items():
            program.append(f"{var_name}: .word {value}")
        
        program.append("")
        
        # Agregar sección de código
        program.extend(self.code)
        
        return "\n".join(program)


# Ejemplo de uso
if __name__ == "__main__":
    # Crear una lista de cuádruplos de ejemplo
    quads = QuadrupleList()
    
    # Ejemplo: suma simple
    # a = 5
    # b = 10
    # c = a + b
    # print(c)
    
    quads.add(QuadOp.ASSIGN, "5", None, "a")
    quads.add(QuadOp.ASSIGN, "10", None, "b")
    quads.add(QuadOp.ADD, "a", "b", "c")
    quads.add(QuadOp.PRINT, "c", None, None)
    
    # Generar código MIPS
    generator = MIPSGenerator()
    mips_code = generator.generate(quads)
    
    print("=== Código MIPS Generado ===")
    print(mips_code)
