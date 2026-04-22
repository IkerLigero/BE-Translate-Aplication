from app.db.base_class import Base 

# Import all models so that SQLAlchemy registers them in Base.metadata
from app.models.user import User
from app.models.translation import Translation