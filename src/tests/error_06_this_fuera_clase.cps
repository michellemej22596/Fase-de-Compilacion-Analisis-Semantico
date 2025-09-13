function funcionGlobal(): void {
    print(this.nombre);  // ERROR: this fuera de clase
}

function main(): void {
    funcionGlobal();
}
