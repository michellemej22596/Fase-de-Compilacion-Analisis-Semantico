// Test: Validación de tipo de retorno
function obtener_numero(): integer {
    return 42;  // Retorna integer ✓
}

function obtener_texto(): string {
    return "Hola";  // Retorna string ✓
}

function es_positivo(n: integer): boolean {
    return n > 0;  // Retorna boolean ✓
}

function main() {
    let num: integer = obtener_numero();
    let txt: string = obtener_texto();
    let pos: boolean = es_positivo(5);
    print(num);
}
