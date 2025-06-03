import os
from dotenv import load_dotenv

# Cargar variables de entorno
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

# Configuración de la base de datos
DB_NAME = os.getenv('DB_NAME', '')
DB_USER = os.getenv('DB_USER', '')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_HOST = os.getenv('DB_HOST', '')
DB_PORT = os.getenv('DB_PORT', '')

print("DB_PASSWORD:", repr(DB_PASSWORD))

DB_CONFIG = {
    'dbname': DB_NAME,
    'user': DB_USER,
    'password': DB_PASSWORD,
    'host': DB_HOST,
    'port': DB_PORT
}

# Configuración de la aplicación
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
MAX_LIBROS_POR_USUARIO = int(os.getenv('MAX_LIBROS_POR_USUARIO', '3'))
DIAS_PRESTAMO = int(os.getenv('DIAS_PRESTAMO', '15'))
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')

APP_CONFIG = {
    'debug': DEBUG,
    'max_books_per_user': MAX_LIBROS_POR_USUARIO,
    'loan_days': DIAS_PRESTAMO,
    'admin_username': ADMIN_USERNAME,
    'admin_password': ADMIN_PASSWORD
}

# Niveles de usuario
USER_LEVELS = {
    'ADMIN': 1,
    'STAFF': 2,
    'USER': 3
}

# Estados de préstamo
LOAN_STATUS = {
    'PENDING': 'pendiente',
    'APPROVED': 'activo',
    'REJECTED': 'rechazado',
    'RETURNED': 'devuelto',
    'OVERDUE': 'vencido'
}

# Estados de libro
BOOK_STATUS = {
    'AVAILABLE': 'disponible',
    'RESERVED': 'reservado',
    'BORROWED': 'prestado'
} 