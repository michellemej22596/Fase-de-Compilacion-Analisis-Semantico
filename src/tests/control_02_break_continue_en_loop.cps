// Test: break y continue dentro de loops
function main() {
    for (let i: integer = 0; i < 10; i = i + 1) {
        if (i == 3) {
            continue;  // continue dentro de loop ✓
        }
        if (i == 7) {
            break;     // break dentro de loop ✓
        }
        print(i);
    }
}
