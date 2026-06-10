import os

# Crear estructura de carpetas
os.makedirs('templates/admin', exist_ok=True)
os.makedirs('templates/docente', exist_ok=True)

templates = {
    'templates/base.html': '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Sistema de Concursos Docentes{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css">
    <style>
        body { background-color: #f8f9fa; }
        .navbar-brand { font-weight: bold; }
        .card { box-shadow: 0 0.125rem 0.25rem rgba(0,0,0,0.075); }
        .btn-primary { background-color: #2c3e50; border-color: #2c3e50; }
        .btn-primary:hover { background-color: #1a252f; border-color: #1a252f; }
        .stat-card { border-left: 4px solid #2c3e50; }
        footer { margin-top: 3rem; padding: 2rem 0; background-color: #2c3e50; color: white; }
    </style>
    {% block extra_css %}{% endblock %}
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="{{ url_for('main.index') }}">
                <i class="bi bi-journal-bookmark-fill"></i> Concursos Docentes
            </a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item">
                        <a class="nav-link" href="{{ url_for('main.index') }}">Inicio</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="{{ url_for('admin.login') }}">
                            <i class="bi bi-shield-lock"></i> Admin
                        </a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }} alert-dismissible fade show" role="alert">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        {% block content %}{% endblock %}
    </div>

    <footer class="text-center">
        <div class="container">
            <p class="mb-0">Sistema de Concursos Docentes &copy; 2026</p>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    {% block extra_js %}{% endblock %}
</body>
</html>''',

    'templates/index.html': '''{% extends 'base.html' %}

{% block title %}Concursos Activos{% endblock %}

{% block content %}
<div class="row mb-4">
    <div class="col-12">
        <h1><i class="bi bi-megaphone-fill"></i> Concursos Activos</h1>
        <p class="text-muted">Inscribite a los concursos disponibles.</p>
    </div>
</div>

{% if concursos %}
    <div class="row">
        {% for concurso in concursos %}
        <div class="col-md-6 col-lg-4 mb-4">
            <div class="card h-100">
                <div class="card-header bg-primary text-white">
                    <h5 class="mb-0">{{ concurso.numero }}</h5>
                </div>
                <div class="card-body">
                    <h6 class="card-title">{{ concurso.titulo }}</h6>
                    <p class="card-text text-muted small">{{ concurso.espacio_curricular }}</p>
                    <ul class="list-unstyled">
                        <li><i class="bi bi-clock"></i> <strong>Caracter:</strong> {{ concurso.caracter_cargo }}</li>
                        <li><i class="bi bi-calendar-event"></i> <strong>Abre:</strong> {{ concurso.fecha_apertura.strftime('%d/%m/%Y %H:%M') if concurso.fecha_apertura else 'N/A' }}</li>
                        <li><i class="bi bi-calendar-x"></i> <strong>Cierra:</strong> {{ concurso.fecha_cierre.strftime('%d/%m/%Y %H:%M') if concurso.fecha_cierre else 'N/A' }}</li>
                        <li><i class="bi bi-people-fill"></i> <strong>Inscriptos:</strong> {{ concurso.inscripciones|length }}</li>
                    </ul>
                </div>
                <div class="card-footer">
                    {% if concurso.esta_activo() and concurso.qr_token %}
                        <a href="{{ url_for('main.inscripcion_publica', token=concurso.qr_token) }}" 
                           class="btn btn-primary w-100">
                            <i class="bi bi-pencil-square"></i> Inscribirme
                        </a>
                    {% else %}
                        <button class="btn btn-secondary w-100" disabled>
                            <i class="bi bi-lock-fill"></i> Cerrado
                        </button>
                    {% endif %}
                </div>
            </div>
        </div>
        {% endfor %}
    </div>
{% else %}
    <div class="alert alert-info">
        <i class="bi bi-info-circle"></i> No hay concursos activos en este momento.
    </div>
{% endif %}
{% endblock %}''',

    'templates/error.html': '''{% extends 'base.html' %}

{% block title %}Error{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-md-8">
        <div class="card border-danger">
            <div class="card-header bg-danger text-white">
                <h4><i class="bi bi-exclamation-triangle"></i> Error</h4>
            </div>
            <div class="card-body">
                <p class="lead">Ocurrio un error al procesar su solicitud.</p>
                <div class="alert alert-danger">
                    <code>{{ error }}</code>
                </div>
                <a href="{{ url_for('main.index') }}" class="btn btn-primary">
                    <i class="bi bi-house"></i> Volver al Inicio
                </a>
            </div>
        </div>
    </div>
</div>
{% endblock %}''',

    'templates/admin/login.html': '''{% extends 'base.html' %}

{% block title %}Login Admin{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-md-6 col-lg-4">
        <div class="card">
            <div class="card-header bg-dark text-white text-center">
                <h4><i class="bi bi-shield-lock"></i> Panel de Administracion</h4>
            </div>
            <div class="card-body">
                <form method="POST">
                    <div class="mb-3">
                        <label for="username" class="form-label">Usuario</label>
                        <input type="text" class="form-control" id="username" name="username" required autofocus>
                    </div>
                    <div class="mb-3">
                        <label for="password" class="form-label">Contrasena</label>
                        <input type="password" class="form-control" id="password" name="password" required>
                    </div>
                    <button type="submit" class="btn btn-primary w-100">
                        <i class="bi bi-box-arrow-in-right"></i> Ingresar
                    </button>
                </form>
            </div>
            <div class="card-footer text-center text-muted small">
                Credenciales por defecto: admin / admin123
            </div>
        </div>
    </div>
</div>
{% endblock %}''',

    'templates/admin/dashboard.html': '''{% extends 'base.html' %}

{% block title %}Dashboard Admin{% endblock %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h1><i class="bi bi-speedometer2"></i> Dashboard</h1>
    <div>
        <span class="text-muted">Bienvenido, {{ session.admin_username }}</span>
        <a href="{{ url_for('admin.logout') }}" class="btn btn-outline-danger btn-sm ms-2">
            <i class="bi bi-box-arrow-right"></i> Salir
        </a>
    </div>
</div>

<div class="row mb-4">
    <div class="col-md-3">
        <div class="card stat-card">
            <div class="card-body">
                <h6 class="text-muted">Total Concursos</h6>
                <h2>{{ total_concursos }}</h2>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card stat-card" style="border-left-color: #28a745;">
            <div class="card-body">
                <h6 class="text-muted">Concursos Activos</h6>
                <h2>{{ concursos_activos }}</h2>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card stat-card" style="border-left-color: #ffc107;">
            <div class="card-body">
                <h6 class="text-muted">Total Inscripciones</h6>
                <h2>{{ total_inscripciones }}</h2>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card stat-card" style="border-left-color: #17a2b8;">
            <div class="card-body">
                <h6 class="text-muted">Docentes en Listado</h6>
                <h2>{{ total_docentes }}</h2>
            </div>
        </div>
    </div>
</div>

<div class="row">
    <div class="col-md-8">
        <div class="card">
            <div class="card-header">
                <h5><i class="bi bi-clock-history"></i> Concursos Recientes</h5>
            </div>
            <div class="card-body">
                {% if concursos_recientes %}
                <table class="table table-hover">
                    <thead>
                        <tr>
                            <th>Numero</th>
                            <th>Titulo</th>
                            <th>Estado</th>
                            <th>Inscriptos</th>
                            <th>Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for c in concursos_recientes %}
                        <tr>
                            <td><strong>{{ c.numero }}</strong></td>
                            <td>{{ c.titulo[:30] }}...</td>
                            <td>
                                <span class="badge bg-{{ 'success' if c.estado == 'ACTIVO' else 'secondary' }}">
                                    {{ c.estado }}
                                </span>
                            </td>
                            <td>{{ c.inscripciones|length }}</td>
                            <td>
                                <a href="{{ url_for('admin.detalle_concurso', id=c.id) }}" class="btn btn-sm btn-primary">
                                    <i class="bi bi-eye"></i>
                                </a>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
                {% else %}
                <p class="text-muted">No hay concursos creados aun.</p>
                {% endif %}
            </div>
        </div>
    </div>
    <div class="col-md-4">
        <div class="card">
            <div class="card-header">
                <h5><i class="bi bi-lightning-charge"></i> Acciones Rapidas</h5>
            </div>
            <div class="card-body">
                <div class="d-grid gap-2">
                    <a href="{{ url_for('admin.crear_concurso') }}" class="btn btn-primary">
                        <i class="bi bi-plus-circle"></i> Crear Concurso
                    </a>
                    <a href="{{ url_for('admin.cargar_listado') }}" class="btn btn-success">
                        <i class="bi bi-file-earmark-pdf"></i> Cargar Listado PDF
                    </a>
                    <a href="{{ url_for('admin.listar_concursos') }}" class="btn btn-info">
                        <i class="bi bi-list-ul"></i> Ver Todos los Concursos
                    </a>
                    <a href="{{ url_for('admin.listar_docentes') }}" class="btn btn-secondary">
                        <i class="bi bi-people"></i> Ver Docentes
                    </a>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}'''
}

# Crear todos los archivos
for ruta, contenido in templates.items():
    with open(ruta, 'w', encoding='utf-8') as f:
        f.write(contenido)
    print(f"✓ Creado: {ruta}")

print("\n✅ Todos los templates fueron creados correctamente!")
print("\nAhora reinicia el servidor: python run.py")