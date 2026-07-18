# ================================================================
# AgendaSalud - Sistema Web de Escritorio para Gestión de Citas
# Dispensario "La Dolorosa" - Grupo 2
# Ingeniería de Software 1 - Universidad Agraria del Ecuador
# Archivo: main.py - Ejecutable directo en VS Code
# ================================================================

# --- BLOQUE 1: INSTALACIÓN AUTOMÁTICA DE DEPENDENCIAS ---
# Este bloque garantiza que el programa funcione aunque falten librerías
import sys # Importa sys para acceder al ejecutable de Python y argumentos del sistema
import subprocess # Importa subprocess para ejecutar comandos pip desde el código
import os # Importa os para manejo de rutas de archivos

def instalar_librerias(): # Define función que instala librerías automáticamente
    """Instala automáticamente librerías opcionales si no existen""" # Docstring explica función
    librerias_opcionales = ["tkcalendar"] # Lista de librerías opcionales que mejoran la app
    for lib in librerias_opcionales: # Recorre cada librería de la lista
        try: # Intenta importar
            __import__(lib) # Intenta importar la librería
            print(f"✓ Librería {lib} ya instalada") # Si existe, muestra check
        except ImportError: # Si no existe, captura error
            try: # Intenta instalar
                print(f"→ Instalando {lib}...") # Mensaje instalando
                subprocess.check_call([sys.executable, "-m", "pip", "install", lib, "--quiet"]) # Ejecuta pip install silencioso
                print(f"✓ {lib} instalada correctamente") # Confirma instalación
            except Exception as e: # Si falla instalación (sin internet)
                print(f"! No se pudo instalar {lib}: {e} - se usará modo básico") # Avisa que usará modo básico sin esa librería

# Llama a la función de instalación automática al iniciar
instalar_librerias() # Ejecuta instalación antes de iniciar la app

# --- BLOQUE 2: IMPORTACIONES PRINCIPALES ---
# Todas estas librerías son estándar de Python (no necesitan internet)
import sqlite3 # Importa sqlite3 para base de datos local sin servidor
import tkinter as tk # Importa tkinter para interfaz gráfica de escritorio
from tkinter import ttk # Importa ttk para widgets modernos (tablas, combos)
from tkinter import messagebox # Importa messagebox para mostrar alertas y confirmaciones
from datetime import datetime, timedelta, date, time # Importa manejo de fechas y horas
import hashlib # Importa hashlib para encriptar contraseñas con SHA256
import re # Importa re para expresiones regulares (validar cédula, teléfono)

# Intento de importar tkcalendar (opcional, si no existe usa Entry normal)
try: # Intenta importar calendario visual
    from tkcalendar import DateEntry # Importa DateEntry para selector de fecha bonito
    TIENE_CALENDARIO = True # Marca que sí tiene calendario visual
except ImportError: # Si no está instalado
    TIENE_CALENDARIO = False # Marca que usará Entry de texto normal

# --- BLOQUE 3: UTILIDADES Y VALIDACIONES ---

def validar_cedula_ecuatoriana(cedula): # Define función que valida cédula ecuatoriana
    """Valida cédula ecuatoriana con algoritmo módulo 10""" # Docstring
    if not cedula.isdigit(): # Verifica que solo tenga dígitos
        return False # Si tiene letras, no válida
    if len(cedula) != 10: # Verifica longitud exacta 10
        return False # Si no tiene 10, no válida
    # Algoritmo oficial del Registro Civil Ecuador
    coeficientes = [2, 1, 2, 1, 2, 1, 2, 1, 2] # Coeficientes para multiplicar
    total = 0 # Inicializa acumulador
    for i in range(9): # Recorre primeros 9 dígitos
        valor = int(cedula[i]) * coeficientes[i] # Multiplica dígito por coeficiente
        if valor >= 10: # Si resultado >=10
            valor -= 9 # Resta 9 (suma de dígitos)
        total += valor # Suma al total
    digito_verificador = (10 - (total % 10)) % 10 # Calcula dígito verificador esperado
    return digito_verificador == int(cedula[9]) # Compara con último dígito

def encriptar_password(password): # Define función para encriptar contraseñas
    """Encripta contraseña con SHA256 para seguridad""" # Docstring
    return hashlib.sha256(password.encode()).hexdigest() # Convierte a hash SHA256

# --- BLOQUE 4: GESTOR DE BASE DE DATOS ---

