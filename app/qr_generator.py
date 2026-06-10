import qrcode
import os
import secrets
from PIL import Image
from flask import request

def generar_qr_concurso(concurso):
    """
    Genera un código QR único para el concurso.
    Detecta automáticamente el dominio actual (localhost o Railway).
    """
    # Generar token único si no existe
    if not concurso.qr_token:
        concurso.qr_token = secrets.token_urlsafe(16)
    
    # Detectar la URL base automáticamente (ej: https://sistema-concursos...up.railway.app)
    base_url = request.host_url.rstrip('/')
    url_inscripcion = f"{base_url}/inscripcion/{concurso.qr_token}"
    
    # Crear carpeta de QRs si no existe
    qr_dir = os.path.join('static', 'qrs')
    os.makedirs(qr_dir, exist_ok=True)
    
    # Nombre del archivo
    filename = f"qr_{concurso.numero.replace('/', '_')}.png"
    filepath = os.path.join(qr_dir, filename)
    
    # Generar QR
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(url_inscripcion)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(filepath)
    
    # Guardar ruta en el concurso
    concurso.qr_image_path = filepath
    
    return filepath, url_inscripcion
