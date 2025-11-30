from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from database import Database
from config import Config
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.config.from_object(Config)

# Inicializar base de datos
db = Database()

# === DECORADOR PARA PROTEGER RUTAS ===
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Debes iniciar sesión primero', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*roles):
    from functools import wraps
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'rol' not in session or session['rol'] not in roles:
                flash('No tienes permisos para acceder a esta sección', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# === RUTAS DE AUTENTICACIÓN ===

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = db.verificar_usuario(username, password)
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['nombre'] = user['nombre_completo']
            session['rol'] = user['rol']
            
            # Registrar login en el log
            db.registrar_log(
                usuario_id=user['id'],
                accion='LOGIN',
                tabla_afectada='usuarios_sistema',
                detalles=f"Usuario {username} inició sesión",
                ip_address=request.remote_addr
            )
            
            flash(f'Bienvenido {user["nombre_completo"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Usuario o contraseña incorrectos', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    # Registrar logout en el log
    db.registrar_log(
        usuario_id=session['user_id'],
        accion='LOGOUT',
        tabla_afectada='usuarios_sistema',
        detalles=f"Usuario {session['username']} cerró sesión",
        ip_address=request.remote_addr
    )
    
    session.clear()
    flash('Sesión cerrada correctamente', 'info')
    return redirect(url_for('login'))

# === DASHBOARD ===

@app.route('/dashboard')
@login_required
def dashboard():
    stats = db.obtener_estadisticas()
    asistencias_hoy = db.obtener_asistencias_hoy()
    planes = db.obtener_planes()
    return render_template('dashboard.html', stats=stats, asistencias=asistencias_hoy, planes=planes)

# === GESTIÓN DE MIEMBROS ===

@app.route('/miembros')
@login_required
def miembros():
    miembros = db.obtener_miembros()
    planes = db.obtener_planes()
    return render_template('miembros.html', miembros=miembros, planes=planes)

@app.route('/miembros/crear', methods=['POST'])
@login_required
@role_required('administrador', 'encargado')
def crear_miembro():
    nombre = request.form.get('nombre')
    apellido = request.form.get('apellido')
    email = request.form.get('email')
    telefono = request.form.get('telefono')
    fecha_nacimiento = request.form.get('fecha_nacimiento')
    fecha_inscripcion = datetime.now().strftime('%Y-%m-%d')
    
    miembro_id = db.crear_miembro(nombre, apellido, email, telefono, fecha_nacimiento, fecha_inscripcion)
    
    if miembro_id:
        db.registrar_log(
            usuario_id=session['user_id'],
            accion='CREATE',
            tabla_afectada='miembros',
            registro_id=miembro_id,
            detalles=f"Creado miembro: {nombre} {apellido}",
            ip_address=request.remote_addr
        )
        flash('Miembro creado exitosamente', 'success')
    else:
        flash('Error al crear miembro', 'danger')
    
    return redirect(url_for('miembros'))

@app.route('/miembros/editar/<int:id>', methods=['POST'])
@login_required
@role_required('administrador', 'encargado')
def editar_miembro(id):
    nombre = request.form.get('nombre')
    apellido = request.form.get('apellido')
    email = request.form.get('email')
    telefono = request.form.get('telefono')
    fecha_nacimiento = request.form.get('fecha_nacimiento')
    estado = request.form.get('estado')
    
    resultado = db.actualizar_miembro(id, nombre, apellido, email, telefono, fecha_nacimiento, estado)
    
    if resultado is not None:
        db.registrar_log(
            usuario_id=session['user_id'],
            accion='UPDATE',
            tabla_afectada='miembros',
            registro_id=id,
            detalles=f"Actualizado miembro: {nombre} {apellido}",
            ip_address=request.remote_addr
        )
        flash('Miembro actualizado exitosamente', 'success')
    else:
        flash('Error al actualizar miembro', 'danger')
    
    return redirect(url_for('miembros'))

@app.route('/miembros/eliminar/<int:id>', methods=['POST'])
@login_required
@role_required('administrador')
def eliminar_miembro(id):
    miembro = db.obtener_miembro(id)
    
    if miembro:
        resultado = db.eliminar_miembro(id)
        
        if resultado is not None:
            db.registrar_log(
                usuario_id=session['user_id'],
                accion='DELETE',
                tabla_afectada='miembros',
                registro_id=id,
                detalles=f"Eliminado miembro: {miembro['nombre']} {miembro['apellido']}",
                ip_address=request.remote_addr
            )
            flash('Miembro eliminado exitosamente', 'success')
        else:
            flash('Error al eliminar miembro', 'danger')
    
    return redirect(url_for('miembros'))

# === GESTIÓN DE MEMBRESÍAS ===

@app.route('/miembros/asignar-membresia', methods=['POST'])
@login_required
@role_required('administrador', 'encargado')
def asignar_membresia():
    miembro_id = request.form.get('miembro_id')
    plan_id = request.form.get('plan_id')
    monto_pagado = request.form.get('monto_pagado')
    
    # Obtener información del plan
    planes = db.obtener_planes()
    plan = next((p for p in planes if p['id'] == int(plan_id)), None)
    
    if plan:
        fecha_inicio = datetime.now()
        fecha_fin = fecha_inicio + timedelta(days=plan['duracion_dias'])
        
        membresia_id = db.crear_membresia(
            miembro_id, 
            plan_id, 
            fecha_inicio.strftime('%Y-%m-%d'),
            fecha_fin.strftime('%Y-%m-%d'),
            monto_pagado
        )
        
        if membresia_id:
            db.registrar_log(
                usuario_id=session['user_id'],
                accion='CREATE',
                tabla_afectada='membresias',
                registro_id=membresia_id,
                detalles=f"Asignada membresía {plan['nombre']} a miembro ID {miembro_id}",
                ip_address=request.remote_addr
            )
            flash('Membresía asignada exitosamente', 'success')
        else:
            flash('Error al asignar membresía', 'danger')
    
    return redirect(url_for('miembros'))

# === GESTIÓN DE ASISTENCIAS ===

@app.route('/asistencias')
@login_required
def asistencias():
    asistencias = db.obtener_asistencias(200)
    miembros = db.obtener_miembros()
    return render_template('asistencias.html', asistencias=asistencias, miembros=miembros)

@app.route('/asistencias/registrar', methods=['POST'])
@login_required
@role_required('administrador', 'encargado')
def registrar_asistencia():
    miembro_id = request.form.get('miembro_id')
    tipo = request.form.get('tipo', 'entrada')
    
    asistencia_id = db.registrar_asistencia(miembro_id, tipo)
    
    if asistencia_id:
        miembro = db.obtener_miembro(miembro_id)
        db.registrar_log(
            usuario_id=session['user_id'],
            accion='CREATE',
            tabla_afectada='asistencias',
            registro_id=asistencia_id,
            detalles=f"Registrada {tipo} de {miembro['nombre']} {miembro['apellido']}",
            ip_address=request.remote_addr
        )
        flash(f'{tipo.capitalize()} registrada exitosamente', 'success')
    else:
        flash('Error al registrar asistencia', 'danger')
    
    return redirect(url_for('asistencias'))

# === GESTIÓN DE USUARIOS ===

@app.route('/usuarios')
@login_required
@role_required('administrador')
def usuarios():
    usuarios = db.obtener_usuarios()
    return render_template('usuarios.html', usuarios=usuarios)

@app.route('/usuarios/crear', methods=['POST'])
@login_required
@role_required('administrador')
def crear_usuario():
    username = request.form.get('username')
    password = request.form.get('password')
    nombre_completo = request.form.get('nombre_completo')
    rol = request.form.get('rol')
    email = request.form.get('email')
    
    usuario_id = db.crear_usuario(username, password, nombre_completo, rol, email)
    
    if usuario_id:
        db.registrar_log(
            usuario_id=session['user_id'],
            accion='CREATE',
            tabla_afectada='usuarios_sistema',
            registro_id=usuario_id,
            detalles=f"Creado usuario: {username} con rol {rol}",
            ip_address=request.remote_addr
        )
        flash('Usuario creado exitosamente', 'success')
    else:
        flash('Error al crear usuario', 'danger')
    
    return redirect(url_for('usuarios'))

# === LOG DE ACTIVIDADES ===

@app.route('/logs')
@login_required
@role_required('administrador', 'encargado')
def logs():
    logs = db.obtener_logs(500)
    return render_template('logs.html', logs=logs)

# === API ENDPOINTS (para peticiones AJAX) ===

@app.route('/api/miembro/<int:id>')
@login_required
def api_obtener_miembro(id):
    miembro = db.obtener_miembro(id)
    return jsonify(miembro) if miembro else jsonify({'error': 'No encontrado'}), 404

@app.route('/api/estadisticas')
@login_required
def api_estadisticas():
    stats = db.obtener_estadisticas()
    return jsonify(stats)

# === MANEJO DE ERRORES ===

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

# === GESTIÓN DE CLASES ===

@app.route('/clases')
@login_required
def clases():
    clases = db.obtener_clases()
    miembros = db.obtener_miembros()
    return render_template('clases.html', clases=clases, miembros=miembros)

@app.route('/clases/crear', methods=['POST'])
@login_required
@role_required('administrador', 'encargado')
def crear_clase():
    nombre = request.form.get('nombre')
    descripcion = request.form.get('descripcion')
    instructor = request.form.get('instructor')
    duracion_minutos = request.form.get('duracion_minutos')
    cupo_maximo = request.form.get('cupo_maximo')
    horario = request.form.get('horario')
    dias_semana = request.form.get('dias_semana')
    
    clase_id = db.crear_clase(nombre, descripcion, instructor, duracion_minutos, cupo_maximo, horario, dias_semana)
    
    if clase_id:
        db.registrar_log(
            usuario_id=session['user_id'],
            accion='CREATE',
            tabla_afectada='clases',
            registro_id=clase_id,
            detalles=f"Creada clase: {nombre}",
            ip_address=request.remote_addr
        )
        flash('Clase creada exitosamente', 'success')
    else:
        flash('Error al crear clase', 'danger')
    
    return redirect(url_for('clases'))

@app.route('/clases/editar/<int:id>', methods=['POST'])
@login_required
@role_required('administrador', 'encargado')
def editar_clase(id):
    nombre = request.form.get('nombre')
    descripcion = request.form.get('descripcion')
    instructor = request.form.get('instructor')
    duracion_minutos = request.form.get('duracion_minutos')
    cupo_maximo = request.form.get('cupo_maximo')
    horario = request.form.get('horario')
    dias_semana = request.form.get('dias_semana')
    
    resultado = db.actualizar_clase(id, nombre, descripcion, instructor, duracion_minutos, cupo_maximo, horario, dias_semana)
    
    if resultado is not None:
        db.registrar_log(
            usuario_id=session['user_id'],
            accion='UPDATE',
            tabla_afectada='clases',
            registro_id=id,
            detalles=f"Actualizada clase: {nombre}",
            ip_address=request.remote_addr
        )
        flash('Clase actualizada exitosamente', 'success')
    else:
        flash('Error al actualizar clase', 'danger')
    
    return redirect(url_for('clases'))

@app.route('/clases/inscribir', methods=['POST'])
@login_required
@role_required('administrador', 'encargado')
def inscribir_clase():
    miembro_id = request.form.get('miembro_id')
    clase_id = request.form.get('clase_id')
    
    inscripcion_id = db.inscribir_miembro_clase(miembro_id, clase_id)
    
    if inscripcion_id:
        db.registrar_log(
            usuario_id=session['user_id'],
            accion='CREATE',
            tabla_afectada='inscripciones_clases',
            registro_id=inscripcion_id,
            detalles=f"Inscrito miembro ID {miembro_id} a clase ID {clase_id}",
            ip_address=request.remote_addr
        )
        flash('Miembro inscrito a la clase exitosamente', 'success')
    else:
        flash('Error al inscribir a la clase', 'danger')
    
    return redirect(url_for('clases'))

@app.route('/api/clase/<int:id>')
@login_required
def api_obtener_clase(id):
    query = "SELECT * FROM clases WHERE id = %s"
    result = db.execute_query(query, (id,))
    clase = result[0] if result else None
    return jsonify(clase) if clase else jsonify({'error': 'No encontrado'}), 404

# === GESTIÓN DE PAGOS ===

@app.route('/pagos')
@login_required
def pagos():
    pagos = db.obtener_pagos(200)
    miembros = db.obtener_miembros()
    ingresos = db.obtener_ingresos_totales()
    return render_template('pagos.html', pagos=pagos, miembros=miembros, ingresos=ingresos)

@app.route('/pagos/registrar', methods=['POST'])
@login_required
@role_required('administrador', 'encargado')
def registrar_pago():
    miembro_id = request.form.get('miembro_id')
    concepto = request.form.get('concepto')
    monto = request.form.get('monto')
    metodo_pago = request.form.get('metodo_pago')
    referencia = request.form.get('referencia')
    notas = request.form.get('notas')
    
    pago_id = db.registrar_pago(miembro_id, concepto, monto, metodo_pago, session['user_id'], referencia, notas)
    
    if pago_id:
        miembro = db.obtener_miembro(miembro_id)
        db.registrar_log(
            usuario_id=session['user_id'],
            accion='CREATE',
            tabla_afectada='pagos',
            registro_id=pago_id,
            detalles=f"Registrado pago de ${monto} - {concepto} de {miembro['nombre']} {miembro['apellido']}",
            ip_address=request.remote_addr
        )
        flash('Pago registrado exitosamente', 'success')
    else:
        flash('Error al registrar pago', 'danger')
    
    return redirect(url_for('pagos'))

# === DESCARGAR LOGS EN PDF ===

@app.route('/logs/descargar-pdf')
@login_required
@role_required('administrador')
def descargar_logs_pdf():
    from reportlab.lib.pagesizes import letter, landscape
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.units import inch
    from io import BytesIO
    from flask import make_response
    
    # Obtener logs
    logs = db.obtener_logs(500)
    
    # Crear PDF en memoria
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
    elements = []
    
    # Estilos
    styles = getSampleStyleSheet()
    
    # Título
    title = Paragraph("<b>Registro de Actividades del Sistema - FitGym Pro</b>", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 0.3*inch))
    
    # Información
    info = Paragraph(f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}<br/>Usuario: {session['nombre']}", styles['Normal'])
    elements.append(info)
    elements.append(Spacer(1, 0.3*inch))
    
    # Datos de la tabla
    data = [['ID', 'Fecha/Hora', 'Usuario', 'Acción', 'Tabla', 'Detalles', 'IP']]
    
    for log in logs:
        data.append([
            str(log['id']),
            log['fecha_hora'].strftime('%d/%m/%Y %H:%M'),
            log['username'],
            log['accion'],
            log['tabla_afectada'],
            (log['detalles'][:40] + '...') if log['detalles'] and len(log['detalles']) > 40 else (log['detalles'] or '-'),
            log['ip_address'] or '-'
        ])
    
    # Crear tabla
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    
    elements.append(table)
    
    # Construir PDF
    doc.build(elements)
    
    # Preparar respuesta
    buffer.seek(0)
    response = make_response(buffer.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=logs_fitgym_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
    
    # Registrar descarga en log
    db.registrar_log(
        usuario_id=session['user_id'],
        accion='EXPORT',
        tabla_afectada='log_actividades',
        detalles='Exportación de logs a PDF',
        ip_address=request.remote_addr
    )
    
    return response



if __name__ == '__main__':
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)