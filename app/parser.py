import re
import logging
from app import db
from app.models import DocenteOficial, Materia, PuntajeMateria

logger = logging.getLogger(__name__)

def extraer_texto_pdf(ruta_pdf):
    """Extrae texto de un archivo PDF usando pdfplumber."""
    try:
        import pdfplumber
        
        texto_completo = ""
        with pdfplumber.open(ruta_pdf) as pdf:
            total_paginas = len(pdf.pages)
            logger.info(f"Procesando PDF con {total_paginas} páginas")
            
            for i, page in enumerate(pdf.pages):
                texto = page.extract_text()
                if texto:
                    texto_completo += texto + "\n"
                
                if (i + 1) % 50 == 0:
                    logger.info(f"  Procesadas {i+1}/{total_paginas} páginas")
        
        return texto_completo
    except Exception as e:
        logger.error(f"Error al extraer texto del PDF: {e}")
        raise

def parsear_listado_texto(texto_raw):
    """
    Parser robusto que extrae docentes por materia.
    Un docente puede tener diferentes categorías/puntajes en diferentes materias.
    """
    # Limpiar metadatos de páginas
    texto = re.sub(r'e-mail:[^\n]*Pág\.\s+\d+\s+de\s+\d+', ' ', texto_raw)
    texto = re.sub(r'MINISTERIO DE EDUCACION[^\n]*', ' ', texto)
    texto = re.sub(r'JUNTA DE CLASIFICACION[^\n]*', ' ', texto)
    texto = re.sub(r'LISTADO DEFINITIVO[^\n]*', ' ', texto)
    texto = re.sub(r'LISTADO GRAL\.[^\n]*', ' ', texto)
    texto = re.sub(r'Legajo Nro\.\s+Doc\.[^\n]*', ' ', texto)
    texto = re.sub(r'REFERENCIAS PRESENTE LISTADO[^\n]*', ' ', texto)
    
    docentes_creados = 0
    puntajes_creados = 0
    materias_creadas = 0
    
    # Buscar encabezados de materia
    # Formato: NOMBRE_MATERIA "Cat. DOCENTE" o "Cat. HABILITANTE" etc.
    patron_materia = r'([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s\(\)\.\-\/]+?)\s*"(Cat\.\s+[^"]+)"'
    matches_materia = list(re.finditer(patron_materia, texto))
    
    logger.info(f"Encontradas {len(matches_materia)} materias en el PDF")
    
    for i, match_materia in enumerate(matches_materia):
        materia_nombre = match_materia.group(1).strip()
        categoria_materia = match_materia.group(2).strip()
        
        if not materia_nombre or len(materia_nombre) < 5:
            continue
        
        # Obtener o crear la materia
        materia = Materia.query.filter_by(nombre=materia_nombre).first()
        if not materia:
            materia = Materia(nombre=materia_nombre)
            db.session.add(materia)
            db.session.flush()
            materias_creadas += 1
        
        # Extraer la sección de texto hasta la siguiente materia
        inicio = match_materia.end()
        fin = matches_materia[i+1].start() if i+1 < len(matches_materia) else len(texto)
        seccion = texto[inicio:fin]
        
        # Patrón para cada docente en esta sección
        # Formato: legajo dni NOMBRE DOMICILIO telefono CAT PJE
        patron_docente = r'(\d{5})\s+(\d{7,8})\s+([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s]+?)\s+([A-Za-zÁÉÍÓÚÑ\s\d\.\-\/\#]+?)\s+(\d{3,4}[\-]?\d{5,7})\s+([DHST])\s+([\d,]+)'
        
        matches_docente = re.finditer(patron_docente, seccion)
        
        for match in matches_docente:
            try:
                legajo = match.group(1)
                dni = match.group(2)
                nombre_completo = match.group(3).strip()
                domicilio = match.group(4).strip()
                telefono = match.group(5)
                categoria = match.group(6).upper()
                puntaje = float(match.group(7).replace(',', '.'))
                
                # Obtener o crear el docente
                docente = DocenteOficial.query.filter_by(dni=dni).first()
                if not docente:
                    docente = DocenteOficial(
                        legajo=legajo,
                        dni=dni,
                        nombre_completo=nombre_completo,
                        telefono=telefono
                    )
                    db.session.add(docente)
                    db.session.flush()
                    docentes_creados += 1
                
                # Verificar si ya existe el puntaje para esta materia
                puntaje_existente = PuntajeMateria.query.filter_by(
                    docente_id=docente.id,
                    materia_id=materia.id
                ).first()
                
                if not puntaje_existente:
                    nuevo_puntaje = PuntajeMateria(
                        docente_id=docente.id,
                        materia_id=materia.id,
                        categoria=categoria,
                        puntaje=puntaje
                    )
                    db.session.add(nuevo_puntaje)
                    puntajes_creados += 1
                else:
                    # Actualizar si cambió
                    if puntaje_existente.categoria != categoria or puntaje_existente.puntaje != puntaje:
                        puntaje_existente.categoria = categoria
                        puntaje_existente.puntaje = puntaje
                
            except Exception as e:
                logger.debug(f"Error al parsear docente: {e}")
                continue
    
    db.session.commit()
    logger.info(f"Parser completado: {docentes_creados} docentes, {materias_creadas} materias, {puntajes_creados} puntajes")
    return docentes_creados, materias_creadas, puntajes_creados

def parsear_pdf(ruta_pdf):
    """Extrae texto del PDF y lo parsea."""
    texto = extraer_texto_pdf(ruta_pdf)
    return parsear_listado_texto(texto)
