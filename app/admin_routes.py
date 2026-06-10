from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file
from app import db
from app.models import Concurso, Inscripcion, DocenteOficial, Admin
from app.utils import login_required_admin, log_auditoria
from datetime import datetime
import os

admin_bp = admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login de administrador."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.check_password(password):
            session['admin_id'] = admin.id
            session['admin_username'] = admin.username
            log_auditoria('ADMIN_LOGIN', f"Usuario: {username}")
            flash('Bienvenido al panel de administración.', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Usuario o contraseña incorrectos.', 'danger')
    
    return render_template('admin/login.html')

@admin_bp.route('/logout')
def logout():
    """Logout de administrador."""
    session.pop('admin_id', None)
    session.pop('admin_username', None)
    flash('Sesión cerrada.', 'info')
    return redirect(url_for('admin.login'))

@admin_bp.route('/dashboard')
@login_required_admin
def dashboard():
    """Dashboard principal del admin."""
    try:
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
    except Exception as e:
        flash(f'Error al cargar dashboard: {str(e)}', 'danger')
        return redirect(url_for('admin.login'))

@admin_bp.route('/concursos')
@login_required_admin
def listar_concursos():
    """Lista todos los concursos."""
    concursos = Concurso.query.order_by(Concurso.creado_en.desc()).all()
    return render_template('admin/listar_concursos.html', concursos=concursos)

@admin_bp.route('/concursos/crear', methods=['GET', 'POST'])
@login_required_admin
def crear_concurso():
    """Crea un nuevo concurso."""
    if request.method == 'POST':
        try:
            numero = request.form.get('numero', '').strip()
            titulo = request.form.get('titulo', '').strip()
            espacio = request.form.get('espacio_curricular', '').strip()
            caracter = request.form.get('caracter_cargo', 'Interino')
            fecha_apertura_str = request.form.get('fecha_apertura')
            fecha_cierre_str = request.form.get('fecha_cierre')
            
            if not numero:
                flash('El número de concurso es obligatorio.', 'warning')
                return render_template('admin/crear_concurso.html')
            
            if Concurso.query.filter_by(numero=numero).first():
                flash('Ya existe un concurso con ese número.', 'danger')
                return render_template('admin/crear_concurso.html')
            
            fecha_apertura = datetime.fromisoformat(fecha_apertura_str) if fecha_apertura_str else datetime.utcnow()
            fecha_cierre = datetime.fromisoformat(fecha_cierre_str) if fecha_cierre_str else None
            
            if fecha_cierre and fecha_cierre <= fecha_apertura:
                flash('La fecha de cierre debe ser posterior a la de apertura.', 'warning')
                return render_template('admin/crear_concurso.html')
            
            nuevo = Concurso(
                numero=numero,
                titulo=titulo,
                espacio_curricular=espacio,
                fecha_apertura=fecha_apertura,
                fecha_cierre=fecha_cierre,
                caracter_cargo=caracter
            )
            db.session.add(nuevo)
            db.session.commit()
            
            log_auditoria('ADMIN_CREAR_CONCURSO', f"Concurso {numero} creado por {session.get('admin_username')}")
            flash(f'Concurso {numero} creado exitosamente.', 'success')
            return redirect(url_for('admin.detalle_concurso', id=nuevo.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear concurso: {str(e)}', 'danger')
    
    return render_template('admin/crear_concurso.html')

@admin_bp.route('/concursos/<int:id>')
@login_required_admin
def detalle_concurso(id):
    """Detalle de un concurso con inscripciones."""
    concurso = Concurso.query.get_or_404(id)
    inscripciones = Inscripcion.query.filter_by(concurso_id=id).order_by(Inscripcion.fecha_inscripcion.desc()).all()
    
    return render_template('admin/detalle_concurso.html', 
                         concurso=concurso, 
                         inscripciones=inscripciones)

@admin_bp.route('/concursos/<int:id>/generar-qr', methods=['POST'])
@login_required_admin
def generar_qr(id):
    """Genera el QR de un concurso."""
    from app.qr_generator import generar_qr_concurso
    concurso = Concurso.query.get_or_404(id)
    
    filepath, url = generar_qr_concurso(concurso)
    db.session.commit()
    
    log_auditoria('ADMIN_GENERAR_QR', f"Concurso {concurso.numero}")
    flash(f'QR generado. URL: {url}', 'success')
    return redirect(url_for('admin.detalle_concurso', id=id))

@admin_bp.route('/concursos/<int:id>/generar-pdf', methods=['POST'])
@login_required_admin
def generar_pdf(id):
    """Genera el PDF del orden de mérito."""
    from app.pdf_generator import generar_pdf_orden_merito
    from app.merit import generar_orden_merito
    
    concurso = Concurso.query.get_or_404(id)
    
    # Generar orden de mérito
    orden = generar_orden_merito(id)
    if "error" in orden:
        flash(f'Error: {orden["error"]}', 'danger')
        return redirect(url_for('admin.detalle_concurso', id=id))
    
    # Generar PDF
    ruta_pdf = generar_pdf_orden_merito(concurso, orden)
    db.session.commit()
    
    log_auditoria('ADMIN_GENERAR_PDF', f"Concurso {concurso.numero}")
    flash('PDF del orden de mérito generado exitosamente.', 'success')
    return redirect(url_for('admin.detalle_concurso', id=id))

@admin_bp.route('/concursos/<int:id>/cerrar', methods=['POST'])
@login_required_admin
def cerrar_concurso(id):
    """Cierra un concurso manualmente."""
    concurso = Concurso.query.get_or_404(id)
    concurso.estado = 'CERRADO'
    db.session.commit()
    
    log_auditoria('ADMIN_CERRAR_CONCURSO', f"Concurso {concurso.numero}")
    flash(f'Concurso {concurso.numero} cerrado.', 'info')
    return redirect(url_for('admin.detalle_concurso', id=id))

@admin_bp.route('/cargar-listado', methods=['GET', 'POST'])
@login_required_admin
def cargar_listado():
    """Carga el listado oficial de docentes."""
    if request.method == 'POST':
        try:
            if 'file' not in request.files:
                flash('No se seleccionó archivo.', 'warning')
                return render_template('admin/cargar_listado.html')
            
            file = request.files['file']
            if file.filename == '':
                flash('No se seleccionó archivo.', 'warning')
                return render_template('admin/cargar_listado.html')
            
            if not file.filename.endswith('.pdf'):
                flash('Solo se aceptan archivos PDF.', 'warning')
                return render_template('admin/cargar_listado.html')
            
            filename = f"listado_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
            ruta_temporal = os.path.join('uploads', filename)
            file.save(ruta_temporal)
            
            from app.parser import parsear_pdf
            cargados = parsear_pdf(ruta_temporal)
            os.remove(ruta_temporal)
            
            log_auditoria('ADMIN_CARGAR_LISTADO', f"{cargados} docentes procesados")
            flash(f'Se procesaron {cargados} docentes oficiales.', 'success')
            return redirect(url_for('admin.cargar_listado'))
        except Exception as e:
            flash(f'Error al procesar PDF: {str(e)}', 'danger')
    
    total_docentes = DocenteOficial.query.count()
    return render_template('admin/cargar_listado.html', total_docentes=total_docentes)

@admin_bp.route('/docentes')
@login_required_admin
def listar_docentes():
    """Lista todos los docentes oficiales."""
    page = request.args.get('page', 1, type=int)
    docentes = DocenteOficial.query.order_by(DocenteOficial.nombre_completo).paginate(page=page, per_page=50)
    return render_template('admin/listar_docentes.html', docentes=docentes)

