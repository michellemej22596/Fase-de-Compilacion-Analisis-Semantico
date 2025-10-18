# Lenguaje Intermedio - Código de Tres Direcciones (Cuádruplos)

## Descripción General

Este documento describe el lenguaje intermedio utilizado en el compilador de Compiscript. El lenguaje intermedio se basa en **código de tres direcciones** representado mediante **cuádruplos**, que sirve como puente entre el análisis semántico y la generación de código MIPS assembler.

## Objetivos del Lenguaje Intermedio

1. **Independencia de la arquitectura**: Facilitar la portabilidad del compilador
2. **Optimización**: Permitir transformaciones y optimizaciones antes de generar código máquina
3. **Simplicidad**: Operaciones atómicas que facilitan la traducción a assembler
4. **Verificación**: Código más fácil de analizar y validar

## Formato de Cuádruplos

Cada cuádruplo tiene la siguiente estructura:

\`\`\`
(operador, arg1, arg2, resultado)
\`\`\`

### Componentes

- **operador**: Tipo de operación a realizar
- **arg1**: Primer operando (puede ser variable, temporal, constante o etiqueta)
- **arg2**: Segundo operando (puede ser variable, temporal, constante, etiqueta o None)
- **resultado**: Destino del resultado (variable, temporal o etiqueta)

### Ejemplo Visual

\`\`\`

Código Fuente:     x = a + b * c;


Cuádruplos:

(0)  (MUL,  b,    c,    t0)

(1)  (ADD,  a,    t0,   t1)

(2)  (ASSIGN, t1, None, x)

\`\`\`

## 🔧 Operadores Soportados

### Operadores Aritméticos

| Operador | Descripción | Formato | Ejemplo |
|----------|-------------|---------|---------|
| `ADD` | Suma | `(ADD, arg1, arg2, result)` | `(ADD, a, b, t0)` |
| `SUB` | Resta | `(SUB, arg1, arg2, result)` | `(SUB, x, 5, t1)` |
| `MUL` | Multiplicación | `(MUL, arg1, arg2, result)` | `(MUL, t0, 2, t2)` |
| `DIV` | División | `(DIV, arg1, arg2, result)` | `(DIV, a, b, t3)` |
| `MOD` | Módulo | `(MOD, arg1, arg2, result)` | `(MOD, x, 10, t4)` |
| `NEG` | Negación unaria | `(NEG, arg1, None, result)` | `(NEG, a, None, t5)` |

### Operadores Lógicos

| Operador | Descripción | Formato | Ejemplo |
|----------|-------------|---------|---------|
| `AND` | AND lógico | `(AND, arg1, arg2, result)` | `(AND, a, b, t0)` |
| `OR` | OR lógico | `(OR, arg1, arg2, result)` | `(OR, x, y, t1)` |
| `NOT` | NOT lógico | `(NOT, arg1, None, result)` | `(NOT, flag, None, t2)` |

### Operadores Relacionales

| Operador | Descripción | Formato | Ejemplo |
|----------|-------------|---------|---------|
| `LT` | Menor que | `(LT, arg1, arg2, result)` | `(LT, a, b, t0)` |
| `LE` | Menor o igual | `(LE, arg1, arg2, result)` | `(LE, x, 10, t1)` |
| `GT` | Mayor que | `(GT, arg1, arg2, result)` | `(GT, y, 0, t2)` |
| `GE` | Mayor o igual | `(GE, arg1, arg2, result)` | `(GE, z, 5, t3)` |
| `EQ` | Igual | `(EQ, arg1, arg2, result)` | `(EQ, a, b, t4)` |
| `NE` | No igual | `(NE, arg1, arg2, result)` | `(NE, x, 0, t5)` |

### Operadores de Asignación y Copia

| Operador | Descripción | Formato | Ejemplo |
|----------|-------------|---------|---------|
| `ASSIGN` | Asignación simple | `(ASSIGN, arg1, None, result)` | `(ASSIGN, t0, None, x)` |
| `COPY` | Copia de valor | `(COPY, arg1, None, result)` | `(COPY, a, None, b)` |

### Operadores de Control de Flujo

| Operador | Descripción | Formato | Ejemplo |
|----------|-------------|---------|---------|
| `GOTO` | Salto incondicional | `(GOTO, label, None, None)` | `(GOTO, L1, None, None)` |
| `IF_FALSE` | Salto condicional | `(IF_FALSE, cond, label, None)` | `(IF_FALSE, t0, L2, None)` |
| `IF_TRUE` | Salto condicional | `(IF_TRUE, cond, label, None)` | `(IF_TRUE, t1, L3, None)` |
| `LABEL` | Etiqueta de destino | `(LABEL, name, None, None)` | `(LABEL, L1, None, None)` |

### Operadores de Funciones

| Operador | Descripción | Formato | Ejemplo |
|----------|-------------|---------|---------|
| `PARAM` | Pasar parámetro | `(PARAM, arg, None, None)` | `(PARAM, x, None, None)` |
| `CALL` | Llamar función | `(CALL, func, n_params, result)` | `(CALL, foo, 2, t0)` |
| `RETURN` | Retornar valor | `(RETURN, value, None, None)` | `(RETURN, t0, None, None)` |
| `BEGIN_FUNC` | Inicio de función | `(BEGIN_FUNC, name, None, None)` | `(BEGIN_FUNC, foo, None, None)` |
| `END_FUNC` | Fin de función | `(END_FUNC, name, None, None)` | `(END_FUNC, foo, None, None)` |

### Operadores de Arrays

| Operador | Descripción | Formato | Ejemplo |
|----------|-------------|---------|---------|
| `ARRAY_LOAD` | Cargar elemento | `(ARRAY_LOAD, array, index, result)` | `(ARRAY_LOAD, arr, i, t0)` |
| `ARRAY_STORE` | Guardar elemento | `(ARRAY_STORE, value, array, index)` | `(ARRAY_STORE, t0, arr, i)` |
| `ARRAY_NEW` | Crear array | `(ARRAY_NEW, size, None, result)` | `(ARRAY_NEW, 10, None, arr)` |

### Operadores de Objetos

| Operador | Descripción | Formato | Ejemplo |
|----------|-------------|---------|---------|
| `NEW` | Crear objeto | `(NEW, class, None, result)` | `(NEW, Point, None, obj)` |
| `GET_FIELD` | Obtener campo | `(GET_FIELD, object, field, result)` | `(GET_FIELD, obj, x, t0)` |
| `SET_FIELD` | Asignar campo | `(SET_FIELD, value, object, field)` | `(SET_FIELD, t0, obj, x)` |
| `CALL_METHOD` | Llamar método | `(CALL_METHOD, object, method, result)` | `(CALL_METHOD, obj, move, None)` |

## Convenciones de Nombres

### Variables Temporales

- **Formato**: `t0`, `t1`, `t2`, ..., `tn`
- **Propósito**: Almacenar resultados intermedios de expresiones
- **Gestión**: Pool de reciclaje para reutilización eficiente
- **Ejemplo**: `t0 = a + b`, luego `t0` puede ser reutilizado

### Etiquetas

- **Formato**: `L0`, `L1`, `L2`, ..., `Ln`
- **Propósito**: Marcar puntos de salto en el código
- **Tipos**:
  - `L_IF_n`: Etiquetas para estructuras if
  - `L_WHILE_n`: Etiquetas para bucles while
  - `L_FOR_n`: Etiquetas para bucles for
  - `L_FUNC_n`: Etiquetas para funciones

### Variables de Usuario

- **Formato**: Nombre original del código fuente
- **Ejemplo**: `x`, `counter`, `myVariable`

### Constantes

- **Formato**: Valor literal
- **Ejemplos**: `5`, `3.14`, `"hello"`, `true`, `false`, `null`

## Ejemplos de Traducción (Para Compiscript)

### Ejemplo 1: Expresión Aritmética Simple

```plaintext
// Código Compiscript
let x: integer = (a + b) * (c - d);

