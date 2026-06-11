from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from app import db
from app.models import Admin, Concurso, DocenteOficial, Inscripcion, Materia, PuntajeMateria
from werkzeug.utils import secure_filename
import os
import secrets
from datetime import datetime
from app.parser import parsear_pdf
from app.qr_generator import generar_qr_concurso
from app.merit import generar_orden_merito
import logging

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash('Debe iniciar sesion', 'danger')
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.check_password(password):
            session['admin_id'] = admin.id
            session['admin_username'] = admin.username
            flash('Bienvenido', 'success')
            return redirect(url_for('admin.dashboard'))
        flash('Credenciales invalidas', 'danger')
    return render_template('admin/login.html')

@admin_bp.route('/logout')
def logout():
    session.clear()
    flash('Sesion cerrada', 'info')
    return redirect(url_for('main.index'))

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    total_concursos = Concurso.query.count()
    concursos_activos = Concurso.query.filter_by(estado='ACTIVO').count()
    total_inscripciones = Inscripcion.query.count()
    total_docentes = DocenteOficial.query.count()
    concursos_recientes = Concurso.query.order_by(Concurso.creado_en.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html',
                         total_concursos=total_concursos,
                         concursos_activos=concursos_activos,
                         total_inscripciones=total_inscripciones,
                         total_docentes=total_docentes,
                         concursos_recientes=concursos_recientes)

@admin_bp.route('/crear-concurso', methods=['GET', 'POST'])
@admin_required
def crear_concurso():
    if request.method == 'POST':
        try:
            numero = request.form.get('numero')
            titulo = request.form.get('titulo')
            materia_id = request.form.get('materia_id')
            caracter = request.form.get('caracter_cargo')
            fecha_apertura = datetime.strptime(request.form.get('fecha_apertura'), '%Y-%m-%dT%H:%M')
            fecha_cierre = datetime.strptime(request.form.get('fecha_cierre'), '%Y-%m-%dT%H:%M')
            
            # Verificar que el numero no exista
            if Concurso.query.filter_by(numero=numero).first():
                flash(f'El concurso {numero} ya existe', 'danger')
                return redirect(url_for('admin.crear_concurso'))
            
            concurso = Concurso(
                numero=numero,
                titulo=titulo,
                materia_id=int(materia_id) if materia_id else None,
                caracter_cargo=caracter,
                fecha_apertura=fecha_apertura,
                fecha_cierre=fecha_cierre,
                estado='ACTIVO'
            )
            
            db.session.add(concurso)
            db.session.commit()
            
            flash(f'Concurso {numero} creado exitosamente', 'success')
            return redirect(url_for('admin.detalle_concurso', id=concurso.id))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error al crear concurso: {e}")
            flash(f'Error al crear concurso: {str(e)}', 'danger')
    
    # Obtener todas las materias para el dropdown
    materias = Materia.query.order_by(Materia.nombre).all()
    return render_template('admin/crear_concurso.html', materias=materias)

@admin_bp.route('/listar-concursos')
@admin_required
def listar_concursos():
    concursos = Concurso.query.order_by(Concurso.creado_en.desc()).all()
    return render_template('admin/listar_concursos.html', concursos=concursos)

@admin_bp.route('/concurso/<int:id>')
@admin_required
def detalle_concurso(id):
    concurso = Concurso.query.get_or_404(id)
    inscripciones = Inscripcion.query.filter_by(concurso_id=id).order_by(Inscripcion.fecha_inscripcion.desc()).all()
    return render_template('admin/detalle_concurso.html', concurso=concurso, inscripciones=inscripciones)

@admin_bp.route('/concurso/<int:id>/generar-qr', methods=['POST'])
@admin_required
def generar_qr(id):
    try:
        concurso = Concurso.query.get_or_404(id)
        filepath, url = generar_qr_concurso(concurso)
        db.session.commit()
        flash(f'QR generado: {url}', 'success')
    except Exception as e:
        logger.error(f"Error al generar QR: {e}")
        flash(f'Error al generar QR: {str(e)}', 'danger')
    return redirect(url_for('admin.detalle_concurso', id=id))

