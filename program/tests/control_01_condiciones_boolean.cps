// Test: Condiciones boolean en estructuras de control
function main() {
    let activo: boolean = true;
    let contador: integer = 0;
    
    if (activo) {           // Condición boolean ✓
        print("Activo");
    }
    
    while (contador < 3) {  // Condición boolean ✓
        contador = contador + 1;
    }
    
    for (let i: integer = 0; i < 5; i = i + 1) {  // Condición boolean ✓
        print(i);
    }
}
