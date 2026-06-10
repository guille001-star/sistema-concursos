from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class Admin(UserMixin, db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Concurso(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(50), unique=True, nullable=False)
    titulo = db.Column(db.String(200))
    espacio_curricular = db.Column(db.String(200))
    fecha_apertura = db.Column(db.DateTime)
    fecha_cierre = db.Column(db.DateTime)
    caracter_cargo = db.Column(db.String(20))
    estado = db.Column(db.String(20), default='ACTIVO')
    observacion = db.Column(db.Text, nullable=True)
    qr_token = db.Column(db.String(100), unique=True, nullable=True)
    qr_image_path = db.Column(db.String(200), nullable=True)
    pdf_listado_path = db.Column(db.String(200), nullable=True)
    pdf_merito_path = db.Column(db.String(200), nullable=True)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)
    actualizado_en = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    inscripciones = db.relationship('Inscripcion', backref='concurso', lazy=True, cascade='all, delete-orphan')
    
    def esta_activo(self):
        ahora = datetime.utcnow()
        return self.estado == 'ACTIVO' and self.fecha_apertura <= ahora <= self.fecha_cierre
    
    def tiempo_restante(self):
        if not self.fecha_cierre:
            return None
        delta = self.fecha_cierre - datetime.utcnow()
        if delta.total_seconds() <= 0:
            return "CERRADO"
        dias = delta.days
        horas, resto = divmod(delta.seconds, 3600)
        minutos, _ = divmod(resto, 60)
        return f"{dias}d {horas}h {minutos}m"

class DocenteOficial(db.Model):
    __tablename__ = 'docentes_oficiales'
    id = db.Column(db.Integer, primary_key=True)
    legajo = db.Column(db.String(20))
    dni = db.Column(db.String(20), index=True, unique=True)
    nombre_completo = db.Column(db.String(250))
    telefono = db.Column(db.String(50))
    categoria = db.Column(db.String(10))
    puntaje = db.Column(db.Float)
    materia_base = db.Column(db.String(200))
    
    def __repr__(self):
        return f'<Docente {self.dni}>'

class Inscripcion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    concurso_id = db.Column(db.Integer, db.ForeignKey('concurso.id'), nullable=False)
    dni_docente = db.Column(db.String(20), db.ForeignKey('docentes_oficiales.dni'), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    codigo_confirmacion = db.Column(db.String(20), unique=True, nullable=True)
    fecha_inscripcion = db.Column(db.DateTime, default=datetime.utcnow)
    estado = db.Column(db.String(20), default='VALIDADO')
    orden_merito = db.Column(db.Integer, nullable=True)
    ip_address = db.Column(db.String(50), nullable=True)
    user_agent = db.Column(db.String(200), nullable=True)
    
    docente = db.relationship('DocenteOficial', backref='inscripciones')
    
    __table_args__ = (
        db.UniqueConstraint('concurso_id', 'dni_docente', name='uq_inscripcion_concurso_dni'),
    )

class LogAuditoria(db.Model):
    __tablename__ = 'logs_auditoria'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    accion = db.Column(db.String(100), nullable=False)
    detalle = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(50), nullable=True)
    user_id = db.Column(db.Integer, nullable=True)
