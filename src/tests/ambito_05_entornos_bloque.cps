// Test: Entornos de símbolos para bloques
function main() {
    let x: integer = 1;
    
    {
        let y: integer = 2;  // Variable local del bloque
        print(x);            // Acceso a variable del bloque padre ✓
        print(y);            // Acceso a variable local ✓
    }
    
    print(x);  // Variable aún accesible ✓
}
