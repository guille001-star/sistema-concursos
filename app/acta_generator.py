from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime
import os

def generar_acta_designacion(concurso, docente_ganador):
    """
    Genera el Acta de Designación en PDF corregido (sin superposiciones y fecha en español).
    """
    actas_dir = os.path.join('static', 'actas')
    os.makedirs(actas_dir, exist_ok=True)
    
    filename = f"acta_{concurso.numero.replace('/', '_')}.pdf"
    filepath = os.path.join(actas_dir, filename)
    
    # Documento con márgenes estándar
    doc = SimpleDocTemplate(filepath, pagesize=A4,
                           rightMargin=2*cm, leftMargin=2*cm,
                           topMargin=2*cm, bottomMargin=1.5*cm)
    
    elementos = []
    estilos = getSampleStyleSheet()
    
    # Estilos
    estilo_titulo = ParagraphStyle(
        'Titulo',
        parent=estilos['Heading1'],
        fontSize=16,
        alignment=TA_CENTER,
        spaceAfter=10,
        textColor=colors.HexColor('#003366'),
        fontName='Helvetica-Bold'
    )
    
    estilo_subtitulo = ParagraphStyle(
        'Subtitulo',
        parent=estilos['Normal'],
        fontSize=9,
        alignment=TA_CENTER,
        spaceAfter=3,
        textColor=colors.black,
        fontName='Helvetica-Bold'
    )
    
    estilo_texto = ParagraphStyle(
        'Texto',
        parent=estilos['Normal'],
        fontSize=10,
        spaceAfter=5,
        textColor=colors.black,
        leading=12
    )
    
    estilo_negrita = ParagraphStyle(
        'Negrita',
        parent=estilos['Normal'],
        fontSize=10,
        spaceAfter=5,
        textColor=colors.black,
        fontName='Helvetica-Bold'
    )
    
    # === ENCABEZADO ===
    elementos.append(Paragraph("<b>MINISTERIO DE EDUCACIÓN DE LA PROVINCIA DEL CHUBUT</b>", estilo_subtitulo))
    elementos.append(Paragraph("<b>DEPARTAMENTO DE DESIGNACIONES DE EDUCACIÓN SECUNDARIA - REGIÓN 1</b>", estilo_subtitulo))
    elementos.append(Spacer(1, 0.3*cm))
    
    # === TÍTULO ===
    numero_acta = f" N° {concurso.numero_acta}" if concurso.numero_acta else ""
    elementos.append(Paragraph(f"<b>ACTA DE DESIGNACIÓN{numero_acta}</b>", estilo_titulo))
    
    # CORRECCIÓN: Fecha en español manualmente para evitar "JUNE"
    meses = {1: 'ENERO', 2: 'FEBRERO', 3: 'MARZO', 4: 'ABRIL', 5: 'MAYO', 6: 'JUNIO', 
             7: 'JULIO', 8: 'AGOSTO', 9: 'SEPTIEMBRE', 10: 'OCTUBRE', 11: 'NOVIEMBRE', 12: 'DICIEMBRE'}
    ahora = datetime.now()
    fecha_actual = f"{ahora.day} DE {meses[ahora.month]} DE {ahora.year}"
    
    elementos.append(Paragraph(f"LAGO PUELO, CHUBUT, {fecha_actual}", estilo_texto))
    elementos.append(Spacer(1, 0.3*cm))
    
    # === TEXTO INTRODUCTORIO ===
    anio_actual = ahora.strftime('%Y')
    elementos.append(Paragraph(
        f"El Departamento de Designaciones de Nivel Secundario de la Región 1 Sede Lago Puelo designa "
        f"en base al listado definitivo de {anio_actual} de la Junta de Clasificación Docente "
        f"por orden de mérito al/la docente:",
        estilo_texto
    ))
    elementos.append(Spacer(1, 0.3*cm))
    
    # === DATOS DEL DOCENTE ===
    elementos.append(Paragraph("<b>DATOS DEL DOCENTE DESIGNADO/A:</b>", estilo_negrita))
    elementos.append(Spacer(1, 0.1*cm))
    
    if docente_ganador:
        nombre = docente_ganador.nombre_completo.upper() if docente_ganador.nombre_completo else '___________________________'
        dni = docente_ganador.dni if docente_ganador.dni else '_______________'
        telefono = docente_ganador.telefono if docente_ganador.telefono else '_________________________'
        
        datos_docente = [
            ['Apellido y Nombres:', nombre, '', ''],
            ['D.N.I.:', dni, 'C.U.I.L.:', '_________________________'],
            ['F. Nac.:', '___ / ___ / ______', 'Domicilio:', '______________________________________'],
            ['Teléfono:', telefono, '', ''],
        ]
        
        tabla_docente = Table(datos_docente, colWidths=[3.5*cm, 6*cm, 2*cm, 5*cm])
        tabla_docente.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            # CORRECCIÓN: Padding lateral aumentado para evitar superposición
            ('LEFTPADDING', (0, 0), (-1, -1), 10), 
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('SPAN', (1, 0), (3, 0)),
            ('SPAN', (1, 3), (3, 3)),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elementos.append(tabla_docente)
    else:
        elementos.append(Paragraph("<i>Sin docente asignado</i>", estilo_texto))
    
    elementos.append(Spacer(1, 0.4*cm))
    
    # === DATOS DEL CARGO ===
    elementos.append(Paragraph("<b>DATOS DEL CARGO / ESPACIO CURRICULAR:</b>", estilo_negrita))
    elementos.append(Spacer(1, 0.1*cm))
    
    materia_nombre = ''
    if concurso.materia:
        materia_nombre = concurso.materia.nombre
    elif concurso.espacio_curricular:
        materia_nombre = concurso.espacio_curricular
    else:
        materia_nombre = '___________________________'
    
    fecha_inicio_str = ''
    if concurso.fecha_inicio:
        fecha_inicio_str = concurso.fecha_inicio.strftime("%d/%m/%Y")
    
    datos_cargo = [
        ['Concurso N°:', concurso.numero, 'Carácter:', concurso.caracter_cargo or '________'],
        ['Título:', concurso.titulo or '____________________', '', ''],
        ['Espacio Curricular:', materia_nombre, '', ''],
        ['Escuela N°:', concurso.escuela_numero or '_______', 'Localidad:', concurso.escuela_localidad or '____________'],
        ['Folio Llamado N°:', concurso.folio_llamado or '_______', 'Horas:', concurso.horas_cargo or '________'],
    ]
    
    if concurso.horario_cargo:
        datos_cargo.append(['Horario:', concurso.horario_cargo, '', ''])
    
    if fecha_inicio_str:
        datos_cargo.append(['Fecha Inicio:', fecha_inicio_str, 'Acta N°:', concurso.numero_acta or '________'])
    
    tabla_cargo = Table(datos_cargo, colWidths=[3.5*cm, 6*cm, 2*cm, 5*cm])
    tabla_cargo.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        # CORRECCIÓN: Padding lateral aumentado
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('SPAN', (1, 1), (3, 1)),
        ('SPAN', (1, 2), (3, 2)),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    if concurso.horario_cargo:
        tabla_cargo.setStyle(TableStyle([
            ('SPAN', (1, -2 if fecha_inicio_str else -1), (3, -2 if fecha_inicio_str else -1)),
        ]))
    
    elementos.append(tabla_cargo)
    
    # === TEXTO FINAL ===
    elementos.append(Spacer(1, 0.4*cm))
    if concurso.folio_llamado and concurso.escuela_localidad:
        desde_texto = f" desde el {fecha_inicio_str}" if fecha_inicio_str else ""
        elementos.append(Paragraph(
            f"En observaciones correspondiente/s al llamado N° {concurso.folio_llamado} de la localidad de {concurso.escuela_localidad}{desde_texto}.",
            estilo_texto
        ))
    
    # === FIRMA ===
    elementos.append(Spacer(1, 1.5*cm))
    
    firma_style = ParagraphStyle(
        'Firma',
        parent=estilos['Normal'],
        alignment=TA_CENTER,
        fontSize=9,
        leading=11
    )
    
    elementos.append(Paragraph(
        "_________________________________________<br/>"
        "<b>FIRMA Y SELLO DE DIRECTOR/A DEL<br/>DPTO. DE DESIGNACIONES</b>",
        firma_style
    ))
    
    elementos.append(Spacer(1, 0.6*cm))
    
    # === PIE DE PÁGINA ===
    pie_style = ParagraphStyle(
        'Pie',
        parent=estilos['Normal'],
        alignment=TA_CENTER,
        fontSize=7,
        textColor=colors.grey,
        leading=9
    )
    elementos.append(Paragraph(
        "Ministerio de Educación - Provincia del Chubut | Dpto. Designaciones Nivel Secundario - Región 1 Lago Puelo<br/>"
        "Remigio Nogués s/n, Lago Puelo, Chubut | Tel: 02944-499415",
        pie_style
    ))
    
    doc.build(elementos)
    return filepath
