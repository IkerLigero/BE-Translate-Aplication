import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import Column, Integer, String, DateTime, Text
from app.db.base_class import Base

class Translation(Base):
    __tablename__ = "translations"

    id = Column(Integer, primary_key=True, index=True)
    original_text = Column(Text, nullable=False)
    target_language = Column(String, nullable=False)
    source_lang = Column(String, nullable=False)
    status = Column(String, default="pending")
    translated_text = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )