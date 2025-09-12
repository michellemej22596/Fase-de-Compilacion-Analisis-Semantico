// Error: Número/tipo de argumentos incorrecto
function suma(a: integer, b: integer): integer {
    return a + b;
}

function main() {
    let resultado: integer = suma(5);  // ERROR: faltan argumentos
}
