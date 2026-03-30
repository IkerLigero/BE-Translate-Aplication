import sys
import os

# Añadir el directorio actual al PATH
sys.path.append(os.getcwd())

# 1. El engine sí está en session
from app.db.session import engine
# 2. El Base está en base_class.py según lo que me mostraste
from app.db.base_class import Base 
# 3. Importamos el modelo para que SQLAlchemy registre la tabla 'translations'
from app.models.translation import Translation 

def run_fix():
    print("--- 🛠️ Iniciando Reset de Base de Datos ---")
    try:
        # Esto eliminará la tabla 'translations' antigua
        Base.metadata.drop_all(bind=engine)
        print("✅ Tabla antigua eliminada.")
        
        # Esto creará la tabla nueva con pdf_lang, source_lang y file_path
        Base.metadata.create_all(bind=engine)
        print("✅ Tabla creada con éxito (nueva estructura completa).")
        
    except Exception as e:
        print(f"❌ Error durante el proceso: {e}")

if __name__ == "__main__":
    run_fix()