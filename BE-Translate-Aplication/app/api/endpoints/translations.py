import io
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import timedelta
from zoneinfo import ZoneInfo
from app.db.session import get_db
from app.models.translation import Translation
from app.schemas.translation import TranslationCreate, TranslationResponse
from app.services.pdf_service import generate_translation_pdf_bytes
from app.worker.tasks import process_pdf_task

# Initialize router
router = APIRouter()

# 1. GET ALL (List) - Return all translations 
@router.get("", response_model=list[TranslationResponse])
def get_all_translations(db: Session = Depends(get_db)):
    """
    Fetch all translations and map fields to match the Schema (avoids 500 error).
    """
    db_translations = db.query(Translation).order_by(Translation.created_at.desc()).all()
    
    results = []
    for t in db_translations:
        results.append({
            "id": t.id,
            "text_to_translate": t.original_text,
            "translated_text": t.translated_text,
            "source_lang": t.source_lang,
            "target_lang": t.target_language,
            "status": t.status,
            "created_at": t.created_at
        })
    return results

# 2. CREATE (POST) - Recive translation request and store in DB with status "pending"
@router.post("", response_model=TranslationResponse)
def create_translation(payload: TranslationCreate, db: Session = Depends(get_db)):
    # 1. Crear el registro en la DB
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
    
    # 2. PREPARAR DATOS PARA EL PDF (Igual que lo tienes en el endpoint /generate)
    pdf_data = {
        "id": str(db_translation.id),
        "source_lang": db_translation.source_lang,
        "target_lang": db_translation.target_language,
        "original_text": db_translation.original_text,
        "translated_text": None, # El worker lo llenará
        "date": db_translation.created_at.strftime("%Y-%m-%d %H:%M:%S")
    }

    # 3. ¡AQUÍ ESTÁ EL TRUCO! Llamamos al worker automáticamente
    process_pdf_task.delay(db_translation.id, pdf_data) 
    
    # 4. Devolvemos la respuesta al Front
    return {
        "id": db_translation.id,
        "text_to_translate": db_translation.original_text,
        "translated_text": db_translation.translated_text,
        "source_lang": db_translation.source_lang,
        "target_lang": db_translation.target_language,
        "status": db_translation.status,
        "created_at": db_translation.created_at
    }

    # 3. DISPARAMOS EL WORKER AQUÍ MISMO
    process_pdf_task.delay(db_translation.id, pdf_data) 

    return {
        "id": db_translation.id,
        "text_to_translate": db_translation.original_text,
        "translated_text": None,
        "source_lang": db_translation.source_lang,
        "target_lang": db_translation.target_language,
        "status": "pending",
        "created_at": db_translation.created_at
    }

# 3. LAUNCH ASYNCHRONOUS TASK (POST), told worker to generate PDF in background.
@router.post("/{translation_id}/generate")
def start_pdf_process(translation_id: int, db: Session = Depends(get_db)):
    translation = db.query(Translation).filter(Translation.id == translation_id).first()
    
    if not translation:
        raise HTTPException(status_code=404, detail="Translation not found")

    pdf_data = {
        "id": str(translation.id),
        "source_lang": translation.source_lang,
        "target_lang": translation.target_language,
        "original_text": translation.original_text,
        "translated_text": translation.translated_text,
        "date": translation.created_at.astimezone(ZoneInfo("Europe/Brussels")).strftime("%Y-%m-%d %H:%M:%S")
    }
    
    process_pdf_task.delay(translation_id, pdf_data) #delay() is the Celery method to launch the task asynchronously in the background.
    
    return {
        "status": "accepted", 
        "translation_id": translation_id,
        "message": "Generating PDF in the background."
    }

# 4. CHECK STATUS (GET) - Retrieve the status of a specific translation
@router.get("/{translation_id}", response_model=TranslationResponse)
def get_translation(translation_id: int, db: Session = Depends(get_db)):
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

# 5. DOWNLOAD PDF (GET)
@router.get("/{translation_id}/pdf")
def get_pdf(translation_id: int, db: Session = Depends(get_db)):
    translation = db.query(Translation).filter(Translation.id == translation_id).first()
    
    if not translation:
        raise HTTPException(status_code=404, detail="Translation not found")

    # Si el estado es error, no intentamos generar el PDF, avisamos al Front
    if translation.status == "error":
        raise HTTPException(
            status_code=400, 
            detail="Cannot generate PDF: The translation failed due to text length or API limits."
        )

    # Si está pendiente, también avisamos para que no descargue algo vacío
    if translation.status == "pending":
        raise HTTPException(
            status_code=202, 
            detail="Translation is still in progress. Please try again in a few seconds."
        )

    # Si está 'completed', procedemos normal
    pdf_data = {
        "id": str(translation.id),
        "source_lang": translation.source_lang,
        "target_lang": translation.target_language,
        "original_text": translation.original_text,
        "translated_text": translation.translated_text,
        "date": translation.created_at.strftime("%Y-%m-%d %H:%M:%S")
    }

    try:
        pdf_content = generate_translation_pdf_bytes(pdf_data)
        return StreamingResponse(
            io.BytesIO(pdf_content),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=Report_{translation_id}.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error generating PDF file.")