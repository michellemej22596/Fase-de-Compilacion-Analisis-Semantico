// Test: Acceso correcto a variables en bloques anidados
function main() {
    let x: integer = 1;
    
    if (true) {
        let y: integer = 2;
        print(x);  // Acceso a variable del bloque padre ✓
        
        if (true) {
            let z: integer = 3;
            print(x);  // Acceso a variable del bloque abuelo ✓
            print(y);  // Acceso a variable del bloque padre ✓
            print(z);  // Acceso a variable local ✓
        }
    }
}
