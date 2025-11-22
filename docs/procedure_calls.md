# Algoritmo de Llamadas a Procedimientos y Retornos

## Introducción

Este documento describe el algoritmo implementado para manejar llamadas a funciones y retornos en el compilador de Compiscript. El sistema sigue las convenciones estándar de MIPS32 con optimizaciones para eficiencia y simplicidad.

## Convención de Llamada MIPS32

El compilador implementa una **convención híbrida** que combina el uso de registros para los primeros argumentos con el stack para argumentos adicionales y variables locales.

### Registros Involucrados

- **`$a0-$a3`**: Primeros 4 argumentos de función
- **`$v0-$v1`**: Valores de retorno (usamos principalmente `$v0`)
- **`$ra`**: Dirección de retorno (Return Address)
- **`$sp`**: Stack Pointer (apunta al tope del stack)
- **`$fp`**: Frame Pointer (apunta a la base del frame actual)

## Estructura del Stack Frame

Cada llamada a función crea un **stack frame** (registro de activación) con la siguiente estructura:

\`\`\`
Direcciones Altas
+------------------+
| Param N          |  ← Parámetros 5+ (si existen)
| Param 6          |
| Param 5          |
+------------------+  ← $sp antes de la llamada
| Return Address   |  offset: 4 desde $fp
+------------------+
| Saved FP         |  offset: 0 desde $fp
+------------------+  ← $fp (Frame Pointer actual)
| Variables        |  ← Variables locales y temporales
| Locales          |
+------------------+  ← $sp (Stack Pointer actual)
Direcciones Bajas
\`\`\`

## Algoritmo de Llamada a Función

### Fase 1: Preparación de Parámetros (PARAM)

El cuádruplo `PARAM` se traduce de forma diferente según la posición del parámetro:

#### Parámetros 1-4: Uso de Registros
```assembly
# Cuádruplo: PARAM arg1
move $a0, <valor_arg1>

# Cuádruplo: PARAM arg2
move $a1, <valor_arg2>

# Cuádruplo: PARAM arg3
move $a2, <valor_arg3>

# Cuádruplo: PARAM arg4
move $a3, <valor_arg4>
