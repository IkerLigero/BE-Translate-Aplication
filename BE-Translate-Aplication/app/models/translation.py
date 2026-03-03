from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from app.db.base_class import Base

class Translation(Base):
    __tablename__ = "translations"

    id = Column(Integer, primary_key=True, index=True)
    original_text = Column(Text, nullable=False)
    target_language = Column(String, nullable=False) # "ex: "en", "es", "fr"
    source_lang = Column(String, nullable=False)
    status = Column(String, default="pending") # pending, processing, completed
    translated_text = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())