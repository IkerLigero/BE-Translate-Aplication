from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.translation import Translation
from app.schemas.translation import TranslationCreate, TranslationResponse

router = APIRouter()

@router.post("/", response_model=TranslationResponse)
def create_translation(payload: TranslationCreate, db: Session = Depends(get_db)):
    # Mapping the names from the Schema (payload) to the names in the Model (DB)
    db_translation = Translation(
        original_text=payload.text_to_translate,  # ← Mapping
        source_lang=payload.source_lang,
        target_language=payload.target_lang,      # ← Mapping
        status="completed", # For now, we mark it as completed for testing
        translated_text=f"Simulated translation of: {payload.text_to_translate}"
    )
    
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    
    # FastAPI is smart and will map back to TranslationResponse automatically
    # But we need to ensure that TranslationResponse understands the DB names or vice versa.
    return {
        "id": db_translation.id,
        "text_to_translate": db_translation.original_text,
        "translated_text": db_translation.translated_text,
        "source_lang": db_translation.source_lang,
        "target_lang": db_translation.target_language,
        "created_at": db_translation.created_at
    }