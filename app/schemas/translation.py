from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

# What we receive from the Frontend
class TranslationCreate(BaseModel):
    text_to_translate: str = Field(..., min_length=1, description="The text to translate")
    pdf_lang: str = Field(..., min_length=2, max_length=2, description="Code of the PDF language")
    target_lang: str = Field(..., min_length=2, max_length=2, description="Code of the target language")
    source_lang: str = Field(..., min_length=2, max_length=2, description="Code of the source language")

# ... -> obligatory field
# description -> for documentation purposes in Swagger -> UI http://localhost:8000/docs

# What we return to the Frontend
class TranslationResponse(BaseModel):
    id: int
    user_id: int
    original_text: str 
    translated_text: Optional[str] = None
    source_lang: str
    pdf_lang: str
    target_language: str = Field(alias="target_language") 
    status: str
    created_at: datetime 
    file_path: Optional[str] = None

    class Config:
        from_attributes = True
        populate_by_name = True