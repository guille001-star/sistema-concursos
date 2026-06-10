import qrcode
import os
import secrets
from PIL import Image
from flask import request

def generar_qr_concurso(concurso):
    if not concurso.qr_token:
        concurso.qr_token = secrets.token_urlsafe(16)
    
    # Usar la variable de entorno APP_URL si existe (Recomendado para Railway)
    # Si no existe, usa request.host_url como fallback para desarrollo local
    base_url = os.environ.get('APP_URL', request.host_url.rstrip('/'))
    url_inscripcion = f"{base_url}/inscripcion/{concurso.qr_token}"
    
    qr_dir = os.path.join('static', 'qrs')
    os.makedirs(qr_dir, exist_ok=True)
    
    filename = f"qr_{concurso.numero.replace('/', '_')}.png"
    filepath = os.path.join(qr_dir, filename)
    
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
    
    concurso.qr_image_path = filepath
    return filepath, url_inscripcion
