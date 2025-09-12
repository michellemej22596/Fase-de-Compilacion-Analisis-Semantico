// Error: Condición no boolean
function main() {
    let numero: integer = 5;
    
    if (numero) {  // ERROR: condición integer en lugar de boolean
        print("Verdadero");
    }
}
