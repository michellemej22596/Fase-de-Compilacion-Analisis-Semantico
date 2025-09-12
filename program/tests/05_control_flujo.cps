// Demuestra: if/else, while, for, break, continue

function main(): void {
    let x: integer = 5;
    
    // If/else
    if (x > 0) {
        print("Positivo");
    } else {
        print("No positivo");
    }
    
    // While con break
    let i: integer = 0;
    while (i < 10) {
        if (i == 3) {
            break;
        }
        print("i = " + i);
        i = i + 1;
    }
    
    // For con continue
    let j: integer = 0;
    for (; j < 5; j = j + 1) {
        if (j == 2) {
            continue;
        }
        print("j = " + j);
    }
}
