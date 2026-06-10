import os
from app import create_app

# 1. Crear la app para ver dónde busca Flask los templates
app = create_app()
template_folder = os.path.abspath(app.template_folder)
print(f"Flask busca templates en: {template_folder}")

# 2. Asegurarse de que las carpetas existan
os.makedirs(template_folder, exist_ok=True)
os.makedirs(os.path.join(template_folder, 'admin'), exist_ok=True)

# 3. Crear templates esenciales
templates = {
    'base.html': '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>{% block title %}Concursos{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-dark bg-dark p-3">
        <a class="navbar-brand" href="/">Concursos Docentes</a>
    </nav>
    <div class="container mt-4">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        {% block content %}{% endblock %}
    </div>
</body>
</html>''',
    
    'index.html': '''{% extends 'base.html' %}
{% block title %}Inicio{% endblock %}
{% block content %}
<h1>Concursos Activos</h1>
{% if concursos %}
    {% for c in concursos %}
    <div class="card mb-3">
        <div class="card-body">
            <h5>{{ c.numero }}</h5>
            <p>{{ c.titulo }}</p>
            <p><small>{{ c.espacio_curricular }}</small></p>
        </div>
    </div>
    {% endfor %}
{% else %}
    <p>No hay concursos activos.</p>
{% endif %}
{% endblock %}''',

    'error.html': '''{% extends 'base.html' %}
{% block title %}Error{% endblock %}
{% block content %}
<div class="alert alert-danger">
    <h4>Error</h4>
    <p>{{ error }}</p>
    <a href="/" class="btn btn-primary">Volver</a>
</div>
{% endblock %}''',

    'admin/login.html': '''{% extends 'base.html' %}
{% block title %}Login{% endblock %}
{% block content %}
<div class="row justify-content-center">
    <div class="col-md-4">
        <div class="card">
            <div class="card-body">
                <h4>Admin Login</h4>
                <form method="POST">
                    <input type="text" name="username" class="form-control mb-2" placeholder="Usuario" required>
                    <input type="password" name="password" class="form-control mb-2" placeholder="Contrasena" required>
                    <button type="submit" class="btn btn-primary w-100">Ingresar</button>
                </form>
                <small class="text-muted">admin / admin123</small>
            </div>
        </div>
    </div>
</div>
{% endblock %}'''
}

# 4. Escribir los archivos
for nombre, contenido in templates.items():
    ruta = os.path.join(template_folder, nombre)
    with open(ruta, 'w', encoding='utf-8') as f:
        f.write(contenido)
    print(f"Creado: {ruta}")

print("\nTemplates creados correctamente!")
print("Ahora reinicia el servidor: Ctrl+C y luego python run.py")