from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import Concurso, Inscripcion, DocenteOficial
import secrets
import logging

logger = logging.getLogger(__name__)
main = Blueprint('main', __name__)

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
            
        # Verificar si ya está inscripto
        existe = Inscripcion.query.filter_by(concurso_id=concurso.id, dni_docente=dni).first()
        if existe:
            flash('Este DNI ya se encuentra inscripto en este concurso.', 'warning')
            return render_template('docente/inscripcion.html', concurso=concurso)
            
        # Verificar si el docente está en el listado oficial
        docente = DocenteOficial.query.filter_by(dni=dni).first()
        if not docente:
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
            # ÉXITO: Renderizamos directamente la vista de éxito con el código
            return render_template('docente/inscripcion.html', concurso=concurso, codigo_confirmacion=codigo)
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error al guardar inscripción: {e}")
            flash('Ocurrió un error al procesar la inscripción. Por favor, intente nuevamente.', 'danger')
            return render_template('docente/inscripcion.html', concurso=concurso)
            
    # GET request
    return render_template('docente/inscripcion.html', concurso=concurso)

