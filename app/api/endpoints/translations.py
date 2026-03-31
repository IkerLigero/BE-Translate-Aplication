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
            "pdf_lang": t.pdf_lang,
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
        pdf_lang=payload.pdf_lang,
        target_language=payload.target_lang,
        status="pending"
    )
    
    db.add(db_translation)
    db.commit() 
    db.refresh(db_translation)
    
    pdf_data = {
        "id": str(db_translation.id),
        "source_lang": db_translation.source_lang,
        "pdf_lang": db_translation.pdf_lang,
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
        "pdf_lang": db_translation.pdf_lang,
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
        "pdf_lang": translation.pdf_lang,
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
        "pdf_lang": translation.pdf_lang,
        "target_lang": translation.target_language,
        "status": translation.status,
        "created_at": translation.created_at
    }


# 5. DOWNLOAD PDF (GET) - Fetch the existing PDF from MinIO storage
@router.get("/{translation_id}/pdf")
def get_pdf(translation_id: int, db: Session = Depends(get_db)):
    translation = db.query(Translation).filter(Translation.id == translation_id).first()
    
    if not translation:
        raise HTTPException(status_code=404, detail="Translation not found")

    # 1. INTENTO DE LECTURA DIRECTA: Si tenemos un path, probamos MinIO primero
    if translation.file_path:
        try:
            pdf_stream = get_pdf_from_minio(translation.file_path)
            return StreamingResponse(
                pdf_stream,
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename=Report_{translation_id}.pdf"}
            )
        except Exception as e:
            # Si el archivo debería estar pero MinIO falla (borrado accidental, etc.)
            print(f"File marked in DB but missing in MinIO: {e}")
            # Continuamos hacia abajo para regenerarlo

    # 2. VERIFICACIÓN DE ESTADO: Si está pendiente, que el front espere
    if translation.status == "pending":
        raise HTTPException(
            status_code=202, 
            detail="PDF is still being cooked. Please wait a few seconds."
        )

    # 3. DISPARO DEL GENERADOR (FALLBACK): Si llegamos aquí es porque no hay PDF
    # Preparamos los datos para el Worker
    pdf_data = {
        "id": str(translation.id),
        "source_lang": translation.source_lang,
        "pdf_lang": translation.pdf_lang,
        "target_lang": translation.target_language,
        "original_text": translation.original_text,
        "translated_text": translation.translated_text, # Reutilizamos la traducción si ya existe
        "date": translation.created_at.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Lanzamos la tarea de nuevo
    process_pdf_task.delay(translation.id, pdf_data)
    
    raise HTTPException(
        status_code=202, 
        detail="PDF was missing. Regeneration task has been triggered. Try again in 5 seconds."
    )