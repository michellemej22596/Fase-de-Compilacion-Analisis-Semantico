// Error: Comparación entre tipos diferentes
function main() {
    let numero: integer = 5;
    let texto: string = "5";
    
    let resultado: boolean = numero == texto;  // ERROR: integer == string
}