// Cuádruplos
(0)  (ADD,    a,    b,    t0)
(1)  (SUB,    c,    d,    t1)
(2)  (MUL,    t0,   t1,   t2)
(3)  (ASSIGN, t2,   None, x)
```

### Ejemplo 2: Estructura If-Else

```plaintext
// Código Compiscript
let x: integer = 10;
if (x > 5) {
    print(x);
} else {
    print(0);
}

// Cuádruplos
(0)  (GT,       x,    5,    t0)
(1)  (IF_FALSE, t0,   L1,   None)
(2)  (PARAM,    x,    None, None)
(3)  (CALL,     print, 1,   None)
(4)  (GOTO,     L2,   None, None)
(5)  (LABEL,    L1,   None, None)
(6)  (PARAM,    0,    None, None)
(7)  (CALL,     print, 1,   None)
(8)  (LABEL,    L2,   None, None)
```

### Ejemplo 3: Bucle While

```plaintext
// Código Compiscript
let i: integer = 0;
while (i < 5) {
    print(i);
    i = i + 1;
}

// Cuádruplos
(0)  (ASSIGN,   0,         None, i)
(1)  (LABEL,    L_WHILE_0, None, None)
(2)  (LT,       i,         5,    t0)
(3)  (IF_FALSE, t0,        L_WHILE_1, None)
(4)  (PARAM,    i,         None, None)
(5)  (CALL,     print,     1,    None)
(6)  (ADD,      i,         1,    t1)
(7)  (ASSIGN,   t1,        None, i)
(8)  (GOTO,     L_WHILE_0, None, None)
(9)  (LABEL,    L_WHILE_1, None, None)
```

### Ejemplo 4: Bucle For

```plaintext
// Código Compiscript
let suma: integer = 0;
for (let i: integer = 0; i < 10; i = i + 1) {
    suma = suma + i;
}

