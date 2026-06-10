import re
from app import db
from app.models import DocenteOficial

def extraer_texto_pdf(ruta_pdf):
    """Extrae texto de un archivo PDF usando pdfplumber"""
    import pdfplumber
    
    texto_completo = ""
    with pdfplumber.open(ruta_pdf) as pdf:
        for page in pdf.pages:
            texto = page.extract_text()
            if texto:
                texto_completo += texto + "\n"
    
    return texto_completo

def parsear_listado_texto(texto_raw):
    """
    Parser robusto para el formato del listado de la Junta de Clasificacion.
    Maneja lineas pegadas, asteriscos, metadatos de paginas, etc.
    """
    # Limpiar metadatos de paginas
    texto_limpio = re.sub(r'e-mail:.*?Pag\.\s+\d+\s+de\s+\d+', '', texto_raw)
    texto_limpio = re.sub(r'MINISTERIO DE EDUCACION.*?LISTADO DEFINITIVO.*?\n', '', texto_limpio)
    texto_limpio = re.sub(r'Legajo\s+Nro\.\s+Doc\..*?\n', '', texto_limpio)
    
    cargados = 0
    materia_actual = "GENERAL"
    categoria_materia_actual = "GENERAL"
    
    # Dividir el texto en bloques por materia
    # Patron: NOMBRE_MATERIA "Cat. CATEGORIA" o "Fuera de Listado"
    bloques = re.split(r'(?=[A-ZÁÉÍÓÚÑ\s\(\)\.\-\/]+\"(?:Cat\.|Fuera))', texto_limpio)
    
    for bloque in bloques:
        bloque = bloque.strip()
        if not bloque:
            continue
        
        # Detectar materia y categoria
        match_materia = re.match(r'([A-ZÁÉÍÓÚÑ\s\(\)\.\-\/]+?)\s*"(Cat\.\s+[^"]+|"Fuera de Listado")"', bloque)
        if match_materia:
            materia_actual = match_materia.group(1).strip()
            categoria_materia_actual = match_materia.group(2).strip()
            bloque = bloque[match_materia.end():]
        
        # Patron para cada docente:
        # [numero*] legajo dni NOMBRE DOMICILIO LOCALIDAD telefono CAT PJE
        patron_docente = r'(?:^|\s)(?:\d+\*\s+)?(\d{5})\s+(\d{7,8})\s+([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s]+?)\s+([A-Za-zÁÉÍÓÚÑ\s\d\.\-\/\#]+?)\s+(\d{3,4}[\-]?\d{5,7})\s+([DHST])\s+([\d,]+)'
        
        matches = re.finditer(patron_docente, bloque)
        
        for match in matches:
            try:
                legajo = match.group(1)
                dni = match.group(2)
                nombre_completo = match.group(3).strip()
                domicilio = match.group(4).strip()
                telefono = match.group(5)
                categoria = match.group(6).upper()
                puntaje = float(match.group(7).replace(',', '.'))
                
                # Verificar si ya existe
                docente = DocenteOficial.query.filter_by(dni=dni).first()
                if docente:
                    # Actualizar si cambio la categoria o puntaje
                    if docente.categoria != categoria or docente.puntaje != puntaje:
                        docente.categoria = categoria
                        docente.puntaje = puntaje
                        docente.materia_base = materia_actual
                else:
                    docente = DocenteOficial(
                        legajo=legajo,
                        dni=dni,
                        nombre_completo=nombre_completo,
                        telefono=telefono,
                        categoria=categoria,
                        puntaje=puntaje,
                        materia_base=materia_actual
                    )
                    db.session.add(docente)
                    cargados += 1
            except Exception as e:
                continue
    
    db.session.commit()
    return cargados

def parsear_pdf(ruta_pdf):
    """Extrae texto del PDF y lo parsea"""
    texto = extraer_texto_pdf(ruta_pdf)
    return parsear_listado_texto(texto)
