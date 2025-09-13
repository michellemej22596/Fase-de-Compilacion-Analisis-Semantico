// Test: Resolución de nombres según ámbito local/global
let global_var: integer = 10;

function test() {
    let local_var: integer = 20;
    print(global_var);  // Acceso a variable global ✓
    print(local_var);   // Acceso a variable local ✓
}

function main() {
    test();
    print(global_var);  // Acceso a variable global ✓
}
