// Test: Función recursiva
function factorial(n: integer): integer {
    if (n <= 1) {
        return 1;
    }
    return n * factorial(n - 1);  // Llamada recursiva ✓
}

function main() {
    let resultado: integer = factorial(5);
    print(resultado);
}
