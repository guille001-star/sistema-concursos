from app import create_app, db
from app.models import Admin, Concurso, DocenteOficial, Materia, PuntajeMateria, Inscripcion, LogAuditoria
import os

app = create_app()

with app.app_context():
    print("⚠️  ATENCIÓN: Esto borrará TODOS los datos de la base de datos.")
    print("   (Docentes, concursos, inscripciones, etc.)")
    confirmacion = input("¿Estás seguro? (escribe 'SI' para continuar): ")
    
    if confirmacion == 'SI':
        try:
            # Usar db.drop_all() que es compatible con SQLite y PostgreSQL
            db.drop_all()
            print("✅ Todas las tablas fueron eliminadas.")
            
            # Recrear todas las tablas con la nueva estructura
            db.create_all()
            print("✅ Todas las tablas fueron recreadas con la nueva estructura.")
            
            # Recrear el usuario admin por defecto
            admin = Admin(username='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("✅ Usuario admin creado (admin / admin123)")
            
            print("\n🎉 Base de datos reseteada correctamente.")
            print("📝 Ahora debes cargar el PDF nuevamente desde el panel de admin.")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error al resetear la base de datos: {e}")
    else:
        print("❌ Operación cancelada.")
