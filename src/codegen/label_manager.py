"""
Gestor de etiquetas para control de flujo en código intermedio.

Genera etiquetas únicas para saltos, bucles y estructuras de control.
"""

from typing import Dict, Optional


class LabelManager:
    """
    Gestor de etiquetas para control de flujo.
    
    Genera nombres únicos para etiquetas y mantiene contadores
    separados para diferentes tipos de estructuras de control.
    
    Ejemplo:
        label_mgr = LabelManager()
        L0 = label_mgr.new_label()           # "L0"
        L_IF_0 = label_mgr.new_label("IF")   # "L_IF_0"
        L_WHILE_0 = label_mgr.new_label("WHILE")  # "L_WHILE_0"
    """
    
    def __init__(self, prefix: str = "L"):
        """
        Inicializa el gestor de etiquetas.
        
        Args:
            prefix: Prefijo base para las etiquetas (default: "L")
        """
        self._prefix = prefix
        self._global_counter = 0
        self._type_counters: Dict[str, int] = {}
    
    def new_label(self, label_type: Optional[str] = None) -> str:
        """
        Genera una nueva etiqueta única.
        
        Args:
            label_type: Tipo de etiqueta (ej: "IF", "WHILE", "FOR")
                       Si es None, usa contador global
        
        Returns:
            Nombre de la etiqueta (ej: "L0", "L_IF_0", "L_WHILE_1")
        """
        if label_type is None:
            # Etiqueta genérica
            label = f"{self._prefix}{self._global_counter}"
            self._global_counter += 1
            return label
        
        # Etiqueta con tipo específico
        label_type = label_type.upper()
        if label_type not in self._type_counters:
            self._type_counters[label_type] = 0
        
        label = f"{self._prefix}_{label_type}_{self._type_counters[label_type]}"
        self._type_counters[label_type] += 1
        return label
    
    def new_label_pair(self, label_type: str) -> tuple[str, str]:
        """
        Genera un par de etiquetas para estructuras de control.
        
        Útil para if-else, while, for, etc. que necesitan
        etiquetas de inicio y fin.
        
        Args:
            label_type: Tipo de estructura (ej: "IF", "WHILE")
        
        Returns:
            Tupla con (etiqueta_inicio, etiqueta_fin)
        """
        start = self.new_label(label_type)
        end = self.new_label(label_type)
        return (start, end)
    
    def reset(self):
        """
        Reinicia todos los contadores de etiquetas.
        
        Útil al comenzar la generación de código para una nueva función.
        """
        self._global_counter = 0
        self._type_counters.clear()
    
    def get_stats(self) -> dict:
        """
        Obtiene estadísticas del uso de etiquetas.
        
        Returns:
            Diccionario con contadores por tipo
        """
        return {
            "global": self._global_counter,
            "by_type": self._type_counters.copy()
        }
    
    def __str__(self) -> str:
        """Representación en string del estado del gestor."""
        stats = self.get_stats()
        return f"LabelManager(global={stats['global']}, types={stats['by_type']})"


class LoopLabelManager:
    """
    Gestor especializado para etiquetas de bucles.
    
    Mantiene una pila de etiquetas para bucles anidados,
    útil para manejar break y continue correctamente.
    """
    
    def __init__(self, label_manager: LabelManager):
        """
        Inicializa el gestor de etiquetas de bucles.
        
        Args:
            label_manager: Gestor de etiquetas base
        """
        self._label_mgr = label_manager
        self._loop_stack: list[tuple[str, str, str]] = []
    
    def push_loop(self, loop_type: str) -> tuple[str, str, str]:
        """
        Crea etiquetas para un nuevo bucle y las apila.
        
        Args:
            loop_type: Tipo de bucle ("WHILE", "FOR", "FOREACH", "DO_WHILE")
        
        Returns:
            Tupla con (etiqueta_inicio, etiqueta_fin, etiqueta_continue)
        """
        start = self._label_mgr.new_label(loop_type)
        end = self._label_mgr.new_label(loop_type)
        continue_label = self._label_mgr.new_label(f"{loop_type}_CONT")
        
        loop_labels = (start, end, continue_label)
        self._loop_stack.append(loop_labels)
        return loop_labels
    
    def pop_loop(self) -> Optional[tuple[str, str, str]]:
        """
        Elimina el bucle actual de la pila.
        
        Returns:
            Etiquetas del bucle eliminado, o None si la pila está vacía
        """
        if not self._loop_stack:
            return None
        return self._loop_stack.pop()
    
    def current_loop(self) -> Optional[tuple[str, str, str]]:
        """
        Obtiene las etiquetas del bucle actual sin eliminarlo.
        
        Returns:
            Tupla con etiquetas del bucle actual, o None si no hay bucles
        """
        if not self._loop_stack:
            return None
        return self._loop_stack[-1]
    
    def get_break_label(self) -> Optional[str]:
        """
        Obtiene la etiqueta de salida del bucle actual.
        
        Returns:
            Etiqueta de fin del bucle, o None si no hay bucles
        """
        loop = self.current_loop()
        return loop[1] if loop else None
    
    def get_continue_label(self) -> Optional[str]:
        """
        Obtiene la etiqueta de continuación del bucle actual.
        
        Returns:
            Etiqueta de continue del bucle, o None si no hay bucles
        """
        loop = self.current_loop()
        return loop[2] if loop else None
    
    def in_loop(self) -> bool:
        """
        Verifica si estamos dentro de un bucle.
        
        Returns:
            True si hay al menos un bucle en la pila
        """
        return len(self._loop_stack) > 0
    
    def loop_depth(self) -> int:
        """
        Obtiene el nivel de anidamiento de bucles.
        
        Returns:
            Número de bucles anidados
        """
        return len(self._loop_stack)
