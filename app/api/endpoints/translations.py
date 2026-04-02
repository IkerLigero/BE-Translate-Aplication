import asyncio
import time
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.db.session import get_db, get_async_db
from app.models.translation import Translation
from app.schemas.translation import TranslationCreate, TranslationResponse
from app.core.storage import get_pdf_from_minio 
from app.services.translation_service import TranslationService

router = APIRouter()

"""
Endpoints for managing translations.
1. GET /translations: List all translations (with pagination and filters later)
2. POST /translations: Create a new translation
3. POST /translations/{id}/generate: Force generation (or regenerate)
4. GET /translations/{id}: Get status and details
5. GET /translations/{id}/pdf: Download PDF (with cache in MinIO)
"""

# ---------------------------------------------------- TEST AREA ---------------------------------------------------------------------

# --- VERSION SÍNCRONA (La "lenta" bajo carga) ---
# --- HISTORIAL (Quitamos la barra para probar) ---
@router.get("", response_model=List[TranslationResponse]) # <--- Prueba dejándolo vacío o solo ""
async def get_translations(db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(Translation).order_by(Translation.created_at.desc()))
    translations = result.scalars().all()
    return translations

# --- TEST SÍNCRONO ---
@router.get("/sync-list", response_model=List[TranslationResponse])
def get_translations_sync(db: Session = Depends(get_db)):
    time.sleep(1) 
    translations = db.query(Translation).order_by(Translation.created_at.desc()).all()
    return translations

# --- TEST ASÍNCRONO (Añadido aparte para Locust) ---
@router.get("/async-list", response_model=List[TranslationResponse])
async def get_translations_async(db: AsyncSession = Depends(get_async_db)):
    await asyncio.sleep(1) 
    result = await db.execute(select(Translation).order_by(Translation.created_at.desc()))
    translations = result.scalars().all()
    return translations 

# ---------------------------------------------------- TEST AREA ---------------------------------------------------------------------



# 2. Create a new translation
@router.post("", response_model=TranslationResponse)
# Calls the service method in "services/translation_service.py" that creates the DB entry and launches the Worker.
def create(payload: TranslationCreate, db: Session = Depends(get_db)):
    return TranslationService.create_translation_process(db, payload)


# 3. Force generation (or regenerate)
@router.post("/{translation_id}/generate")
def force_generate(translation_id: int, db: Session = Depends(get_db)):
    # First, we check if the translation exists. If not, we return a 404 error.
    translation = db.query(Translation).filter(Translation.id == translation_id).first()
    if not translation:
        raise HTTPException(status_code=404, detail="Translation not found")
    # If it exists, we call the service method that triggers the regeneration (or generation) of the PDF.
    TranslationService.trigger_regeneration(db, translation)
    return {"status": "accepted", "message": "Regeneration triggered"}


# 4. Get status / details
@router.get("/{translation_id}", response_model=TranslationResponse)
def get_status(translation_id: int, db: Session = Depends(get_db)):
    translation = db.query(Translation).filter(Translation.id == translation_id).first()
    if not translation:
        raise HTTPException(status_code=404, detail="Translation not found")
    return translation


# 5. Download PDF (with cache in MinIO)
@router.get("/{translation_id}/pdf")
def download_pdf(translation_id: int, db: Session = Depends(get_db)):
    translation = db.query(Translation).filter(Translation.id == translation_id).first()
    #Look at the translation in the DB. If it doesn't exist, return 404.
    if not translation:
        raise HTTPException(status_code=404, detail="Translation not found")

    # Step A: If it already exists in MinIO, serve it instantly
    if translation.file_path:
        try:
            pdf_stream = get_pdf_from_minio(translation.file_path) # Search in MinIO using the file path stored in the DB. This returns a stream.
            return StreamingResponse(pdf_stream, media_type="application/pdf")
        except Exception:
            pass # If MinIO fails, try to regenerate below

    # Step B: If it's pending, let the frontend wait
    if translation.status == "pending":
        raise HTTPException(status_code=202, detail="Still processing...")

    # Step C: Fallback (If it's missing or deleted, re-launch the worker)
    TranslationService.trigger_regeneration(db, translation)
    raise HTTPException(status_code=202, detail="PDF was missing. Regeneration started.")