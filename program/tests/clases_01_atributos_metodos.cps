// Test: Validación de atributos y métodos existentes
class Calculadora {
    let valor: integer;
    
    function sumar(n: integer): integer {
        return valor + n;
    }
}

function main() {
    let calc: Calculadora = new Calculadora();
    calc.valor = 10;                    // Acceso a atributo existente ✓
    let resultado: integer = calc.sumar(5);  // Llamada a método existente ✓
    print(resultado);
}
