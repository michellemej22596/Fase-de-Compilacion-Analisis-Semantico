"""
Gestor de registros MIPS.

Maneja la asignación y liberación de registros temporales y salvados.
"""

from typing import Optional, Set, Dict


class RegisterManager:
    """
    Gestiona la asignación de registros MIPS.
    
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
        
        # Mapeo de variables/temporales a registros
        self.var_to_reg: Dict[str, str] = {}
        
        # Registros especiales
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
    
    def allocate_temp(self, var_name: Optional[str] = None) -> str:
        """
        Asigna un registro temporal.
        
        Args:
            var_name: Nombre de la variable/temporal (opcional)
            
        Returns:
            Nombre del registro asignado (ej: "$t0")
            
        Raises:
            RuntimeError: Si no hay registros temporales disponibles
        """
        # Si la variable ya tiene un registro asignado, retornarlo
        if var_name and var_name in self.var_to_reg:
            return self.var_to_reg[var_name]
        
        # Buscar un registro temporal libre
        for reg in self.temp_registers:
            if reg not in self.used_temps:
                self.used_temps.add(reg)
                if var_name:
                    self.var_to_reg[var_name] = reg
                return reg
        
        # Si no hay registros libres, usar spilling (guardar en memoria)
        raise RuntimeError("No hay registros temporales disponibles. Implementar spilling.")
    
    def allocate_saved(self, var_name: str) -> str:
        """
        Asigna un registro salvado para una variable.
        
        Args:
            var_name: Nombre de la variable
            
        Returns:
            Nombre del registro asignado (ej: "$s0")
            
        Raises:
            RuntimeError: Si no hay registros salvados disponibles
        """
        # Si la variable ya tiene un registro asignado, retornarlo
        if var_name in self.var_to_reg:
            return self.var_to_reg[var_name]
        
        # Buscar un registro salvado libre
        for reg in self.saved_registers:
            if reg not in self.used_saved:
                self.used_saved.add(reg)
                self.var_to_reg[var_name] = reg
                return reg
        
        raise RuntimeError("No hay registros salvados disponibles. Implementar spilling.")
    
    def free_temp(self, reg: str):
        """Libera un registro temporal."""
        if reg in self.used_temps:
            self.used_temps.remove(reg)
            # Remover del mapeo de variables
            for var, r in list(self.var_to_reg.items()):
                if r == reg:
                    del self.var_to_reg[var]
    
    def free_saved(self, reg: str):
        """Libera un registro salvado."""
        if reg in self.used_saved:
            self.used_saved.remove(reg)
            # Remover del mapeo de variables
            for var, r in list(self.var_to_reg.items()):
                if r == reg:
                    del self.var_to_reg[var]
    
    def get_register(self, var_name: str) -> Optional[str]:
        """
        Obtiene el registro asignado a una variable.
        
        Args:
            var_name: Nombre de la variable
            
        Returns:
            Nombre del registro o None si no está asignado
        """
        return self.var_to_reg.get(var_name)
    
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
        self.var_to_reg.clear()
