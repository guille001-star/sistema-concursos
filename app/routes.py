from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import Concurso, Inscripcion, DocenteOficial
import secrets
import logging

logger = logging.getLogger(__name__)
main = Blueprint('main', __name__)

def normalizar_dni(dni):
    """Elimina puntos, guiones y espacios del DNI para comparación."""
    if not dni:
        return ''
    return ''.join(filter(str.isdigit, str(dni)))

@main.route('/')
def index():
    concursos = Concurso.query.filter_by(estado='ACTIVO').order_by(Concurso.fecha_cierre.asc()).all()
    return render_template('docente/index.html', concursos=concursos)

@main.route('/inscripcion/<token>', methods=['GET', 'POST'])
def inscripcion(token):
    concurso = Concurso.query.filter_by(qr_token=token).first_or_404()
    
    if request.method == 'POST':
        dni = request.form.get('dni', '').strip()
        email = request.form.get('email', '').strip()
        
        if not dni or not email:
            flash('Todos los campos son obligatorios', 'danger')
            return render_template('docente/inscripcion.html', concurso=concurso)
        
        # Normalizar DNI ingresado
        dni_normalizado = normalizar_dni(dni)
            
        # Verificar si ya está inscripto (comparando DNI normalizado)
        inscripciones_existentes = Inscripcion.query.filter_by(concurso_id=concurso.id).all()
        for inscripcion in inscripciones_existentes:
            if normalizar_dni(inscripcion.dni_docente) == dni_normalizado:
                flash('Este DNI ya se encuentra inscripto en este concurso.', 'warning')
                return render_template('docente/inscripcion.html', concurso=concurso)
            
        # Buscar docente con DNI normalizado
        docentes = DocenteOficial.query.all()
        docente_encontrado = None
        for docente in docentes:
            if normalizar_dni(docente.dni) == dni_normalizado:
                docente_encontrado = docente
                break
                
        if not docente_encontrado:
            flash('El DNI ingresado no figura en el listado oficial de la Junta de Clasificación.', 'danger')
            return render_template('docente/inscripcion.html', concurso=concurso)
            
        # Generar código de confirmación
        codigo = secrets.token_hex(4).upper()
        
        nueva_inscripcion = Inscripcion(
            concurso_id=concurso.id,
            dni_docente=dni,
            email=email,
            codigo_confirmacion=codigo,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        try:
            db.session.add(nueva_inscripcion)
            db.session.commit()
            return render_template('docente/inscripcion.html', concurso=concurso, codigo_confirmacion=codigo)
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error al guardar inscripción: {e}")
            flash('Ocurrió un error al procesar la inscripción. Por favor, intente nuevamente.', 'danger')
            return render_template('docente/inscripcion.html', concurso=concurso)
            
    # GET request
    return render_template('docente/inscripcion.html', concurso=concurso)
