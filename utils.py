import os
from datetime import datetime, timedelta
from typing import List, Optional
from colorama import init, Fore, Style
from tabulate import tabulate
from config import (
    DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT,
    MAX_LIBROS_POR_USUARIO, DIAS_PRESTAMO,
    ADMIN_USERNAME, ADMIN_PASSWORD
)

# Inicializar colorama
init()

def limpiar_pantalla():
    """Limpia la pantalla de la consola."""
    os.system('cls' if os.name == 'nt' else 'clear')

def mostrar_titulo(titulo: str):
    """Muestra un título formateado."""
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'=' * 50}")
    print(f"{titulo.center(50)}")
    print(f"{'=' * 50}{Style.RESET_ALL}\n")

def mostrar_error(mensaje: str):
    """Muestra un mensaje de error en rojo."""
    print(f"\n{Fore.RED}❌ {mensaje}{Style.RESET_ALL}")

def mostrar_exito(mensaje: str):
    """Muestra un mensaje de éxito en verde."""
    print(f"\n{Fore.GREEN}✅ {mensaje}{Style.RESET_ALL}")

def mostrar_advertencia(mensaje: str):
    """Muestra un mensaje de advertencia en amarillo."""
    print(f"\n{Fore.YELLOW}⚠️ {mensaje}{Style.RESET_ALL}")

def formatear_fecha(fecha: datetime) -> str:
    """Formatea una fecha en formato dd-mm-yyyy."""
    return fecha.strftime("%d-%m-%Y")

def calcular_fecha_devolucion() -> datetime:
    """Calcula la fecha de devolución basada en la configuración."""
    return datetime.now() + timedelta(days=DIAS_PRESTAMO)

def validar_dni(dni: str) -> bool:
    """Valida el formato del DNI."""
    return dni.isdigit() and len(dni) == 8

def validar_isbn(isbn: str) -> bool:
    """Valida el formato del ISBN."""
    # Eliminar guiones y espacios
    isbn = isbn.replace('-', '').replace(' ', '')
    return isbn.isdigit() and len(isbn) in [10, 13]

def validar_cdj(cdj: str) -> bool:
    """Valida el formato del código CDJ."""
    # El código CDJ debe tener el formato: XXX.XX
    partes = cdj.split('.')
    return len(partes) == 2 and partes[0].isdigit() and partes[1].isdigit()

def mostrar_tabla(encabezados: list, datos: list):
    """Muestra una tabla formateada."""
    print(tabulate(datos, headers=encabezados, tablefmt="grid"))

def esperar_tecla():
    """Espera a que el usuario presione una tecla."""
    input("\nPresione Enter para continuar...")

def confirmar_accion(mensaje: str) -> bool:
    """Pide confirmación al usuario para una acción."""
    respuesta = input(f"\n{mensaje} (s/n): ").lower()
    return respuesta == 's'

def mostrar_menu(opciones: list) -> str:
    """Muestra un menú y retorna la opción seleccionada."""
    for opcion in opciones:
        print(opcion)
    
    while True:
        seleccion = input("\nSeleccione una opción: ").strip()
        if seleccion in [str(i) for i in range(1, len(opciones) + 1)]:
            return seleccion
        mostrar_error("Opción inválida") 