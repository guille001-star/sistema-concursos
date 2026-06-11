from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for, session
from app import db
from app.models import Concurso, Inscripcion, DocenteOficial, LogAuditoria
from app.parser import parsear_listado_texto, parsear_pdf
from app.merit import generar_orden_merito
from app.qr_generator import generar_qr_concurso
from app.pdf_generator import generar_pdf_orden_merito
from app.utils import log_auditoria, validar_fecha_concurso, sanitizar_input, formatear_error
from functools import lru_cache
from datetime import datetime, timedelta
import secrets
import os

main = Blueprint('main', __name__)

@main.route('/')
def index():
    """Página principal con lista de concursos activos."""
    try:
        concursos = Concurso.query.filter_by(estado='ACTIVO').order_by(Concurso.fecha_apertura.desc()).all()
        return render_template('index.html', concursos=concursos)
    except Exception as e:
        log_auditoria('ERROR_INDEX', str(e))
        return render_template('error.html', error=str(e)), 500

@main.route('/api/cargar-listado', methods=['POST'])
def cargar_listado():
    """Carga el listado oficial (texto o PDF)."""
    try:
        if 'file' in request.files:
            file = request.files['file']
            if file.filename == '':
                return jsonify({"error": "No se seleccionó archivo"}), 400
            
            filename = f"listado_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
            ruta_temporal = os.path.join('uploads', filename)
            file.save(ruta_temporal)
            
            cargados = parsear_pdf(ruta_temporal)
            os.remove(ruta_temporal)
            
            log_auditoria('CARGA_LISTADO_PDF', f"{cargados} docentes procesados")
            return jsonify({"mensaje": f"Se procesaron {cargados} docentes oficiales del PDF"}), 200
        else:
            data = request.json
            texto = data.get('texto', '')
            if not texto:
                return jsonify({"error": "Texto vacío"}), 400
            
            cargados = parsear_listado_texto(texto)
            log_auditoria('CARGA_LISTADO_TEXTO', f"{cargados} docentes procesados")
            return jsonify({"mensaje": f"Se procesaron {cargados} docentes oficiales"}), 200
    except Exception as e:
        log_auditoria('ERROR_CARGA_LISTADO', str(e))
        return jsonify(formatear_error(e)), 500

@main.route('/api/concurso', methods=['POST'])
def crear_concurso():
    """Crea un nuevo concurso."""
    try:
        data = request.json
        
        # Validaciones
        if not data.get('numero'):
            return jsonify({"error": "Número de concurso requerido"}), 400
        
        if Concurso.query.filter_by(numero=data['numero']).first():
            return jsonify({"error": "Ya existe un concurso con ese número"}), 409
        
        # Parsear fechas
        fecha_apertura = datetime.fromisoformat(data['fecha_apertura']) if data.get('fecha_apertura') else datetime.utcnow()
        fecha_cierre = datetime.fromisoformat(data['fecha_cierre']) if data.get('fecha_cierre') else None
        
        if fecha_cierre and fecha_cierre <= fecha_apertura:
            return jsonify({"error": "La fecha de cierre debe ser posterior a la de apertura"}), 400
        
        nuevo = Concurso(
            numero=data['numero'],
            titulo=data.get('titulo', ''),
            espacio_curricular=data.get('espacio_curricular', ''),
            fecha_apertura=fecha_apertura,
            fecha_cierre=fecha_cierre,
            caracter_cargo=data.get('caracter_cargo', 'Interino')
        )
        db.session.add(nuevo)
        db.session.commit()
        
        log_auditoria('CREAR_CONCURSO', f"Concurso {nuevo.numero} creado")
        return jsonify({"id": nuevo.id, "mensaje": "Concurso creado"}), 201
    except Exception as e:
        db.session.rollback()
        log_auditoria('ERROR_CREAR_CONCURSO', str(e))
        return jsonify(formatear_error(e)), 500

@main.route('/api/concurso/<int:id>/merito', methods=['POST'])
def calcular_merito(id):
    """Genera el orden de mérito de un concurso."""
    try:
        resultado = generar_orden_merito(id)
        if "error" in resultado:
            return jsonify(resultado), 400 if "No hay inscripciones" in resultado["error"] else 404
        
        log_auditoria('GENERAR_MERITO', f"Concurso ID {id}, {len(resultado)} inscriptos")
        return jsonify(resultado), 200
    except Exception as e:
        log_auditoria('ERROR_GENERAR_MERITO', str(e))
        return jsonify(formatear_error(e)), 500

@main.route('/api/inscripcion', methods=['POST'])
def registrar_inscripcion():
    """Registra una inscripción de docente."""
    try:
        data = request.json
        
        # Validaciones
        if not data.get('concurso_id') or not data.get('dni'):
            return jsonify({"error": "Datos incompletos"}), 400
        
        concurso = Concurso.query.get(data['concurso_id'])
        if not concurso:
            return jsonify({"error": "Concurso no encontrado"}), 404
        
        # Validar fecha
        valido, mensaje = validar_fecha_concurso(concurso)
        if not valido:
            return jsonify({"error": mensaje}), 400
        
        # Validar que el docente existe en el listado oficial
        docente = DocenteOficial.query.filter_by(dni=data['dni']).first()
        if not docente:
            return jsonify({"error": "El DNI no figura en el listado oficial"}), 404
        
        # Validar que no esté ya inscripto
        inscripcion_existente = Inscripcion.query.filter_by(
            concurso_id=data['concurso_id'],
            dni_docente=data['dni']
        ).first()
        if inscripcion_existente:
            return jsonify({"error": "Ya está inscripto en este concurso"}), 409
        
        # Generar código de confirmación único
        codigo_confirmacion = secrets.token_hex(4).upper()
        
        nueva = Inscripcion(
            concurso_id=data['concurso_id'],
            dni_docente=data['dni'],
            email=data.get('email'),
            codigo_confirmacion=codigo_confirmacion,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')[:200]
        )
        db.session.add(nueva)
        db.session.commit()
        
        log_auditoria('INSCRIPCION', f"Concurso {concurso.numero}, DNI {data['dni']}, Código {codigo_confirmacion}")
        
        return jsonify({
            "mensaje": "Inscripción registrada",
            "codigo_confirmacion": codigo_confirmacion,
            "docente": docente.nombre_completo,
            "concurso": concurso.numero
        }), 201
    except Exception as e:
        db.session.rollback()
        log_auditoria('ERROR_INSCRIPCION', str(e))
        return jsonify(formatear_error(e)), 500

