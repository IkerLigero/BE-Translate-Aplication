from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base # O donde tengas tu Base de SQLAlchemy

class User(Base):
    __tablename__ = "users"

    # Define the columns for the User model
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Define the relationship to the Translation model
    translations = relationship("Translation", back_populates="owner")