class DatabaseManager: # Define clase que maneja toda la base de datos
    def __init__(self, db_name="agendasalud.db"): # Constructor, recibe nombre BD
        self.db_name = db_name # Guarda nombre BD en atributo
        self.init_database() # Llama a inicializar BD al crear objeto

    def get_connection(self): # Define método que obtiene conexión a BD
        conn = sqlite3.connect(self.db_name) # Conecta a archivo SQLite
        conn.row_factory = sqlite3.Row # Configura para acceder por nombre columna
        return conn # Retorna conexión

    def init_database(self): # Define método que crea tablas si no existen
        conn = self.get_connection() # Obtiene conexión
        cursor = conn.cursor() # Crea cursor para ejecutar SQL

        # Tabla pacientes - RF-01
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pacientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cedula TEXT UNIQUE NOT NULL,
                nombres TEXT NOT NULL,
                apellidos TEXT NOT NULL,
                telefono TEXT,
                direccion TEXT,
                fecha_nacimiento TEXT,
                fecha_registro TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """) # Ejecuta SQL crear tabla pacientes

        # Tabla especialidades - RF-03
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS especialidades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL,
                descripcion TEXT
            )
        """) # Crea tabla especialidades

        # Tabla médicos - RF-02
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS medicos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombres TEXT NOT NULL,
                especialidad_id INTEGER,
                horario_inicio TEXT DEFAULT '08:00',
                horario_fin TEXT DEFAULT '17:00',
                estado TEXT DEFAULT 'Activo',
                FOREIGN KEY (especialidad_id) REFERENCES especialidades(id)
            )
        """) # Crea tabla médicos con FK especialidad

        # Tabla citas - RF-04, RF-05, RF-06, RF-07
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS citas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paciente_id INTEGER NOT NULL,
                medico_id INTEGER NOT NULL,
                fecha TEXT NOT NULL,
                hora TEXT NOT NULL,
                estado TEXT DEFAULT 'Pendiente',
                consultorio TEXT DEFAULT 'Consultorio 1',
                fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (paciente_id) REFERENCES pacientes(id),
                FOREIGN KEY (medico_id) REFERENCES medicos(id),
                UNIQUE(medico_id, fecha, hora)
            )
        """) # Crea tabla citas con restricción UNIQUE para evitar cruces horarios

        # Tabla usuarios - RF-11
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                rol TEXT NOT NULL,
                nombre_completo TEXT
            )
        """) # Crea tabla usuarios para login

        # Insertar datos iniciales si no existen
        self.insertar_datos_iniciales(cursor) # Llama a insertar datos prueba

        conn.commit() # Guarda cambios
        conn.close() # Cierra conexión

    def insertar_datos_iniciales(self, cursor): # Define método inserta datos de prueba
        # Verifica si ya hay usuarios
        cursor.execute("SELECT COUNT(*) as total FROM usuarios") # Cuenta usuarios
        if cursor.fetchone()["total"] == 0: # Si no hay usuarios
            # Inserta usuarios de prueba con contraseñas encriptadas
            cursor.execute("INSERT INTO usuarios (username, password, rol, nombre_completo) VALUES (?, ?, ?, ?)",
                           ("admin", encriptar_password("Admin123*"), "Administrativo", "Administrador Sistema")) # Inserta admin
            cursor.execute("INSERT INTO usuarios (username, password, rol, nombre_completo) VALUES (?, ?, ?, ?)",
                           ("medico1", encriptar_password("Medico123*"), "Médico", "Dr. Juan Pérez")) # Inserta médico
            print("✓ Usuarios de prueba creados: admin/Admin123* y medico1/Medico123*") # Mensaje consola

        # Especialidades iniciales
        cursor.execute("SELECT COUNT(*) as total FROM especialidades") # Cuenta especialidades
        if cursor.fetchone()["total"] == 0: # Si no hay
            especialidades = [("Medicina General", "Atención primaria"), ("Odontología", "Salud bucal"), ("Pediatría", "Niños"), ("Ginecología", "Salud femenina")] # Lista especialidades
            for nombre, desc in especialidades: # Recorre lista
                cursor.execute("INSERT INTO especialidades (nombre, descripcion) VALUES (?, ?)", (nombre, desc)) # Inserta cada una

        # Médicos iniciales
        cursor.execute("SELECT COUNT(*) as total FROM medicos") # Cuenta médicos
        if cursor.fetchone()["total"] == 0: # Si no hay
            cursor.execute("SELECT id FROM especialidades WHERE nombre='Medicina General'") # Obtiene id medicina general
            esp_id = cursor.fetchone()["id"] # Guarda id
            cursor.execute("INSERT INTO medicos (nombres, especialidad_id, horario_inicio, horario_fin) VALUES (?, ?, ?, ?)",
                           ("Dra. María López", esp_id, "08:00", "12:00")) # Inserta médico 1
            cursor.execute("INSERT INTO medicos (nombres, especialidad_id, horario_inicio, horario_fin) VALUES (?, ?, ?, ?)",
                           ("Dr. Carlos Ruiz", esp_id, "14:00", "17:00")) # Inserta médico 2

# Instancia global de BD
db_manager = DatabaseManager() # Crea gestor BD global al iniciar programa

# --- BLOQUE 5: VENTANA DE LOGIN ---

class LoginWindow: # Define clase ventana login
    def __init__(self, root): # Constructor recibe ventana principal
        self.root = root # Guarda referencia ventana
        self.root.title("AgendaSalud - Login - Dispensario La Dolorosa") # Título ventana
        self.root.geometry("400x350") # Tamaño ventana
        self.root.configure(bg="#f0f4f8") # Color fondo

        # Frame central
        frame = tk.Frame(root, bg="white", padx=20, pady=20, bd=1, relief="solid") # Crea frame blanco con borde
        frame.place(relx=0.5, rely=0.5, anchor="center") # Centra frame

        tk.Label(frame, text="AgendaSalud", font=("Arial", 20, "bold"), bg="white", fg="#2E86C1").pack(pady=10) # Título grande
        tk.Label(frame, text='Dispensario "La Dolorosa"', font=("Arial", 10), bg="white").pack() # Subtítulo
        tk.Label(frame, text="Inicio de Sesión", font=("Arial", 12, "bold"), bg="white").pack(pady=10) # Label login

        tk.Label(frame, text="Usuario:", bg="white").pack(anchor="w") # Label usuario
        self.entry_user = tk.Entry(frame, width=30, font=("Arial", 11)) # Campo texto usuario
        self.entry_user.pack(pady=5) # Coloca campo
        self.entry_user.insert(0, "admin") # Valor por defecto para prueba rápida

        tk.Label(frame, text="Contraseña:", bg="white").pack(anchor="w") # Label contraseña
        self.entry_pass = tk.Entry(frame, width=30, show="*", font=("Arial", 11)) # Campo contraseña oculto con *
        self.entry_pass.pack(pady=5) # Coloca campo
        self.entry_pass.insert(0, "Admin123*") # Valor por defecto

        tk.Button(frame, text="Iniciar Sesión", bg="#2E86C1", fg="white", font=("Arial", 11, "bold"),
                  command=self.validar_login, width=20).pack(pady=15) # Botón login que llama validar_login

        tk.Label(frame, text="Usuarios prueba:\nadmin / Admin123* (Admin)\nmedico1 / Medico123* (Médico)",
                 font=("Arial", 8), bg="white", fg="gray", justify="left").pack() # Ayuda usuarios

        self.entry_pass.bind("<Return>", lambda e: self.validar_login()) # Permite Enter para login

    def validar_login(self): # Define método valida credenciales
        username = self.entry_user.get().strip() # Obtiene usuario sin espacios
        password = self.entry_pass.get().strip() # Obtiene contraseña sin espacios

        if not username or not password: # Verifica campos vacíos
            messagebox.showerror("Error", "Ingrese usuario y contraseña") # Muestra error
            return # Sale

        conn = db_manager.get_connection() # Conecta BD
        cursor = conn.cursor() # Crea cursor
        cursor.execute("SELECT * FROM usuarios WHERE username=?", (username,)) # Busca usuario
        user = cursor.fetchone() # Obtiene resultado
        conn.close() # Cierra conexión

        if user and user["password"] == encriptar_password(password): # Verifica existe y contraseña coincide encriptada
            messagebox.showinfo("Bienvenido", f"Bienvenido {user['nombre_completo']} - Rol: {user['rol']}") # Mensaje bienvenida
            self.root.destroy() # Cierra ventana login
            # Abre ventana principal
            main_root = tk.Tk() # Crea nueva ventana principal
            app = MainApp(main_root, user) # Instancia app principal con datos usuario
            main_root.mainloop() # Inicia loop principal
        else: # Si no coincide
            messagebox.showerror("Error", "Usuario o contraseña incorrectos") # Muestra error login

# --- BLOQUE 6: APLICACIÓN PRINCIPAL ---

class MainApp: # Define clase aplicación principal con todas las funcionalidades
    def __init__(self, root, usuario): # Constructor recibe ventana y usuario logueado
        self.root = root # Guarda ventana
        self.usuario = usuario # Guarda datos usuario logueado
        self.root.title(f"AgendaSalud - {usuario['nombre_completo']} ({usuario['rol']}) - Dispensario La Dolorosa") # Título con usuario y rol
        self.root.geometry("1200x700") # Tamaño ventana grande
        self.root.configure(bg="#f0f4f8") # Color fondo

        # Notebook con pestañas (Pacientes, Médicos, etc.)
        self.notebook = ttk.Notebook(root) # Crea sistema de pestañas
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10) # Expande en ventana

        # Crea cada pestaña
        self.tab_pacientes = tk.Frame(self.notebook, bg="white") # Frame pestaña pacientes
        self.tab_medicos = tk.Frame(self.notebook, bg="white") # Frame médicos
        self.tab_especialidades = tk.Frame(self.notebook, bg="white") # Frame especialidades
        self.tab_agendar = tk.Frame(self.notebook, bg="white") # Frame agendar
        self.tab_panel = tk.Frame(self.notebook, bg="white") # Frame panel día

        self.notebook.add(self.tab_pacientes, text="Pacientes (RF-01, RF-09)") # Añade pestaña pacientes con icono
        self.notebook.add(self.tab_medicos, text="Medicos (RF-02)") # Añade médicos
        self.notebook.add(self.tab_especialidades, text="Especialidades (RF-03)") # Añade especialidades
        self.notebook.add(self.tab_agendar, text="Agendar Cita (RF-04, RF-07)") # Añade agendar
        self.notebook.add(self.tab_panel, text="Panel Citas del Dia (RF-08)") # Añade panel día

        # Inicializa cada pestaña con sus controles
        self.init_pacientes() # Inicializa UI pacientes
        self.init_medicos() # Inicializa médicos
        self.init_especialidades() # Inicializa especialidades
        self.init_agendar() # Inicializa agendar
        self.init_panel() # Inicializa panel

        # Barra estado inferior
        tk.Label(root, text=f"Usuario: {usuario['username']} | Rol: {usuario['rol']} | AgendaSalud v1.0 MVP - Grupo 2",
                 bg="#2E86C1", fg="white", anchor="w").pack(fill="x", side="bottom") # Label estado con info usuario

    # --- PESTAÑA PACIENTES ---
    def init_pacientes(self): # Define inicialización pestaña pacientes
        # Frame búsqueda
        frame_search = tk.Frame(self.tab_pacientes, bg="white") # Frame superior búsqueda
        frame_search.pack(fill="x", padx=10, pady=10) # Coloca frame

        tk.Label(frame_search, text="Buscar por cédula o nombre:", bg="white").pack(side="left") # Label búsqueda
        self.entry_buscar_pac = tk.Entry(frame_search, width=30) # Campo búsqueda
        self.entry_buscar_pac.pack(side="left", padx=10) # Coloca campo
        tk.Button(frame_search, text="Buscar", command=self.buscar_pacientes, bg="#2E86C1", fg="white").pack(side="left") # Botón buscar
        tk.Button(frame_search, text="Mostrar Todos", command=self.cargar_pacientes).pack(side="left", padx=5) # Botón mostrar todos

        # Tabla pacientes
        columns = ("ID", "Cédula", "Nombres", "Apellidos", "Teléfono", "Dirección") # Columnas tabla
        self.tree_pac = ttk.Treeview(self.tab_pacientes, columns=columns, show="headings", height=15) # Crea tabla
        for col in columns: # Recorre columnas
            self.tree_pac.heading(col, text=col) # Pone título columna
            self.tree_pac.column(col, width=120) # Ancho columna
        self.tree_pac.pack(fill="both", expand=True, padx=10, pady=10) # Expande tabla

        # Frame formulario
        frame_form = tk.LabelFrame(self.tab_pacientes, text="Registro / Edición Paciente - RF-01", bg="white", padx=10, pady=10) # Frame con borde y título
        frame_form.pack(fill="x", padx=10, pady=5) # Coloca frame

        tk.Label(frame_form, text="Cédula (10 dígitos):", bg="white").grid(row=0, column=0, sticky="w") # Label cédula
        self.entry_cedula = tk.Entry(frame_form, width=15) # Campo cédula
        self.entry_cedula.grid(row=0, column=1, padx=5, pady=2) # Posiciona en grid

        tk.Label(frame_form, text="Nombres:", bg="white").grid(row=0, column=2, sticky="w") # Label nombres
        self.entry_nombres = tk.Entry(frame_form, width=20) # Campo nombres
        self.entry_nombres.grid(row=0, column=3, padx=5) # Posiciona

        tk.Label(frame_form, text="Apellidos:", bg="white").grid(row=0, column=4, sticky="w") # Label apellidos
        self.entry_apellidos = tk.Entry(frame_form, width=20) # Campo apellidos
        self.entry_apellidos.grid(row=0, column=5, padx=5) # Posiciona

        tk.Label(frame_form, text="Teléfono:", bg="white").grid(row=1, column=0, sticky="w") # Label teléfono
        self.entry_telefono = tk.Entry(frame_form, width=15) # Campo teléfono
        self.entry_telefono.grid(row=1, column=1, padx=5, pady=2) # Posiciona

        tk.Label(frame_form, text="Dirección:", bg="white").grid(row=1, column=2, sticky="w") # Label dirección
        self.entry_direccion = tk.Entry(frame_form, width=40) # Campo dirección
        self.entry_direccion.grid(row=1, column=3, columnspan=3, padx=5, sticky="w") # Posiciona abarcando columnas

        tk.Button(frame_form, text="Guardar Paciente", bg="#27AE60", fg="white", command=self.guardar_paciente).grid(row=0, column=6, rowspan=2, padx=10) # Botón guardar
        tk.Button(frame_form, text="Limpiar", command=self.limpiar_paciente).grid(row=0, column=7, rowspan=2) # Botón limpiar

        self.cargar_pacientes() # Carga pacientes al iniciar

    def cargar_pacientes(self): # Define método carga pacientes en tabla
        for item in self.tree_pac.get_children(): # Recorre filas actuales tabla
            self.tree_pac.delete(item) # Borra cada fila para recargar
        conn = db_manager.get_connection() # Conecta BD
        cursor = conn.cursor() # Crea cursor
        cursor.execute("SELECT * FROM pacientes ORDER BY id DESC") # Consulta todos pacientes
        for row in cursor.fetchall(): # Recorre cada paciente
            self.tree_pac.insert("", "end", values=(row["id"], row["cedula"], row["nombres"], row["apellidos"], row["telefono"], row["direccion"])) # Inserta fila en tabla
        conn.close() # Cierra conexión

    def buscar_pacientes(self): # Define método búsqueda pacientes RF-09
        texto = self.entry_buscar_pac.get().strip() # Obtiene texto búsqueda
        if not texto: # Si vacío
            self.cargar_pacientes() # Muestra todos
            return # Sale
        for item in self.tree_pac.get_children(): # Limpia tabla
            self.tree_pac.delete(item) # Borra filas
        conn = db_manager.get_connection() # Conecta BD
        cursor = conn.cursor() # Cursor
        cursor.execute("SELECT * FROM pacientes WHERE cedula LIKE ? OR nombres LIKE ? OR apellidos LIKE ?",
                       (f"%{texto}%", f"%{texto}%", f"%{texto}%")) # Consulta con LIKE búsqueda parcial
        for row in cursor.fetchall(): # Recorre resultados
            self.tree_pac.insert("", "end", values=(row["id"], row["cedula"], row["nombres"], row["apellidos"], row["telefono"], row["direccion"])) # Inserta en tabla
        conn.close() # Cierra

    def guardar_paciente(self): # Define método guardar paciente RF-01
        cedula = self.entry_cedula.get().strip() # Obtiene cédula
        nombres = self.entry_nombres.get().strip() # Obtiene nombres
        apellidos = self.entry_apellidos.get().strip() # Obtiene apellidos
        telefono = self.entry_telefono.get().strip() # Obtiene teléfono
        direccion = self.entry_direccion.get().strip() # Obtiene dirección

        if not cedula or not nombres or not apellidos: # Valida campos obligatorios
            messagebox.showerror("Error", "Cédula, nombres y apellidos son obligatorios") # Muestra error
            return # Sale

        if not validar_cedula_ecuatoriana(cedula): # Valida cédula con algoritmo
            messagebox.showerror("Error", f"Cédula {cedula} no válida - debe ser ecuatoriana de 10 dígitos") # Error cédula
            return # Sale

        conn = db_manager.get_connection() # Conecta BD
        cursor = conn.cursor() # Cursor
        try: # Intenta insertar
            cursor.execute("INSERT INTO pacientes (cedula, nombres, apellidos, telefono, direccion) VALUES (?, ?, ?, ?, ?)",
                           (cedula, nombres, apellidos, telefono, direccion)) # Inserta paciente
            conn.commit() # Guarda
            messagebox.showinfo("Éxito", f"Paciente {nombres} {apellidos} registrado correctamente") # Éxito
            self.limpiar_paciente() # Limpia formulario
            self.cargar_pacientes() # Recarga tabla
        except sqlite3.IntegrityError: # Si cédula duplicada
            messagebox.showerror("Error", f"Ya existe paciente con cédula {cedula}") # Error duplicado
        finally: # Siempre
            conn.close() # Cierra conexión

    def limpiar_paciente(self): # Define método limpia formulario paciente
        self.entry_cedula.delete(0, tk.END) # Borra campo cédula
        self.entry_nombres.delete(0, tk.END) # Borra nombres
        self.entry_apellidos.delete(0, tk.END) # Borra apellidos
        self.entry_telefono.delete(0, tk.END) # Borra teléfono
        self.entry_direccion.delete(0, tk.END) # Borra dirección

    # --- PESTAÑA MÉDICOS ---
    def init_medicos(self): # Define inicialización pestaña médicos
        columns = ("ID", "Nombres", "Especialidad", "Horario Inicio", "Horario Fin", "Estado") # Columnas
        self.tree_med = ttk.Treeview(self.tab_medicos, columns=columns, show="headings", height=15) # Tabla médicos
        for col in columns: # Configura columnas
            self.tree_med.heading(col, text=col) # Título
            self.tree_med.column(col, width=130) # Ancho
        self.tree_med.pack(fill="both", expand=True, padx=10, pady=10) # Expande

        frame_form = tk.LabelFrame(self.tab_medicos, text="Registro Médico - RF-02", bg="white", padx=10, pady=10) # Frame formulario
        frame_form.pack(fill="x", padx=10, pady=5) # Coloca

        tk.Label(frame_form, text="Nombres:", bg="white").grid(row=0, column=0, sticky="w") # Label nombres
        self.entry_med_nombre = tk.Entry(frame_form, width=25) # Campo nombres médico
        self.entry_med_nombre.grid(row=0, column=1, padx=5) # Posiciona

        tk.Label(frame_form, text="Especialidad:", bg="white").grid(row=0, column=2, sticky="w") # Label especialidad
        self.combo_especialidad = ttk.Combobox(frame_form, width=20, state="readonly") # Combo especialidades
        self.combo_especialidad.grid(row=0, column=3, padx=5) # Posiciona

        tk.Label(frame_form, text="Horario:", bg="white").grid(row=0, column=4, sticky="w") # Label horario
        self.entry_horario_ini = tk.Entry(frame_form, width=8) # Campo hora inicio
        self.entry_horario_ini.insert(0, "08:00") # Valor por defecto
        self.entry_horario_ini.grid(row=0, column=5, padx=2) # Posiciona
        self.entry_horario_fin = tk.Entry(frame_form, width=8) # Campo hora fin
        self.entry_horario_fin.insert(0, "17:00") # Valor por defecto
        self.entry_horario_fin.grid(row=0, column=6, padx=2) # Posiciona

        tk.Button(frame_form, text="Guardar Médico", bg="#27AE60", fg="white", command=self.guardar_medico).grid(row=0, column=7, padx=10) # Botón guardar

        self.cargar_medicos() # Carga médicos
        self.cargar_combo_especialidades() # Carga combo especialidades

    def cargar_combo_especialidades(self): # Define método carga combo especialidades
        conn = db_manager.get_connection() # Conecta BD
        cursor = conn.cursor() # Cursor
        cursor.execute("SELECT id, nombre FROM especialidades") # Consulta especialidades
        self.lista_esp = cursor.fetchall() # Guarda lista
        self.combo_especialidad["values"] = [f"{r['id']} - {r['nombre']}" for r in self.lista_esp] # Llena combo con id - nombre
        conn.close() # Cierra

    def cargar_medicos(self): # Define método carga médicos en tabla
        for item in self.tree_med.get_children(): # Limpia tabla
            self.tree_med.delete(item) # Borra fila
        conn = db_manager.get_connection() # Conecta
        cursor = conn.cursor() # Cursor
        cursor.execute("""
            SELECT m.id, m.nombres, e.nombre as esp_nombre, m.horario_inicio, m.horario_fin, m.estado
            FROM medicos m LEFT JOIN especialidades e ON m.especialidad_id = e.id
        """) # Consulta con JOIN especialidad
        for row in cursor.fetchall(): # Recorre
            self.tree_med.insert("", "end", values=(row["id"], row["nombres"], row["esp_nombre"], row["horario_inicio"], row["horario_fin"], row["estado"])) # Inserta fila
        conn.close() # Cierra

    def guardar_medico(self): # Define método guarda médico RF-02
        nombres = self.entry_med_nombre.get().strip() # Obtiene nombres
        esp_text = self.combo_especialidad.get() # Obtiene texto combo especialidad
        h_ini = self.entry_horario_ini.get().strip() # Obtiene hora inicio
        h_fin = self.entry_horario_fin.get().strip() # Obtiene hora fin

        if not nombres or not esp_text: # Valida obligatorios
            messagebox.showerror("Error", "Nombres y especialidad obligatorios") # Error
            return # Sale

        try: # Intenta extraer id especialidad
            esp_id = int(esp_text.split(" - ")[0]) # Separa por " - " y toma id
        except: # Si falla
            messagebox.showerror("Error", "Seleccione especialidad válida") # Error
            return # Sale

        conn = db_manager.get_connection() # Conecta
        cursor = conn.cursor() # Cursor
        cursor.execute("INSERT INTO medicos (nombres, especialidad_id, horario_inicio, horario_fin) VALUES (?, ?, ?, ?)",
                       (nombres, esp_id, h_ini, h_fin)) # Inserta médico
        conn.commit() # Guarda
        conn.close() # Cierra
        messagebox.showinfo("Éxito", f"Médico {nombres} registrado") # Éxito
        self.cargar_medicos() # Recarga tabla
        self.entry_med_nombre.delete(0, tk.END) # Limpia campo

    # --- PESTAÑA ESPECIALIDADES ---
    def init_especialidades(self): # Define inicialización especialidades
        columns = ("ID", "Nombre", "Descripción") # Columnas
        self.tree_esp = ttk.Treeview(self.tab_especialidades, columns=columns, show="headings", height=15) # Tabla especialidades
        for col in columns: # Configura
            self.tree_esp.heading(col, text=col) # Título
            self.tree_esp.column(col, width=200) # Ancho
        self.tree_esp.pack(fill="both", expand=True, padx=10, pady=10) # Expande

        frame = tk.LabelFrame(self.tab_especialidades, text="Nueva Especialidad - RF-03", bg="white", padx=10, pady=10) # Frame formulario
        frame.pack(fill="x", padx=10, pady=5) # Coloca

        tk.Label(frame, text="Nombre:", bg="white").pack(side="left") # Label nombre
        self.entry_esp_nombre = tk.Entry(frame, width=25) # Campo nombre especialidad
        self.entry_esp_nombre.pack(side="left", padx=5) # Coloca

        tk.Label(frame, text="Descripción:", bg="white").pack(side="left") # Label descripción
        self.entry_esp_desc = tk.Entry(frame, width=30) # Campo descripción
        self.entry_esp_desc.pack(side="left", padx=5) # Coloca

        tk.Button(frame, text="Guardar", bg="#27AE60", fg="white", command=self.guardar_especialidad).pack(side="left", padx=10) # Botón guardar

        self.cargar_especialidades() # Carga especialidades

    def cargar_especialidades(self): # Define método carga especialidades
        for item in self.tree_esp.get_children(): # Limpia tabla
            self.tree_esp.delete(item) # Borra fila
        conn = db_manager.get_connection() # Conecta
        cursor = conn.cursor() # Cursor
        cursor.execute("SELECT * FROM especialidades") # Consulta
        for row in cursor.fetchall(): # Recorre
            self.tree_esp.insert("", "end", values=(row["id"], row["nombre"], row["descripcion"])) # Inserta
        conn.close() # Cierra

    def guardar_especialidad(self): # Define método guarda especialidad RF-03
        nombre = self.entry_esp_nombre.get().strip() # Obtiene nombre
        desc = self.entry_esp_desc.get().strip() # Obtiene descripción
        if not nombre: # Valida obligatorio
            messagebox.showerror("Error", "Nombre obligatorio") # Error
            return # Sale
        conn = db_manager.get_connection() # Conecta
        cursor = conn.cursor() # Cursor
        try: # Intenta insertar
            cursor.execute("INSERT INTO especialidades (nombre, descripcion) VALUES (?, ?)", (nombre, desc)) # Inserta
            conn.commit() # Guarda
            messagebox.showinfo("Éxito", f"Especialidad {nombre} creada") # Éxito
            self.cargar_especialidades() # Recarga tabla
            self.cargar_combo_especialidades() # Actualiza combo médicos
            self.entry_esp_nombre.delete(0, tk.END) # Limpia
            self.entry_esp_desc.delete(0, tk.END) # Limpia
        except sqlite3.IntegrityError: # Si duplicado
            messagebox.showerror("Error", "Especialidad ya existe") # Error duplicado
        finally: # Siempre
            conn.close() # Cierra

    # --- PESTAÑA AGENDAR CITA ---
    def init_agendar(self): # Define inicialización agendar cita RF-04
        frame = tk.LabelFrame(self.tab_agendar, text="Agendar Nueva Cita - RF-04 Validación Disponibilidad", bg="white", padx=10, pady=10) # Frame agendar
        frame.pack(fill="x", padx=10, pady=10) # Coloca

        tk.Label(frame, text="Cédula Paciente:", bg="white").grid(row=0, column=0, sticky="w") # Label cédula paciente
        self.entry_ag_pac_cedula = tk.Entry(frame, width=15) # Campo cédula paciente para agendar
        self.entry_ag_pac_cedula.grid(row=0, column=1, padx=5) # Posiciona
        tk.Button(frame, text="Buscar Paciente", command=self.buscar_paciente_agendar).grid(row=0, column=2) # Botón buscar paciente
        self.label_pac_info = tk.Label(frame, text="Paciente: No seleccionado", bg="white", fg="blue") # Label info paciente seleccionado
        self.label_pac_info.grid(row=0, column=3, columnspan=3, padx=10) # Posiciona
        self.paciente_seleccionado_id = None # Variable guarda id paciente seleccionado

        tk.Label(frame, text="Médico:", bg="white").grid(row=1, column=0, sticky="w", pady=10) # Label médico
        self.combo_ag_medico = ttk.Combobox(frame, width=30, state="readonly") # Combo médicos para agendar
        self.combo_ag_medico.grid(row=1, column=1, columnspan=2, padx=5, pady=10, sticky="w") # Posiciona
        self.combo_ag_medico.bind("<<ComboboxSelected>>", lambda e: self.actualizar_disponibilidad()) # Al seleccionar médico actualiza disponibilidad

        tk.Label(frame, text="Fecha (YYYY-MM-DD):", bg="white").grid(row=1, column=3, sticky="w") # Label fecha
        if TIENE_CALENDARIO: # Si tiene tkcalendar
            self.entry_ag_fecha = DateEntry(frame, width=12, date_pattern='yyyy-mm-dd') # Usa DateEntry calendario visual
        else: # Si no tiene
            self.entry_ag_fecha = tk.Entry(frame, width=12) # Usa Entry normal
            self.entry_ag_fecha.insert(0, datetime.now().strftime("%Y-%m-%d")) # Valor por defecto hoy
        self.entry_ag_fecha.grid(row=1, column=4, padx=5) # Posiciona
        tk.Button(frame, text="Ver Disponibilidad", bg="#2E86C1", fg="white", command=self.actualizar_disponibilidad).grid(row=1, column=5, padx=5) # Botón ver disponibilidad

        # Frame horarios disponibles
        frame_hor = tk.LabelFrame(self.tab_agendar, text="Horarios Disponibles - Verde Libre / Rojo Ocupado - RF-07", bg="white", padx=10, pady=10) # Frame horarios
        frame_hor.pack(fill="both", expand=True, padx=10, pady=5) # Expande

        self.listbox_horarios = tk.Listbox(frame_hor, height=10, font=("Arial", 11)) # Listbox muestra horarios
        self.listbox_horarios.pack(fill="both", expand=True, side="left") # Expande izquierda

        tk.Button(frame_hor, text="Agendar Cita Seleccionada (RF-04)", bg="#27AE60", fg="white", font=("Arial", 12, "bold"),
                  command=self.agendar_cita, height=3, width=25).pack(side="right", padx=20) # Botón agendar grande verde

        self.cargar_combo_medicos_agendar() # Carga combo médicos al iniciar

    def cargar_combo_medicos_agendar(self): # Define método carga combo médicos para agendar
        conn = db_manager.get_connection() # Conecta
        cursor = conn.cursor() # Cursor
        cursor.execute("SELECT id, nombres FROM medicos WHERE estado='Activo'") # Consulta médicos activos
        medicos = cursor.fetchall() # Obtiene lista
        self.combo_ag_medico["values"] = [f"{r['id']} - {r['nombres']}" for r in medicos] # Llena combo
        conn.close() # Cierra

    def buscar_paciente_agendar(self): # Define método busca paciente para agendar
        cedula = self.entry_ag_pac_cedula.get().strip() # Obtiene cédula
        if not cedula: # Si vacía
            messagebox.showerror("Error", "Ingrese cédula paciente") # Error
            return # Sale
        conn = db_manager.get_connection() # Conecta
        cursor = conn.cursor() # Cursor
        cursor.execute("SELECT id, nombres, apellidos FROM pacientes WHERE cedula=?", (cedula,)) # Busca paciente por cédula
        pac = cursor.fetchone() # Obtiene paciente
        conn.close() # Cierra
        if pac: # Si encontró
            self.paciente_seleccionado_id = pac["id"] # Guarda id paciente seleccionado
            self.label_pac_info.config(text=f"Paciente: {pac['nombres']} {pac['apellidos']} (ID: {pac['id']})") # Muestra info paciente
        else: # Si no encontró
            self.paciente_seleccionado_id = None # Limpia id
            self.label_pac_info.config(text="Paciente: NO ENCONTRADO - Registre primero en pestaña Pacientes") # Mensaje no encontrado
            messagebox.showerror("Error", "Paciente no encontrado - regístrelo en pestaña Pacientes") # Error

    def actualizar_disponibilidad(self): # Define método consulta disponibilidad RF-07
        med_text = self.combo_ag_medico.get() # Obtiene texto combo médico
        if not med_text: # Si no seleccionó médico
            messagebox.showerror("Error", "Seleccione médico") # Error
            return # Sale
        try: # Intenta obtener id médico
            medico_id = int(med_text.split(" - ")[0]) # Extrae id
        except: # Si falla
            return # Sale

        # Obtiene fecha
        if TIENE_CALENDARIO: # Si tiene calendario visual
            fecha = self.entry_ag_fecha.get_date().strftime("%Y-%m-%d") # Obtiene fecha de DateEntry
        else: # Si es Entry normal
            fecha = self.entry_ag_fecha.get().strip() # Obtiene texto fecha

        # Validación fecha no pasada
        try: # Intenta validar fecha
            fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date() # Convierte a fecha
            if fecha_obj < date.today(): # Si fecha pasada
                messagebox.showerror("Error", "No se puede agendar en fecha pasada") # Error
                return # Sale
        except: # Si formato inválido
            messagebox.showerror("Error", "Formato fecha debe ser YYYY-MM-DD") # Error formato
            return # Sale

        self.listbox_horarios.delete(0, tk.END) # Limpia lista horarios

        # Genera horarios posibles 08:00-17:00 cada 30 min
        horarios_base = ["08:00", "08:30", "09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
                         "14:00", "14:30", "15:00", "15:30", "16:00", "16:30"] # Lista horarios base

        conn = db_manager.get_connection() # Conecta BD
        cursor = conn.cursor() # Cursor
        cursor.execute("SELECT hora FROM citas WHERE medico_id=? AND fecha=? AND estado!='Cancelada'", (medico_id, fecha)) # Consulta citas ocupadas ese médico y fecha
        ocupadas = [r["hora"] for r in cursor.fetchall()] # Lista horas ocupadas
        conn.close() # Cierra

        for h in horarios_base: # Recorre horarios base
            if h in ocupadas: # Si está ocupada
                self.listbox_horarios.insert(tk.END, f"OCUPADO {h} - OCUPADO") # Muestra como ocupado
            else: # Si libre
                self.listbox_horarios.insert(tk.END, f"LIBRE {h} - LIBRE") # Muestra como libre

        if not ocupadas: # Si ninguna ocupada
            self.listbox_horarios.insert(tk.END, "") # Línea vacía
            self.listbox_horarios.insert(tk.END, f"Total {len(horarios_base)} horarios libres para {fecha}") # Mensaje total libres

    def agendar_cita(self): # Define método agendar cita RF-04
        if not self.paciente_seleccionado_id: # Verifica paciente seleccionado
            messagebox.showerror("Error", "Busque y seleccione paciente primero") # Error
            return # Sale

        med_text = self.combo_ag_medico.get() # Obtiene médico
        if not med_text: # Si no seleccionó
            messagebox.showerror("Error", "Seleccione médico") # Error
            return # Sale

        seleccion = self.listbox_horarios.curselection() # Obtiene selección lista horarios
        if not seleccion: # Si no seleccionó horario
            messagebox.showerror("Error", "Seleccione un horario LIBRE de la lista") # Error
            return # Sale

        texto_horario = self.listbox_horarios.get(seleccion[0]) # Obtiene texto horario seleccionado
        if "OCUPADO" in texto_horario: # Si eligió ocupado
            messagebox.showerror("Error", "No puede agendar horario ocupado - seleccione LIBRE") # Error
            return # Sale

        if "LIBRE" not in texto_horario: # Si no es libre
            return # Sale

        hora = texto_horario.split(" ")[1] # Extrae hora del texto

        try: # Intenta extraer id médico
            medico_id = int(med_text.split(" - ")[0]) # Id médico
        except: # Si falla
            return # Sale

        if TIENE_CALENDARIO: # Obtiene fecha según tipo widget
            fecha = self.entry_ag_fecha.get_date().strftime("%Y-%m-%d") # Fecha de DateEntry
        else: # Entry normal
            fecha = self.entry_ag_fecha.get().strip() # Texto fecha

        conn = db_manager.get_connection() # Conecta BD
        cursor = conn.cursor() # Cursor
        try: # Intenta insertar cita
            cursor.execute("INSERT INTO citas (paciente_id, medico_id, fecha, hora, estado) VALUES (?, ?, ?, ?, 'Pendiente')",
                           (self.paciente_seleccionado_id, medico_id, fecha, hora)) # Inserta cita
            conn.commit() # Guarda
            cita_id = cursor.lastrowid # Obtiene id cita creada

            # Muestra confirmación visual RF-10
            self.mostrar_confirmacion(cita_id) # Llama a mostrar comprobante

            self.actualizar_disponibilidad() # Actualiza lista disponibilidad
            self.cargar_panel() # Actualiza panel día
            messagebox.showinfo("Éxito", f"Cita agendada ID {cita_id} para {fecha} {hora}") # Mensaje éxito
        except sqlite3.IntegrityError: # Si hay cruce horario (UNIQUE violation)
            messagebox.showerror("Error", f"Horario {fecha} {hora} ya ocupado para ese médico - seleccione otro") # Error cruce
        finally: # Siempre
            conn.close() # Cierra conexión

    def mostrar_confirmacion(self, cita_id): # Define método muestra comprobante visual RF-10
        conn = db_manager.get_connection() # Conecta
        cursor = conn.cursor() # Cursor
        cursor.execute("""
            SELECT c.id, c.fecha, c.hora, c.consultorio, c.estado,
                   p.nombres || ' ' || p.apellidos as paciente, p.cedula,
                   m.nombres as medico, e.nombre as especialidad
            FROM citas c
            JOIN pacientes p ON c.paciente_id = p.id
            JOIN medicos m ON c.medico_id = m.id
            LEFT JOIN especialidades e ON m.especialidad_id = e.id
            WHERE c.id=?
        """, (cita_id,)) # Consulta datos completos cita
        cita = cursor.fetchone() # Obtiene cita
        conn.close() # Cierra

        if not cita: # Si no existe
            return # Sale

        # Ventana comprobante
        win = tk.Toplevel(self.root) # Crea ventana emergente
        win.title(f"Comprobante Cita #{cita_id} - Confirmación Visual") # Título ventana comprobante
        win.geometry("500x400") # Tamaño
        win.configure(bg="white") # Fondo blanco

        tk.Label(win, text="COMPROBANTE DE CITA MÉDICA", font=("Arial", 14, "bold"), bg="white").pack(pady=10) # Título comprobante
        tk.Label(win, text='Dispensario "La Dolorosa"', font=("Arial", 10), bg="white").pack() # Subtítulo dispensario
        tk.Label(win, text="-" * 50, bg="white").pack() # Línea separadora

        info = f"""
