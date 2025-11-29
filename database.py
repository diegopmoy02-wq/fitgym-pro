import mysql.connector
from mysql.connector import Error
from config import Config
from datetime import datetime

class Database:
    def __init__(self):
        self.config = Config.DB_CONFIG
        self.connection = None
    
    def connect(self):
        """Establece conexión con la base de datos"""
        try:
            self.connection = mysql.connector.connect(**self.config)
            if self.connection.is_connected():
                return True
        except Error as e:
            print(f"Error al conectar a MySQL: {e}")
            return False
    
    def disconnect(self):
        """Cierra la conexión con la base de datos"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
    
    def execute_query(self, query, params=None, commit=False):
        """Ejecuta una consulta SQL"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
            
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, params or ())
            
            if commit:
                self.connection.commit()
                return cursor.lastrowid
            else:
                result = cursor.fetchall()
                cursor.close()
                return result
        except Error as e:
            print(f"Error en la consulta: {e}")
            if commit:
                self.connection.rollback()
            return None
    
    def registrar_log(self, usuario_id, accion, tabla_afectada, registro_id=None, detalles=None, ip_address=None):
        """Registra una acción en el log de actividades"""
        query = """
            INSERT INTO log_actividades 
            (usuario_id, accion, tabla_afectada, registro_id, detalles, ip_address)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        params = (usuario_id, accion, tabla_afectada, registro_id, detalles, ip_address)
        return self.execute_query(query, params, commit=True)
    
    # === FUNCIONES DE USUARIOS ===
    
    def verificar_usuario(self, username, password):
        """Verifica las credenciales de un usuario"""
        query = """
            SELECT id, username, nombre_completo, rol, email, activo
            FROM usuarios_sistema
            WHERE username = %s AND password = %s AND activo = TRUE
        """
        result = self.execute_query(query, (username, password))
        return result[0] if result else None
    
    def obtener_usuarios(self):
        """Obtiene todos los usuarios del sistema"""
        query = "SELECT id, username, nombre_completo, rol, email, activo, fecha_creacion FROM usuarios_sistema ORDER BY id"
        return self.execute_query(query)
    
    def crear_usuario(self, username, password, nombre_completo, rol, email):
        """Crea un nuevo usuario del sistema"""
        query = """
            INSERT INTO usuarios_sistema (username, password, nombre_completo, rol, email)
            VALUES (%s, %s, %s, %s, %s)
        """
        return self.execute_query(query, (username, password, nombre_completo, rol, email), commit=True)
    
    # === FUNCIONES DE MIEMBROS ===
    
    def obtener_miembros(self):
        """Obtiene todos los miembros del gimnasio"""
        query = """
            SELECT m.*, 
                   p.nombre as plan_actual,
                   mem.fecha_fin as vencimiento_membresia
            FROM miembros m
            LEFT JOIN membresias mem ON m.id = mem.miembro_id AND mem.estado = 'activa'
            LEFT JOIN planes p ON mem.plan_id = p.id
            ORDER BY m.id DESC
        """
        return self.execute_query(query)
    
    def obtener_miembro(self, miembro_id):
        """Obtiene un miembro específico"""
        query = "SELECT * FROM miembros WHERE id = %s"
        result = self.execute_query(query, (miembro_id,))
        return result[0] if result else None
    
    def crear_miembro(self, nombre, apellido, email, telefono, fecha_nacimiento, fecha_inscripcion):
        """Crea un nuevo miembro"""
        query = """
            INSERT INTO miembros (nombre, apellido, email, telefono, fecha_nacimiento, fecha_inscripcion)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        return self.execute_query(query, (nombre, apellido, email, telefono, fecha_nacimiento, fecha_inscripcion), commit=True)
    
    def actualizar_miembro(self, miembro_id, nombre, apellido, email, telefono, fecha_nacimiento, estado):
        """Actualiza un miembro existente"""
        query = """
            UPDATE miembros 
            SET nombre = %s, apellido = %s, email = %s, telefono = %s, 
                fecha_nacimiento = %s, estado = %s
            WHERE id = %s
        """
        return self.execute_query(query, (nombre, apellido, email, telefono, fecha_nacimiento, estado, miembro_id), commit=True)
    
    def eliminar_miembro(self, miembro_id):
        """Elimina un miembro (solo administrador)"""
        query = "DELETE FROM miembros WHERE id = %s"
        return self.execute_query(query, (miembro_id,), commit=True)
    
    # === FUNCIONES DE PLANES ===
    
    def obtener_planes(self):
        """Obtiene todos los planes de membresía"""
        query = "SELECT * FROM planes WHERE activo = TRUE ORDER BY duracion_dias"
        return self.execute_query(query)
    
    def crear_plan(self, nombre, descripcion, duracion_dias, precio):
        """Crea un nuevo plan de membresía"""
        query = """
            INSERT INTO planes (nombre, descripcion, duracion_dias, precio)
            VALUES (%s, %s, %s, %s)
        """
        return self.execute_query(query, (nombre, descripcion, duracion_dias, precio), commit=True)
    
    # === FUNCIONES DE MEMBRESÍAS ===
    
    def crear_membresia(self, miembro_id, plan_id, fecha_inicio, fecha_fin, monto_pagado):
        """Crea una nueva membresía para un miembro"""
        query = """
            INSERT INTO membresias (miembro_id, plan_id, fecha_inicio, fecha_fin, monto_pagado)
            VALUES (%s, %s, %s, %s, %s)
        """
        return self.execute_query(query, (miembro_id, plan_id, fecha_inicio, fecha_fin, monto_pagado), commit=True)
    
    def obtener_membresias_activas(self):
        """Obtiene todas las membresías activas"""
        query = """
            SELECT mem.*, m.nombre, m.apellido, p.nombre as plan_nombre
            FROM membresias mem
            JOIN miembros m ON mem.miembro_id = m.id
            JOIN planes p ON mem.plan_id = p.id
            WHERE mem.estado = 'activa'
            ORDER BY mem.fecha_fin
        """
        return self.execute_query(query)
    
    # === FUNCIONES DE ASISTENCIAS ===
    
    def registrar_asistencia(self, miembro_id, tipo='entrada'):
        """Registra una asistencia (entrada/salida)"""
        query = """
            INSERT INTO asistencias (miembro_id, tipo)
            VALUES (%s, %s)
        """
        return self.execute_query(query, (miembro_id, tipo), commit=True)
    
    def obtener_asistencias_hoy(self):
        """Obtiene las asistencias del día actual"""
        query = """
            SELECT a.*, m.nombre, m.apellido
            FROM asistencias a
            JOIN miembros m ON a.miembro_id = m.id
            WHERE DATE(a.fecha_hora) = CURDATE()
            ORDER BY a.fecha_hora DESC
        """
        return self.execute_query(query)
    
    def obtener_asistencias(self, limite=100):
        """Obtiene el historial de asistencias"""
        query = """
            SELECT a.*, m.nombre, m.apellido
            FROM asistencias a
            JOIN miembros m ON a.miembro_id = m.id
            ORDER BY a.fecha_hora DESC
            LIMIT %s
        """
        return self.execute_query(query, (limite,))
    
    # === FUNCIONES DE LOG ===
    
    def obtener_logs(self, limite=100):
        """Obtiene el registro de actividades"""
        query = """
            SELECT l.*, u.username, u.nombre_completo
            FROM log_actividades l
            JOIN usuarios_sistema u ON l.usuario_id = u.id
            ORDER BY l.fecha_hora DESC
            LIMIT %s
        """
        return self.execute_query(query, (limite,))
    
    # === FUNCIONES DE ESTADÍSTICAS ===
    
    def obtener_estadisticas(self):
        """Obtiene estadísticas generales del gimnasio"""
        stats = {}
        
        # Total de miembros activos
        query = "SELECT COUNT(*) as total FROM miembros WHERE estado = 'activo'"
        result = self.execute_query(query)
        stats['miembros_activos'] = result[0]['total'] if result else 0
        
        # Membresías activas
        query = "SELECT COUNT(*) as total FROM membresias WHERE estado = 'activa'"
        result = self.execute_query(query)
        stats['membresias_activas'] = result[0]['total'] if result else 0
        
        # Asistencias hoy
        query = "SELECT COUNT(*) as total FROM asistencias WHERE DATE(fecha_hora) = CURDATE()"
        result = self.execute_query(query)
        stats['asistencias_hoy'] = result[0]['total'] if result else 0
        
        # Ingresos del mes
        query = """
            SELECT COALESCE(SUM(monto_pagado), 0) as total 
            FROM membresias 
            WHERE MONTH(fecha_inicio) = MONTH(CURDATE()) 
            AND YEAR(fecha_inicio) = YEAR(CURDATE())
        """
        result = self.execute_query(query)
        stats['ingresos_mes'] = float(result[0]['total']) if result else 0.0
        
        return stats
    
    # === FUNCIONES DE CLASES ===
    
    def obtener_clases(self):
        """Obtiene todas las clases disponibles"""
        query = """
            SELECT c.*, 
                   COUNT(ic.id) as inscritos
            FROM clases c
            LEFT JOIN inscripciones_clases ic ON c.id = ic.clase_id AND ic.estado = 'activa'
            WHERE c.activo = TRUE
            GROUP BY c.id
            ORDER BY c.nombre
        """
        return self.execute_query(query)
    
    def crear_clase(self, nombre, descripcion, instructor, duracion_minutos, cupo_maximo, horario, dias_semana):
        """Crea una nueva clase"""
        query = """
            INSERT INTO clases (nombre, descripcion, instructor, duracion_minutos, cupo_maximo, horario, dias_semana)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        return self.execute_query(query, (nombre, descripcion, instructor, duracion_minutos, cupo_maximo, horario, dias_semana), commit=True)
    
    def actualizar_clase(self, clase_id, nombre, descripcion, instructor, duracion_minutos, cupo_maximo, horario, dias_semana):
        """Actualiza una clase existente"""
        query = """
            UPDATE clases 
            SET nombre = %s, descripcion = %s, instructor = %s, duracion_minutos = %s,
                cupo_maximo = %s, horario = %s, dias_semana = %s
            WHERE id = %s
        """
        return self.execute_query(query, (nombre, descripcion, instructor, duracion_minutos, cupo_maximo, horario, dias_semana, clase_id), commit=True)
    
    def eliminar_clase(self, clase_id):
        """Desactiva una clase"""
        query = "UPDATE clases SET activo = FALSE WHERE id = %s"
        return self.execute_query(query, (clase_id,), commit=True)
    
    def inscribir_miembro_clase(self, miembro_id, clase_id):
        """Inscribe un miembro a una clase"""
        query = """
            INSERT INTO inscripciones_clases (miembro_id, clase_id)
            VALUES (%s, %s)
        """
        return self.execute_query(query, (miembro_id, clase_id), commit=True)
    
    def obtener_inscripciones_clase(self, clase_id):
        """Obtiene los miembros inscritos en una clase"""
        query = """
            SELECT ic.*, m.nombre, m.apellido
            FROM inscripciones_clases ic
            JOIN miembros m ON ic.miembro_id = m.id
            WHERE ic.clase_id = %s AND ic.estado = 'activa'
            ORDER BY ic.fecha_inscripcion
        """
        return self.execute_query(query, (clase_id,))
    
    # === FUNCIONES DE PAGOS ===
    
    def obtener_pagos(self, limite=100):
        """Obtiene el historial de pagos"""
        query = """
            SELECT p.*, m.nombre, m.apellido, u.username
            FROM pagos p
            JOIN miembros m ON p.miembro_id = m.id
            JOIN usuarios_sistema u ON p.usuario_registro_id = u.id
            ORDER BY p.fecha_pago DESC
            LIMIT %s
        """
        return self.execute_query(query, (limite,))
    
    def registrar_pago(self, miembro_id, concepto, monto, metodo_pago, usuario_id, referencia=None, notas=None):
        """Registra un nuevo pago"""
        query = """
            INSERT INTO pagos (miembro_id, concepto, monto, metodo_pago, usuario_registro_id, referencia, notas)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        return self.execute_query(query, (miembro_id, concepto, monto, metodo_pago, usuario_id, referencia, notas), commit=True)
    
    def obtener_pagos_miembro(self, miembro_id):
        """Obtiene el historial de pagos de un miembro específico"""
        query = """
            SELECT p.*, u.username
            FROM pagos p
            JOIN usuarios_sistema u ON p.usuario_registro_id = u.id
            WHERE p.miembro_id = %s
            ORDER BY p.fecha_pago DESC
        """
        return self.execute_query(query, (miembro_id,))
    
    def obtener_ingresos_totales(self):
        """Obtiene estadísticas de ingresos"""
        stats = {}
        
        # Ingresos del día
        query = "SELECT COALESCE(SUM(monto), 0) as total FROM pagos WHERE DATE(fecha_pago) = CURDATE() AND estado = 'completado'"
        result = self.execute_query(query)
        stats['ingresos_hoy'] = float(result[0]['total']) if result else 0.0
        
        # Ingresos del mes
        query = """
            SELECT COALESCE(SUM(monto), 0) as total 
            FROM pagos 
            WHERE MONTH(fecha_pago) = MONTH(CURDATE()) 
            AND YEAR(fecha_pago) = YEAR(CURDATE())
            AND estado = 'completado'
        """
        result = self.execute_query(query)
        stats['ingresos_mes'] = float(result[0]['total']) if result else 0.0
        
        # Ingresos del año
        query = "SELECT COALESCE(SUM(monto), 0) as total FROM pagos WHERE YEAR(fecha_pago) = YEAR(CURDATE()) AND estado = 'completado'"
        result = self.execute_query(query)
        stats['ingresos_anio'] = float(result[0]['total']) if result else 0.0
        
        return stats