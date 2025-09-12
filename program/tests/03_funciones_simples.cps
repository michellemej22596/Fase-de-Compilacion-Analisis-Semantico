// Demuestra: declaración de funciones, parámetros, return, recursión

function sumar(x: integer, y: integer): integer {
    return x + y;
}

function saludar(nombre: string): void {
    print("Hola " + nombre);
}

function factorial(n: integer): integer {
    if (n <= 1) {
        return 1;
    }
    return n * factorial(n - 1);
}

function main(): void {
    let resultado: integer = sumar(5, 3);
    saludar("Carlos");
    let fact: integer = factorial(4);
    print("Resultado: " + resultado);
    print("Factorial: " + fact);
}
