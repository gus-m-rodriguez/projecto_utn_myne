import os
from datetime import datetime, timedelta
from database import Database
from models import Usuario, Libro, Prestamo, Categoria, Biblioteca
from utils import (
    limpiar_pantalla, mostrar_titulo, mostrar_error, 
    mostrar_exito, mostrar_advertencia, formatear_fecha,
    mostrar_menu, esperar_tecla, confirmar_accion, mostrar_tabla
)
from config import (
    DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT,
    MAX_LIBROS_POR_USUARIO, DIAS_PRESTAMO,
    ADMIN_USERNAME, ADMIN_PASSWORD
)
import csv
import re

class SistemaBiblioteca:
    def __init__(self):
        self.db = Database(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        self.biblioteca = Biblioteca()
        self.usuario_actual = None

    def iniciar_sesion(self):
        """Maneja el proceso de inicio de sesión"""
        while True:
            limpiar_pantalla()
            mostrar_titulo("INICIO DE SESIÓN")
            print("\nIngrese sus credenciales (escriba 'salir' como usuario para finalizar el programa):")
            nombre = input("Usuario: ").strip()
            if nombre.lower() == "salir":
                return False
            password = input("Contraseña: ").strip()

            # Verificar credenciales de administrador
            if nombre == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                self.usuario_actual = Usuario(
                    nombre=ADMIN_USERNAME,
                    password=ADMIN_PASSWORD,
                    nivel="admin",
                    estado="activo"
                )
                mostrar_exito("¡Bienvenido Administrador!")
                return True

            # Buscar usuarios activos con ese nombre
            usuarios = [u for u in self.db.get_usuarios() if u.nombre == nombre and getattr(u, 'estado', 'activo') == 'activo']
            if not usuarios:
                mostrar_error("Usuario no encontrado o no está activo")
                if not confirmar_accion("¿Desea intentar nuevamente?"):
                    return False
                continue
            if len(usuarios) > 1:
                dni = input("Hay más de un usuario activo con ese nombre. Ingrese su DNI: ").strip()
                usuario = next((u for u in usuarios if u.dni == dni), None)
                if not usuario:
                    mostrar_error("No se encontró un usuario activo con ese nombre y DNI")
                    if not confirmar_accion("¿Desea intentar nuevamente?"):
                        return False
                    continue
            else:
                usuario = usuarios[0]
            if usuario.nivel == "admin" and usuario.nombre == ADMIN_USERNAME:
                usuario.estado = "activo"  # El admin principal nunca puede ser inactivado
            if usuario.estado != "activo":
                mostrar_error("El usuario no está activo. Contacte al administrador.")
                if not confirmar_accion("¿Desea intentar nuevamente?"):
                    return False
                continue
            if usuario.password != password:
                mostrar_error("Contraseña incorrecta")
                if not confirmar_accion("¿Desea intentar nuevamente?"):
                    return False
                continue
            self.usuario_actual = usuario
            mostrar_exito(f"¡Bienvenido {usuario.nombre}!")
            return True

    def menu_principal(self):
        """Muestra el menú principal y maneja las opciones"""
        if self.usuario_actual.nivel == "admin":
            opciones = [
                "1. Gestión de Usuarios",
                "2. Consultas/Listar Libros",
                "3. Gestión de Libros",
                "4. Gestión de Préstamos",
                "5. Gestión de Categorías",
                "6. Reportes",
                "7. Salir"
            ]
        else:
            opciones = [
                "1. Consultas/Listar Libros",
                "2. Solicitar préstamo",
                "3. Ver mis préstamos",
                "4. Historial",
                "5. Modificar mis datos",
                "6. Salir"
            ]

        while True:
            limpiar_pantalla()
            mostrar_titulo("MENÚ PRINCIPAL")
            print(f"\nUsuario actual: {self.usuario_actual.nombre}")
            print(f"Nivel: {self.usuario_actual.nivel}\n")
            
            opcion = mostrar_menu(opciones)
            
            if self.usuario_actual.nivel == "admin":
                if opcion == "1":
                    self.menu_usuarios()
                elif opcion == "2":
                    self.menu_listar_libros()
                elif opcion == "3":
                    self.menu_libros()
                elif opcion == "4":
                    self.menu_prestamos()
                elif opcion == "5":
                    self.menu_categorias()
                elif opcion == "6":
                    self.menu_reportes()
                elif opcion == "7":
                    if confirmar_accion("¿Está seguro que desea salir?"):
                        break
            else:
                if opcion == "1":
                    self.menu_listar_libros()
                elif opcion == "2":
                    self.solicitar_prestamo()
                elif opcion == "3":
                    self.ver_mis_prestamos()
                elif opcion == "4":
                    self.menu_historial_usuario()
                elif opcion == "5":
                    self.modificar_mis_datos()
                elif opcion == "6":
                    if confirmar_accion("¿Está seguro que desea salir?"):
                        break

    def menu_usuarios(self):
        """Maneja el menú de gestión de usuarios"""
        if self.usuario_actual.nivel != "admin":
            mostrar_error("No tiene permisos para acceder a esta sección")
            esperar_tecla()
            return

        opciones = [
            "1. Registrar nuevo usuario",
            "2. Modificar usuario",
            "3. Eliminar usuario",
            "4. Activar usuario",
            "5. Listar usuarios",
            "6. Volver"
        ]

        while True:
            limpiar_pantalla()
            mostrar_titulo("GESTIÓN DE USUARIOS")
            opcion = mostrar_menu(opciones)
            
            if opcion == "1":
                self.registrar_usuario()
            elif opcion == "2":
                self.modificar_usuario()
            elif opcion == "3":
                self.eliminar_usuario()
            elif opcion == "4":
                self.activar_usuario()
            elif opcion == "5":
                self.listar_usuarios()
            elif opcion == "6":
                break

    def activar_usuario(self):
        limpiar_pantalla()
        mostrar_titulo("ACTIVAR USUARIO INACTIVO")
        dni = input("Ingrese el DNI del usuario a activar: ").strip()
        if not dni.isdigit() or not (1000000 <= int(dni) <= 99999999):
            mostrar_error("El DNI debe ser un número entre 1.000.000 y 99.999.999.")
            esperar_tecla()
            return
        usuarios = self.db.get_usuarios()
        usuario = next((u for u in usuarios if u.dni == dni), None)
        if not usuario:
            mostrar_error("No existe un usuario con ese DNI. Puede darlo de alta desde el registro de usuario.")
            esperar_tecla()
            return
        if getattr(usuario, 'estado', 'activo') == 'activo':
            mostrar_advertencia(f"El usuario '{usuario.nombre}' con DNI {dni} ya se encuentra activo.")
            esperar_tecla()
            return
        print(f"Usuario encontrado: {usuario.nombre}")
        if not confirmar_accion(f"¿Desea activar al usuario '{usuario.nombre}' con DNI {dni}?"):
            return
        usuario.estado = 'activo'
        if self.db.actualizar_usuario(usuario):
            mostrar_exito(f"Usuario '{usuario.nombre}' activado correctamente.")
        else:
            mostrar_error("Error al activar el usuario. Por favor, intente nuevamente o contacte al administrador.")
        esperar_tecla()

    def menu_libros(self):
        """Maneja el menú de gestión de libros"""
        opciones = [
            "1. Registrar nuevo libro",
            "2. Modificar libro",
            "3. Eliminar libro",
            "4. Buscar libro",
            "5. Volver"
        ]

        while True:
            limpiar_pantalla()
            mostrar_titulo("GESTIÓN DE LIBROS")
            opcion = mostrar_menu(opciones)
            
            if opcion == "1":
                self.registrar_libro()
            elif opcion == "2":
                self.modificar_libro()
            elif opcion == "3":
                self.eliminar_libro()
            elif opcion == "4":
                self.buscar_libro()
            elif opcion == "5":
                break

    def menu_prestamos(self):
        """Maneja el menú de gestión de préstamos"""
        opciones = [
            "1. Realizar préstamo",
            "2. Devolver libro",
            "3. Ver préstamos activos",
            "4. Ver préstamos vencidos",
            "5. Aprobar solicitudes pendientes",
            "6. Listar histórico de préstamos",
            "7. Volver"
        ]

        while True:
            limpiar_pantalla()
            mostrar_titulo("GESTIÓN DE PRÉSTAMOS")
            opcion = mostrar_menu(opciones)
            
            if opcion == "1":
                self.realizar_prestamo()
            elif opcion == "2":
                self.devolver_libro()
            elif opcion == "3":
                self.ver_prestamos_activos()
            elif opcion == "4":
                self.ver_prestamos_vencidos()
            elif opcion == "5":
                self.aprobar_prestamos_pendientes()
            elif opcion == "6":
                self.listar_historico_prestamos()
            elif opcion == "7":
                break

    def menu_categorias(self):
        """Maneja el menú de gestión de categorías"""
        opciones = [
            "1. Agregar categoría",
            "2. Modificar categoría",
            "3. Eliminar categoría",
            "4. Listar categorías",
            "5. Volver"
        ]
        while True:
            limpiar_pantalla()
            mostrar_titulo("GESTIÓN DE CATEGORÍAS")
            opcion = mostrar_menu(opciones)
            if opcion == "1":
                self.agregar_categoria()
            elif opcion == "2":
                self.modificar_categoria()
            elif opcion == "3":
                self.eliminar_categoria()
            elif opcion == "4":
                self.listar_categorias()
            elif opcion == "5":
                break

    def menu_reportes(self):
        """Maneja el menú de reportes"""
        opciones = [
            "1. Libros más prestados",
            "2. Usuarios con más préstamos",
            "3. Libros disponibles",
            "4. Libros no disponibles",
            "5. Libros prestados por usuario",
            "6. Libros atrasados por usuario",
            "7. Libros atrasados en general",
            "8. Volver"
        ]

        while True:
            limpiar_pantalla()
            mostrar_titulo("REPORTES")
            opcion = mostrar_menu(opciones)
            
            if opcion == "1":
                self.reporte_libros_mas_prestados()
            elif opcion == "2":
                self.reporte_usuarios_mas_prestamos()
            elif opcion == "3":
                self.reporte_libros_disponibles()
            elif opcion == "4":
                self.reporte_libros_prestados()
            elif opcion == "5":
                self.reporte_libros_prestados_por_usuario()
            elif opcion == "6":
                self.reporte_libros_atrasados_por_usuario()
            elif opcion == "7":
                self.reporte_libros_atrasados_general()
            elif opcion == "8":
                break

    def registrar_usuario(self):
        try:
            limpiar_pantalla()
            mostrar_titulo("REGISTRAR NUEVO USUARIO")
            print("\nIngrese los datos del usuario:")
            while True:
                nombre = input("Nombre de usuario: ").strip()
                if not nombre:
                    mostrar_error("El nombre de usuario es obligatorio")
                    continue
                break
            while True:
                password = input("Contraseña: ").strip()
                if len(password) < 6:
                    mostrar_error("La contraseña debe tener al menos 6 caracteres.")
                    continue
                break
            # Validación de DNI interactiva con opción de salir
            while True:
                dni = input("DNI (o escriba 'salir' para cancelar): ").strip()
                if dni.lower() == 'salir':
                    mostrar_advertencia("Registro cancelado por el usuario.")
                    esperar_tecla()
                    return
                if not dni.isdigit() or not (1000000 <= int(dni) <= 99999999):
                    mostrar_error("El DNI debe ser un número entre 1.000.000 y 99.999.999.")
                    continue
                usuarios = self.db.get_usuarios()
                usuario_existente = next((u for u in usuarios if u.dni == dni), None)
                if usuario_existente:
                    if hasattr(usuario_existente, 'estado') and usuario_existente.estado == 'activo':
                        mostrar_error(f"El DNI {dni} ya está registrado para el usuario: {usuario_existente.nombre} (activo). No se puede registrar otro usuario con el mismo DNI.")
                        esperar_tecla()
                        return
                    else:
                        mostrar_advertencia(f"El DNI {dni} corresponde a un usuario inactivo: {usuario_existente.nombre}.")
                        if confirmar_accion("¿Desea reactivar este usuario y actualizar sus datos?"):
                            # Permitir actualizar datos y reactivar
                            usuario_existente.nombre = nombre
                            usuario_existente.password = password
                            # Validación de email
                            while True:
                                email = input(f"Email [{usuario_existente.email}]: ").strip()
                                if not email:
                                    email = usuario_existente.email
                                    break
                                if not re.match(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,3}(\.[A-Za-z]{2})?$', email):
                                    mostrar_error("Formato de correo electrónico inválido.")
                                    continue
                                break
                            telefono = input(f"Teléfono [{usuario_existente.telefono}]: ").strip() or usuario_existente.telefono
                            direccion = input(f"Dirección [{usuario_existente.direccion}]: ").strip() or usuario_existente.direccion
                            niveles = ["usuario", "admin"]
                            print(f"Nivel actual: {usuario_existente.nivel}")
                            print("Seleccione el nuevo nivel (deje en blanco para no modificar):")
                            for i, nivel_op in enumerate(niveles, 1):
                                print(f"{i}. {nivel_op}")
                            nivel_opcion = input("Nivel [1-2]: ").strip()
                            if nivel_opcion in ["1", "2"]:
                                usuario_existente.nivel = niveles[int(nivel_opcion) - 1]
                            usuario_existente.email = email
                            usuario_existente.telefono = telefono
                            usuario_existente.direccion = direccion
                            usuario_existente.estado = 'activo'
                            if self.db.actualizar_usuario(usuario_existente):
                                mostrar_exito("Usuario reactivado y actualizado correctamente")
                            else:
                                mostrar_error("Error al reactivar el usuario. Por favor, intente nuevamente o contacte al administrador.")
                            esperar_tecla()
                            return
                        else:
                            mostrar_advertencia("No se realizó el registro ni la reactivación.")
                            esperar_tecla()
                            return
                break
            # Validación de email
            while True:
                email = input("Email: ").strip()
                if not email:
                    break
                if not re.match(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,3}(\.[A-Za-z]{2})?$', email):
                    mostrar_error("Formato de correo electrónico inválido.")
                    continue
                break
            telefono = input("Teléfono: ").strip()
            direccion = input("Dirección: ").strip()
            # Selección de nivel de usuario
            niveles = ["usuario", "admin"]
            print("\nSeleccione el nivel del usuario:")
            for i, nivel_op in enumerate(niveles, 1):
                print(f"{i}. {nivel_op}")
            while True:
                nivel_opcion = input("Nivel [1-2]: ").strip()
                if nivel_opcion in ["1", "2"]:
                    nivel = niveles[int(nivel_opcion) - 1]
                    break
                else:
                    mostrar_error("Opción inválida")
            usuario = Usuario(
                nombre=nombre,
                password=password,
                nivel=nivel,
                dni=dni,
                email=email,
                telefono=telefono,
                direccion=direccion,
                estado='activo'
            )
            if self.db.insert_usuario(usuario):
                mostrar_exito("Usuario registrado correctamente")
            else:
                mostrar_error("Error al registrar el usuario. Por favor, intente nuevamente o contacte al administrador.")
            esperar_tecla()
        except Exception as e:
            mostrar_error(f"Ocurrió un error inesperado durante el registro: {str(e)}")
            esperar_tecla()

    def modificar_usuario(self):
        try:
            limpiar_pantalla()
            mostrar_titulo("MODIFICAR USUARIO")
            nombre = input("\nIngrese el nombre del usuario a modificar: ").strip()
            usuarios = [u for u in self.db.get_usuarios() if u.nombre == nombre and getattr(u, 'estado', 'activo') == 'activo']
            if not usuarios:
                mostrar_error("Usuario no encontrado o no está activo")
                esperar_tecla()
                return
            if len(usuarios) > 1:
                dni = input("Hay más de un usuario activo con ese nombre. Ingrese su DNI: ").strip()
                usuario = next((u for u in usuarios if u.dni == dni), None)
                if not usuario:
                    mostrar_error("No se encontró un usuario activo con ese nombre y DNI")
                    esperar_tecla()
                    return
            else:
                usuario = usuarios[0]
            print("\nDeje en blanco los campos que no desee modificar:")
            # Validación de email
            while True:
                email = input(f"Email [{usuario.email}]: ").strip()
                if not email:
                    email = usuario.email
                    break
                if not re.match(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,3}(\.[A-Za-z]{2})?$', email):
                    mostrar_error("Formato de correo electrónico inválido.")
                    continue
                break
            telefono = input(f"Teléfono [{usuario.telefono}]: ").strip()
            direccion = input(f"Dirección [{usuario.direccion}]: ").strip()
            # Validación de nueva contraseña si se ingresa
            while True:
                password = input("Nueva contraseña (opcional): ").strip()
                if password and len(password) < 6:
                    mostrar_error("La contraseña debe tener al menos 6 caracteres.")
                    continue
                break
            # Validación de DNI único si se modifica
            while True:
                dni = input(f"DNI [{usuario.dni}]: ").strip()
                if not dni:
                    dni = usuario.dni
                    break
                if not dni.isdigit() or not (1000000 <= int(dni) <= 99999999):
                    mostrar_error("El DNI debe ser un número entre 1.000.000 y 99.999.999.")
                    continue
                if dni != usuario.dni:
                    usuarios = self.db.get_usuarios()
                    if any(u.dni == dni and getattr(u, 'estado', 'activo') == 'activo' for u in usuarios):
                        mostrar_error("Ya existe un usuario activo con ese DNI. No se puede modificar.")
                        continue
                break
            # Modificar nivel
            niveles = ["usuario", "admin"]
            print(f"Nivel actual: {usuario.nivel}")
            print("Seleccione el nuevo nivel (deje en blanco para no modificar):")
            for i, nivel_op in enumerate(niveles, 1):
                print(f"{i}. {nivel_op}")
            nivel_opcion = input("Nivel [1-2]: ").strip()
            if nivel_opcion in ["1", "2"]:
                usuario.nivel = niveles[int(nivel_opcion) - 1]
            if email:
                usuario.email = email
            if telefono:
                usuario.telefono = telefono
            if direccion:
                usuario.direccion = direccion
            if dni:
                usuario.dni = dni
            if password:
                usuario.password = password
            # No se permite modificar el campo estado desde aquí
            if self.db.actualizar_usuario(usuario):
                mostrar_exito("Usuario modificado correctamente")
            else:
                mostrar_error("Error al modificar el usuario. Por favor, intente nuevamente o contacte al administrador.")
            esperar_tecla()
        except Exception as e:
            mostrar_error(f"Ocurrió un error inesperado durante la modificación: {str(e)}")
            esperar_tecla()

    def eliminar_usuario(self):
        try:
            limpiar_pantalla()
            mostrar_titulo("ELIMINAR USUARIO")
            nombre = input("\nIngrese el nombre del usuario a eliminar: ").strip()
            usuarios = [u for u in self.db.get_usuarios() if u.nombre == nombre and getattr(u, 'estado', 'activo') == 'activo']
            if not usuarios:
                mostrar_error("Usuario no encontrado o no está activo")
                esperar_tecla()
                return
            if len(usuarios) > 1:
                dni = input("Hay más de un usuario activo con ese nombre. Ingrese su DNI: ").strip()
                usuario = next((u for u in usuarios if u.dni == dni), None)
                if not usuario:
                    mostrar_error("No se encontró un usuario activo con ese nombre y DNI")
                    esperar_tecla()
                    return
            else:
                usuario = usuarios[0]
            if usuario.nivel == "admin" and usuario.nombre == ADMIN_USERNAME:
                mostrar_error("No se puede deshabilitar al usuario principal 'admin'")
                esperar_tecla()
                return
            if usuario.nivel == "admin":
                if self.usuario_actual.nombre != "admin":
                    mostrar_error("Solo el usuario principal 'admin' puede eliminar cuentas de administrador")
                    esperar_tecla()
                    return
            # Verificar si el usuario tiene préstamos activos
            prestamos_usuario = self.db.get_prestamos_usuario(usuario.id)
            prestamos_activos = [p for p in prestamos_usuario if p.estado in ("activo", "pendiente")]
            if prestamos_activos:
                mostrar_error(f"El usuario '{usuario.nombre}' tiene préstamos activos o pendientes. Debe devolver todos los libros antes de ser deshabilitado.")
                esperar_tecla()
                return
            if not confirmar_accion(f"¿Está seguro que desea deshabilitar al usuario {usuario.nombre}?"):
                return
            usuario.estado = 'inactivo'
            if self.db.actualizar_usuario(usuario):
                mostrar_exito("Usuario deshabilitado correctamente")
            else:
                mostrar_error("Error al deshabilitar el usuario. Por favor, intente nuevamente o contacte al administrador.")
            esperar_tecla()
        except Exception as e:
            mostrar_error(f"Ocurrió un error inesperado durante la deshabilitación: {str(e)}")
            esperar_tecla()

    def listar_usuarios(self):
        """Muestra la lista de usuarios registrados"""
        limpiar_pantalla()
        mostrar_titulo("LISTA DE USUARIOS")
        usuarios = self.db.get_usuarios()
        if not usuarios:
            mostrar_advertencia("No hay usuarios registrados")
            esperar_tecla()
            return
        datos = []
        for u in usuarios:
            datos.append([
                u.nombre,
                u.nivel,
                u.dni,
                u.email,
                u.telefono,
                u.estado
            ])
        mostrar_tabla(
            ["Nombre", "Nivel", "DNI", "Email", "Teléfono", "Estado"],
            datos
        )
        if confirmar_accion("¿Desea exportar este informe a un archivo CSV?"):
            self.exportar_csv("usuarios.csv", ["Nombre", "Nivel", "DNI", "Email", "Teléfono", "Estado"], datos)
        esperar_tecla()

    def solicitar_prestamo(self):
        limpiar_pantalla()
        mostrar_titulo("SOLICITAR PRÉSTAMO")
        # No es necesario validar estado aquí, ya que solo usuarios activos pueden iniciar sesión
        # Validación: máximo 5 libros prestados o reservados
        prestamos_usuario = self.db.get_prestamos_usuario(self.usuario_actual.id)
        prestamos_activos = [p for p in prestamos_usuario if p.estado in ("activo", "pendiente")]
        if len(prestamos_activos) >= 5:
            mostrar_error("No puede solicitar más libros: ya tiene 5 libros prestados o reservados.")
            esperar_tecla()
            return
        # Validación: préstamos vencidos
        prestamos_vencidos = [p for p in prestamos_usuario if p.estado == "activo" and p.fecha_devolucion < datetime.now()]
        if prestamos_vencidos:
            mostrar_error("No puede solicitar libros: tiene préstamos vencidos con atraso. Debe devolverlos antes de solicitar nuevos libros.")
            esperar_tecla()
            return
        while True:
            codigo = input("Ingrese el código CDJ del libro (o * para cancelar): ").strip()
            if codigo == "*":
                return
            libro = self.db.get_libro(codigo)
            if not libro:
                mostrar_error("Libro no encontrado")
                if not confirmar_accion("¿Desea intentar con otro código?"):
                    return
                continue
            break
        # Verificar si el usuario ya tiene un préstamo activo de este libro
        if self.db.tiene_prestamo_activo(self.usuario_actual.id, libro.id):
            mostrar_error("Ya tiene un préstamo activo de este libro")
            esperar_tecla()
            return
        # Verificar disponibilidad de ejemplares
        prestamos_activos_libro = self.db.buscar_prestamos_activos_por_libro(libro.id)
        cantidad_prestados = len([p for p in prestamos_activos_libro if p.estado in ("activo", "pendiente")])
        cantidad_disponibles = libro.cantidad - cantidad_prestados
        if cantidad_disponibles < 1:
            mostrar_error("No hay ejemplares disponibles para solicitar el préstamo")
            esperar_tecla()
            return
        if not confirmar_accion(f"¿Desea solicitar el préstamo de '{libro.titulo}'?"):
            return
        fecha_prestamo = datetime.now()
        fecha_devolucion = fecha_prestamo + timedelta(days=14)  # O el valor de préstamo que uses
        prestamo = Prestamo(
            usuario_id=self.usuario_actual.id,
            libro_id=libro.id,
            fecha_prestamo=fecha_prestamo,
            fecha_devolucion=fecha_devolucion,
            estado="pendiente"
        )
        if self.db.insert_prestamo(prestamo):
            mostrar_exito("Solicitud de préstamo realizada exitosamente. Queda pendiente de autorización.")
        else:
            mostrar_error("Error al solicitar el préstamo")
        esperar_tecla()

    def ver_mis_prestamos(self):
        """Muestra solo los préstamos activos del usuario actual"""
        limpiar_pantalla()
        mostrar_titulo("MIS PRÉSTAMOS ACTIVOS")
        prestamos = self.db.get_prestamos_usuario(self.usuario_actual.id)
        prestamos = [p for p in prestamos if p.estado == "activo"]
        if not prestamos:
            mostrar_advertencia("No tiene préstamos activos")
            esperar_tecla()
            return
        datos = []
        for p in prestamos:
            libro = self.db.get_libro_por_id(p.libro_id)
            if not libro:
                continue
            datos.append([
                libro.codigo_cdj,
                libro.isbn,
                libro.titulo,
                libro.autor,
                1
            ])
        mostrar_tabla(["CDJ", "ISBN", "Título", "Autor", "Cantidad"], datos)
        esperar_tecla()

    def menu_historial_usuario(self):
        """Submenú de historial de préstamos del usuario activo"""
        opciones = [
            "1. Buscar Historial por Autor",
            "2. Buscar Historial por CDJ",
            "3. Buscar entre fechas",
            "4. Libros más solicitados",
            "5. Listado completo",
            "6. Volver"
        ]
        while True:
            limpiar_pantalla()
            mostrar_titulo("HISTORIAL DE PRÉSTAMOS")
            opcion = mostrar_menu(opciones)
            if opcion == "1":
                self.historial_por_autor()
            elif opcion == "2":
                self.historial_por_cdj()
            elif opcion == "3":
                self.historial_entre_fechas()
            elif opcion == "4":
                self.historial_mas_solicitados()
            elif opcion == "5":
                self.historial_completo()
            elif opcion == "6":
                break

    def _historial_tabla(self, prestamos):
        # Agrupa por libro y cuenta cantidad de veces solicitado
        from collections import Counter
        libros = [self.db.get_libro_por_id(p.libro_id) for p in prestamos if self.db.get_libro_por_id(p.libro_id)]
        counter = Counter([l.id for l in libros])
        datos = []
        for libro_id, cantidad in counter.items():
            libro = self.db.get_libro_por_id(libro_id)
            datos.append([
                libro.codigo_cdj,
                libro.isbn,
                libro.titulo,
                libro.autor,
                cantidad
            ])
        datos.sort(key=lambda x: (int(x[0][:2]), int(x[0][2:]) if x[0][2:].isdigit() else 0))
        mostrar_tabla(["CDJ", "ISBN", "Título", "Autor", "Cantidad"], datos)

    def historial_por_autor(self):
        limpiar_pantalla()
        mostrar_titulo("HISTORIAL POR AUTOR")
        texto = input("Ingrese el nombre o parte del nombre del autor: ").strip().lower()
        prestamos = self.db.get_prestamos_usuario(self.usuario_actual.id)
        prestamos = [p for p in prestamos if texto in (self.db.get_libro_por_id(p.libro_id).autor.lower() if self.db.get_libro_por_id(p.libro_id) else "")]
        if not prestamos:
            mostrar_advertencia("No se encontraron préstamos para ese autor")
            esperar_tecla()
            return
        self._historial_tabla(prestamos)
        esperar_tecla()

    def historial_por_cdj(self):
        limpiar_pantalla()
        mostrar_titulo("HISTORIAL POR CDJ")
        cdj_input = input("Ingrese el CDJ completo o parcial: ").strip()
        prestamos = self.db.get_prestamos_usuario(self.usuario_actual.id)
        prestamos = [p for p in prestamos if cdj_input in (self.db.get_libro_por_id(p.libro_id).codigo_cdj if self.db.get_libro_por_id(p.libro_id) else "")]
        if not prestamos:
            mostrar_advertencia("No se encontraron préstamos para ese CDJ")
            esperar_tecla()
            return
        self._historial_tabla(prestamos)
        esperar_tecla()

    def historial_entre_fechas(self):
        limpiar_pantalla()
        mostrar_titulo("HISTORIAL ENTRE FECHAS")
        print("Ingrese las fechas en formato DD-MM-YYYY. Puede usar * para indicar sin límite.")
        while True:
            fecha_ini = input("Fecha inicial (DD-MM-YYYY o *): ").strip()
            if fecha_ini == "*":
                fecha_ini_dt = None
                break
            try:
                fecha_ini_dt = datetime.strptime(fecha_ini, "%d-%m-%Y")
                break
            except ValueError:
                mostrar_error("Formato de fecha incorrecto. Intente nuevamente.")
        while True:
            fecha_fin = input("Fecha final (DD-MM-YYYY o *): ").strip()
            if fecha_fin == "*":
                fecha_fin_dt = None
                break
            try:
                fecha_fin_dt = datetime.strptime(fecha_fin, "%d-%m-%Y")
                break
            except ValueError:
                mostrar_error("Formato de fecha incorrecto. Intente nuevamente.")

        prestamos = self.db.get_prestamos_usuario(self.usuario_actual.id)
        filtrados = []
        for p in prestamos:
            # Verificar si la fecha de préstamo está en el rango
            fecha_prestamo_en_rango = (
                (fecha_ini_dt is None or p.fecha_prestamo >= fecha_ini_dt) and
                (fecha_fin_dt is None or p.fecha_prestamo <= fecha_fin_dt)
            )
            # Verificar si la fecha de devolución real está en el rango (si existe)
            fecha_devolucion_real_en_rango = False
            if p.fecha_devolucion_real:
                fecha_devolucion_real_en_rango = (
                    (fecha_ini_dt is None or p.fecha_devolucion_real >= fecha_ini_dt) and
                    (fecha_fin_dt is None or p.fecha_devolucion_real <= fecha_fin_dt)
                )
            # Incluir el préstamo si cualquiera de las fechas está en el rango
            if fecha_prestamo_en_rango or fecha_devolucion_real_en_rango:
                filtrados.append(p)

        if not filtrados:
            mostrar_advertencia("No se encontraron préstamos en ese rango de fechas")
            esperar_tecla()
            return

        filtrados.sort(key=lambda x: x.fecha_prestamo)
        datos = []
        for p in filtrados:
            libro = self.db.get_libro_por_id(p.libro_id)
            if not libro:
                continue
            fecha_prestamo = formatear_fecha(p.fecha_prestamo)
            fecha_devolucion_real = formatear_fecha(p.fecha_devolucion_real) if p.fecha_devolucion_real else "-"
            datos.append([
                libro.codigo_cdj,
                libro.isbn,
                libro.titulo,
                libro.autor,
                fecha_prestamo,
                fecha_devolucion_real,
                p.estado
            ])
        mostrar_tabla(
            ["CDJ", "ISBN", "Título", "Autor", "F. Solicitud", "F. Devolución Real", "Estado"],
            datos
        )
        esperar_tecla()

    def historial_mas_solicitados(self):
        limpiar_pantalla()
        mostrar_titulo("LIBROS MÁS SOLICITADOS")
        prestamos = self.db.get_prestamos_usuario(self.usuario_actual.id)
        from collections import Counter
        libros = [self.db.get_libro_por_id(p.libro_id) for p in prestamos if self.db.get_libro_por_id(p.libro_id)]
        counter = Counter([l.id for l in libros])
        if not counter:
            mostrar_advertencia("No se encontraron préstamos")
            esperar_tecla()
            return
        datos = []
        for libro_id, cantidad in counter.most_common():
            libro = self.db.get_libro_por_id(libro_id)
            datos.append([
                libro.codigo_cdj,
                libro.isbn,
                libro.titulo,
                libro.autor,
                cantidad
            ])
        mostrar_tabla(["CDJ", "ISBN", "Título", "Autor", "Cantidad"], datos)
        esperar_tecla()

    def historial_completo(self):
        limpiar_pantalla()
        mostrar_titulo("HISTORIAL COMPLETO")
        prestamos = self.db.get_prestamos_usuario(self.usuario_actual.id)
        if not prestamos:
            mostrar_advertencia("No se encontraron préstamos")
            esperar_tecla()
            return
        self._historial_tabla(prestamos)
        esperar_tecla()

    def registrar_libro(self):
        try:
            limpiar_pantalla()
            mostrar_titulo("REGISTRAR NUEVO LIBRO")
            titulo = input("Título: ").strip()
            autor = input("Autor: ").strip()
            isbn = input("ISBN: ").strip()
            editorial = input("Editorial: ").strip()
            anio_publicacion = input("Año de publicación: ").strip()
            cantidad = input("Cantidad de ejemplares: ").strip()
            # Selección de categoría por CDJ
            categorias = self.db.get_categorias()
            while True:
                print("\nCategorías disponibles:")
                self.listar_categorias(modo_simple=True)
                codigo_cdj_libro = input("Ingrese el Código CDJ completo para el libro (ej: 01XXX): ").strip()
                if len(codigo_cdj_libro) < 3 or not codigo_cdj_libro.isdigit():
                    mostrar_error("El código CDJ debe tener al menos 3 dígitos numéricos.")
                    continue
                cdj_categoria = codigo_cdj_libro[:2]
                if not any(c.codigo_cdj == cdj_categoria for c in categorias):
                    mostrar_error(f"La categoría con CDJ '{cdj_categoria}' no existe. Ingrese un código válido.")
                    continue
                # Validar que el resto del CDJ no esté repetido
                libros = self.db.get_libros()
                if any(l.codigo_cdj == codigo_cdj_libro for l in libros):
                    mostrar_error("El código CDJ de libro ya está en uso. Ingrese un identificador de libro diferente.")
                    continue
                break
            categoria = next((c for c in categorias if c.codigo_cdj == cdj_categoria), None)
            categoria_id = categoria.id if categoria else None
            if not titulo or not autor or not codigo_cdj_libro:
                mostrar_error("Título, Autor y Código CDJ son obligatorios")
                esperar_tecla()
                return
            try:
                cantidad_int = int(cantidad)
                if cantidad_int < 1:
                    mostrar_error("La cantidad debe ser mayor a 0")
                    esperar_tecla()
                    return
            except ValueError:
                mostrar_error("Cantidad inválida")
                esperar_tecla()
                return
            libro = Libro(
                titulo=titulo,
                autor=autor,
                isbn=isbn,
                codigo_cdj=codigo_cdj_libro,
                editorial=editorial,
                anio_publicacion=int(anio_publicacion) if anio_publicacion.isdigit() else 0,
                categoria_id=categoria_id,
                cantidad=cantidad_int
            )
            success, error_message = self.db.insert_libro(libro)
            if success:
                mostrar_exito("Libro registrado correctamente")
            else:
                mostrar_error(f"Error inesperado al registrar el libro: {error_message}")
            esperar_tecla()
        except Exception as e:
            mostrar_error(f"Ocurrió un error inesperado durante el registro del libro: {str(e)}")
            esperar_tecla()

    def modificar_libro(self):
        try:
            limpiar_pantalla()
            mostrar_titulo("MODIFICAR LIBRO")
            while True:
                codigo = input("Ingrese el código CDJ del libro a modificar (o * para cancelar): ").strip()
                if codigo == "*":
                    return
                libro = self.db.get_libro(codigo)
                if not libro:
                    mostrar_error("Libro no encontrado")
                    if not confirmar_accion("¿Desea intentar con otro código?"):
                        return
                    continue
                break

            print("\nDeje en blanco los campos que no desee modificar.")
            print("Valores actuales entre paréntesis.")

            prestamos_activos = len(self.db.buscar_prestamos_activos_por_libro(libro.id))
            libros = self.db.get_libros()
            categorias = self.db.get_categorias()

            titulo = input(f"Título ({libro.titulo}): ").strip()
            autor = input(f"Autor ({libro.autor}): ").strip()
            isbn = input(f"ISBN ({libro.isbn}): ").strip()
            editorial = input(f"Editorial ({libro.editorial}): ").strip()
            anio_publicacion = input(f"Año de publicación ({libro.anio_publicacion}): ").strip()
            cantidad = input(f"Cantidad de ejemplares ({libro.cantidad}): ").strip()
            nuevo_cdj = input(f"Código CDJ ({libro.codigo_cdj}): ").strip()

            if titulo:
                libro.titulo = titulo
            if autor:
                libro.autor = autor
            if isbn:
                if isbn and any(l.isbn == isbn and l.id != libro.id for l in libros if l.isbn):
                    mostrar_error("El ISBN ya está en uso por otro libro.")
                    esperar_tecla()
                    return
                libro.isbn = isbn
            if editorial:
                libro.editorial = editorial
            if anio_publicacion:
                try:
                    libro.anio_publicacion = int(anio_publicacion)
                except ValueError:
                    mostrar_error("El año de publicación debe ser un número entero.")
                    esperar_tecla()
                    return
            if cantidad:
                try:
                    nueva_cantidad = int(cantidad)
                    if nueva_cantidad < prestamos_activos:
                        mostrar_error(f"No se puede reducir la cantidad a {nueva_cantidad} porque hay {prestamos_activos} ejemplares prestados")
                        esperar_tecla()
                        return
                    libro.cantidad = nueva_cantidad
                except ValueError:
                    mostrar_error("La cantidad debe ser un número entero.")
                    esperar_tecla()
                    return
            if nuevo_cdj and nuevo_cdj != libro.codigo_cdj:
                if not nuevo_cdj.isdigit() or len(nuevo_cdj) < 3:
                    mostrar_error("El código CDJ debe ser numérico y tener al menos 3 dígitos.")
                    esperar_tecla()
                    return
                if any(l.codigo_cdj == nuevo_cdj and l.id != libro.id for l in libros):
                    mostrar_error("El código CDJ ya está en uso por otro libro.")
                    esperar_tecla()
                    return
                cdj_categoria = nuevo_cdj[:2]
                if not any(c.codigo_cdj == cdj_categoria for c in categorias):
                    mostrar_error(f"No existe una categoría con CDJ '{cdj_categoria}'.")
                    esperar_tecla()
                    return
                libro.codigo_cdj = nuevo_cdj

            if self.db.actualizar_libro(libro):
                self.actualizar_estado_libro_por_disponibilidad(libro.id)
                mostrar_exito("Libro modificado exitosamente")
            else:
                mostrar_error("Error al modificar el libro. Por favor, intente nuevamente o contacte al administrador.")
            esperar_tecla()
        except Exception as e:
            mostrar_error(f"Ocurrió un error inesperado durante la modificación del libro: {str(e)}")
            esperar_tecla()

    def eliminar_libro(self):
        try:
            limpiar_pantalla()
            mostrar_titulo("ELIMINAR LIBRO")
            codigo_cdj = input("Ingrese el código CDJ del libro a eliminar: ").strip()
            libro = self.db.get_libro(codigo_cdj)
            if not libro:
                mostrar_error("Libro no encontrado")
                esperar_tecla()
                return
            if not confirmar_accion(f"¿Está seguro que desea eliminar el libro '{libro.titulo}'?"):
                return
            if self.db.eliminar_libro(libro.id):
                mostrar_exito("Libro eliminado correctamente")
            else:
                mostrar_error("Error al eliminar el libro. Por favor, intente nuevamente o contacte al administrador.")
            esperar_tecla()
        except Exception as e:
            mostrar_error(f"Ocurrió un error inesperado durante la eliminación del libro: {str(e)}")
            esperar_tecla()

    def buscar_libro(self):
        """Busca un libro por título, autor o código CDJ"""
        limpiar_pantalla()
        mostrar_titulo("BUSCAR LIBRO")
        termino = input("Ingrese título, autor o código CDJ: ").strip().lower()
        libros = self.db.buscar_libros(termino)
        if not libros:
            mostrar_advertencia("No se encontraron libros")
            esperar_tecla()
            return
        datos = []
        for libro in libros:
            datos.append([
                libro.titulo,
                libro.autor,
                libro.codigo_cdj,
                libro.estado
            ])
        mostrar_tabla(["Título", "Autor", "Código CDJ", "Estado"], datos)
        esperar_tecla()

    def menu_listar_libros(self):
        """Submenú para listar libros de diferentes formas"""
        opciones = [
            "1. Listar libros por autor",
            "2. Listar libros por categoría con CDJ",
            "3. Listar navegando por categoría",
            "4. Listar todos los libros",
            "5. Volver"
        ]
        while True:
            limpiar_pantalla()
            mostrar_titulo("LISTAR LIBROS")
            opcion = mostrar_menu(opciones)
            if opcion == "1":
                self.listar_libros_por_autor()
            elif opcion == "2":
                self.listar_libros_por_categoria_cdj()
            elif opcion == "3":
                self.listar_libros_navegando_categoria()
            elif opcion == "4":
                self.listar_libros_general()
            elif opcion == "5":
                break

    def listar_libros_por_autor(self):
        limpiar_pantalla()
        mostrar_titulo("LISTAR LIBROS POR AUTOR")
        texto = input("Ingrese el nombre o parte del nombre del autor: ").strip().lower()
        libros = self.db.get_libros()
        if not libros:
            mostrar_advertencia("No hay libros registrados")
            esperar_tecla()
            return
        # Filtrar por autor
        libros_filtrados = [l for l in libros if texto in l.autor.lower()]
        if not libros_filtrados:
            mostrar_advertencia("No se encontraron libros para ese autor")
            esperar_tecla()
            return
        # Agrupar por autor y ordenar por CDJ
        libros_filtrados.sort(key=lambda l: (l.autor.lower(), int(l.codigo_cdj[:2]), int(l.codigo_cdj[2:]) if l.codigo_cdj[2:].isdigit() else 0))
        datos = []
        for libro in libros_filtrados:
            prestamos_activos = self.db.buscar_prestamos_activos_por_libro(libro.id)
            cantidad_prestados = len([p for p in prestamos_activos if p.estado == "activo"])
            cantidad_disponibles = max(libro.cantidad - cantidad_prestados, 0)
            datos.append([
                libro.codigo_cdj,
                libro.isbn,
                libro.titulo,
                libro.autor,
                libro.cantidad,
                cantidad_disponibles,
                cantidad_prestados
            ])
        mostrar_tabla(["CDJ", "ISBN", "Título", "Autor", "Total", "Disponibles", "Prestados"], datos)
        esperar_tecla()

    def listar_libros_por_categoria_cdj(self):
        limpiar_pantalla()
        mostrar_titulo("LISTAR LIBROS POR CATEGORÍA (CDJ)")
        categorias = self.db.get_categorias()
        libros = self.db.get_libros()
        while True:
            cdj_input = input("Ingrese los dos primeros dígitos del CDJ (0-99), un dígito, o * para todas: ").strip()
            if cdj_input == "*":
                # Mostrar todos agrupados por categoría
                libros.sort(key=lambda l: (int(l.codigo_cdj[:2]), int(l.codigo_cdj[2:]) if l.codigo_cdj[2:].isdigit() else 0))
                break
            if not cdj_input.isdigit() or not (1 <= len(cdj_input) <= 2):
                mostrar_error("Debe ingresar uno o dos dígitos, o *.")
                continue
            cdj_input = cdj_input.zfill(2) if len(cdj_input) == 2 else cdj_input
            # Validar existencia de categoría
            if len(cdj_input) == 1:
                if not any(c.codigo_cdj.startswith(cdj_input) for c in categorias):
                    mostrar_error("No existe ninguna categoría con ese dígito inicial.")
                    continue
                libros = [l for l in libros if l.codigo_cdj.startswith(cdj_input)]
            else:
                if not any(c.codigo_cdj == cdj_input for c in categorias):
                    mostrar_error("No existe ninguna categoría con ese CDJ.")
                    continue
                libros = [l for l in libros if l.codigo_cdj.startswith(cdj_input)]
            libros.sort(key=lambda l: (int(l.codigo_cdj[:2]), int(l.codigo_cdj[2:]) if l.codigo_cdj[2:].isdigit() else 0))
            break
        if not libros:
            mostrar_advertencia("No se encontraron libros para esa categoría")
            esperar_tecla()
            return
        datos = []
        for libro in libros:
            prestamos_activos = self.db.buscar_prestamos_activos_por_libro(libro.id)
            cantidad_prestados = len([p for p in prestamos_activos if p.estado == "activo"])
            cantidad_disponibles = max(libro.cantidad - cantidad_prestados, 0)
            datos.append([
                libro.codigo_cdj,
                libro.isbn,
                libro.titulo,
                libro.autor,
                libro.cantidad,
                cantidad_disponibles,
                cantidad_prestados
            ])
        mostrar_tabla(["CDJ", "ISBN", "Título", "Autor", "Total", "Disponibles", "Prestados"], datos)
        esperar_tecla()

    def listar_libros_navegando_categoria(self):
        limpiar_pantalla()
        mostrar_titulo("NAVEGAR POR CATEGORÍA")
        categorias = self.db.get_categorias()
        if not categorias:
            mostrar_advertencia("No hay categorías registradas")
            esperar_tecla()
            return
        categorias.sort(key=lambda c: int(c.codigo_cdj))
        datos = [[c.codigo_cdj, c.nombre, c.descripcion] for c in categorias]
        mostrar_tabla(["CDJ", "Nombre", "Descripción"], datos)
        cdj_input = input("Ingrese el CDJ de la categoría a consultar: ").strip().zfill(2)
        if not any(c.codigo_cdj == cdj_input for c in categorias):
            mostrar_error("No existe ninguna categoría con ese CDJ.")
            esperar_tecla()
            return
        libros = self.db.get_libros()
        libros = [l for l in libros if l.codigo_cdj.startswith(cdj_input)]
        libros.sort(key=lambda l: (int(l.codigo_cdj[:2]), int(l.codigo_cdj[2:]) if l.codigo_cdj[2:].isdigit() else 0))
        if not libros:
            mostrar_advertencia("No se encontraron libros para esa categoría")
            esperar_tecla()
            return
        datos = []
        for libro in libros:
            prestamos_activos = self.db.buscar_prestamos_activos_por_libro(libro.id)
            cantidad_prestados = len([p for p in prestamos_activos if p.estado == "activo"])
            cantidad_disponibles = max(libro.cantidad - cantidad_prestados, 0)
            datos.append([
                libro.codigo_cdj,
                libro.isbn,
                libro.titulo,
                libro.autor,
                libro.cantidad,
                cantidad_disponibles,
                cantidad_prestados
            ])
        mostrar_tabla(["CDJ", "ISBN", "Título", "Autor", "Total", "Disponibles", "Prestados"], datos)
        esperar_tecla()

    def listar_libros_general(self):
        limpiar_pantalla()
        mostrar_titulo("LISTA DE LIBROS")
        libros = self.db.get_libros()
        if not libros:
            mostrar_advertencia("No hay libros registrados")
            esperar_tecla()
            return
        def cdj_sort_key(libro):
            cdj = libro.codigo_cdj.strip()
            cat = int(cdj[:2].zfill(2)) if len(cdj) >= 2 and cdj[:2].isdigit() else 0
            ident = int(cdj[2:].zfill(3)) if len(cdj) > 2 and cdj[2:].isdigit() else 0
            return (cat, ident)
        libros.sort(key=cdj_sort_key)
        datos = []
        for libro in libros:
            prestamos_activos = self.db.buscar_prestamos_activos_por_libro(libro.id)
            cantidad_prestados = len([p for p in prestamos_activos if p.estado == "activo"])
            cantidad_disponibles = max(libro.cantidad - cantidad_prestados, 0)
            datos.append([
                libro.codigo_cdj,
                libro.isbn,
                libro.titulo,
                libro.autor,
                libro.cantidad,
                cantidad_disponibles,
                cantidad_prestados
            ])
        mostrar_tabla(["CDJ", "ISBN", "Título", "Autor", "Total", "Disponibles", "Prestados"], datos)
        if hasattr(self, 'usuario_actual') and getattr(self.usuario_actual, 'nivel', None) == 'admin':
            if confirmar_accion("¿Desea exportar este informe a un archivo CSV?"):
                self.exportar_csv("libros.csv", ["CDJ", "ISBN", "Título", "Autor", "Total", "Disponibles", "Prestados"], datos)
        esperar_tecla()

    def realizar_prestamo(self):
        try:
            limpiar_pantalla()
            mostrar_titulo("REALIZAR PRÉSTAMO")
            usuario_nombre = input("Nombre del usuario: ").strip()
            usuarios = [u for u in self.db.get_usuarios() if u.nombre == usuario_nombre]
            if not usuarios:
                mostrar_error("Usuario no encontrado")
                esperar_tecla()
                return
            if len(usuarios) > 1:
                dni = input("Hay más de un usuario con ese nombre. Ingrese el DNI: ").strip()
                usuario = next((u for u in usuarios if u.dni == dni), None)
                if not usuario:
                    mostrar_error("No se encontró un usuario con ese nombre y DNI")
                    esperar_tecla()
                    return
            else:
                usuario = usuarios[0]
            # Validar estado del usuario
            if not hasattr(usuario, 'estado') or usuario.estado != 'activo':
                mostrar_error("El usuario está inactivo. No se puede realizar el préstamo.")
                esperar_tecla()
                return
            prestamos_usuario = self.db.get_prestamos_usuario(usuario.id)
            prestamos_activos = [p for p in prestamos_usuario if p.estado in ("activo", "pendiente")]
            if len(prestamos_activos) >= 5:
                mostrar_error(f"El usuario '{usuario.nombre}' ya tiene 5 libros prestados o reservados. No puede recibir más libros.")
                esperar_tecla()
                return
            prestamos_vencidos = [p for p in prestamos_usuario if p.estado == "activo" and p.fecha_devolucion < datetime.now()]
            if prestamos_vencidos:
                mostrar_error(f"El usuario '{usuario.nombre}' tiene préstamos vencidos con atraso. Debe devolverlos antes de recibir nuevos libros.")
                esperar_tecla()
                return
            codigo_cdj = input("Código CDJ del libro: ").strip()
            libro = self.db.get_libro(codigo_cdj)
            if not libro:
                mostrar_error("Libro no encontrado")
                esperar_tecla()
                return
            if self.db.tiene_prestamo_activo(usuario.id, libro.id):
                mostrar_error(f"El usuario '{usuario.nombre}' ya tiene un préstamo activo de este libro.")
                esperar_tecla()
                return
            prestamos_activos_libro = self.db.buscar_prestamos_activos_por_libro(libro.id)
            cantidad_prestados = len([p for p in prestamos_activos_libro if p.estado in ("activo", "pendiente")])
            cantidad_disponibles = libro.cantidad - cantidad_prestados
            if cantidad_disponibles < 1:
                mostrar_error("No hay ejemplares disponibles para prestar este libro")
                esperar_tecla()
                return
            fecha_prestamo = datetime.now()
            fecha_devolucion = fecha_prestamo + timedelta(days=DIAS_PRESTAMO)
            prestamo = Prestamo(
                usuario_id=usuario.id,
                libro_id=libro.id,
                fecha_prestamo=fecha_prestamo,
                fecha_devolucion=fecha_devolucion,
                estado="activo"
            )
            self.db.insert_prestamo(prestamo)
            self.actualizar_estado_libro_por_disponibilidad(libro.id)
            mostrar_exito("Préstamo realizado correctamente")
            esperar_tecla()
        except Exception as e:
            mostrar_error(f"Ocurrió un error inesperado durante el préstamo: {str(e)}")
            esperar_tecla()

    def devolver_libro(self):
        try:
            limpiar_pantalla()
            mostrar_titulo("DEVOLVER LIBRO")
            usuario_nombre = input("Nombre del usuario: ").strip()
            usuario = self.db.get_usuario(usuario_nombre)
            if not usuario:
                mostrar_error("Usuario no encontrado")
                esperar_tecla()
                return
            while True:
                prestamos = [p for p in self.db.get_prestamos_usuario(usuario.id) if p.estado == "activo"]
                if not prestamos:
                    mostrar_advertencia("El usuario no tiene libros prestados actualmente")
                    esperar_tecla()
                    return
                datos = []
                cdj_validos = []
                for p in prestamos:
                    libro = self.db.get_libro_por_id(p.libro_id)
                    if libro:
                        datos.append([
                            libro.codigo_cdj,
                            libro.isbn,
                            libro.titulo,
                            libro.autor
                        ])
                        cdj_validos.append(libro.codigo_cdj)
                mostrar_tabla(["CDJ", "ISBN", "Título", "Autor"], datos)
                cdj = input("Código CDJ del libro a devolver (o 'salir' para cancelar): ").strip()
                if cdj.lower() == 'salir':
                    return
                if cdj not in cdj_validos:
                    mostrar_error("Debe ingresar un CDJ válido de la lista.")
                    esperar_tecla()
                    continue
                libro = self.db.get_libro(cdj)
                prestamo = next((p for p in prestamos if p.libro_id == libro.id), None)
                if not prestamo:
                    mostrar_error("No se encontró el préstamo activo para ese libro.")
                    esperar_tecla()
                    continue
                self.db.actualizar_estado_prestamo(prestamo.id, "devuelto")
                self.actualizar_estado_libro_por_disponibilidad(libro.id)
                mostrar_exito(f"Libro '{libro.titulo}' devuelto correctamente.")
                if not confirmar_accion("¿Desea devolver otro libro de este usuario?"):
                    break
                limpiar_pantalla()
                mostrar_titulo("DEVOLVER LIBRO")
                print(f"Usuario: {usuario.nombre}")
        except Exception as e:
            mostrar_error(f"Ocurrió un error inesperado durante la devolución: {str(e)}")
            esperar_tecla()

    def ver_prestamos_activos(self):
        """Muestra todos los préstamos activos"""
        limpiar_pantalla()
        mostrar_titulo("PRÉSTAMOS ACTIVOS")
        prestamos = self.db.get_prestamos_activos()
        if not prestamos:
            mostrar_advertencia("No hay préstamos activos")
            esperar_tecla()
            return
        datos = []
        for p in prestamos:
            usuario = self.db.get_usuario_por_id(p.usuario_id)
            libro = self.db.get_libro_por_id(p.libro_id)
            if not libro:
                datos.append(["Libro no encontrado", "-", "-", "-", p.estado])
                continue
            datos.append([
                usuario.nombre if usuario else "-",
                libro.titulo,
                formatear_fecha(p.fecha_prestamo),
                formatear_fecha(p.fecha_devolucion),
                p.estado
            ])
        mostrar_tabla(["Usuario", "Libro", "Fecha Préstamo", "Fecha Devolución", "Estado"], datos)
        esperar_tecla()

    def ver_prestamos_vencidos(self):
        """Muestra todos los préstamos vencidos"""
        limpiar_pantalla()
        mostrar_titulo("PRÉSTAMOS VENCIDOS")
        prestamos = self.db.get_prestamos_vencidos()
        if not prestamos:
            mostrar_advertencia("No hay préstamos vencidos")
            esperar_tecla()
            return
        datos = []
        for p in prestamos:
            usuario = self.db.get_usuario_por_id(p.usuario_id)
            libro = self.db.get_libro_por_id(p.libro_id)
            if not libro:
                datos.append(["Libro no encontrado", "-", "-", "-", p.estado])
                continue
            datos.append([
                usuario.nombre if usuario else "-",
                libro.titulo,
                formatear_fecha(p.fecha_prestamo),
                formatear_fecha(p.fecha_devolucion),
                p.estado
            ])
        mostrar_tabla(["Usuario", "Libro", "Fecha Préstamo", "Fecha Devolución", "Estado"], datos)
        esperar_tecla()

    def reporte_libros_mas_prestados(self):
        """Muestra los libros más prestados"""
        limpiar_pantalla()
        mostrar_titulo("LIBROS MÁS PRESTADOS")
        # Consulta a la base de datos
        with self.db.conn.cursor() as cur:
            cur.execute('''
                SELECT l.titulo, l.autor, l.isbn, l.codigo_cdj, COUNT(p.id) as cantidad
                FROM libros l
                JOIN prestamos p ON l.id = p.libro_id
                WHERE p.estado IN ('activo', 'devuelto')
                GROUP BY l.id
                ORDER BY cantidad DESC, l.titulo
                LIMIT 20
            ''')
            rows = cur.fetchall()
        if not rows:
            mostrar_advertencia("No hay préstamos registrados")
        else:
            mostrar_tabla(["Título", "Autor", "ISBN", "Código CDJ", "Cantidad"], rows)
        esperar_tecla()

    def reporte_usuarios_mas_prestamos(self):
        """Muestra los usuarios con más préstamos (solo usuarios activos)"""
        limpiar_pantalla()
        mostrar_titulo("USUARIOS CON MÁS PRÉSTAMOS")
        with self.db.conn.cursor() as cur:
            cur.execute('''
                SELECT u.nombre, u.dni, u.email, COUNT(p.id) as cantidad
                FROM usuarios u
                JOIN prestamos p ON u.id = p.usuario_id
                WHERE u.estado = 'activo'
                GROUP BY u.id
                ORDER BY cantidad DESC, u.nombre
                LIMIT 20
            ''')
            rows = cur.fetchall()
        if not rows:
            mostrar_advertencia("No hay préstamos registrados")
        else:
            mostrar_tabla(["Nombre", "DNI", "Email", "Cantidad"], rows)
        esperar_tecla()

    def reporte_libros_disponibles(self):
        """Muestra los libros disponibles"""
        limpiar_pantalla()
        mostrar_titulo("LIBROS DISPONIBLES")
        libros = [l for l in self.db.get_libros() if l.estado == "disponible"]
        if not libros:
            mostrar_advertencia("No hay libros disponibles")
        else:
            datos = [[l.titulo, l.autor, l.isbn, l.codigo_cdj, getattr(l, 'cantidad', 1)] for l in libros]
            mostrar_tabla(["Título", "Autor", "ISBN", "Código CDJ", "Cantidad"], datos)
        esperar_tecla()

    def reporte_libros_prestados(self):
        """Muestra los libros actualmente no disponibles"""
        limpiar_pantalla()
        mostrar_titulo("LIBROS NO DISPONIBLES")
        libros = [l for l in self.db.get_libros() if l.estado == "prestado"]
        if not libros:
            mostrar_advertencia("No hay libros no disponibles actualmente")
            esperar_tecla()
            return
        # Ordenar por CDJ
        def cdj_sort_key(libro):
            cdj = libro.codigo_cdj.strip()
            cat = int(cdj[:2].zfill(2)) if len(cdj) >= 2 and cdj[:2].isdigit() else 0
            ident = int(cdj[2:].zfill(3)) if len(cdj) > 2 and cdj[2:].isdigit() else 0
            return (cat, ident)
        libros.sort(key=cdj_sort_key)
        datos = []
        for libro in libros:
            prestamos_activos = self.db.buscar_prestamos_activos_por_libro(libro.id)
            cantidad_prestados = len([p for p in prestamos_activos if p.estado == "activo"])
            cantidad_disponibles = max(libro.cantidad - cantidad_prestados, 0)
            datos.append([
                libro.codigo_cdj,
                libro.isbn,
                libro.titulo,
                libro.autor,
                getattr(libro, 'cantidad', 1)
            ])
        mostrar_tabla(["CDJ", "ISBN", "Título", "Autor", "Cantidad"], datos)
        esperar_tecla()

    def reporte_libros_prestados_por_usuario(self):
        """Permite ver los libros actualmente prestados filtrados por usuario (solo usuarios activos)"""
        limpiar_pantalla()
        mostrar_titulo("LIBROS PRESTADOS POR USUARIO")
        nombre = input("Ingrese el nombre del usuario: ").strip()
        usuarios = [u for u in self.db.get_usuarios() if u.nombre == nombre and getattr(u, 'estado', 'activo') == 'activo']
        if not usuarios:
            mostrar_error("Usuario no encontrado o no está activo")
            esperar_tecla()
            return
        if len(usuarios) > 1:
            dni = input("Hay más de un usuario activo con ese nombre. Ingrese su DNI: ").strip()
            usuario = next((u for u in usuarios if u.dni == dni), None)
            if not usuario:
                mostrar_error("No se encontró un usuario activo con ese nombre y DNI")
                esperar_tecla()
                return
        else:
            usuario = usuarios[0]
        # Buscar préstamos activos de ese usuario
        with self.db.conn.cursor() as cur:
            cur.execute('''
                SELECT l.titulo, l.autor, l.isbn, l.codigo_cdj, p.fecha_prestamo, p.fecha_devolucion
                FROM libros l
                JOIN prestamos p ON l.id = p.libro_id
                WHERE p.usuario_id = %s AND p.estado = 'activo'
            ''', (usuario.id,))
            rows = cur.fetchall()
        if not rows:
            mostrar_advertencia("El usuario no tiene libros prestados actualmente")
        else:
            mostrar_tabla(["Título", "Autor", "ISBN", "Código CDJ", "Fecha Préstamo", "Fecha Devolución"], rows)
        esperar_tecla()

    def reporte_libros_atrasados_por_usuario(self):
        """Muestra los libros atrasados de un usuario (búsqueda parcial) y ordenados por CDJ"""
        limpiar_pantalla()
        mostrar_titulo("LIBROS ATRASADOS POR USUARIO")
        texto = input("Ingrese el nombre o parte del nombre del usuario: ").strip().lower()
        usuarios = self.db.get_usuarios()
        usuarios_filtrados = [u for u in usuarios if texto in u.nombre.lower()]
        if not usuarios_filtrados:
            mostrar_advertencia("No se encontraron usuarios con ese nombre")
            esperar_tecla()
            return
        prestamos = self.db.get_prestamos_vencidos()
        prestamos_filtrados = [p for p in prestamos if any(u.id == p.usuario_id for u in usuarios_filtrados)]
        if not prestamos_filtrados:
            mostrar_advertencia("No hay préstamos atrasados para ese usuario o usuarios")
            esperar_tecla()
            return
        prestamos_filtrados.sort(key=lambda p: (p.usuario_id, int(self.db.get_libro_por_id(p.libro_id).codigo_cdj[:2]), int(self.db.get_libro_por_id(p.libro_id).codigo_cdj[2:]) if self.db.get_libro_por_id(p.libro_id).codigo_cdj[2:].isdigit() else 0))
        datos = []
        for p in prestamos_filtrados:
            usuario = self.db.get_usuario_por_id(p.usuario_id)
            libro = self.db.get_libro_por_id(p.libro_id)
            if not libro or not usuario:
                continue
            dias_atraso = (datetime.now() - p.fecha_devolucion).days
            datos.append([
                libro.codigo_cdj,
                libro.titulo,
                libro.autor,
                usuario.nombre,
                formatear_fecha(p.fecha_prestamo),
                formatear_fecha(p.fecha_devolucion),
                dias_atraso
            ])
        mostrar_tabla(["CDJ", "Título", "Autor", "Usuario", "F. Préstamo", "F. Devolución", "Días atraso"], datos)
        esperar_tecla()

    def reporte_libros_atrasados_general(self):
        """Muestra todos los libros atrasados ordenados por CDJ"""
        limpiar_pantalla()
        mostrar_titulo("LIBROS ATRASADOS (GENERAL)")
        prestamos = self.db.get_prestamos_vencidos()
        if not prestamos:
            mostrar_advertencia("No hay préstamos atrasados")
            esperar_tecla()
            return
        # Ordenar por CDJ
        prestamos.sort(key=lambda p: (int(self.db.get_libro_por_id(p.libro_id).codigo_cdj[:2]), int(self.db.get_libro_por_id(p.libro_id).codigo_cdj[2:]) if self.db.get_libro_por_id(p.libro_id).codigo_cdj[2:].isdigit() else 0))
        datos = []
        for p in prestamos:
            usuario = self.db.get_usuario_por_id(p.usuario_id)
            libro = self.db.get_libro_por_id(p.libro_id)
            if not libro or not usuario:
                continue
            dias_atraso = (datetime.now() - p.fecha_devolucion).days
            datos.append([
                libro.codigo_cdj,
                libro.titulo,
                libro.autor,
                usuario.nombre,
                formatear_fecha(p.fecha_prestamo),
                formatear_fecha(p.fecha_devolucion),
                dias_atraso
            ])
        mostrar_tabla(["CDJ", "Título", "Autor", "Usuario", "F. Préstamo", "F. Devolución", "Días atraso"], datos)
        esperar_tecla()

    def agregar_categoria(self):
        limpiar_pantalla()
        mostrar_titulo("AGREGAR CATEGORÍA")
        nombre = input("Nombre: ").strip()
        descripcion = input("Descripción: ").strip()
        while True:
            codigo_cdj = input("Código CDJ (00-99): ").strip()
            if not codigo_cdj.isdigit() or not (0 <= int(codigo_cdj) <= 99):
                mostrar_error("El código CDJ debe ser un número entre 00 y 99.")
                continue
            codigo_cdj = codigo_cdj.zfill(2)
            # Verificar unicidad
            categorias = self.db.get_categorias()
            if any(c.codigo_cdj == codigo_cdj for c in categorias):
                mostrar_error("Ya existe una categoría con ese código CDJ.")
                continue
            break
        if not nombre:
            mostrar_error("El nombre es obligatorio")
            esperar_tecla()
            return
        categoria = Categoria(nombre=nombre, descripcion=descripcion, codigo_cdj=codigo_cdj)
        if self.db.insert_categoria(categoria):
            mostrar_exito("Categoría agregada correctamente")
        else:
            mostrar_error("Error al agregar la categoría")
        esperar_tecla()

    def modificar_categoria(self):
        try:
            limpiar_pantalla()
            mostrar_titulo("MODIFICAR CATEGORÍA")
            while True:
                codigo = input("Ingrese el código CDJ de la categoría a modificar (o * para cancelar): ").strip()
                if codigo == "*":
                    return
                categorias = self.db.get_categorias()
                categoria = next((c for c in categorias if c.codigo_cdj == codigo), None)
                if not categoria:
                    mostrar_error("Categoría no encontrada")
                    if not confirmar_accion("¿Desea intentar con otro código?"):
                        return
                    continue
                break

            print("\nDeje en blanco los campos que no desee modificar.")
            print("Valores actuales entre paréntesis.")
            nombre = input(f"Nombre ({categoria.nombre}): ").strip()
            if nombre:
                categoria.nombre = nombre
            while True:
                nuevo_cdj = input(f"Código CDJ ({categoria.codigo_cdj}): ").strip()
                if not nuevo_cdj:
                    break
                if len(nuevo_cdj) != 2 or not nuevo_cdj.isdigit():
                    mostrar_error("El código CDJ debe tener exactamente 2 dígitos numéricos")
                    if not confirmar_accion("¿Desea intentar nuevamente?"):
                        return
                    continue
                if any(c.codigo_cdj == nuevo_cdj and c.id != categoria.id for c in categorias):
                    mostrar_error("Ya existe una categoría con ese código CDJ")
                    if not confirmar_accion("¿Desea intentar con otro código?"):
                        return
                    continue
                break
            if nuevo_cdj:
                libros = [l for l in self.db.get_libros() if l.categoria_id == categoria.id]
                if libros:
                    print(f"\nSe encontraron {len(libros)} libros asociados a esta categoría.")
                    if not confirmar_accion("¿Desea actualizar automáticamente el código CDJ de estos libros?"):
                        return
                    for libro in libros:
                        nuevo_cdj_libro = nuevo_cdj + libro.codigo_cdj[2:]
                        libro.codigo_cdj = nuevo_cdj_libro
                        self.db.actualizar_libro(libro)
                categoria.codigo_cdj = nuevo_cdj
            if self.db.actualizar_categoria(categoria):
                mostrar_exito("Categoría modificada exitosamente")
            else:
                mostrar_error("Error al modificar la categoría")
            esperar_tecla()
        except Exception as e:
            mostrar_error(f"Ocurrió un error inesperado durante la modificación de la categoría: {str(e)}")
            esperar_tecla()

    def eliminar_categoria(self):
        try:
            limpiar_pantalla()
            mostrar_titulo("ELIMINAR CATEGORÍA")
            self.listar_categorias(modo_simple=True)
            codigo_cdj = input("Ingrese el Código CDJ de la categoría a eliminar: ").strip().zfill(2)
            categorias = self.db.get_categorias()
            categoria = next((c for c in categorias if c.codigo_cdj == codigo_cdj), None)
            if not categoria:
                mostrar_error("Categoría no encontrada")
                esperar_tecla()
                return
            if not confirmar_accion("¿Está seguro que desea eliminar esta categoría?"):
                return
            if self.db.eliminar_categoria(categoria.id):
                mostrar_exito("Categoría eliminada correctamente")
            else:
                mostrar_error("Error al eliminar la categoría")
            esperar_tecla()
        except Exception as e:
            error_msg = str(e)
            if ("violates foreign key constraint" in error_msg or
                "referida desde la tabla" in error_msg or
                "is still referenced from table" in error_msg):
                mostrar_error("No se puede eliminar la categoría porque tiene libros asignados. Debe reasignar o eliminar esos libros antes de eliminar la categoría.")
            else:
                mostrar_error(f"Ocurrió un error inesperado durante la eliminación de la categoría: {error_msg}")
            esperar_tecla()

    def listar_categorias(self, modo_simple=False):
        categorias = self.db.get_categorias()
        if not categorias:
            mostrar_advertencia("No hay categorías registradas")
            esperar_tecla()
            return
        # Ordenar por código CDJ numérico
        categorias.sort(key=lambda c: int(c.codigo_cdj))
        datos = []
        for c in categorias:
            cdj = c.codigo_cdj.zfill(2)
            if modo_simple:
                datos.append([cdj, c.nombre])
            else:
                datos.append([cdj, c.nombre, c.descripcion])
        if modo_simple:
            mostrar_tabla(["Código CDJ", "Nombre"], datos)
        else:
            limpiar_pantalla()
            mostrar_titulo("LISTA DE CATEGORÍAS")
            mostrar_tabla(["Código CDJ", "Nombre", "Descripción"], datos)
            esperar_tecla()

    def exportar_csv(self, nombre_archivo, encabezados, datos):
        # Crear la carpeta si no existe
        carpeta_descargas = os.path.join(os.getcwd(), "Descargas Sistema")
        if not os.path.exists(carpeta_descargas):
            os.makedirs(carpeta_descargas)
        
        # Generar nombre de archivo con fecha
        fecha_actual = datetime.now().strftime("%Y%m%d%H%M")
        nombre_archivo_con_fecha = f"{fecha_actual}_{nombre_archivo}"
        
        # Guardar el archivo en la carpeta de descargas
        ruta = os.path.join(carpeta_descargas, nombre_archivo_con_fecha)
        with open(ruta, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(encabezados)
            writer.writerows(datos)
        mostrar_exito(f"Archivo CSV generado: {nombre_archivo_con_fecha}")

    def listar_historico_prestamos(self):
        limpiar_pantalla()
        mostrar_titulo("HISTÓRICO DE PRÉSTAMOS")
        prestamos = self.db.get_todos_prestamos()
        if not prestamos:
            mostrar_advertencia("No hay préstamos registrados")
            esperar_tecla()
            return
        datos = []
        for p in prestamos:
            usuario = self.db.get_usuario_por_id(p.usuario_id)
            libro = self.db.get_libro_por_id(p.libro_id)
            if not usuario or not libro:
                continue
            datos.append([
                usuario.nombre,
                libro.codigo_cdj,
                libro.isbn,
                libro.titulo,
                libro.autor,
                formatear_fecha(p.fecha_prestamo),
                formatear_fecha(p.fecha_devolucion),
                p.estado
            ])
        mostrar_tabla(["Usuario", "CDJ", "ISBN", "Título", "Autor", "F. Préstamo", "F. Devolución", "Estado"], datos)
        if confirmar_accion("¿Desea exportar este informe a un archivo CSV?"):
            self.exportar_csv("prestamos_historico.csv", ["Usuario", "CDJ", "ISBN", "Título", "Autor", "F. Préstamo", "F. Devolución", "Estado"], datos)
        esperar_tecla()

    def modificar_mis_datos(self):
        """Permite al usuario modificar su contraseña, dirección y correo electrónico"""
        limpiar_pantalla()
        mostrar_titulo("MODIFICAR MIS DATOS")
        usuario = self.usuario_actual
        print("="*50)
        print(f"  Nombre de usuario: {usuario.nombre}")
        print(f"  Teléfono: {usuario.telefono}")
        print(f"  DNI: {usuario.dni}")
        print("="*50)
        # Validar nueva contraseña si se ingresa
        while True:
            password = input("Nueva contraseña (opcional, mínimo 6 caracteres): ").strip()
            if password and len(password) < 6:
                mostrar_error("La contraseña debe tener al menos 6 caracteres.")
                continue
            break
        # Validar email
        while True:
            email = input(f"Email [{usuario.email}]: ").strip()
            if not email:
                email = usuario.email
                break
            if not re.match(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,3}(\.[A-Za-z]{2})?$', email):
                mostrar_error("Formato de correo electrónico inválido.")
                continue
            break
        direccion = input(f"Dirección [{usuario.direccion}]: ").strip()
        if password:
            usuario.password = password
        if email:
            usuario.email = email
        if direccion:
            usuario.direccion = direccion
        if self.db.actualizar_usuario(usuario):
            mostrar_exito("Datos modificados correctamente")
        else:
            mostrar_error("Error al modificar los datos")
        esperar_tecla()

    def aprobar_prestamos_pendientes(self):
        try:
            limpiar_pantalla()
            mostrar_titulo("APROBAR SOLICITUDES DE PRÉSTAMO")
            prestamos = self.db.get_prestamos_pendientes()
            if not prestamos:
                mostrar_advertencia("No hay solicitudes pendientes")
                esperar_tecla()
                return
            for p in prestamos:
                usuario = self.db.get_usuario_por_id(p.usuario_id)
                libro = self.db.get_libro_por_id(p.libro_id)
                print(f"\nUsuario: {usuario.nombre if usuario else '-'} | Libro: {libro.titulo if libro else '-'} | Fecha Solicitud: {formatear_fecha(p.fecha_prestamo)}")
                print(f"Estado actual: {p.estado}")
                opcion = input("¿Aprobar (a), Rechazar (r), Omitir (Enter)? ").strip().lower()
                if opcion == "a":
                    if self.db.tiene_prestamo_activo(usuario.id, libro.id):
                        self.db.actualizar_estado_prestamo(p.id, "rechazado")
                        mostrar_error("El usuario ya tiene un préstamo activo de este libro. La solicitud fue rechazada automáticamente.")
                        continue
                    prestamos_activos_libro = self.db.buscar_prestamos_activos_por_libro(libro.id)
                    cantidad_prestados = len([pr for pr in prestamos_activos_libro if pr.estado == "activo"])
                    if cantidad_prestados >= libro.cantidad:
                        mostrar_error("No hay ejemplares disponibles para aprobar este préstamo.")
                        continue
                    if self.db.actualizar_estado_prestamo(p.id, "activo"):
                        self.actualizar_estado_libro_por_disponibilidad(libro.id)
                        mostrar_exito("Préstamo aprobado y libro asignado.")
                    else:
                        mostrar_error("Error al aprobar el préstamo")
                elif opcion == "r":
                    if self.db.actualizar_estado_prestamo(p.id, "rechazado"):
                        mostrar_exito("Préstamo rechazado.")
                    else:
                        mostrar_error("Error al rechazar el préstamo")
            esperar_tecla()
        except Exception as e:
            mostrar_error(f"Ocurrió un error inesperado durante la aprobación de préstamos: {str(e)}")
            esperar_tecla()

    def ejecutar(self):
        """Método principal que ejecuta el sistema"""
        try:
            while True:
                if self.iniciar_sesion():
                    self.menu_principal()
                else:
                    break
        except Exception as e:
            mostrar_error(f"Error inesperado: {str(e)}")
        finally:
            self.db.close()
            mostrar_exito("¡Gracias por usar el sistema!")

    def actualizar_estado_libro_por_disponibilidad(self, libro_id):
        libro = self.db.get_libro_por_id(libro_id)
        if not libro:
            return
        prestamos = self.db.buscar_prestamos_activos_por_libro(libro_id)
        cantidad_prestados = len([p for p in prestamos if p.estado == "activo"])
        cantidad_pendientes = len([p for p in prestamos if p.estado == "pendiente"])
        disponibles = libro.cantidad - cantidad_prestados - cantidad_pendientes
        if disponibles > 0:
            nuevo_estado = "disponible"
        elif cantidad_pendientes > 0:
            nuevo_estado = "reservado"
        else:
            nuevo_estado = "prestado"
        self.db.actualizar_estado_libro(libro_id, nuevo_estado)

if __name__ == "__main__":
    sistema = SistemaBiblioteca()
    sistema.ejecutar() 