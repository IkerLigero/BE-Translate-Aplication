import io
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import timedelta
from zoneinfo import ZoneInfo
from app.db.session import get_db
from app.models.translation import Translation
from app.schemas.translation import TranslationCreate, TranslationResponse
# New: storage utility to fetch files from MinIO
from app.core.storage import get_pdf_from_minio 
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

# 2. CREATE (POST) - Receive translation, store in DB, and trigger the worker.
@router.post("", response_model=TranslationResponse)
def create_translation(payload: TranslationCreate, db: Session = Depends(get_db)):
    """
    Initializes a translation record in the database and dispatches 
    the asynchronous processing task to the Celery worker.
    """
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
    
    pdf_data = {
        "id": str(db_translation.id),
        "source_lang": db_translation.source_lang,
        "target_lang": db_translation.target_language,
        "original_text": db_translation.original_text,
        "translated_text": None, 
        "date": db_translation.created_at.strftime("%Y-%m-%d %H:%M:%S")
    }

    process_pdf_task.delay(db_translation.id, pdf_data) 
    
    return {
        "id": db_translation.id,
        "text_to_translate": db_translation.original_text,
        "translated_text": db_translation.translated_text,
        "source_lang": db_translation.source_lang,
        "target_lang": db_translation.target_language,
        "status": db_translation.status,
        "created_at": db_translation.created_at
    }


# 3. LAUNCH ASYNCHRONOUS TASK (POST) - Force PDF generation for an existing record
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
    
    process_pdf_task.delay(translation_id, pdf_data)
    
    return {
        "status": "accepted", 
        "translation_id": translation_id,
        "message": "Generating/Updating PDF in the background."
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


# 5. DOWNLOAD PDF (GET) - Fetch the existing PDF from MinIO storage
@router.get("/{translation_id}/pdf")
def get_pdf(translation_id: int, db: Session = Depends(get_db)):
    """
    Retrieves the pre-generated PDF from MinIO storage instead of generating it on the fly.
    """
    translation = db.query(Translation).filter(Translation.id == translation_id).first()
    
    if not translation:
        raise HTTPException(status_code=404, detail="Translation not found")

    if translation.status == "error":
        raise HTTPException(
            status_code=400, 
            detail="Cannot download PDF: The translation process failed."
        )

    if translation.status == "pending" or not translation.file_path:
        raise HTTPException(
            status_code=202, 
            detail="File not ready. Translation or PDF generation is still in progress."
        )

    try:
        # Fetch the file stream directly from MinIO using the stored file_path
        pdf_stream = get_pdf_from_minio(translation.file_path)

        # Return the file stream to the client
        return StreamingResponse(
            pdf_stream,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=Report_{translation_id}.pdf"}
        )
    except Exception as e:
        # If MinIO fails to find the object or connection is lost
        print(f"Storage Error: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving PDF from storage.")