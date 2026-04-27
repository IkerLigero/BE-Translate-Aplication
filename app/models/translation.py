import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Translation(Base):
    __tablename__ = "translations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    original_text = Column(String(4500), nullable=False)
    target_language = Column(String, nullable=False)
    pdf_lang = Column(String, nullable=False)
    source_lang = Column(String, nullable=False)
    status = Column(String, default="pending")
    translated_text = Column(Text, nullable=True)
    created_at = Column(
            DateTime(timezone=True), 
            
            default=lambda: datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=1)))
        )
    file_path = Column(String, nullable=True)
    
    # Relationship to the User model
    owner = relationship("User", back_populates="translations")