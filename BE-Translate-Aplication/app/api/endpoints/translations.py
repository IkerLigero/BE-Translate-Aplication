import io
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.translation import Translation
from app.schemas.translation import TranslationCreate, TranslationResponse
from app.services.pdf_service import generate_translation_pdf_bytes

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

@router.get("/{translation_id}/pdf")
def get_pdf(translation_id: int, db: Session = Depends(get_db)):
    # 1. Buscar en DB
    translation = db.query(Translation).filter(Translation.id == translation_id).first()
    
    if not translation:
        raise HTTPException(status_code=404, detail="No encontrado")

    # 2. Formatear datos
    pdf_data = {
        "id": str(translation.id),
        "source_lang": translation.source_lang,
        "target_lang": translation.target_language,
        "original_text": translation.original_text,
        "translated_text": translation.translated_text,
        "date": translation.created_at.strftime("%d/%m/%Y %H:%M")
    }

    # 3. Generar y enviar el PDF sin tocar el disco duro
    try:
        pdf_content = generate_translation_pdf_bytes(pdf_data)
        
        return StreamingResponse(
            io.BytesIO(pdf_content),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=TMS_Report_{translation_id}.pdf"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en generación: {str(e)}")