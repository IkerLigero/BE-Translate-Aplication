from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# What we receive from the Frontend (without ID and date)
class TranslationCreate(BaseModel):
    text_to_translate: str
    source_lang: str
    target_lang: str

# What we return to the Frontend (with ID and date)
class TranslationResponse(BaseModel):
    id: int
    text_to_translate: str
    translated_text: Optional[str]
    source_lang: str
    target_lang: str
    created_at: datetime

    class Config:
        from_attributes = True