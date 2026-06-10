from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime
import os
import hashlib

def generar_pdf_orden_merito(concurso, orden_merito, ruta_salida=None):
    """
    Genera el PDF oficial del orden de mérito.
    """
    if not ruta_salida:
        pdf_dir = os.path.join('static', 'pdfs')
        os.makedirs(pdf_dir, exist_ok=True)
        ruta_salida = os.path.join(pdf_dir, f"merito_{concurso.numero.replace('/', '_')}.pdf")
    
    doc = SimpleDocTemplate(
        ruta_salida,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    styles = getSampleStyleSheet()
    
    # Estilos personalizados
    titulo_style = ParagraphStyle(
        'Titulo',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=0.5*cm,
        alignment=TA_CENTER
    )
    
    subtitulo_style = ParagraphStyle(
        'Subtitulo',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#333333'),
        spaceAfter=0.3*cm,
        alignment=TA_CENTER
    )
    
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_LEFT
    )
    
    elementos = []
    
    # Encabezado
    elementos.append(Paragraph("SISTEMA DE CONCURSOS DOCENTES", titulo_style))
    elementos.append(Paragraph("ORDEN DE MÉRITO OFICIAL", subtitulo_style))
    elementos.append(Spacer(1, 0.5*cm))
    
    # Información del concurso
    info_concurso = [
        ['Número de Concurso:', concurso.numero],
        ['Título:', concurso.titulo or 'N/A'],
        ['Espacio Curricular:', concurso.espacio_curricular or 'N/A'],
        ['Carácter del Cargo:', concurso.caracter_cargo or 'N/A'],
        ['Estado:', concurso.estado],
        ['Fecha de Generación:', datetime.utcnow().strftime('%d/%m/%Y %H:%M:%S')],
    ]
    
    if concurso.observacion:
        info_concurso.append(['Observación:', concurso.observacion])
    
    tabla_info = Table(info_concurso, colWidths=[5*cm, 10*cm])
    tabla_info.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elementos.append(tabla_info)
    elementos.append(Spacer(1, 0.5*cm))
    
    # Tabla de orden de mérito
    if orden_merito:
        datos_tabla = [['Posición', 'DNI', 'Apellido y Nombre', 'Categoría', 'Puntaje']]
        
        for item in orden_merito:
            datos_tabla.append([
                str(item['orden']),
                item['dni'],
                item['nombre'][:40],  # Truncar si es muy largo
                item['categoria'],
                f"{item['puntaje']:.2f}"
            ])
        
        tabla_merito = Table(datos_tabla, colWidths=[2*cm, 3*cm, 7*cm, 2*cm, 2*cm])
        tabla_merito.setStyle(TableStyle([
            # Encabezado
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            # Cuerpo
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Posición centrada
            ('ALIGN', (3, 1), (4, -1), 'CENTER'),  # Categoría y puntaje centrados
            
            # Bordes
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            
            # Filas alternadas
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            
            # Padding
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elementos.append(tabla_merito)
    else:
        elementos.append(Paragraph("No hay inscriptos en este concurso.", normal_style))
    
    elementos.append(Spacer(1, 1*cm))
    
    # Pie de página con hash de verificación
    contenido_pdf = open(ruta_salida, 'rb').read() if os.path.exists(ruta_salida) else b''
    hash_verificacion = hashlib.sha256(contenido_pdf).hexdigest()[:16] if contenido_pdf else 'PENDIENTE'
    
    pie_style = ParagraphStyle(
        'Pie',
        parent=styles['Normal'],
        fontSize=7,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    
    elementos.append(Paragraph(
        f"Documento generado automáticamente | Hash: {hash_verificacion} | "
        f"Total de inscriptos: {len(orden_merito) if orden_merito else 0}",
        pie_style
    ))
    
    # Construir PDF
    doc.build(elementos)
    
    # Actualizar ruta en el concurso
    concurso.pdf_merito_path = ruta_salida
    
    return ruta_salida
