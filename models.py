from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

@dataclass
class Usuario:
    id: int = 0
    nombre: str = ""
    password: str = ""
    nivel: str = "usuario"  # admin, staff, usuario
    dni: str = ""
    email: str = ""
    telefono: str = ""
    direccion: str = ""
    fecha_registro: datetime = datetime.now()
    estado: str = "activo"  # activo, inactivo

    @property
    def es_admin(self) -> bool:
        return self.nivel == "admin"

    @property
    def es_staff(self) -> bool:
        return self.nivel == "staff"

@dataclass
class Categoria:
    id: int = 0
    nombre: str = ""
    descripcion: str = ""
    codigo_cdj: str = ""  # Código de Clasificación Decimal Japonesa

@dataclass
class Libro:
    id: int = 0
    titulo: str = ""
    autor: str = ""
    isbn: str = ""
    codigo_cdj: str = ""
    categoria_id: int = 0
    editorial: str = ""
    anio_publicacion: int = 0
    estado: str = "disponible"  # disponible, prestado, reservado
    fecha_registro: datetime = datetime.now()
    cantidad: int = 1  # Nuevo campo para la cantidad de ejemplares

@dataclass
class Prestamo:
    id: int = 0
    usuario_id: int = 0
    libro_id: int = 0
    fecha_prestamo: datetime = datetime.now()
    fecha_devolucion: datetime = datetime.now()
    fecha_devolucion_real: Optional[datetime] = None
    estado: str = "activo"  # activo, devuelto, vencido

    @property
    def esta_vencido(self) -> bool:
        return self.estado == "activo" and datetime.now() > self.fecha_devolucion

class Biblioteca:
    def __init__(self):
        self.usuarios: List[Usuario] = []
        self.libros: List[Libro] = []
        self.prestamos: List[Prestamo] = []
        self.categorias: List[Categoria] = []

    def buscar_usuario(self, nombre: str) -> Optional[Usuario]:
        """Busca un usuario por su nombre"""
        for usuario in self.usuarios:
            if usuario.nombre.lower() == nombre.lower():
                return usuario
        return None

    def buscar_libro(self, codigo_cdj: str) -> Optional[Libro]:
        """Busca un libro por su código CDJ"""
        for libro in self.libros:
            if libro.codigo_cdj == codigo_cdj:
                return libro
        return None

    def get_prestamos_usuario(self, usuario_id: int) -> List[Prestamo]:
        """Obtiene los préstamos de un usuario"""
        return [p for p in self.prestamos if p.usuario_id == usuario_id]

    def get_libros_disponibles(self) -> List[Libro]:
        """Obtiene los libros disponibles"""
        return [l for l in self.libros if l.estado == "disponible"]

    def get_prestamos_vencidos(self) -> List[Prestamo]:
        """Obtiene los préstamos vencidos"""
        return [p for p in self.prestamos if p.esta_vencido] 