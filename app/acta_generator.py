from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
import os

def generar_acta_designacion(concurso, docente_ganador):
    """
    Genera el Acta de Designación en PDF con formato oficial.
    Usa los datos disponibles y deja espacios para completar manualmente.
    """
    # Crear carpeta de actas si no existe
    actas_dir = os.path.join('static', 'actas')
    os.makedirs(actas_dir, exist_ok=True)
    
    # Nombre del archivo
    filename = f"acta_{concurso.numero.replace('/', '_')}.pdf"
    filepath = os.path.join(actas_dir, filename)
    
    # Crear el documento (orientación vertical)
    doc = SimpleDocTemplate(filepath, pagesize=A4,
                           rightMargin=2*cm, leftMargin=2*cm,
                           topMargin=2.5*cm, bottomMargin=2*cm)
    
    elementos = []
    estilos = getSampleStyleSheet()
    
    # Estilos personalizados
    estilo_titulo = ParagraphStyle(
        'Titulo',
        parent=estilos['Heading1'],
        fontSize=16,
        alignment=TA_CENTER,
        spaceAfter=15,
        textColor=colors.HexColor('#003366'),
        fontName='Helvetica-Bold'
    )
    
    estilo_subtitulo = ParagraphStyle(
        'Subtitulo',
        parent=estilos['Normal'],
        fontSize=10,
        alignment=TA_CENTER,
        spaceAfter=20,
        textColor=colors.black
    )
    
    estilo_texto = ParagraphStyle(
        'Texto',
        parent=estilos['Normal'],
        fontSize=11,
        spaceAfter=8,
        textColor=colors.black,
        leading=14
    )
    
    estilo_negrita = ParagraphStyle(
        'Negrita',
        parent=estilos['Normal'],
        fontSize=11,
        spaceAfter=8,
        textColor=colors.black,
        fontName='Helvetica-Bold',
        leading=14
    )
    
    # Encabezado institucional
    elementos.append(Paragraph("<b>MINISTERIO DE EDUCACIÓN DE LA PROVINCIA DEL CHUBUT</b>", estilo_subtitulo))
    elementos.append(Paragraph("<b>DEPARTAMENTO DE DESIGNACIONES DE EDUCACIÓN SECUNDARIA</b>", estilo_subtitulo))
    elementos.append(Paragraph("<b>REGIÓN 1</b>", estilo_subtitulo))
    elementos.append(Spacer(1, 0.5*cm))
    
    # Título del acta
    elementos.append(Paragraph("ACTA DE DESIGNACIÓN", estilo_titulo))
    
    # Fecha y lugar
    fecha_actual = datetime.now().strftime("%d de %B de %Y").upper()
    elementos.append(Paragraph(f"LAGO PUELO, CHUBUT, {fecha_actual}", estilo_texto))
    elementos.append(Spacer(1, 0.3*cm))
    
    # Texto introductorio
    elementos.append(Paragraph(
        f"El Departamento de Designaciones de Nivel Secundario de la Región 1 Sede Lago Puelo designa "
        f"en base al listado definitivo de {datetime.now().strftime('%Y')} de la Junta de Clasificación Docente "
        f"por orden de mérito al/la docente:",
        estilo_texto
    ))
    elementos.append(Spacer(1, 0.5*cm))
    
    # Datos del docente
    elementos.append(Paragraph("<b>DATOS DEL DOCENTE DESIGNADO/A:</b>", estilo_negrita))
    elementos.append(Spacer(1, 0.2*cm))
    
    if docente_ganador:
        elementos.append(Paragraph(
            f"<b>Apellido y Nombres:</b> {docente_ganador.nombre_completo.upper() if docente_ganador.nombre_completo else '___________________________'}",
            estilo_texto
        ))
        elementos.append(Paragraph(
            f"<b>D.N.I.:</b> {docente_ganador.dni if docente_ganador.dni else '_______________'}",
            estilo_texto
        ))
        elementos.append(Paragraph(
            f"<b>C.U.I.L.:</b> _________________________",  # Espacio en blanco
            estilo_texto
        ))
        elementos.append(Paragraph(
            f"<b>F. Nac.:</b> ___ / ___ / ______  <b>Domicilio:</b> _________________________________________",
            estilo_texto
        ))
        elementos.append(Paragraph(
            f"<b>Teléfono:</b> _________________________",
            estilo_texto
        ))
    else:
        elementos.append(Paragraph("<i>Sin docente asignado</i>", estilo_texto))
    
    elementos.append(Spacer(1, 0.5*cm))
    
    # Datos del cargo
    elementos.append(Paragraph("<b>ESPACIO CURRICULAR / CARGO:</b>", estilo_negrita))
    elementos.append(Spacer(1, 0.3*cm))
    
    # Tabla de datos del cargo
    datos_tabla = [
        ['Concurso N°:', concurso.numero],
        ['Título:', concurso.titulo or '___________________________'],
        ['Espacio Curricular:', concurso.espacio_curricular or (concurso.materia.nombre if concurso.materia else '___________________________')],
        ['Carácter del Cargo:', concurso.caracter_cargo],
        ['Folio del Llamado:', 'N° _______'],  # Espacio en blanco
    ]
    
    tabla_cargo = Table(datos_tabla, colWidths=[4*cm, 10*cm])
    tabla_cargo.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
    ]))
    
    elementos.append(tabla_cargo)
    elementos.append(Spacer(1, 0.5*cm))
    
    # Texto de observaciones
    elementos.append(Paragraph(
        "<b>OBSERVACIONES:</b> EN OBSERVACIONES correspondiente/s al llamado N°______ de la localidad de Lago Puelo. "
        "Desde el ___/___/______.",
        estilo_texto
    ))
    elementos.append(Spacer(1, 1*cm))
    
    # Espacio para firma y sello
    elementos.append(Spacer(1, 2*cm))
    
    linea_firma = Paragraph(
        "_________________________________________<br/>"
        "<b>FIRMA Y SELLO DE DIRECTOR/A DEL<br/>DPTO. DE DESIGNACIONES</b>",
        ParagraphStyle('Firma', parent=estilos['Normal'], alignment=TA_CENTER, fontSize=9)
    )
    elementos.append(linea_firma)
    
    elementos.append(Spacer(1, 1.5*cm))
    
    # Pie de página
    pie = Paragraph(
        "<font size='8' color='#666666'>"
        "Ministerio de Educación de la Provincia del Chubut<br/>"
        "Departamento de Designaciones Nivel Secundario - Región 1 Lago Puelo<br/>"
        "Remigio Nogués s/n, Lago Puelo, Chubut | Tel: 02944-499415"
        "</font>",
        ParagraphStyle('Pie', parent=estilos['Normal'], alignment=TA_CENTER, fontSize=8, textColor=colors.grey)
    )
    elementos.append(pie)
    
    # Generar el PDF
    doc.build(elementos)
    
    return filepath
