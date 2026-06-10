from functools import wraps
from flask import request, jsonify, session, redirect, url_for, flash
from datetime import datetime
from app.models import LogAuditoria, db
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def log_auditoria(accion, detalle=None, user_id=None):
    """Registra una acción en el log de auditoría."""
    try:
        log = LogAuditoria(
            accion=accion,
            detalle=detalle,
            ip_address=request.remote_addr,
            user_id=user_id
        )
        db.session.add(log)
        db.session.commit()
        logger.info(f"[AUDITORIA] {accion}: {detalle}")
    except Exception as e:
        logger.error(f"Error al registrar auditoría: {e}")
        db.session.rollback()

def login_required_admin(f):
    """Decorator para proteger rutas de admin."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash('Debe iniciar sesión para acceder a esta página.', 'warning')
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

def validar_fecha_concurso(concurso):
    """Valida que el concurso esté en período de inscripción."""
    ahora = datetime.utcnow()
    
    if concurso.estado != 'ACTIVO':
        return False, f"El concurso está {concurso.estado}"
    
    if ahora < concurso.fecha_apertura:
        return False, f"El concurso abre el {concurso.fecha_apertura.strftime('%d/%m/%Y %H:%M')}"
    
    if ahora > concurso.fecha_cierre:
        return False, f"El concurso cerró el {concurso.fecha_cierre.strftime('%d/%m/%Y %H:%M')}"
    
    return True, "OK"

def sanitizar_input(texto):
    """Sanitiza inputs de usuario para prevenir XSS."""
    if not texto:
        return ""
    return texto.replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')

def formatear_error(error):
    """Formatea errores para respuesta JSON."""
    return {
        'error': str(error),
        'timestamp': datetime.utcnow().isoformat()
    }
