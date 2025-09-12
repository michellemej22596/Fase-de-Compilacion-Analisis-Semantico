// Test: Validación de número y tipo de argumentos
function suma(a: integer, b: integer): integer {
    return a + b;
}

function saludo(nombre: string): string {
    return "Hola " + nombre;
}

function main() {
    let resultado: integer = suma(5, 3);        // 2 argumentos integer ✓
    let mensaje: string = saludo("Juan");       // 1 argumento string ✓
    print(resultado);
}
