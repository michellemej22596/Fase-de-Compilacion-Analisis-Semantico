// Demuestra: declaración de arrays, acceso por índice, foreach

function main(): void {
    let numeros: integer[] = [1, 2, 3, 4, 5];
    let nombres: string[] = ["Ana", "Bob", "Carlos"];
    
    // Acceso por índice
    print("Primer número: " + numeros[0]);
    print("Segundo nombre: " + nombres[1]);
    
    // Modificación
    numeros[0] = 10;
    print("Número modificado: " + numeros[0]);
    
    // Foreach
    foreach (num in numeros) {
        print("Número: " + num);
    }
    
    foreach (nombre in nombres) {
        print("Nombre: " + nombre);
    }
}
