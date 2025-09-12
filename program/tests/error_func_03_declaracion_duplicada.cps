// Error: Declaración duplicada de función
function test(): integer {
    return 1;
}

function test(): string {  // ERROR: función duplicada
    return "Hola";
}

function main() {
    print(test());
}
