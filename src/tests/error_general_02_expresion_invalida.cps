// Error: Expresión inválida
function test(): integer {
    return 5;
}

function main() {
    let resultado: integer = test * 2;  // ERROR: multiplicar función por número
}