@main.route('/api/docentes', methods=['GET'])
def listar_docentes():
    """Lista todos los docentes oficiales."""
    try:
        docentes = DocenteOficial.query.all()
        lista = [{
            "dni": doc.dni,
            "nombre": doc.nombre_completo,
            "categoria": doc.categoria,
            "puntaje": doc.puntaje,
            "materia": doc.materia_base
        } for doc in docentes]
        return jsonify(lista), 200
    except Exception as e:
        return jsonify(formatear_error(e)), 500

@main.route('/inscripcion/<token>', methods=['GET', 'POST'])
def inscripcion_publica(token):
    """Portal público de inscripción para docentes."""
    try:
        concurso = Concurso.query.filter_by(qr_token=token).first()
        if not concurso:
            flash('Enlace de inscripción no válido.', 'danger')
            return redirect(url_for('main.index'))
        
        if request.method == 'POST':
            dni = request.form.get('dni', '').strip()
            email = request.form.get('email', '').strip()
            
            if not dni or not email:
                flash('DNI y email son obligatorios.', 'warning')
                return render_template('docente/inscripcion.html', concurso=concurso)
            
            # Validar fecha
            valido, mensaje = validar_fecha_concurso(concurso)
            if not valido:
                flash(mensaje, 'danger')
                return render_template('docente/inscripcion.html', concurso=concurso)
            
            # Validar docente en listado oficial
            docente = DocenteOficial.query.filter_by(dni=dni).first()
            if not docente:
                flash('El DNI no figura en el listado oficial de docentes.', 'danger')
                return render_template('docente/inscripcion.html', concurso=concurso)
            
            # Validar no duplicado
            inscripcion_existente = Inscripcion.query.filter_by(
                concurso_id=concurso.id,
                dni_docente=dni
            ).first()
            if inscripcion_existente:
                flash('Ya está inscripto en este concurso.', 'warning')
                return render_template('docente/inscripcion.html', concurso=concurso)
            
            # Generar código de confirmación
            codigo_confirmacion = secrets.token_hex(4).upper()
            
            nueva = Inscripcion(
                concurso_id=concurso.id,
                dni_docente=dni,
                email=email,
                codigo_confirmacion=codigo_confirmacion,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', '')[:200]
            )
            db.session.add(nueva)
            db.session.commit()
            
            log_auditoria('INSCRIPCION_PUBLICA', f"Concurso {concurso.numero}, DNI {dni}")
            
            return render_template('docente/confirmacion.html', 
                                 concurso=concurso,
                                 docente=docente,
                                 codigo=codigo_confirmacion)
        
        return render_template('docente/inscripcion.html', concurso=concurso)
    except Exception as e:
        log_auditoria('ERROR_INSCRIPCION_PUBLICA', str(e))
        flash('Ocurrió un error. Intente nuevamente.', 'danger')
        return redirect(url_for('main.index'))

@main.route('/api/concurso/<int:id>/qr', methods=['POST'])
def generar_qr(id):
    """Genera el QR de un concurso."""
    try:
        concurso = Concurso.query.get(id)
        if not concurso:
            return jsonify({"error": "Concurso no encontrado"}), 404
        
        filepath, url = generar_qr_concurso(concurso)
        db.session.commit()
        
        log_auditoria('GENERAR_QR', f"Concurso {concurso.numero}")
        
        return jsonify({
            "qr_path": filepath,
            "url_inscripcion": url
        }), 200
    except Exception as e:
        db.session.rollback()
        log_auditoria('ERROR_GENERAR_QR', str(e))
        return jsonify(formatear_error(e)), 500

@main.route('/api/concurso/<int:id>/pdf-merito', methods=['POST'])
def generar_pdf_merito(id):
    """Genera el PDF del orden de mérito."""
    try:
        concurso = Concurso.query.get(id)
        if not concurso:
            return jsonify({"error": "Concurso no encontrado"}), 404
        
        # Generar orden de mérito primero
        orden = generar_orden_merito(id)
        if "error" in orden:
            return jsonify(orden), 400
        
        # Generar PDF
        ruta_pdf = generar_pdf_orden_merito(concurso, orden)
        db.session.commit()
        
        log_auditoria('GENERAR_PDF_MERITO', f"Concurso {concurso.numero}")
        
        return jsonify({
            "pdf_path": ruta_pdf,
            "total_inscriptos": len(orden)
        }), 200
    except Exception as e:
        db.session.rollback()
        log_auditoria('ERROR_GENERAR_PDF_MERITO', str(e))
        return jsonify(formatear_error(e)), 500

