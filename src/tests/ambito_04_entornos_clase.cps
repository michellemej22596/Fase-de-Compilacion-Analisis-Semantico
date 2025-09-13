// Test: Entornos de símbolos para clases
class Persona {
    let nombre: string;
    let edad: integer;
    
    function saludar(): string {
        return "Hola, soy " + nombre;  // Acceso a campo de clase ✓
    }
}

function main() {
    let p: Persona = new Persona();
    p.nombre = "Juan";
    print(p.saludar());
}