// Cuádruplos
(0)  (ASSIGN,   0,         None, suma)
(1)  (ASSIGN,   0,         None, i)
(2)  (LABEL,    L_FOR_0,   None, None)
(3)  (LT,       i,         10,   t0)
(4)  (IF_FALSE, t0,        L_FOR_1, None)
(5)  (ADD,      suma,      i,    t1)
(6)  (ASSIGN,   t1,        None, suma)
(7)  (ADD,      i,         1,    t2)
(8)  (ASSIGN,   t2,        None, i)
(9)  (GOTO,     L_FOR_0,   None, None)
(10) (LABEL,    L_FOR_1,   None, None)
```

### Ejemplo 5: Llamada a Función

```plaintext
// Código Compiscript
function factorial(n: integer): integer {
    if (n <= 1) {
        return 1;
    } else {
        return n * factorial(n - 1);
    }
}

function main() {
    let resultado: integer = factorial(5);
    print(resultado);
}

// Cuádruplos
(0)  (BEGIN_FUNC, factorial, None, None)
(1)  (LE,         n,         1,    t0)
(2)  (IF_FALSE,   t0,        L1,   None)
(3)  (RETURN,     1,         None, None)
(4)  (GOTO,       L2,        None, None)
(5)  (LABEL,      L1,        None, None)
(6)  (SUB,        n,         1,    t1)
(7)  (PARAM,      t1,        None, None)
(8)  (CALL,       factorial, 1,    t2)
(9)  (MUL,        n,         t2,   t3)
(10) (RETURN,     t3,        None, None)
(11) (LABEL,      L2,        None, None)
(12) (END_FUNC,   factorial, None, None)
(13) (BEGIN_FUNC, main,      None, None)
(14) (PARAM,      5,         None, None)
(15) (CALL,       factorial, 1,    t4)
(16) (ASSIGN,     t4,        None, resultado)
(17) (PARAM,      resultado, None, None)
(18) (CALL,       print,     1,    None)
(19) (END_FUNC,   main,      None, None)
```

### Ejemplo 6: Acceso a Arrays

```plaintext
// Código Compiscript
function main() {
    let numeros: integer[] = [1, 2, 3, 4, 5];
    let suma: integer = 0;
    let i: integer = 0;
    
    while (i < 5) {
        suma = suma + numeros[i];
        i = i + 1;
    }
    
    print(suma);
}

