import qrcode
import os
import secrets
from PIL import Image
from flask import request

def generar_qr_concurso(concurso, forzar_nuevo=False):
    """
    Genera el código QR para un concurso.
    
    Args:
        concurso: Objeto Concurso
        forzar_nuevo: Si es True, genera un nuevo token. Si es False, mantiene el existente.
    
    Returns:
        Tuple con (filepath, url_inscripcion)
    """
    # Si forzamos o no tiene token, creamos uno nuevo
    if forzar_nuevo or not concurso.qr_token:
        concurso.qr_token = secrets.token_urlsafe(16)
    
    # Usar la variable de entorno APP_URL si existe (Recomendado para Railway)
    base_url = os.environ.get('APP_URL', request.host_url.rstrip('/'))
    url_inscripcion = f"{base_url}/inscripcion/{concurso.qr_token}"
    
    # Crear carpeta de QRs si no existe
    qr_dir = os.path.join('static', 'qrs')
    os.makedirs(qr_dir, exist_ok=True)
    
    # Nombre del archivo
    filename = f"qr_{concurso.numero.replace('/', '_')}.png"
    filepath = os.path.join(qr_dir, filename)
    
    # Generar el QR
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(url_inscripcion)
    qr.make(fit=True)
    
    # Crear la imagen
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(filepath)
    
    # Guardar la ruta en el concurso
    concurso.qr_image_path = filepath
    
    return filepath, url_inscripcion
