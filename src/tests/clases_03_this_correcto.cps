// Test: this en ámbito correcto
class Contador {
    let valor: integer;
    
    function incrementar() {
        this.valor = this.valor + 1;  // this dentro de clase ✓
    }
    
    function obtener(): integer {
        return this.valor;            // this dentro de clase ✓
    }
}

function main() {
    let c: Contador = new Contador();
    c.valor = 0;
    c.incrementar();
    print(c.obtener());
}
