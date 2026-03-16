import io
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import timedelta

from app.db.session import get_db
from app.models.translation import Translation
from app.schemas.translation import TranslationCreate, TranslationResponse
from app.services.pdf_service import generate_translation_pdf_bytes

from app.worker.tasks import process_pdf_task

router = APIRouter()

# 1. CREATE TRANSLATION (POST)
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

# 2. LAUNCH ASYNCHRONOUS TASK (POST)
@router.post("/{translation_id}/generate")
def start_pdf_process(translation_id: int, db: Session = Depends(get_db)):
    """
    Send the PDF generation task to Celery. This will run in the background and won't block the API response.
    """
    translation = db.query(Translation).filter(Translation.id == translation_id).first()
    
    if not translation:
        raise HTTPException(status_code=404, detail="Translation not found")

    # Prepare the data for Typst
    local_date = translation.created_at
    pdf_data = {
        "id": str(translation.id),
        "source_lang": translation.source_lang,
        "target_lang": translation.target_language,
        "original_text": translation.original_text,
        "translated_text": translation.translated_text,
        "date": local_date.strftime("%d/%m/%Y %H:%M") 
    }
    
    # .delay() envía el encargo a Redis. El worker lo recogerá.
    process_pdf_task.delay(translation_id, pdf_data)
    
    return {
        "status": "accepted", 
        "translation_id": translation_id,
        "message": "Generating PDF in the background. The worker will update the status upon completion."
    }

# 3. CHECK STATUS/DETAILS (GET)
@router.get("/{translation_id}", response_model=TranslationResponse)
def get_translation(translation_id: int, db: Session = Depends(get_db)):
    """
    Allows checking if the status is already 'completed' after the Celery task has run.
    """
    translation = db.query(Translation).filter(Translation.id == translation_id).first()
    
    if not translation:
        raise HTTPException(status_code=404, detail="Translation not found")
    
    return {
        "id": translation.id,
        "text_to_translate": translation.original_text,
        "translated_text": translation.translated_text,
        "source_lang": translation.source_lang,
        "target_lang": translation.target_language,
        "status": translation.status,
        "created_at": translation.created_at
    }

# 4. DOWNLOAD PDF (GET - SYNCHRONOUS)
@router.get("/{translation_id}/pdf")
def get_pdf(translation_id: int, db: Session = Depends(get_db)):
    """
    Generates and downloads the PDF immediately (blocking).
    """
    translation = db.query(Translation).filter(Translation.id == translation_id).first()
    
    if not translation:
        raise HTTPException(status_code=404, detail="Not found")

    local_date = translation.created_at

    pdf_data = {
        "id": str(translation.id),
        "source_lang": translation.source_lang,
        "target_lang": translation.target_language,
        "original_text": translation.original_text,
        "translated_text": translation.translated_text,
        "date": local_date.strftime("%d/%m/%Y %H:%M") 
    }

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
        raise HTTPException(status_code=500, detail=f"Error generating PDF: {str(e)}")
    

@router.get("/", response_model=list[TranslationResponse])
def get_all_translations(db: Session = Depends(get_db)):
    """
    Obtiene todas las traducciones y mapea los campos manualmente 
    para evitar errores de validación (500 Internal Server Error).
    """
    db_translations = db.query(Translation).order_by(Translation.created_at.desc()).all()
    
    # Mapeamos manualmente cada objeto de la DB al formato del Schema
    results = []
    for t in db_translations:
        results.append({
            "id": t.id,
            "text_to_translate": t.original_text,    # Mapeo: original_text -> text_to_translate
            "translated_text": t.translated_text,
            "source_lang": t.source_lang,
            "target_lang": t.target_language,        # Mapeo: target_language -> target_lang
            "status": t.status,
            "created_at": t.created_at
        })
    
    return results