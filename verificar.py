import os
from app import create_app

# Inicializar la app para obtener las rutas absolutas correctas
app = create_app()
print(f"🔍 Flask buscará templates en: {app.template_folder}")

# Verificar y crear archivos esenciales si faltan o están vacíos
archivos_a_verificar = {
    'base.html': '<!DOCTYPE html><html><head><title>{% block title %}App{% endblock %}</title></head><body>{% block content %}{% endblock %}</body></html>',
    'index.html': "{% extends 'base.html' %}\n{% block title %}Inicio{% endblock %}\n{% block content %}<h1>✅ Sistema Funcionando</h1><p>Los templates se cargan correctamente.</p>{% endblock %}",
    'error.html': "{% extends 'base.html' %}\n{% block title %}Error{% endblock %}\n{% block content %}<h1>Error</h1><p>{{ error }}</p><a href='/'>Volver</a>{% endblock %}"
}

for nombre, contenido in archivos_a_verificar.items():
    ruta_completa = os.path.join(app.template_folder, nombre)
    
    # Crear o sobrescribir si está vacío
    if not os.path.exists(ruta_completa) or os.path.getsize(ruta_completa) == 0:
        with open(ruta_completa, 'w', encoding='utf-8') as f:
            f.write(contenido)
        print(f"✅ Creado: {nombre}")
    else:
        print(f"✔️ Ya existe y tiene contenido: {nombre}")

# Crear carpeta admin si no existe
admin_dir = os.path.join(app.template_folder, 'admin')
os.makedirs(admin_dir, exist_ok=True)
login_path = os.path.join(admin_dir, 'login.html')
if not os.path.exists(login_path) or os.path.getsize(login_path) == 0:
    with open(login_path, 'w', encoding='utf-8') as f:
        f.write("{% extends 'base.html' %}\n{% block content %}<h1>Admin Login</h1><form method='POST'><input name='username' placeholder='User'><input name='password' type='password' placeholder='Pass'><button type='submit'>Entrar</button></form><p>admin / admin123</p>{% endblock %}")
    print("✅ Creado: admin/login.html")

print("\n🎉 ¡Verificación completada! Ahora reinicia el servidor.")