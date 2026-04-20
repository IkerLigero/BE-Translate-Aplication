# Importamos la clase base que ya tienes
from app.db.base_class import Base 

# Importamos todos los modelos para que SQLAlchemy los registre en Base.metadata
from app.models.user import User
from app.models.translation import Translation