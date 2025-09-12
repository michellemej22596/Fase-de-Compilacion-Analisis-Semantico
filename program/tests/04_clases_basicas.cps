// Demuestra: clases, atributos, métodos, this, instanciación

class Persona {
    var nombre: string;
    var edad: integer;
    
    function init(n: string, e: integer): void {
        this.nombre = n;
        this.edad = e;
    }
    
    function presentarse(): void {
        print("Soy " + this.nombre + " y tengo " + this.edad + " años");
    }
    
    function cumplirAnos(): void {
        this.edad = this.edad + 1;
    }
}

function main(): void {
    let persona: Persona = new Persona();
    persona.init("Luis", 30);
    persona.presentarse();
    persona.cumplirAnos();
    persona.presentarse();
}
