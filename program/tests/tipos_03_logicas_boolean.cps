// Test: Operaciones lógicas con boolean (&&, ||, !)
function main() {
    let p: boolean = true;
    let q: boolean = false;
    
    let and_op: boolean = p && q;   // false
    let or_op: boolean = p || q;    // true
    let not_p: boolean = !p;        // false
    let not_q: boolean = !q;        // true
    
    print(and_op);
}
