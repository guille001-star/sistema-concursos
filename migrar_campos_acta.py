from app import create_app, db
from app.models import Admin, Concurso, DocenteOficial, Inscripcion, Materia, PuntajeMateria, LogAuditoria
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("🔧 Agregando campos al modelo Concurso...")
    try:
        # Agregar columnas una por una (ignorando si ya existen)
        columnas = [
            "folio_llamado VARCHAR(50)",
            "escuela_numero VARCHAR(20)",
            "escuela_localidad VARCHAR(100)",
            "horas_cargo VARCHAR(50)",
            "horario_cargo TEXT",
            "fecha_inicio DATE",
            "numero_acta VARCHAR(50)"
        ]
        
        for columna in columnas:
            nombre_col = columna.split()[0]
            sql = f"ALTER TABLE concurso ADD COLUMN IF NOT EXISTS {nombre_col} {columna.split(' ', 1)[1]}"
            try:
                db.session.execute(text(sql))
                print(f"  ✅ Columna {nombre_col} agregada/verificada")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print(f"  ℹ️  Columna {nombre_col} ya existe")
                else:
                    print(f"  ⚠️  Error en {nombre_col}: {e}")
        
        db.session.commit()
        print("\n✅ Migración de base de datos completada exitosamente")
        
    except Exception as e:
        db.session.rollback()
        print(f"\n❌ Error en la migración: {e}")
