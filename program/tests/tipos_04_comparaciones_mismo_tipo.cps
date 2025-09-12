// Test: Comparaciones entre tipos compatibles (==, !=, <, <=, >, >=)
function main() {
    let a: integer = 10;
    let b: integer = 5;
    
    let igual: boolean = a == b;     // false
    let diferente: boolean = a != b; // true
    let menor: boolean = a < b;      // false
    let mayor: boolean = a > b;      // true
    let menor_igual: boolean = a <= b; // false
    let mayor_igual: boolean = a >= b; // true
    
    print(igual);
}
