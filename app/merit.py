from app.models import Inscripcion, DocenteOficial, Concurso, PuntajeMateria
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
    Usa el puntaje específico para la materia del concurso.
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
                logger.warning(f"Docente {insc.dni_docente} no encontrado")
                continue
            
            # Obtener el puntaje específico para la materia del concurso
            if concurso.materia_id:
                puntaje_materia = PuntajeMateria.query.filter_by(
                    docente_id=doc.id,
                    materia_id=concurso.materia_id
                ).first()
                
                if puntaje_materia:
                    categoria = puntaje_materia.categoria.upper()
                    puntaje = puntaje_materia.puntaje
                else:
                    # Si no tiene puntaje para esta materia, es "Fuera de Listado"
                    categoria = 'T'
                    puntaje = 0.0
            else:
                # Si el concurso no tiene materia asignada, usar el mejor puntaje del docente
                mejor_puntaje = PuntajeMateria.query.filter_by(docente_id=doc.id).order_by(PuntajeMateria.puntaje.desc()).first()
                if mejor_puntaje:
                    categoria = mejor_puntaje.categoria.upper()
                    puntaje = mejor_puntaje.puntaje
                else:
                    categoria = 'T'
                    puntaje = 0.0
            
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
