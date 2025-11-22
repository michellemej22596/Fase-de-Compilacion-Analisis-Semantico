# Algoritmo de Asignación de Registros

## Introducción

El compilador de Compiscript implementa un sistema de asignación de registros MIPS32 que gestiona eficientemente los recursos limitados del procesador. Este documento describe el funcionamiento del algoritmo implementado en `src/mips/register_manager.py`.

## Arquitectura de Registros MIPS32

El algoritmo trabaja con los siguientes conjuntos de registros:

### Registros Temporales (`$t0-$t9`)
- **Cantidad**: 10 registros
- **Propósito**: Variables temporales generadas durante la evaluación de expresiones
- **Convención**: Caller-save (el llamador debe guardarlos antes de una llamada)
- **Uso**: Resultados intermedios, operaciones aritméticas, evaluación de condiciones

### Registros Salvados (`$s0-$s7`)
- **Cantidad**: 8 registros
- **Propósito**: Variables del programa con alcance más largo
- **Convención**: Callee-save (la función llamada debe preservarlos)
- **Uso**: Variables locales que persisten entre llamadas a funciones

### Registros Especiales
- **`$v0-$v1`**: Valores de retorno de funciones
- **`$a0-$a3`**: Primeros 4 argumentos de funciones
- **`$zero`**: Constante 0
- **`$sp`**: Stack Pointer
- **`$fp`**: Frame Pointer
- **`$ra`**: Return Address

## Algoritmo de Asignación

### 1. Asignación de Registros Temporales

El método `allocate_temp()` implementa una estrategia de tres niveles:

#### Nivel 1: Reutilización
\`\`\`python
if var_name and var_name in self.var_to_reg:
    return self.var_to_reg[var_name]
\`\`\`
- Si la variable ya tiene un registro asignado, se reutiliza inmediatamente
- Evita movimientos innecesarios y mantiene la coherencia
- Optimiza el uso de registros para variables que se referencian múltiples veces

#### Nivel 2: Asignación desde Pool
\`\`\`python
for reg in self.temp_registers:
    if reg not in self.used_temps:
        self.used_temps.add(reg)
        if var_name:
            self.var_to_reg[var_name] = reg
        return reg
\`\`\`
- Busca el primer registro temporal libre
- Usa una estrategia **FIFO** (First-In-First-Out)
- Marca el registro como usado en el conjunto `used_temps`
- Mantiene el mapeo variable → registro en `var_to_reg`

#### Nivel 3: Manejo de Saturación
\`\`\`python
raise RuntimeError("No hay registros disponibles")
\`\`\`
- Cuando se agotan los 10 registros temporales
- Actualmente lanza una excepción
- Indica que se necesita implementar *spilling* (guardar en memoria)

### 2. Asignación de Registros Salvados

El método `allocate_saved()` sigue un patrón similar pero para variables persistentes:

\`\`\`python
def allocate_saved(self, var_name: str) -> str:
    if var_name in self.var_to_reg:
        return self.var_to_reg[var_name]
    
    for reg in self.saved_registers:
        if reg not in self.used_saved:
            self.used_saved.add(reg)
            self.var_to_reg[var_name] = reg
            return reg
    
    raise RuntimeError("No hay registros salvados disponibles")
\`\`\`

### 3. Liberación de Registros

El algoritmo permite liberar registros explícitamente:

\`\`\`python
def free_temp(self, reg: str):
    if reg in self.used_temps:
        self.used_temps.remove(reg)
        for var, r in list(self.var_to_reg.items()):
            if r == reg:
                del self.var_to_reg[var]
\`\`\`

- Marca el registro como disponible
- Elimina el mapeo variable → registro
- Permite reutilización en asignaciones futuras

## Características Destacadas

### Mapeo Persistente
El diccionario `var_to_reg` mantiene un registro de qué variable está en qué registro durante toda la compilación de una función. Esto garantiza consistencia y evita cargas/almacenamientos redundantes.

### Separación de Contextos
Mantiene pools separados para temporales y salvados, respetando las convenciones de llamada MIPS32 y facilitando el manejo correcto del stack frame.

### Simplicidad y Eficiencia
El algoritmo es directo y eficiente para la mayoría de los programas, con complejidad **O(1)** para búsqueda de registros libres y **O(1)** para consultas de mapeo.

### Detección de Saturación
El sistema detecta claramente cuando se agotan los registros, permitiendo depuración efectiva y planificación de mejoras.

## Estrategias de Optimización Implementadas

### 1. Verificación Temprana de Asignación
Antes de buscar un nuevo registro, el algoritmo verifica si la variable ya tiene uno asignado, evitando búsquedas innecesarias.

### 2. Pool de Registros Disponibles
Mantiene conjuntos activos de registros libres (`used_temps`, `used_saved`) para búsqueda rápida.

### 3. Mapeo Directo
El diccionario `var_to_reg` proporciona acceso **O(1)** para consultar el registro de cualquier variable.

## Casos de Uso

### Expresión Aritmética Simple
\`\`\`python
# Cuádruplo: t0 = a + b
reg_a = allocate_saved("a")      # Asigna $s0
reg_b = allocate_saved("b")      # Asigna $s1
reg_t0 = allocate_temp("t0")     # Asigna $t0
# Genera: add $t0, $s0, $s1
\`\`\`

### Reutilización de Registro
\`\`\`python
# Primera vez: t1 = a * 2
reg_t1 = allocate_temp("t1")     # Asigna $t1

# Segunda vez: result = t1 + 3
reg_t1 = allocate_temp("t1")     # Retorna $t1 (reutiliza)
\`\`\`

### Liberación Explícita
\`\`\`python
reg = allocate_temp("temp_var")
# ... usar el registro ...
free_temp(reg)                    # Libera para reutilización
\`\`\`

## Recomendaciones para Mejoras Futuras

### Spilling a Memoria
Cuando se agoten los registros, implementar un mecanismo que:
- Seleccione una variable víctima (ej: la menos usada recientemente)
- Guarde su valor en el stack frame
- Libere el registro para nueva asignación
- Recargue el valor cuando sea necesario

### Análisis de Vida de Variables
Implementar análisis de *liveness* para determinar cuándo una variable ya no será usada:
- Liberar registros automáticamente cuando su variable "muere"
- Reducir presión sobre los registros disponibles
- Eliminar movimientos innecesarios

### Graph Coloring
Para optimización avanzada, considerar el algoritmo de coloreo de grafos:
- Construir un grafo de interferencia entre variables
- Aplicar coloreo de grafos con K colores (K = número de registros)
- Asignar colores (registros) de forma óptima
- Realizar spilling solo cuando sea estrictamente necesario

### Heurísticas de Priorización
Asignar registros salvados a variables más frecuentemente accedidas y registros temporales a cálculos intermedios efímeros.

## Conclusión

El algoritmo de asignación de registros implementado es robusto y efectivo para programas de complejidad baja a media. Su diseño modular y claro facilita futuras extensiones como spilling, análisis de liveness, y optimizaciones avanzadas basadas en graph coloring.