"""
Gestor de etiquetas para control de flujo en código intermedio.

Genera etiquetas únicas para saltos, bucles y estructuras de control.
"""

from typing import Dict, Optional


class LabelManager:
    """
    Gestor de etiquetas para control de flujo.
    
    Genera nombres únicos para etiquetas y mantiene contadores
    separados para diferentes tipos de estructuras de control.
    
    Ejemplo:
        label_mgr = LabelManager()
        L0 = label_mgr.new_label()           # "L0"
        L_IF_0 = label_mgr.new_label("IF")   # "L_IF_0"
        L_WHILE_0 = label_mgr.new_label("WHILE")  # "L_WHILE_0"
    """
    
    def __init__(self, prefix: str = "L"):
        """
        Inicializa el gestor de etiquetas.
        
        Args:
            prefix: Prefijo base para las etiquetas (default: "L")
        """
        self._prefix = prefix
        self._global_counter = 0
        self._type_counters: Dict[str, int] = {}
    
    def new_label(self, label_type: Optional[str] = None) -> str:
        """
        Genera una nueva etiqueta única.
        
        Args:
            label_type: Tipo de etiqueta (ej: "IF", "WHILE", "FOR")
                       Si es None, usa contador global
        
        Returns:
            Nombre de la etiqueta (ej: "L0", "L_IF_0", "L_WHILE_1")
        """
        if label_type is None:
            # Etiqueta genérica
            label = f"{self._prefix}{self._global_counter}"
            self._global_counter += 1
            return label
        
        # Etiqueta con tipo específico
        label_type = label_type.upper()
        if label_type not in self._type_counters:
            self._type_counters[label_type] = 0
        
        label = f"{self._prefix}_{label_type}_{self._type_counters[label_type]}"
        self._type_counters[label_type] += 1
        return label
    
    def new_label_pair(self, label_type: str) -> tuple[str, str]:
        """
        Genera un par de etiquetas para estructuras de control.
        
        Útil para if-else, while, for, etc. que necesitan
        etiquetas de inicio y fin.
        
        Args:
            label_type: Tipo de estructura (ej: "IF", "WHILE")
        
        Returns:
            Tupla con (etiqueta_inicio, etiqueta_fin)
        """
        start = self.new_label(label_type)
        end = self.new_label(label_type)
        return (start, end)
    
    def reset(self):
        """
        Reinicia todos los contadores de etiquetas.
        
        Útil al comenzar la generación de código para una nueva función.
        """
        self._global_counter = 0
        self._type_counters.clear()
    
    def get_stats(self) -> dict:
        """
        Obtiene estadísticas del uso de etiquetas.
        
        Returns:
            Diccionario con contadores por tipo
        """
        return {
            "global": self._global_counter,
            "by_type": self._type_counters.copy()
        }
    
    def __str__(self) -> str:
        """Representación en string del estado del gestor."""
        stats = self.get_stats()
        return f"LabelManager(global={stats['global']}, types={stats['by_type']})"


class LoopLabelManager:
    """
    Gestor especializado para etiquetas de bucles.
    
    Mantiene una pila de etiquetas para bucles anidados,
    útil para manejar break y continue correctamente.
    """
    
    def __init__(self, label_manager: LabelManager):
        """
        Inicializa el gestor de etiquetas de bucles.
        
        Args:
            label_manager: Gestor de etiquetas base
        """
        self._label_mgr = label_manager
        self._loop_stack: list[tuple[str, str, str]] = []
    
    def push_loop(self, loop_type: str) -> tuple[str, str, str]:
        """
        Crea etiquetas para un nuevo bucle y las apila.
        
        Args:
            loop_type: Tipo de bucle ("WHILE", "FOR", "FOREACH", "DO_WHILE")
        
        Returns:
            Tupla con (etiqueta_inicio, etiqueta_fin, etiqueta_continue)
        """
        start = self._label_mgr.new_label(loop_type)
        end = self._label_mgr.new_label(loop_type)
        continue_label = self._label_mgr.new_label(f"{loop_type}_CONT")
        
        loop_labels = (start, end, continue_label)
        self._loop_stack.append(loop_labels)
        return loop_labels
    
    def pop_loop(self) -> Optional[tuple[str, str, str]]:
        """
        Elimina el bucle actual de la pila.
        
        Returns:
            Etiquetas del bucle eliminado, o None si la pila está vacía
        """
        if not self._loop_stack:
            return None
        return self._loop_stack.pop()
    
    def current_loop(self) -> Optional[tuple[str, str, str]]:
        """
        Obtiene las etiquetas del bucle actual sin eliminarlo.
        
        Returns:
            Tupla con etiquetas del bucle actual, o None si no hay bucles
        """
        if not self._loop_stack:
            return None
        return self._loop_stack[-1]
    
    def get_break_label(self) -> Optional[str]:
        """
        Obtiene la etiqueta de salida del bucle actual.
        
        Returns:
            Etiqueta de fin del bucle, o None si no hay bucles
        """
        loop = self.current_loop()
        return loop[1] if loop else None
    
    def get_continue_label(self) -> Optional[str]:
        """
        Obtiene la etiqueta de continuación del bucle actual.
        
        Returns:
            Etiqueta de continue del bucle, o None si no hay bucles
        """
        loop = self.current_loop()
        return loop[2] if loop else None
    
    def in_loop(self) -> bool:
        """
        Verifica si estamos dentro de un bucle.
        
        Returns:
            True si hay al menos un bucle en la pila
        """
        return len(self._loop_stack) > 0
    
    def loop_depth(self) -> int:
        """
        Obtiene el nivel de anidamiento de bucles.
        
        Returns:
            Número de bucles anidados
        """
        return len(self._loop_stack)