@admin_bp.route('/concurso/<int:id>/generar-pdf', methods=['POST'])
@admin_required
def generar_pdf(id):
    try:
        from app.pdf_generator import generar_pdf_merito
        concurso = Concurso.query.get_or_404(id)
        resultado = generar_orden_merito(id)
        
        if 'error' in resultado:
            flash(resultado['error'], 'danger')
            return redirect(url_for('admin.detalle_concurso', id=id))
        
        filepath = generar_pdf_merito(concurso, resultado)
        concurso.pdf_merito_path = filepath
        db.session.commit()
        
        flash('PDF de orden de merito generado', 'success')
    except Exception as e:
        logger.error(f"Error al generar PDF: {e}")
        flash(f'Error al generar PDF: {str(e)}', 'danger')
    return redirect(url_for('admin.detalle_concurso', id=id))

@admin_bp.route('/concurso/<int:id>/cerrar', methods=['POST'])
@admin_required
def cerrar_concurso(id):
    try:
        concurso = Concurso.query.get_or_404(id)
        concurso.estado = 'CERRADO'
        db.session.commit()
        flash(f'Concurso {concurso.numero} cerrado', 'info')
    except Exception as e:
        logger.error(f"Error al cerrar concurso: {e}")
        flash(f'Error al cerrar concurso: {str(e)}', 'danger')
    return redirect(url_for('admin.detalle_concurso', id=id))

@admin_bp.route('/cargar-listado', methods=['GET', 'POST'])
@admin_required
def cargar_listado():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No se selecciono archivo', 'danger')
            return redirect(url_for('admin.cargar_listado'))
        
        file = request.files['file']
        if file.filename == '':
            flash('No se selecciono archivo', 'danger')
            return redirect(url_for('admin.cargar_listado'))
        
        if not file.filename.endswith('.pdf'):
            flash('Solo se aceptan archivos PDF', 'danger')
            return redirect(url_for('admin.cargar_listado'))
        
        try:
            # Guardar el archivo temporalmente
            uploads_dir = os.path.join('uploads')
            os.makedirs(uploads_dir, exist_ok=True)
            filepath = os.path.join(uploads_dir, secure_filename(file.filename))
            file.save(filepath)
            
            # Procesar el PDF
            docentes_creados, materias_creadas, puntajes_creados = parsear_pdf(filepath)
            
            flash(f'PDF procesado: {docentes_creados} docentes, {materias_creadas} materias, {puntajes_creados} puntajes', 'success')
        except Exception as e:
            logger.error(f"Error al procesar PDF: {e}")
            flash(f'Error al procesar PDF: {str(e)}', 'danger')
        
        return redirect(url_for('admin.cargar_listado'))
    
    total_docentes = DocenteOficial.query.count()
    return render_template('admin/cargar_listado.html', total_docentes=total_docentes)

@admin_bp.route('/docentes')
@admin_required
def listar_docentes():
    page = request.args.get('page', 1, type=int)
    docentes = DocenteOficial.query.order_by(DocenteOficial.nombre_completo).paginate(page=page, per_page=50)
    return render_template('admin/listar_docentes.html', docentes=docentes)


@admin_bp.route('/reset-db', methods=['POST'])
@admin_required
def reset_db_temporal():
    """Resetea la base de datos. ELIMINAR DESPUÉS DE USAR."""
    try:
        db.drop_all()
        db.create_all()
        
        # Recrear admin
        admin = Admin(username='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        
        flash('Base de datos reseteada correctamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('admin.dashboard'))



# ENDPOINT TEMPORAL - ELIMINAR DESPUÉS DE USAR
@admin_bp.route('/reset-db', methods=['GET', 'POST'])
@admin_required
def reset_db_temporal():
    """Resetea la base de datos. ELIMINAR DESPUÉS DE USAR."""
    if request.method == 'GET':
        return '''
        <html>
        <head><title>Reset DB</title></head>
        <body style="font-family: Arial; padding: 40px; text-align: center;">
            <h1>⚠️ Resetear Base de Datos</h1>
            <p>Esto borrará TODOS los datos (docentes, concursos, inscripciones).</p>
            <form method="POST">
                <button type="submit" style="background: red; color: white; padding: 15px 30px; font-size: 18px; border: none; border-radius: 5px; cursor: pointer;">
                    CONFIRMAR RESET
                </button>
            </form>
            <p style="margin-top: 20px;"><a href="/admin/dashboard">Cancelar y volver al Dashboard</a></p>
        </body>
        </html>
        '''
    
    # Si es POST, ejecutar el reset
    try:
        db.drop_all()
        db.create_all()
        
        # Recrear admin
        admin = Admin(username='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        
        flash('Base de datos reseteada correctamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('admin.dashboard'))

