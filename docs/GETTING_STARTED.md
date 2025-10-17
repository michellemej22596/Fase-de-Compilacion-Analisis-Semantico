# Guía de Inicio - Compilador Compiscript
## Requisitos Previos

- **Python 3.8 o superior**
- **pip** (gestor de paquetes de Python)
- **Java 11 o superior** (para ANTLR)

## Instalación

### 1. Clonar el Repositorio

\`\`\`bash
git clone <url-del-repositorio>
cd Fase-de-Compilacion-Analisis-Semantico
\`\`\`

### 2. Crear Ambiente Virtual (Recomendado)

**En Windows:**
\`\`\`bash
python -m venv venv
venv\Scripts\activate
\`\`\`

**En Linux/Mac:**
\`\`\`bash
python3 -m venv venv
source venv/bin/activate
\`\`\`

### 3. Instalar Dependencias

\`\`\`bash
pip install -r requirements.txt
\`\`\`

Si quieres ejecutar los tests:
\`\`\`bash
pip install -r requirements-test.txt
\`\`\`

## Ejecución del IDE

### Iniciar el IDE de Streamlit

\`\`\`bash
streamlit run src/ide/app.py
\`\`\`

El IDE se abrirá automáticamente en tu navegador en `http://localhost:8501`

### Uso del IDE

1. **Escribir Código**: Escribe tu código Compiscript en el editor de texto
2. **Analizar**: Haz clic en el botón "Analizar" para compilar
3. **Ver Resultados**: Navega por las pestañas para ver:
   - **AST**: Árbol de sintaxis abstracta
   - **Tabla de Símbolos**: Variables y funciones declaradas
   - **Código Intermedio**: Cuádruplos generados (TAC)
   - **Código MIPS**: Código assembler MIPS32

### Ejemplos Incluidos

El IDE incluye ejemplos predefinidos que puedes cargar:
- Expresiones aritméticas y lógicas
- Declaraciones y asignaciones
- Estructuras de control (if/else)
- Loops (while, for, do-while)
- Funciones con parámetros
- Break y continue

## Estructura del Proyecto

\`\`\`
Fase-de-Compilacion-Analisis-Semantico/
├── src/                          # Código fuente principal

│   ├── ide/                      # IDE de Streamlit

│   │   └── app.py               # Aplicación principal

│   ├── codegen/                  # Generación de código intermedio

│   ├── mips/                     # Generación de código MIPS

│   ├── parsing/                  # Parser ANTLR

│   └── semantic/                 # Análisis semántico

├── tests/                        # Tests automatizados

├── docs/                         # Documentación

│   ├── GETTING_STARTED.md       # Esta guía

│   ├── TESTING.md               # Guía de testing

│   └── EXAMPLES_*.md            # Ejemplos de código

├── program/                      # Alias para src/

└── requirements.txt              # Dependencias
\`\`\`

## Características Principales

###  Análisis Léxico y Sintáctico
- Parser generado con ANTLR4
- Detección de errores de sintaxis
- Generación de AST

###  Análisis Semántico
- Tabla de símbolos con scopes
- Verificación de tipos
- Detección de variables no declaradas
- Validación de funciones

###  Generación de Código Intermedio
- Cuádruplos (Three-Address Code)
- Expresiones aritméticas, lógicas y relacionales
- Estructuras de control (if/else, while, for, do-while)
- Funciones con parámetros y return
- Break y continue

###  Generación de Código MIPS
- Traducción de cuádruplos a MIPS32
- Gestión de registros
- Stack frames para funciones
- Syscalls para I/O

## Ejemplos de Uso

### Ejemplo 1: Programa Simple

```compiscript
let x: integer = 5;
let y: integer = 10;

if (x < y) {
    print(y);
}
