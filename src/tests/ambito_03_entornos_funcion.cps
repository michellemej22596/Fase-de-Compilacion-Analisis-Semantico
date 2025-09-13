// Test: Entornos de símbolos para funciones
function suma(a: integer, b: integer): integer {
    let resultado: integer = a + b;  // Variables locales de función
    return resultado;
}

function main() {
    let x: integer = suma(5, 3);
    print(x);
}
