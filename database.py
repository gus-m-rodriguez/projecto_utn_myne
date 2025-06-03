import psycopg2
from psycopg2.extras import DictCursor
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from config import DB_CONFIG, APP_CONFIG
from models import Usuario, Libro, Prestamo, Categoria

class Database:
    def __init__(self, dbname: str, user: str, password: str, host: str, port: str):
        """Inicializa la conexión a la base de datos"""
        self.conn_params = {
            'dbname': dbname,
            'user': user,
            'password': password,
            'host': host,
            'port': port
        }
        self.conn = None
        self.connect()
    
    def connect(self):
        """Establece la conexión con la base de datos"""
        try:
            self.conn = psycopg2.connect(**self.conn_params)
            self.conn.autocommit = True
        except psycopg2.Error as e:
            error_msg = str(e)
            if "database" in error_msg.lower() and "does not exist" in error_msg.lower():
                raise Exception("La base de datos no existe. Por favor, asegúrese de que la base de datos esté instalada correctamente.")
            elif "password authentication failed" in error_msg.lower():
                raise Exception("Error de autenticación. Verifique las credenciales de la base de datos.")
            elif "could not connect to server" in error_msg.lower():
                raise Exception("No se pudo conectar al servidor de la base de datos. Verifique que el servidor esté en ejecución.")
            else:
                raise Exception(f"Error al conectar a la base de datos: {error_msg}")
    
    def insert_usuario(self, usuario: Usuario) -> bool:
        """Inserta un nuevo usuario en la base de datos"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO usuarios (nombre, password, nivel, dni, email, telefono, direccion, estado)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    usuario.nombre,
                    usuario.password,
                    usuario.nivel,
                    usuario.dni,
                    usuario.email,
                    usuario.telefono,
                    usuario.direccion,
                    usuario.estado
                ))
                usuario.id = cur.fetchone()[0]
                return True
        except psycopg2.Error as e:
            print(f"Error al insertar usuario: {e}")
            return False
    
    def get_usuario(self, nombre: str, password: str = None) -> Optional[Usuario]:
        """Obtiene un usuario por su nombre y opcionalmente su contraseña"""
        try:
            with self.conn.cursor(cursor_factory=DictCursor) as cur:
                if password:
                    cur.execute("""
                        SELECT * FROM usuarios
                        WHERE nombre = %s AND password = %s
                    """, (nombre, password))
                else:
                    cur.execute("""
                        SELECT * FROM usuarios
                        WHERE nombre = %s
                    """, (nombre,))
                
                row = cur.fetchone()
                if row:
                    return Usuario(
                        id=row['id'],
                        nombre=row['nombre'],
                        password=row['password'],
                        nivel=row['nivel'],
                        dni=row['dni'],
                        email=row['email'],
                        telefono=row['telefono'],
                        direccion=row['direccion'],
                        fecha_registro=row['fecha_registro'],
                        estado=row['estado']
                    )
                return None
        except psycopg2.Error as e:
            print(f"Error al obtener usuario: {e}")
            return None
    
    def get_usuarios(self) -> List[Usuario]:
        """Obtiene todos los usuarios registrados"""
        try:
            with self.conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("SELECT * FROM usuarios ORDER BY nombre")
                return [
                    Usuario(
                        id=row['id'],
                        nombre=row['nombre'],
                        password=row['password'],
                        nivel=row['nivel'],
                        dni=row['dni'],
                        email=row['email'],
                        telefono=row['telefono'],
                        direccion=row['direccion'],
                        fecha_registro=row['fecha_registro'],
                        estado=row['estado']
                    )
                    for row in cur.fetchall()
                ]
        except psycopg2.Error as e:
            print(f"Error al obtener usuarios: {e}")
            return []
    
    def actualizar_usuario(self, usuario: Usuario) -> bool:
        """Actualiza los datos de un usuario existente"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    UPDATE usuarios
                    SET email = %s,
                        telefono = %s,
                        direccion = %s,
                        password = %s,
                        nivel = %s,
                        estado = %s
                    WHERE id = %s
                """, (
                    usuario.email,
                    usuario.telefono,
                    usuario.direccion,
                    usuario.password,
                    usuario.nivel,
                    usuario.estado,
                    usuario.id
                ))
                return cur.rowcount > 0
        except psycopg2.Error as e:
            print(f"Error al actualizar usuario: {e}")
            return False
    
    def eliminar_usuario(self, usuario_id: int) -> bool:
        """Elimina un usuario de la base de datos"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("DELETE FROM usuarios WHERE id = %s", (usuario_id,))
                return cur.rowcount > 0
        except psycopg2.Error as e:
            print(f"Error al eliminar usuario: {e}")
            return False
    
    def insert_libro(self, libro: Libro) -> tuple:
        """Inserta un nuevo libro en la base de datos. Retorna (success, error_message)"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO libros (titulo, autor, isbn, codigo_cdj, categoria_id, editorial, anio_publicacion, estado, cantidad)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    libro.titulo,
                    libro.autor,
                    libro.isbn,
                    libro.codigo_cdj,
                    libro.categoria_id,
                    libro.editorial,
                    libro.anio_publicacion,
                    libro.estado,
                    libro.cantidad
                ))
                libro.id = cur.fetchone()[0]
                return True, None
        except psycopg2.Error as e:
            return False, str(e)
    
    def actualizar_libro(self, libro: Libro) -> bool:
        """Actualiza los datos de un libro existente"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    UPDATE libros
                    SET titulo = %s,
                        autor = %s,
                        isbn = %s,
                        editorial = %s,
                        anio_publicacion = %s,
                        cantidad = %s,
                        codigo_cdj = %s
                    WHERE id = %s
                """,
                (
                    libro.titulo,
                    libro.autor,
                    libro.isbn,
                    libro.editorial,
                    libro.anio_publicacion,
                    libro.cantidad,
                    libro.codigo_cdj,
                    libro.id
                ))
                return cur.rowcount > 0
        except psycopg2.Error as e:
            print(f"Error al actualizar libro: {e}")
            return False
    
    def eliminar_libro(self, libro_id: int) -> bool:
        """Elimina un libro de la base de datos"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("DELETE FROM libros WHERE id = %s", (libro_id,))
                return cur.rowcount > 0
        except psycopg2.Error as e:
            print(f"Error al eliminar libro: {e}")
            return False
    
    def buscar_libros(self, termino: str) -> List[Libro]:
        """Busca libros por título, autor o código CDJ"""
        try:
            with self.conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("""
                    SELECT * FROM libros
                    WHERE LOWER(titulo) LIKE %s OR LOWER(autor) LIKE %s OR LOWER(codigo_cdj) LIKE %s
                """, (f"%{termino}%", f"%{termino}%", f"%{termino}%"))
                return [Libro(**dict(row)) for row in cur.fetchall()]
        except psycopg2.Error as e:
            print(f"Error al buscar libros: {e}")
            return []
    
    def get_libros(self) -> List[Libro]:
        """Obtiene todos los libros registrados"""
        try:
            with self.conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("SELECT * FROM libros ORDER BY titulo")
                return [Libro(**dict(row)) for row in cur.fetchall()]
        except psycopg2.Error as e:
            print(f"Error al obtener libros: {e}")
            return []
    
    def insert_prestamo(self, prestamo: Prestamo) -> int:
        """Inserta un nuevo préstamo y retorna su ID."""
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO prestamos (usuario_id, libro_id, fecha_prestamo, 
                                     fecha_devolucion, estado)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (prestamo.usuario_id, prestamo.libro_id, prestamo.fecha_prestamo,
                  prestamo.fecha_devolucion, prestamo.estado))
            return cur.fetchone()[0]
    
    def get_prestamos_usuario(self, usuario_id: int) -> List[Prestamo]:
        """Obtiene todos los préstamos de un usuario."""
        with self.conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("""
                SELECT * FROM prestamos
                WHERE usuario_id = %s
                ORDER BY fecha_prestamo DESC
            """, (usuario_id,))
            return [Prestamo(**dict(row)) for row in cur.fetchall()]
    
    def get_prestamos_vencidos(self) -> List[Prestamo]:
        """Obtiene todos los préstamos vencidos."""
        try:
            with self.conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("""
                    SELECT * FROM prestamos
                    WHERE estado = 'activo' AND fecha_devolucion < NOW()
                """)
                return [Prestamo(**dict(row)) for row in cur.fetchall()]
        except psycopg2.Error as e:
            print(f"Error al obtener préstamos vencidos: {e}")
            return []
    
    def actualizar_estado_prestamo(self, prestamo_id: int, nuevo_estado: str) -> bool:
        """Actualiza el estado de un préstamo. Si el estado es 'devuelto', también registra la fecha de devolución real."""
        try:
            with self.conn.cursor() as cur:
                if nuevo_estado == "devuelto":
                    from datetime import datetime
                    cur.execute("""
                        UPDATE prestamos
                        SET estado = %s, fecha_devolucion_real = %s
                        WHERE id = %s
                    """, (nuevo_estado, datetime.now(), prestamo_id))
                else:
                    cur.execute("""
                        UPDATE prestamos
                        SET estado = %s
                        WHERE id = %s
                    """, (nuevo_estado, prestamo_id))
                return cur.rowcount > 0
        except psycopg2.Error as e:
            print(f"Error al actualizar estado del préstamo: {e}")
            return False
    
    def actualizar_estado_libro(self, libro_id: int, nuevo_estado: str) -> bool:
        """Actualiza el estado de un libro."""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    UPDATE libros
                    SET estado = %s
                    WHERE id = %s
                """, (nuevo_estado, libro_id))
                return cur.rowcount > 0
        except psycopg2.Error as e:
            print(f"Error al actualizar estado del libro: {e}")
            return False
    
    def close(self):
        """Cierra la conexión a la base de datos"""
        if self.conn:
            self.conn.close()
    
    def get_libro(self, codigo_cdj: str) -> Optional[Libro]:
        """Obtiene un libro por su código CDJ."""
        try:
            with self.conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("""
                    SELECT * FROM libros
                    WHERE codigo_cdj = %s
                """, (codigo_cdj,))
                row = cur.fetchone()
                if row:
                    return Libro(**dict(row))
                return None
        except psycopg2.Error as e:
            print(f"Error al obtener libro: {e}")
            return None
    
    def buscar_prestamos_activos_por_libro(self, libro_id: int) -> List[Prestamo]:
        """Busca préstamos activos o pendientes para un libro específico"""
        try:
            with self.conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("""
                    SELECT * FROM prestamos
                    WHERE libro_id = %s AND estado IN ('activo', 'pendiente')
                """, (libro_id,))
                return [Prestamo(**dict(row)) for row in cur.fetchall()]
        except psycopg2.Error as e:
            print(f"Error al buscar préstamos activos por libro: {e}")
            return []
    
    def get_prestamos_activos(self) -> List[Prestamo]:
        """Obtiene todos los préstamos activos"""
        try:
            with self.conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("""
                    SELECT * FROM prestamos 
                    WHERE estado = 'activo' 
                    ORDER BY fecha_prestamo DESC
                """)
                return [Prestamo(**dict(row)) for row in cur.fetchall()]
        except psycopg2.Error as e:
            print(f"Error al obtener préstamos activos: {e}")
            return []
    
    def get_usuario_por_id(self, usuario_id: int) -> Optional[Usuario]:
        """Obtiene un usuario por su ID"""
        try:
            with self.conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("SELECT * FROM usuarios WHERE id = %s", (usuario_id,))
                row = cur.fetchone()
                if row:
                    return Usuario(
                        id=row['id'],
                        nombre=row['nombre'],
                        password=row['password'],
                        nivel=row['nivel'],
                        dni=row['dni'],
                        email=row['email'],
                        telefono=row['telefono'],
                        direccion=row['direccion'],
                        fecha_registro=row['fecha_registro']
                    )
                return None
        except psycopg2.Error as e:
            print(f"Error al obtener usuario por ID: {e}")
            return None
    
    def get_libro_por_id(self, libro_id: int) -> Optional[Libro]:
        """Obtiene un libro por su ID"""
        try:
            with self.conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("SELECT * FROM libros WHERE id = %s", (libro_id,))
                row = cur.fetchone()
                if row:
                    return Libro(**dict(row))
                return None
        except psycopg2.Error as e:
            print(f"Error al obtener libro por ID: {e}")
            return None
    
    def get_prestamos_pendientes(self) -> List[Prestamo]:
        """Obtiene todos los préstamos pendientes de aprobación"""
        try:
            with self.conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("""
                    SELECT * FROM prestamos 
                    WHERE estado = 'pendiente'
                    ORDER BY fecha_prestamo ASC
                """)
                return [Prestamo(**dict(row)) for row in cur.fetchall()]
        except psycopg2.Error as e:
            print(f"Error al obtener préstamos pendientes: {e}")
            return []
    
    def get_categorias(self) -> List[Categoria]:
        """Obtiene todas las categorías registradas"""
        try:
            with self.conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("SELECT * FROM categorias ORDER BY nombre")
                return [Categoria(**dict(row)) for row in cur.fetchall()]
        except Exception as e:
            print(f"Error al obtener categorías: {e}")
            return []

    def insert_categoria(self, categoria: Categoria) -> bool:
        """Inserta una nueva categoría en la base de datos"""
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO categorias (nombre, descripcion, codigo_cdj)
                    VALUES (%s, %s, %s)
                    RETURNING id
                    """,
                    (categoria.nombre, categoria.descripcion, categoria.codigo_cdj)
                )
                categoria.id = cur.fetchone()[0]
                return True
        except Exception as e:
            print(f"Error al insertar categoría: {e}")
            return False

    def actualizar_categoria(self, categoria: Categoria) -> bool:
        """Actualiza los datos de una categoría existente"""
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE categorias
                    SET nombre = %s, descripcion = %s, codigo_cdj = %s
                    WHERE id = %s
                    """,
                    (categoria.nombre, categoria.descripcion, categoria.codigo_cdj, categoria.id)
                )
                return cur.rowcount > 0
        except Exception as e:
            print(f"Error al actualizar categoría: {e}")
            return False

    def eliminar_categoria(self, categoria_id: int) -> bool:
        """Elimina una categoría de la base de datos"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("DELETE FROM categorias WHERE id = %s", (categoria_id,))
                return cur.rowcount > 0
        except Exception as e:
            raise

    def get_todos_prestamos(self):
        """Obtiene todos los préstamos del sistema (histórico completo)"""
        try:
            with self.conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("SELECT * FROM prestamos ORDER BY fecha_prestamo DESC")
                return [Prestamo(**dict(row)) for row in cur.fetchall()]
        except psycopg2.Error as e:
            print(f"Error al obtener todos los préstamos: {e}")
            return []

    def tiene_prestamo_activo(self, usuario_id: int, libro_id: int) -> bool:
        """Verifica si un usuario ya tiene un préstamo activo de un libro específico."""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT COUNT(*) 
                    FROM prestamos 
                    WHERE usuario_id = %s 
                    AND libro_id = %s 
                    AND estado = 'activo'
                """, (usuario_id, libro_id))
                return cur.fetchone()[0] > 0
        except psycopg2.Error as e:
            print(f"Error al verificar préstamo activo: {e}")
            return False 