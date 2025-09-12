// Error: Tipo de retorno incorrecto
function obtener_numero(): integer {
    return "Hola";  // ERROR: retorna string en lugar de integer
}

function main() {
    let num: integer = obtener_numero();
}
