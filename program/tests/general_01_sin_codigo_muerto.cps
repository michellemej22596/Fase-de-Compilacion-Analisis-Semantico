// Test: Sin código muerto
function main() {
    let x: integer = 10;
    
    if (x > 5) {
        print("Mayor");
        // No hay código después de return/break
    } else {
        print("Menor");
    }
    
    print("Fin");  // Código alcanzable ✓
}
