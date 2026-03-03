from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.translation import Translation
from app.schemas.translation import TranslationCreate, TranslationResponse

router = APIRouter()

@router.post("/", response_model=TranslationResponse)
def create_translation(payload: TranslationCreate, db: Session = Depends(get_db)):
    # Mapeamos los nombres del Schema (payload) a los nombres del Modelo (DB)
    db_translation = Translation(
        original_text=payload.text_to_translate,  # ← Mapeo
        source_lang=payload.source_lang,
        target_language=payload.target_lang,      # ← Mapeo
        status="completed", # Por ahora lo marcamos como completado para la prueba
        translated_text=f"Traducción simulada de: {payload.text_to_translate}"
    )
    
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    
    # FastAPI es inteligente y mapeará de vuelta al TranslationResponse automáticamente
    # Pero debemos asegurarnos que TranslationResponse entienda los nombres de la DB o viceversa.
    return {
        "id": db_translation.id,
        "text_to_translate": db_translation.original_text,
        "translated_text": db_translation.translated_text,
        "source_lang": db_translation.source_lang,
        "target_lang": db_translation.target_language,
        "created_at": db_translation.created_at
    }