from __future__ import annotations  # Permite usar anotaciones de tipo hacia adelante (por ejemplo, clases que se refieren a sí mismas).
from dataclasses import dataclass  # Usamos `dataclass` para generar clases de manera más sencilla y estructurada.
from typing import Optional, Dict  # Importa los tipos `Optional` y `Dict` para tipos más flexibles.

# Clase base para representar los tipos. Los tipos se definen como clases hijas de esta.
class Type:
    name: str = "<type>"  # Nombre del tipo, se establece por defecto a "<type>".

    # Método para comparar si dos tipos son iguales
    def __eq__(self, other):
        return isinstance(other, Type) and self.name == other.name

    # Método para mostrar una representación del tipo como cadena
    def __str__(self):
        return self.name


# Tipos primitivos derivados de la clase base `Type`.
class IntType(Type):    name = "Int"    # Tipo de datos entero.
class FloatType(Type):  name = "Float"  # Tipo de datos con punto flotante.
class BoolType(Type):   name = "Bool"   # Tipo de datos booleano.
class StringType(Type): name = "String" # Tipo de datos cadena de texto.
class NullType(Type):   name = "Null"   # Tipo nulo, usado para representar la ausencia de valor.
class VoidType(Type):   name = "Void"   # Tipo vacío, usado principalmente para funciones que no devuelven valor.


# Clase que representa un tipo de arreglo, que contiene un tipo de elemento.
@dataclass(frozen=True)  # Usamos `frozen=True` para que esta clase sea inmutable (una vez creada no puede modificarse).
class ArrayType(Type):
    elem: Type  # Tipo de los elementos del arreglo.

    def __str__(self):
        return f"[{self.elem}]"  # Representación en cadena de un arreglo con el tipo de sus elementos.

    @property
    def name(self):
        return f"Array<{self.elem}>"  # Nombre del tipo, p.ej., "Array<Int>".


# Clase que representa un tipo de clase personalizada, que contiene un nombre de clase y sus miembros.
@dataclass  # Usamos `dataclass` porque esta clase tiene datos asociados (nombre de clase y miembros).
class ClassType(Type):
    class_name: str  # Nombre de la clase.
    members: Dict[str, Type]  # Miembros de la clase, representados por un diccionario de nombre -> tipo.

    def __str__(self):
        return self.class_name  # Representación de la clase como su nombre.

    @property
    def name(self):
        return self.class_name  # El nombre de la clase es el nombre de la clase en sí.


# Instancias singleton de los tipos primitivos, para evitar crear múltiples instancias del mismo tipo.
INT    = IntType()    # Instancia del tipo Int.
FLOAT  = FloatType()  # Instancia del tipo Float.
BOOL   = BoolType()   # Instancia del tipo Bool.
STR    = StringType() # Instancia del tipo String.
NULL   = NullType()   # Instancia del tipo Null.
VOID   = VoidType()   # Instancia del tipo Void.
