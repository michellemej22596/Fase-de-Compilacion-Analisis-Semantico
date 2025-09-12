// Demuestra: promoción de tipos, operaciones mixtas

function main(): void {
    let entero: integer = 5;
    let decimal: float = 3.14;
    
    // Promoción automática integer -> float
    let resultado: float = entero + decimal;
    print("Resultado: " + resultado);
    
    // Comparaciones entre tipos compatibles
    let mayor: boolean = decimal > entero;
    print("Mayor: " + mayor);
    
    // Concatenación con strings
    let mensaje: string = "El número es: " + entero;
    print(mensaje);
}
