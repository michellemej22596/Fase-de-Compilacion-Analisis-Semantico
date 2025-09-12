// Demuestra: operadores +, -, *, /, %, &&, ||, !

function main(): void {
    let a: integer = 10;
    let b: integer = 3;
    
    // Operaciones aritméticas
    let suma: integer = a + b;
    let resta: integer = a - b;
    let multiplicacion: integer = a * b;
    let division: integer = a / b;
    let modulo: integer = a % b;
    
    // Operaciones lógicas
    let verdadero: boolean = true;
    let falso: boolean = false;
    let y_logico: boolean = verdadero && falso;
    let o_logico: boolean = verdadero || falso;
    let negacion: boolean = !verdadero;
    
    print("Suma: " + suma);
    print("Y lógico: " + y_logico);
}
