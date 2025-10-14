"""
Gestor de variables temporales para generación de código intermedio.

Implementa un pool de temporales con reciclaje automático para
optimizar el uso de registros en la fase de generación de código MIPS.
"""

from typing import Set, Optional


class TempManager:
    """
    Gestor de variables temporales con reciclaje.
    
    Genera nombres únicos para temporales (t0, t1, t2, ...)
    y permite reciclar temporales que ya no se usan.
    
    Ejemplo:
        temp_mgr = TempManager()
        t0 = temp_mgr.new_temp()  # "t0"
        t1 = temp_mgr.new_temp()  # "t1"
        temp_mgr.free_temp(t0)    # Libera t0
        t2 = temp_mgr.new_temp()  # "t0" (reciclado)
    """
    
    def __init__(self, prefix: str = "t"):
        """
        Inicializa el gestor de temporales.
        
        Args:
            prefix: Prefijo para los nombres de temporales (default: "t")
        """
        self._prefix = prefix
        self._counter = 0
        self._free_pool: Set[int] = set()
        self._in_use: Set[str] = set()
    
    def new_temp(self) -> str:
        """
        Genera una nueva variable temporal.
        
        Intenta reciclar temporales libres antes de crear nuevos.
        
        Returns:
            Nombre de la variable temporal (ej: "t0", "t1", ...)
        """
        # Intentar reciclar un temporal libre
        if self._free_pool:
            num = min(self._free_pool)
            self._free_pool.remove(num)
            temp_name = f"{self._prefix}{num}"
            self._in_use.add(temp_name)
            return temp_name
        
        # Crear un nuevo temporal
        temp_name = f"{self._prefix}{self._counter}"
        self._counter += 1
        self._in_use.add(temp_name)
        return temp_name
    
    def free_temp(self, temp: str) -> bool:
        """
        Libera una variable temporal para reciclaje.
        
        Args:
            temp: Nombre de la temporal a liberar
            
        Returns:
            True si se liberó exitosamente, False si no estaba en uso
        """
        if temp not in self._in_use:
            return False
        
        # Extraer el número del temporal
        if temp.startswith(self._prefix):
            try:
                num = int(temp[len(self._prefix):])
                self._free_pool.add(num)
                self._in_use.remove(temp)
                return True
            except ValueError:
                return False
        
        return False
    
    def is_temp(self, name: str) -> bool:
        """
        Verifica si un nombre corresponde a una temporal.
        
        Args:
            name: Nombre a verificar
            
        Returns:
            True si es una temporal, False en caso contrario
        """
        return name.startswith(self._prefix) and name[len(self._prefix):].isdigit()
    
    def reset(self):
        """
        Reinicia el gestor de temporales.
        
        Útil al comenzar la generación de código para una nueva función.
        """
        self._counter = 0
        self._free_pool.clear()
        self._in_use.clear()
    
    def get_stats(self) -> dict:
        """
        Obtiene estadísticas del uso de temporales.
        
        Returns:
            Diccionario con estadísticas de uso
        """
        return {
            "total_created": self._counter,
            "in_use": len(self._in_use),
            "available": len(self._free_pool),
            "max_concurrent": self._counter - len(self._free_pool)
        }
    
    def __str__(self) -> str:
        """Representación en string del estado del gestor."""
        stats = self.get_stats()
        return (f"TempManager(created={stats['total_created']}, "
                f"in_use={stats['in_use']}, "
                f"available={stats['available']})")


class ScopedTempManager(TempManager):
    """
    Gestor de temporales con soporte para ámbitos anidados.
    
    Permite crear contextos de temporales que se liberan automáticamente
    al salir del contexto (útil para expresiones complejas).
    """
    
    def __init__(self, prefix: str = "t"):
        super().__init__(prefix)
        self._scope_stack: list[Set[str]] = []
    
    def push_scope(self):
        """Crea un nuevo ámbito de temporales."""
        self._scope_stack.append(set())
    
    def pop_scope(self):
        """
        Elimina el ámbito actual y libera todas sus temporales.
        
        Returns:
            Conjunto de temporales que fueron liberadas
        """
        if not self._scope_stack:
            return set()
        
        scope_temps = self._scope_stack.pop()
        for temp in scope_temps:
            self.free_temp(temp)
        
        return scope_temps
    
    def new_temp(self) -> str:
        """
        Genera una nueva temporal y la registra en el ámbito actual.
        
        Returns:
            Nombre de la variable temporal
        """
        temp = super().new_temp()
        
        # Registrar en el ámbito actual si existe
        if self._scope_stack:
            self._scope_stack[-1].add(temp)
        
        return temp
    
    def __enter__(self):
        """Soporte para context manager (with statement)."""
        self.push_scope()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Libera temporales al salir del contexto."""
        self.pop_scope()
        return False
