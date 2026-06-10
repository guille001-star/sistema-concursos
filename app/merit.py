from app.models import Inscripcion, DocenteOficial, Concurso
from app import db
import logging

logger = logging.getLogger(__name__)

PRIORIDAD_CAT = {
    'D': 1,   # Docente - MÁXIMA prioridad
    'H': 2,   # Habilitante
    'S': 3,   # Supletorio
    'T': 4    # Fuera de Listado - NO GANA
}

def generar_orden_merito(concurso_id):
    """
    Genera el orden de mérito de un concurso.
    Retorna lista ordenada o dict con error.
    """
    try:
        concurso = Concurso.query.get(concurso_id)
        if not concurso:
            return {"error": "Concurso no encontrado"}

        inscripciones = Inscripcion.query.filter_by(
            concurso_id=concurso_id, 
            estado='VALIDADO'
        ).all()

        if not inscripciones:
            return {"error": "No hay inscripciones validadas"}

        lista = []
        for insc in inscripciones:
            doc = DocenteOficial.query.filter_by(dni=insc.dni_docente).first()
            if not doc:
                logger.warning(f"Docente {insc.dni_docente} no encontrado en listado oficial")
                continue
            
            categoria = doc.categoria.upper() if doc.categoria else 'T'
            puntaje = float(doc.puntaje) if doc.puntaje else 0.0
            
            lista.append({
                'inscripcion_id': insc.id,
                'docente': doc,
                'categoria': categoria,
                'peso': PRIORIDAD_CAT.get(categoria, 4),
                'puntaje': puntaje
            })

        # Ordenar: 1° Categoría (D>H>S>T), 2° Puntaje (desc), 3° Nombre (asc)
        lista.sort(key=lambda x: (
            x['peso'], 
            -x['puntaje'], 
            x['docente'].nombre_completo or ''
        ))

        # Verificar si queda desierto (solo T)
        hay_docentes_validos = any(item['peso'] <= 3 for item in lista)
        
        if not hay_docentes_validos and lista:
            concurso.estado = 'DESIERTO'
            concurso.observacion = f'Concurso desierto: todos los inscriptos están Fuera de Listado (T)'
        else:
            concurso.estado = 'MERITO_GENERADO'
            concurso.observacion = None
        
        # Construir resultado
        resultado = []
        for i, item in enumerate(lista):
            resultado.append({
                'orden': i + 1,
                'dni': item['docente'].dni,
                'nombre': item['docente'].nombre_completo,
                'categoria': item['categoria'],
                'puntaje': item['puntaje'],
                'es_ganador': i == 0 and hay_docentes_validos,
                'estado_concurso': concurso.estado
            })
        
        db.session.commit()
        logger.info(f"Orden de mérito generado para concurso {concurso_id}: {len(resultado)} inscriptos")
        return resultado

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error al generar orden de mérito: {e}")
        return {"error": f"Error al generar orden de mérito: {str(e)}"}
