// Demuestra: herencia de clases, override de métodos

class Animal {
    var nombre: string;
    
    function init(n: string): void {
        this.nombre = n;
    }
    
    function hacerSonido(): void {
        print(this.nombre + " hace un sonido");
    }
}

class Perro : Animal {
    function hacerSonido(): void {
        print(this.nombre + " ladra: Guau!");
    }
    
    function moverCola(): void {
        print(this.nombre + " mueve la cola");
    }
}

function main(): void {
    let animal: Animal = new Animal();
    animal.init("Genérico");
    animal.hacerSonido();
    
    let perro: Perro = new Perro();
    perro.init("Rex");
    perro.hacerSonido();
    perro.moverCola();
}
