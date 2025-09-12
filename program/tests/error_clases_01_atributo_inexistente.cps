// Error: Atributo inexistente
class Persona {
    let nombre: string;
}

function main() {
    let p: Persona = new Persona();
    p.edad = 25;  // ERROR: atributo 'edad' no existe
}
