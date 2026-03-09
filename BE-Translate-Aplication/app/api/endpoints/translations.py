from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.translation import Translation
from app.schemas.translation import TranslationCreate, TranslationResponse
from typing import List

router = APIRouter()

@router.post("/", response_model=TranslationResponse)
def create_translation(payload: TranslationCreate, db: Session = Depends(get_db)):
    db_translation = Translation(
        original_text=payload.text_to_translate,
        source_lang=payload.source_lang,
        target_language=payload.target_lang,
        status="pending",
        translated_text=None
    )
    
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    
    
    return {
        "id": db_translation.id,
        "text_to_translate": db_translation.original_text,
        "translated_text": db_translation.translated_text,
        "source_lang": db_translation.source_lang,
        "target_lang": db_translation.target_language,
        "status": db_translation.status,
        "created_at": db_translation.created_at
    }
    
    

@router.get("/", response_model=List[TranslationResponse])
def list_translations(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):

    # 1. Consulting the DB for translations with pagination
    translations = db.query(Translation).offset(skip).limit(limit).all()
    
    # 2. Mapping the results to the format expected by TranslationResponse
    # Since the column names in the DB and the Schema are different,
    # we do it manually to avoid errors.
    return [
        {
            "id": t.id,
            "text_to_translate": t.original_text,
            "translated_text": t.translated_text,
            "source_lang": t.source_lang,
            "target_lang": t.target_language,
            "created_at": t.created_at,
            "status": t.status
        }
        for t in translations
    ]