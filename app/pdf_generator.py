from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime
import os

def generar_pdf_orden_merito(concurso, resultado):
    """
    Genera un PDF profesional con el orden de mérito del concurso.
    
    Args:
        concurso: Objeto Concurso con los datos del concurso
        resultado: Lista de diccionarios con el orden de mérito calculado
    
    Returns:
        Ruta del archivo PDF generado
    """
    # Crear carpeta de PDFs si no existe
    pdf_dir = os.path.join('static', 'pdfs')
    os.makedirs(pdf_dir, exist_ok=True)
    
    # Nombre del archivo
    filename = f"orden_merito_{concurso.numero.replace('/', '_')}.pdf"
    filepath = os.path.join(pdf_dir, filename)
    
    # Crear el documento
    doc = SimpleDocTemplate(filepath, pagesize=A4, 
                           rightMargin=2*cm, leftMargin=2*cm,
                           topMargin=2*cm, bottomMargin=2*cm)
    
    # Lista de elementos
    elementos = []
    
    # Estilos
    estilos = getSampleStyleSheet()
    estilo_titulo = ParagraphStyle(
        'Titulo',
        parent=estilos['Heading1'],
        fontSize=18,
        alignment=TA_CENTER,
        spaceAfter=20,
        textColor=colors.HexColor('#1a1a1a')
    )
    
    estilo_subtitulo = ParagraphStyle(
        'Subtitulo',
        parent=estilos['Heading2'],
        fontSize=14,
        alignment=TA_CENTER,
        spaceAfter=15,
        textColor=colors.HexColor('#333333')
    )
    
    estilo_info = ParagraphStyle(
        'Info',
        parent=estilos['Normal'],
        fontSize=11,
        spaceAfter=8,
        textColor=colors.HexColor('#444444')
    )
    
    # Encabezado
    elementos.append(Paragraph("ORDEN DE MÉRITO", estilo_titulo))
    elementos.append(Spacer(1, 0.3*cm))
    
    # Datos del concurso
    elementos.append(Paragraph(f"<b>Concurso N°:</b> {concurso.numero}", estilo_info))
    elementos.append(Paragraph(f"<b>Título:</b> {concurso.titulo or 'N/A'}", estilo_info))
    
    if concurso.materia:
        elementos.append(Paragraph(f"<b>Materia/Espacio Curricular:</b> {concurso.materia.nombre}", estilo_info))
    
    elementos.append(Paragraph(f"<b>Carácter del Cargo:</b> {concurso.caracter_cargo}", estilo_info))
    
    if concurso.fecha_apertura:
        elementos.append(Paragraph(f"<b>Fecha de Apertura:</b> {concurso.fecha_apertura.strftime('%d/%m/%Y')}", estilo_info))
    
    if concurso.fecha_cierre:
        elementos.append(Paragraph(f"<b>Fecha de Cierre:</b> {concurso.fecha_cierre.strftime('%d/%m/%Y')}", estilo_info))
    
    elementos.append(Spacer(1, 0.5*cm))
    elementos.append(Paragraph(f"<b>Estado del Concurso:</b> {concurso.estado}", estilo_info))
    
    if concurso.observacion:
        elementos.append(Spacer(1, 0.3*cm))
        elementos.append(Paragraph(f"<b>Observación:</b> {concurso.observacion}", estilo_info))
    
    elementos.append(Spacer(1, 0.8*cm))
    
    # Tabla de orden de mérito
    if resultado and isinstance(resultado, list) and len(resultado) > 0:
        elementos.append(Paragraph("LISTADO DE INSCRIPTOS POR ORDEN DE MÉRITO", estilo_subtitulo))
        elementos.append(Spacer(1, 0.4*cm))
        
        # Encabezados de la tabla
        datos_tabla = [['Orden', 'DNI', 'Apellido y Nombres', 'Categoría', 'Puntaje', 'Estado']]
        
        for item in resultado:
            estado = 'GANADOR' if item.get('es_ganador') else ''
            datos_tabla.append([
                str(item['orden']),
                item['dni'],
                item['nombre'][:40] if len(item['nombre']) > 40 else item['nombre'],
                item['categoria'],
                f"{item['puntaje']:.2f}",
                estado
            ])
        
        # Crear la tabla
        tabla = Table(datos_tabla, colWidths=[1.5*cm, 2.5*cm, 7*cm, 2*cm, 2*cm, 2.5*cm])
        
        # Estilo de la tabla
        estilo_tabla = TableStyle([
            # Encabezados
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            
            # Filas de datos
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),
            ('ALIGN', (2, 1), (2, -1), 'LEFT'),
            ('ALIGN', (3, 1), (3, -1), 'CENTER'),
            ('ALIGN', (4, 1), (4, -1), 'CENTER'),
            ('ALIGN', (5, 1), (5, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            
            # Bordes
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('LINEBELOW', (0, 0), (-1, 0), 1.5, colors.HexColor('#2c3e50')),
            
            # Resaltar al ganador
            ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#d4edda')),
            ('TEXTCOLOR', (0, 1), (-1, 1), colors.HexColor('#155724')),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ])
        
        # Aplicar colores alternados
        for i in range(2, len(datos_tabla)):
            if i % 2 == 0:
                estilo_tabla.add('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f8f9fa'))
        
        tabla.setStyle(estilo_tabla)
        elementos.append(tabla)
        
        # Pie de página
        elementos.append(Spacer(1, 1*cm))
        estilo_fecha = ParagraphStyle(
            'Fecha',
            parent=estilos['Normal'],
            fontSize=9,
            alignment=TA_CENTER,
            textColor=colors.grey
        )
        elementos.append(Paragraph(
            f"Documento generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M')}",
            estilo_fecha
        ))
    else:
        elementos.append(Paragraph("<b>No hay inscripciones para generar el orden de mérito.</b>", estilo_info))
    
    # Generar el PDF
    doc.build(elementos)
    
    return filepath