// Cuádruplos
(0)  (BEGIN_FUNC,  main,      None, None)
(1)  (ARRAY_NEW,   5,         None, numeros)
(2)  (ARRAY_STORE, 1,         numeros, 0)
(3)  (ARRAY_STORE, 2,         numeros, 1)
(4)  (ARRAY_STORE, 3,         numeros, 2)
(5)  (ARRAY_STORE, 4,         numeros, 3)
(6)  (ARRAY_STORE, 5,         numeros, 4)
(7)  (ASSIGN,      0,         None, suma)
(8)  (ASSIGN,      0,         None, i)
(9)  (LABEL,       L_WHILE_0, None, None)
(10) (LT,          i,         5,    t0)
(11) (IF_FALSE,    t0,        L_WHILE_1, None)
(12) (ARRAY_LOAD,  numeros,   i,    t1)
(13) (ADD,         suma,      t1,   t2)
(14) (ASSIGN,      t2,        None, suma)
(15) (ADD,         i,         1,    t3)
(16) (ASSIGN,      t3,        None, i)
(17) (GOTO,        L_WHILE_0, None, None)
(18) (LABEL,       L_WHILE_1, None, None)
(19) (PARAM,       suma,      None, None)
(20) (CALL,        print,     1,    None)
(21) (END_FUNC,    main,      None, None)
```

### Ejemplo 7: Clases y Objetos

```plaintext
// Código Compiscript
class Punto {
    let x: integer;
    let y: integer;
    
    function distancia(): integer {
        return x * x + y * y;
    }
}

function main() {
    let p: Punto = new Punto();
    p.x = 3;
    p.y = 4;
    let d: integer = p.distancia();
    print(d);
}

// Cuádruplos
(0)  (BEGIN_FUNC,  Punto.distancia, None, None)
(1)  (GET_FIELD,   this,           x,    t0)
(2)  (GET_FIELD,   this,           x,    t1)
(3)  (MUL,         t0,             t1,   t2)
(4)  (GET_FIELD,   this,           y,    t3)
(5)  (GET_FIELD,   this,           y,    t4)
(6)  (MUL,         t3,             t4,   t5)
(7)  (ADD,         t2,             t5,   t6)
(8)  (RETURN,      t6,             None, None)
(9)  (END_FUNC,    Punto.distancia, None, None)
(10) (BEGIN_FUNC,  main,           None, None)
(11) (NEW,         Punto,          None, p)
(12) (SET_FIELD,   3,              p,    x)
(13) (SET_FIELD,   4,              p,    y)
(14) (PARAM,       p,              None, None)
(15) (CALL_METHOD, p,              distancia, t7)
(16) (ASSIGN,      t7,             None, d)
(17) (PARAM,       d,              None, None)
(18) (CALL,        print,          1,    None)
(19) (END_FUNC,    main,           None, None)
```

### Ejemplo 8: Expresión Ternaria

```plaintext
// Código Compiscript
let a: integer = 10;
let b: integer = 20;
let max: integer = a > b ? a : b;
print(max);

// Cuádruplos
(0)  (ASSIGN,   10,   None, a)
(1)  (ASSIGN,   20,   None, b)
(2)  (GT,       a,    b,    t0)
(3)  (IF_FALSE, t0,   L1,   None)
(4)  (ASSIGN,   a,    None, t1)
(5)  (GOTO,     L2,   None, None)
(6)  (LABEL,    L1,   None, None)
(7)  (ASSIGN,   b,    None, t1)
(8)  (LABEL,    L2,   None, None)
(9)  (ASSIGN,   t1,   None, max)
(10) (PARAM,    max,  None, None)
(11) (CALL,     print, 1,   None)
```

### Ejemplo 9: Foreach (Específico de Compiscript)

```plaintext
// Código Compiscript
function main() {
    let numeros: integer[] = [10, 20, 30, 40];
    let suma: integer = 0;
    
    foreach (num in numeros) {
        suma = suma + num;
    }
    
    print(suma);
}

