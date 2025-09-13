// Test: Asignación con tipos correctos
function main() {
    let numero: integer = 42;
    let texto: string = "Hola";
    let bandera: boolean = true;
    let decimal: float = 3.14;
    
    numero = 100;           // integer a integer ✓
    texto = "Mundo";        // string a string ✓
    bandera = false;        // boolean a boolean ✓
    decimal = 2.71;         // float a float ✓
    
    print(numero);
}
