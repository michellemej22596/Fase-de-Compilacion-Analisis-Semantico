## 1. Expresiones Aritméticas

### Caso 1.1: Suma simple
let a: integer = 5;
let b: integer = 3;
let c: integer = a + b;


### Caso 1.2: Expresión con precedencia
let a: integer = 5;
let b: integer = 10;
let c: integer = 3;
let result: integer = a + b * c;


### Caso 1.3: Expresión con paréntesis
let a: integer = 5;
let b: integer = 10;
let c: integer = 3;
let result: integer = (a + b) * c;


### Caso 1.4: Todas las operaciones
let a: integer = 20;
let b: integer = 5;
let suma: integer = a + b;
let resta: integer = a - b;
let mult: integer = a * b;
let div: integer = a / b;
let mod: integer = a % b;


## 2. Print Statements

### Caso 2.1: Print de variable
let x: integer = 10;
let y: integer = 20;
let sum: integer = x + y;
print(sum);


### Caso 2.2: Print de expresión
let a: integer = 5;
let b: integer = 3;
print(a + b);


### Caso 2.3: Múltiples prints
let x: integer = 10;
print(x);
let y: integer = 20;
print(y);
print(x + y);


## 3. Sentencias If-Else

### Caso 3.1: If simple
let a: integer = 10;
let b: integer = 5;

if (a > b) {
    let c: integer = a + b;
}


### Caso 3.2: If-Else completo
let x: integer = 10;
let y: integer = 20;
let max: integer = 0;

if (x > y) {
    max = x;
} else {
    max = y;
}


### Caso 3.3: If-Else con print
let a: integer = 15;
let b: integer = 10;

if (a > b) {
    print(a);
} else {
    print(b);
}


## 4. Expresiones Lógicas

### Caso 4.1: Operadores relacionales
let a: integer = 10;
let b: integer = 20;

let menor: boolean = a < b;
let mayor: boolean = a > b;
let igual: boolean = a == b;
let diferente: boolean = a != b;


### Caso 4.2: AND lógico
let a: integer = 10;
let b: integer = 20;
let c: integer = 15;

if (a < b && b > c) {
    print(b);
}


### Caso 4.3: OR lógico
let x: integer = 5;
let y: integer = 10;

if (x > 10 || y > 5) {
    print(y);
}


### Caso 4.4: NOT lógico
let flag: boolean = true;

if (!flag) {
    print(0);
} else {
    print(1);
}


## 5. While Loops (Pendiente - error push_loop)

### Caso 5.1: While simple
let i: integer = 0;
let sum: integer = 0;

while (i < 5) {
    sum = sum + i;
    print(sum);
    i = i + 1;
}


## 6. For Loops (Pendiente - error push_loop)

### Caso 6.1: For simple
let total: integer = 0;

for (let i: integer = 0; i < 10; i = i + 1) {
    total = total + i;
    print(total);
}


## 7. Expresiones Complejas

### Caso 7.1: Múltiples operaciones
let a: integer = 5;
let b: integer = 10;
let c: integer = 3;
let d: integer = 2;

let result: integer = (a + b) * c - d;
print(result);


### Caso 7.2: División y módulo
let x: integer = 17;
let y: integer = 5;

let quotient: integer = x / y;
let remainder: integer = x % y;

print(quotient);
print(remainder);