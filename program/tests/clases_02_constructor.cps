// Test: Constructor llamado correctamente
class Persona {
    let nombre: string;
    let edad: integer;
    
    function Persona(n: string, e: integer) {  // Constructor
        nombre = n;
        edad = e;
    }
}

function main() {
    let p: Persona = new Persona("Juan", 25);  // Constructor llamado correctamente ✓
    print(p.nombre);
}