Cita ID: {cita['id']}
Paciente: {cita['paciente']}
Cédula: {cita['cedula']}
Médico: {cita['medico']}
Especialidad: {cita['especialidad']}
Fecha: {cita['fecha']}
Hora: {cita['hora']}
Consultorio: {cita['consultorio']}
Estado: {cita['estado']}
Fecha Creación: {datetime.now().strftime('%Y-%m-%d %H:%M')}
        """ # Texto comprobante con datos

        tk.Label(win, text=info, font=("Courier", 11), bg="white", justify="left").pack(pady=10, padx=20) # Muestra info comprobante

        tk.Button(win, text="Cerrar", command=win.destroy).pack() # Botón cerrar

    # --- PESTAÑA PANEL DÍA ---
    def init_panel(self): # Define inicialización panel citas día RF-08
        frame_filtros = tk.Frame(self.tab_panel, bg="white") # Frame filtros
        frame_filtros.pack(fill="x", padx=10, pady=10) # Coloca

        tk.Label(frame_filtros, text="Fecha Panel (YYYY-MM-DD):", bg="white").pack(side="left") # Label fecha panel
        if TIENE_CALENDARIO: # Si tiene calendario
            self.entry_panel_fecha = DateEntry(frame_filtros, width=12, date_pattern='yyyy-mm-dd') # DateEntry
        else: # Si no
            self.entry_panel_fecha = tk.Entry(frame_filtros, width=12) # Entry normal
            self.entry_panel_fecha.insert(0, datetime.now().strftime("%Y-%m-%d")) # Hoy por defecto
        self.entry_panel_fecha.pack(side="left", padx=5) # Coloca

        tk.Label(frame_filtros, text="Filtrar Médico:", bg="white").pack(side="left", padx=10) # Label filtrar médico
        self.combo_panel_medico = ttk.Combobox(frame_filtros, width=20, state="readonly") # Combo filtro médico
        self.combo_panel_medico.pack(side="left") # Coloca

        tk.Button(frame_filtros, text="Actualizar Panel", bg="#2E86C1", fg="white", command=self.cargar_panel).pack(side="left", padx=10) # Botón actualizar panel
        tk.Button(frame_filtros, text="Ver Comprobante", command=self.ver_comprobante_panel).pack(side="left") # Botón ver comprobante
        tk.Button(frame_filtros, text="Reprogramar Cita (RF-05)", bg="#F39C12", fg="white", command=self.reprogramar_cita).pack(side="left", padx=5) # Botón reprogramar
        tk.Button(frame_filtros, text="Cancelar Cita (RF-06)", bg="#E74C3C", fg="white", command=self.cancelar_cita).pack(side="left") # Botón cancelar

        columns = ("ID", "Hora", "Paciente", "Cédula", "Médico", "Especialidad", "Estado", "Consultorio") # Columnas panel
        self.tree_panel = ttk.Treeview(self.tab_panel, columns=columns, show="headings", height=20) # Tabla panel día
        for col in columns: # Configura columnas
            self.tree_panel.heading(col, text=col) # Título columna
            self.tree_panel.column(col, width=110) # Ancho
        self.tree_panel.pack(fill="both", expand=True, padx=10, pady=10) # Expande tabla

        self.cargar_combo_medicos_panel() # Carga combo médicos filtro
        self.cargar_panel() # Carga panel inicial con fecha hoy

    def cargar_combo_medicos_panel(self): # Define método carga combo filtro médicos panel
        conn = db_manager.get_connection() # Conecta
        cursor = conn.cursor() # Cursor
        cursor.execute("SELECT id, nombres FROM medicos") # Consulta médicos
        medicos = cursor.fetchall() # Obtiene lista
        self.combo_panel_medico["values"] = ["Todos"] + [f"{r['id']} - {r['nombres']}" for r in medicos] # Llena combo con Todos + médicos
        self.combo_panel_medico.set("Todos") # Selecciona Todos por defecto
        conn.close() # Cierra

    def cargar_panel(self): # Define método carga panel citas día RF-08
        for item in self.tree_panel.get_children(): # Limpia tabla panel
            self.tree_panel.delete(item) # Borra fila

        # Obtiene fecha panel
        if TIENE_CALENDARIO: # Si tiene calendario
            fecha = self.entry_panel_fecha.get_date().strftime("%Y-%m-%d") # Fecha de DateEntry
        else: # Si Entry
            fecha = self.entry_panel_fecha.get().strip() # Texto fecha

        filtro_med = self.combo_panel_medico.get() # Obtiene filtro médico
        medico_id_filtro = None # Inicializa id filtro
        if filtro_med and filtro_med != "Todos": # Si filtro no es Todos
            try: # Intenta extraer id
                medico_id_filtro = int(filtro_med.split(" - ")[0]) # Id médico filtro
            except: # Si falla
                pass # Ignora

        conn = db_manager.get_connection() # Conecta
        cursor = conn.cursor() # Cursor

        # Construye consulta base panel día
        query = """
            SELECT c.id, c.hora, p.nombres || ' ' || p.apellidos as paciente, p.cedula,
                   m.nombres as medico, e.nombre as especialidad, c.estado, c.consultorio
            FROM citas c
            JOIN pacientes p ON c.paciente_id = p.id
            JOIN medicos m ON c.medico_id = m.id
            LEFT JOIN especialidades e ON m.especialidad_id = e.id
            WHERE c.fecha=? AND c.estado!='Cancelada'
        """ # Consulta base filtra por fecha y no canceladas
        params = [fecha] # Parámetros

        if medico_id_filtro: # Si hay filtro médico
            query += " AND c.medico_id=?" # Añade condición médico
            params.append(medico_id_filtro) # Añade parámetro id médico

        query += " ORDER BY c.hora" # Ordena por hora

        cursor.execute(query, params) # Ejecuta consulta panel
        for row in cursor.fetchall(): # Recorre resultados
            self.tree_panel.insert("", "end", values=(row["id"], row["hora"], row["paciente"], row["cedula"], row["medico"], row["especialidad"], row["estado"], row["consultorio"])) # Inserta fila panel
        conn.close() # Cierra

    def ver_comprobante_panel(self): # Define método ver comprobante desde panel
        seleccion = self.tree_panel.selection() # Obtiene selección tabla panel
        if not seleccion: # Si no seleccionó
            messagebox.showerror("Error", "Seleccione una cita del panel") # Error
            return # Sale
        cita_id = self.tree_panel.item(seleccion[0])["values"][0] # Obtiene id cita de primera columna
        self.mostrar_confirmacion(cita_id) # Muestra comprobante

    def reprogramar_cita(self): # Define método reprogramar cita RF-05
        seleccion = self.tree_panel.selection() # Obtiene selección panel
        if not seleccion: # Si no seleccionó
            messagebox.showerror("Error", "Seleccione cita a reprogramar") # Error
            return # Sale
        cita_id = self.tree_panel.item(seleccion[0])["values"][0] # Id cita seleccionada

        # Ventana reprogramar
        win = tk.Toplevel(self.root) # Crea ventana emergente reprogramar
        win.title(f"Reprogramar Cita ID {cita_id} - RF-05") # Título
        win.geometry("400x250") # Tamaño
        win.configure(bg="white") # Fondo blanco

        tk.Label(win, text=f"Reprogramar Cita #{cita_id}", font=("Arial", 12, "bold"), bg="white").pack(pady=10) # Título ventana

        tk.Label(win, text="Nueva Fecha (YYYY-MM-DD):", bg="white").pack() # Label nueva fecha
        if TIENE_CALENDARIO: # Si tiene calendario
            entry_nueva_fecha = DateEntry(win, width=15, date_pattern='yyyy-mm-dd') # DateEntry nueva fecha
        else: # Si no
            entry_nueva_fecha = tk.Entry(win, width=15) # Entry normal
            entry_nueva_fecha.insert(0, (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")) # Mañana por defecto
        entry_nueva_fecha.pack(pady=5) # Coloca

        tk.Label(win, text="Nueva Hora (HH:MM):", bg="white").pack() # Label nueva hora
        entry_nueva_hora = tk.Entry(win, width=10) # Campo nueva hora
        entry_nueva_hora.insert(0, "09:00") # Valor por defecto
        entry_nueva_hora.pack(pady=5) # Coloca

        def guardar_reprog(): # Define función interna guarda reprogramación
            if TIENE_CALENDARIO: # Obtiene fecha según widget
                nueva_fecha = entry_nueva_fecha.get_date().strftime("%Y-%m-%d") # Fecha DateEntry
            else: # Entry
                nueva_fecha = entry_nueva_fecha.get().strip() # Texto fecha
            nueva_hora = entry_nueva_hora.get().strip() # Obtiene nueva hora

            conn = db_manager.get_connection() # Conecta BD
            cursor = conn.cursor() # Cursor
            try: # Intenta actualizar
                cursor.execute("UPDATE citas SET fecha=?, hora=? WHERE id=?", (nueva_fecha, nueva_hora, cita_id)) # Actualiza fecha y hora cita
                conn.commit() # Guarda
                messagebox.showinfo("Éxito", f"Cita {cita_id} reprogramada a {nueva_fecha} {nueva_hora}") # Éxito
                win.destroy() # Cierra ventana reprogramar
                self.cargar_panel() # Recarga panel
            except sqlite3.IntegrityError: # Si cruce horario
                messagebox.showerror("Error", f"Horario {nueva_fecha} {nueva_hora} ocupado - elija otro") # Error cruce
            finally: # Siempre
                conn.close() # Cierra

        tk.Button(win, text="Guardar Reprogramación", bg="#27AE60", fg="white", command=guardar_reprog).pack(pady=15) # Botón guardar reprogramación

    def cancelar_cita(self): # Define método cancelar cita RF-06
        seleccion = self.tree_panel.selection() # Obtiene selección panel
        if not seleccion: # Si no seleccionó
            messagebox.showerror("Error", "Seleccione cita a cancelar") # Error
            return # Sale
        cita_id = self.tree_panel.item(seleccion[0])["values"][0] # Id cita

        if not messagebox.askyesno("Confirmar", f"¿Cancelar cita ID {cita_id}? Se liberará el horario"): # Pregunta confirmación
            return # Si dice no, sale

        conn = db_manager.get_connection() # Conecta
        cursor = conn.cursor() # Cursor
        cursor.execute("UPDATE citas SET estado='Cancelada' WHERE id=?", (cita_id,)) # Actualiza estado a Cancelada
        conn.commit() # Guarda
        conn.close() # Cierra
        messagebox.showinfo("Éxito", f"Cita {cita_id} cancelada - horario liberado") # Mensaje éxito cancelación
        self.cargar_panel() # Recarga panel

# --- BLOQUE 7: PUNTO DE ENTRADA PRINCIPAL ---

if __name__ == "__main__": # Verifica que se ejecuta como programa principal
    print("=" * 60) # Línea separadora consola
    print("AgendaSalud - Dispensario La Dolorosa - Iniciando...") # Mensaje inicio consola
    print("=" * 60) # Línea separadora
    root = tk.Tk() # Crea ventana principal Tkinter
    login = LoginWindow(root) # Crea ventana login
    root.mainloop() # Inicia loop principal interfaz
    print("AgendaSalud cerrado correctamente") # Mensaje cierre consola
