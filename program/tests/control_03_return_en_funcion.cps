// Test: return dentro de función
function calcular(x: integer): integer {
    if (x < 0) {
        return 0;      // return dentro de función ✓
    }
    return x * 2;      // return dentro de función ✓
}

function main() {
    let resultado: integer = calcular(5);
    print(resultado);
}
