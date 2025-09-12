// Test: Expresiones con sentido semántico
function main() {
    let a: integer = 5;
    let b: integer = 3;
    let texto: string = "Hola";
    
    let suma: integer = a + b;           // Suma de enteros ✓
    let concatenacion: string = texto + " Mundo";  // Concatenación ✓
    let comparacion: boolean = a > b;    // Comparación ✓
    
    print(suma);
}