// Cuádruplos
(0)  (BEGIN_FUNC,  main,      None, None)
(1)  (ARRAY_NEW,   4,         None, numeros)
(2)  (ARRAY_STORE, 10,        numeros, 0)
(3)  (ARRAY_STORE, 20,        numeros, 1)
(4)  (ARRAY_STORE, 30,        numeros, 2)
(5)  (ARRAY_STORE, 40,        numeros, 3)
(6)  (ASSIGN,      0,         None, suma)
(7)  (ASSIGN,      0,         None, _iter_idx)
(8)  (ASSIGN,      4,         None, _len)
(9)  (LABEL,       L_FOREACH_0, None, None)
(10) (GE,          _iter_idx, _len, t0)
(11) (IF_TRUE,     t0,        L_FOREACH_1, None)
(12) (ARRAY_LOAD,  numeros,   _iter_idx, num)
(13) (ADD,         suma,      num,   t1)
(14) (ASSIGN,      t1,        None, suma)
(15) (ADD,         _iter_idx, 1,     t2)
(16) (ASSIGN,      t2,        None, _iter_idx)
(17) (GOTO,        L_FOREACH_0, None, None)
(18) (LABEL,       L_FOREACH_1, None, None)
(19) (PARAM,       suma,      None, None)
(20) (CALL,        print,     1,    None)
(21) (END_FUNC,    main,      None, None)
```

## Gestión de Variables Temporales

### Algoritmo de Asignación

1. **Solicitud**: Cuando se necesita un temporal, se solicita al gestor
2. **Asignación**: Se asigna el próximo temporal disponible del pool
3. **Uso**: El temporal se marca como "en uso"
4. **Liberación**: Cuando ya no se necesita, se devuelve al pool
5. **Reciclaje**: El temporal queda disponible para futuras asignaciones

### Pool de Temporales

\`\`\`python
class TempManager:
    def __init__(self):
        self.counter = 0
        self.available = []  # Pool de temporales libres
        self.in_use = set()  # Temporales actualmente en uso
    
    def new_temp(self):
        if self.available:
            temp = self.available.pop()
        else:
            temp = f"t{self.counter}"
            self.counter += 1
        self.in_use.add(temp)
        return temp
    
    def free_temp(self, temp):
        if temp in self.in_use:
            self.in_use.remove(temp)
            self.available.append(temp)
\`\`\`

### Ejemplo de Reciclaje

\`\`\`

// Código Fuente

let a = x + y;

let b = z * w;

let c = a + b;


// Cuádruplos (con reciclaje)

(0)  (ADD,    x,  y,    t0)    // t0 asignado

(1)  (ASSIGN, t0, None, a)

(2)  (MUL,    z,  w,    t0)    // t0 reciclado (ya no se usa en línea 1)

(3)  (ASSIGN, t0, None, b)

(4)  (ADD,    a,  b,    t0)    // t0 reciclado nuevamente

(5)  (ASSIGN, t0, None, c)

\`\`\`

## Supuestos y Limitaciones

### Supuestos

1. **Tipos estáticos**: Los tipos se conocen en tiempo de compilación
2. **Memoria suficiente**: Se asume memoria suficiente para temporales
3. **Evaluación de izquierda a derecha**: Las expresiones se evalúan en orden
4. **Short-circuit**: Los operadores lógicos `&&` y `||` usan evaluación perezosa
5. **Parámetros por valor**: Los argumentos se pasan por valor (copia)

### Limitaciones

1. **Sin optimización**: El código intermedio no está optimizado
2. **Temporales ilimitados**: No hay límite en el número de temporales (se optimizará en MIPS)
3. **Sin análisis de flujo**: No se realiza análisis de flujo de datos
4. **Sin eliminación de código muerto**: Se generan todos los cuádruplos sin optimización

## Próximos Pasos

Este lenguaje intermedio será traducido a código MIPS assembler en la siguiente fase, donde se considerarán:

1. **Asignación de registros**: Mapeo de temporales a registros MIPS
2. **Gestión de memoria**: Stack frames y registros de activación
3. **Convenciones de llamada**: Paso de parámetros y valores de retorno
4. **Optimizaciones**: Eliminación de código muerto, propagación de constantes
