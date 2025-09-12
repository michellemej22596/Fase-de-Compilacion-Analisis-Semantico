// Test: Funciones anidadas y closures
function crear_contador(): function {
    let contador: integer = 0;
    
    function incrementar(): integer {
        contador = contador + 1;  // Captura variable del entorno ✓
        return contador;
    }
    
    return incrementar;  // Retorna función anidada ✓
}

function main() {
    let cont = crear_contador();
    print(cont());
}
