"""
Gestor de registros MIPS mejorado con spilling y análisis de vida de variables.

Maneja la asignación y liberación de registros temporales y salvados,
implementando spilling automático cuando no hay registros disponibles.
"""

from typing import Optional, Set, Dict, List
from dataclasses import dataclass


@dataclass
class VariableInfo:
    """Información sobre una variable en memoria."""
    name: str
    register: Optional[str]  # Registro actual (None si está en memoria)
    stack_offset: int  # Offset en el stack (-4, -8, etc.)
    last_use: int  # Última instrucción donde se usa (para LRU)
    is_dirty: bool  # True si el valor en registro ha sido modificado
    live: bool  # True si la variable está viva (se usará más adelante)


class RegisterManager:
    """
    Gestor de registros MIPS con spilling automático.
    
    Estrategias implementadas:
    1. LRU (Least Recently Used): Vuelca el registro usado hace más tiempo
    2. Dirty bit: Solo escribe a memoria si el valor fue modificado
    3. Análisis de vida: Prioriza mantener variables vivas en registros
    4. Reutilización: Reutiliza registros de variables muertas sin escribir
    
    Registros disponibles:
    - $t0-$t9: Registros temporales (10 registros)
    - $s0-$s7: Registros salvados (8 registros)
    - $v0-$v1: Valores de retorno
    - $a0-$a3: Argumentos de función
    """
    
    def __init__(self):
        # Registros temporales disponibles
        self.temp_registers = [f"$t{i}" for i in range(10)]
        
        # Registros salvados disponibles
        self.saved_registers = [f"$s{i}" for i in range(8)]
        
        # Registros actualmente en uso
        self.used_temps: Set[str] = set()
        self.used_saved: Set[str] = set()
        
        # Mapeo de variables a información completa
        self.var_info: Dict[str, VariableInfo] = {}
        
        # Mapeo inverso: registro -> variable
        self.reg_to_var: Dict[str, str] = {}
        
        # Contador de instrucciones (para LRU)
        self.instruction_counter = 0
        
        # Stack offset para spilling (empieza en -4 para variables locales)
        self.current_stack_offset = -4
        
        # Código generado por spilling
        self.spill_code: List[str] = []
        
        # Registros especiales (no gestionados)
        self.zero = "$zero"  # Siempre 0
        self.sp = "$sp"      # Stack pointer
        self.fp = "$fp"      # Frame pointer
        self.ra = "$ra"      # Return address
        self.v0 = "$v0"      # Return value / syscall
        self.v1 = "$v1"      # Return value
        self.a0 = "$a0"      # Argument 1
        self.a1 = "$a1"      # Argument 2
        self.a2 = "$a2"      # Argument 3
        self.a3 = "$a3"      # Argument 4
    
    def increment_instruction(self):
        """Incrementa el contador de instrucciones (llamar en cada operación)."""
        self.instruction_counter += 1
    
    def allocate_temp(self, var_name: Optional[str] = None, is_write: bool = False) -> str:
        """
        Asigna un registro temporal con spilling automático.
        
        Args:
            var_name: Nombre de la variable/temporal (opcional)
            is_write: True si se va a escribir en este registro
            
        Returns:
            Nombre del registro asignado (ej: "$t0")
        """
        
        # Si la variable ya tiene un registro asignado, actualizarlo y retornarlo
        if var_name and var_name in self.var_info:
            info = self.var_info[var_name]
            if info.register:
                info.last_use = self.instruction_counter
                if is_write:
                    info.is_dirty = True
                return info.register
            else:
                # La variable está en memoria (spilled), restaurarla
                reg = self._restore_from_memory(var_name)
                if is_write:
                    self.var_info[var_name].is_dirty = True
                return reg
        
        # Buscar un registro temporal libre
        for reg in self.temp_registers:
            if reg not in self.used_temps:
                self.used_temps.add(reg)
                if var_name:
                    self._register_variable(var_name, reg, is_write)
                return reg
        
        # No hay registros libres: aplicar spilling
        return self._spill_and_allocate_temp(var_name, is_write)
    
    def allocate_saved(self, var_name: str, is_write: bool = False) -> str:
        """
        Asigna un registro salvado con spilling automático.
        
        Args:
            var_name: Nombre de la variable
            is_write: True si se va a escribir en este registro
            
        Returns:
            Nombre del registro asignado (ej: "$s0")
        """
        
        # Si la variable ya tiene un registro asignado, retornarlo
        if var_name in self.var_info:
            info = self.var_info[var_name]
            if info.register:
                info.last_use = self.instruction_counter
                if is_write:
                    info.is_dirty = True
                return info.register
            else:
                # Restaurar desde memoria
                reg = self._restore_from_memory(var_name)
                if is_write:
                    self.var_info[var_name].is_dirty = True
                return reg
        
        # Buscar un registro salvado libre
        for reg in self.saved_registers:
            if reg not in self.used_saved:
                self.used_saved.add(reg)
                self._register_variable(var_name, reg, is_write)
                return reg
        
        # No hay registros libres: aplicar spilling
        return self._spill_and_allocate_saved(var_name, is_write)
    
    def _spill_and_allocate_temp(self, var_name: Optional[str], is_write: bool) -> str:
        """
        Aplica spilling a un registro temporal usando estrategia LRU.
        
        Returns:
            Registro liberado y asignado
        """
        
        # Encontrar el registro temporal usado hace más tiempo
        victim_reg = None
        oldest_use = float('inf')
        
        for reg in self.temp_registers:
            if reg in self.used_temps and reg in self.reg_to_var:
                victim_var = self.reg_to_var[reg]
                info = self.var_info[victim_var]
                
                # Priorizar variables que no están vivas
                if not info.live:
                    victim_reg = reg
                    break
                
                # Si todas están vivas, elegir la menos recientemente usada
                if info.last_use < oldest_use:
                    oldest_use = info.last_use
                    victim_reg = reg
        
        if not victim_reg:
            raise RuntimeError("Error crítico: no se pudo encontrar registro para spilling")
        
        # Guardar el contenido del registro víctima en memoria
        self._spill_register(victim_reg)
        
        # Asignar el registro liberado
        if var_name:
            self._register_variable(var_name, victim_reg, is_write)
        
        return victim_reg
    
    def _spill_and_allocate_saved(self, var_name: str, is_write: bool) -> str:
        """
        Aplica spilling a un registro salvado usando estrategia LRU.
        
        Returns:
            Registro liberado y asignado
        """
        
        victim_reg = None
        oldest_use = float('inf')
        
        for reg in self.saved_registers:
            if reg in self.used_saved and reg in self.reg_to_var:
                victim_var = self.reg_to_var[reg]
                info = self.var_info[victim_var]
                
                if not info.live:
                    victim_reg = reg
                    break
                
                if info.last_use < oldest_use:
                    oldest_use = info.last_use
                    victim_reg = reg
        
        if not victim_reg:
            raise RuntimeError("Error crítico: no se pudo encontrar registro salvado para spilling")
        
        self._spill_register(victim_reg)
        self._register_variable(var_name, victim_reg, is_write)
        
        return victim_reg
    
    def _spill_register(self, reg: str):
        """
        Vuelca el contenido de un registro a memoria.
        
        Args:
            reg: Registro a volcar
        """
        
        if reg not in self.reg_to_var:
            return
        
        var_name = self.reg_to_var[reg]
        info = self.var_info[var_name]
        
        # Solo escribir a memoria si el valor fue modificado (optimización)
        if info.is_dirty:
            # Generar código para guardar en stack
            self.spill_code.append(f"# Spilling {var_name} from {reg} to stack")
            self.spill_code.append(f"sw {reg}, {info.stack_offset}($sp)")
        
        # Actualizar estado: la variable ya no está en registro
        info.register = None
        info.is_dirty = False
        
        # Limpiar mapeos
        del self.reg_to_var[reg]
        
        # Liberar el registro
        if reg in self.used_temps:
            self.used_temps.remove(reg)
        if reg in self.used_saved:
            self.used_saved.remove(reg)
    
    def _restore_from_memory(self, var_name: str) -> str:
        """
        Restaura una variable desde memoria a un registro.
        
        Args:
            var_name: Variable a restaurar
            
        Returns:
            Registro donde se restauró
        """
        
        info = self.var_info[var_name]
        
        # Buscar un registro libre
        reg = None
        for r in self.temp_registers:
            if r not in self.used_temps:
                reg = r
                self.used_temps.add(r)
                break
        
        # Si no hay libres, hacer spilling
        if not reg:
            reg = self._spill_and_allocate_temp(None, False)
        
        # Cargar desde memoria
        self.spill_code.append(f"# Restoring {var_name} from stack to {reg}")
        self.spill_code.append(f"lw {reg}, {info.stack_offset}($sp)")
        
        # Actualizar mapeos
        info.register = reg
        info.last_use = self.instruction_counter
        self.reg_to_var[reg] = var_name
        
        return reg
    
    def _register_variable(self, var_name: str, reg: str, is_write: bool):
        """
        Registra una nueva variable en el sistema.
        
        Args:
            var_name: Nombre de la variable
            reg: Registro asignado
            is_write: Si se va a escribir en el registro
        """
        
        if var_name not in self.var_info:
            # Asignar nuevo offset en stack para esta variable
            self.var_info[var_name] = VariableInfo(
                name=var_name,
                register=reg,
                stack_offset=self.current_stack_offset,
                last_use=self.instruction_counter,
                is_dirty=is_write,
                live=True  # Por defecto, asumir que está viva
            )
            self.current_stack_offset -= 4  # Cada variable ocupa 4 bytes
        else:
            # Actualizar registro existente
            info = self.var_info[var_name]
            info.register = reg
            info.last_use = self.instruction_counter
            if is_write:
                info.is_dirty = True
        
        self.reg_to_var[reg] = var_name
    
    def free_temp(self, reg: str):
        """Libera un registro temporal."""
        
        if reg in self.used_temps:
            # Si hay una variable asociada, marcarla como no viva
            if reg in self.reg_to_var:
                var_name = self.reg_to_var[reg]
                if var_name in self.var_info:
                    self.var_info[var_name].live = False
                del self.reg_to_var[reg]
            
            self.used_temps.remove(reg)
    
    def free_saved(self, reg: str):
        """Libera un registro salvado."""
        
        if reg in self.used_saved:
            if reg in self.reg_to_var:
                var_name = self.reg_to_var[reg]
                if var_name in self.var_info:
                    self.var_info[var_name].live = False
                del self.reg_to_var[reg]
            
            self.used_saved.remove(reg)
    
    def free(self, reg: str):
        """
        Libera un registro (temporal o salvado).
        
        Args:
            reg: Registro a liberar
        """
        if reg in self.temp_registers:
            self.free_temp(reg)
        elif reg in self.saved_registers:
            self.free_saved(reg)
    
    def mark_variable_live(self, var_name: str):
        """Marca una variable como viva (se usará más adelante)."""
        if var_name in self.var_info:
            self.var_info[var_name].live = True
    
    def mark_variable_dead(self, var_name: str):
        """Marca una variable como muerta (no se usará más)."""
        if var_name in self.var_info:
            self.var_info[var_name].live = False
    
    def get_register(self, var_name: str) -> Optional[str]:
        """
        Obtiene el registro asignado a una variable.
        
        Args:
            var_name: Nombre de la variable
            
        Returns:
            Nombre del registro o None si no está en registro
        """
        if var_name in self.var_info:
            return self.var_info[var_name].register
        return None
    
    def get_spill_code(self) -> List[str]:
        """
        Obtiene y limpia el código generado por operaciones de spilling.
        
        Returns:
            Lista de instrucciones MIPS para spilling/restore
        """
        code = self.spill_code.copy()
        self.spill_code.clear()
        return code
    
    def get_stack_size(self) -> int:
        """
        Calcula el tamaño total del stack necesario.
        
        Returns:
            Tamaño en bytes (negativo porque el stack crece hacia abajo)
        """
        return abs(self.current_stack_offset) + 4  # +4 porque empezamos en -4
    
    def is_register(self, name: str) -> bool:
        """Verifica si un nombre es un registro MIPS."""
        return name.startswith("$")
    
    def is_temp_var(self, name: str) -> bool:
        """Verifica si un nombre es una variable temporal (t0, t1, etc)."""
        return name.startswith("t") and name[1:].isdigit()
    
    def reset(self):
        """Reinicia el gestor de registros."""
        self.used_temps.clear()
        self.used_saved.clear()
        self.var_info.clear()
        self.reg_to_var.clear()
        self.instruction_counter = 0
        self.current_stack_offset = -4
        self.spill_code.clear()
