import asyncio
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.db.session import get_async_db
from app.models.translation import Translation
from app.schemas.translation import TranslationCreate, TranslationResponse
from app.core.storage import get_pdf_from_minio 
from app.services.translation_service import TranslationService

router = APIRouter()

# 1. GET /translations: List all translations
@router.get("", response_model=List[TranslationResponse])
async def get_translations(db: AsyncSession = Depends(get_async_db)):
    """
    List all translations in the database, ordered by creation date (newest first).
    """
    result = await db.execute(
        select(Translation).order_by(Translation.created_at.desc())
    )
    translations = result.scalars().all()
    return translations


# 2. POST /translations: Create a new translation
@router.post("", response_model=TranslationResponse)
async def create(payload: TranslationCreate, db: AsyncSession = Depends(get_async_db)):
    """
    Create a new translation entry in the database and start the translation process.
    """
    return await TranslationService.create_translation_process(db, payload)


# 3. POST /translations/{id}/generate: Force generation (or regenerate)
@router.post("/{translation_id}/generate")
async def force_generate(translation_id: int, db: AsyncSession = Depends(get_async_db)):
    # Search for the translation in the database
    result = await db.execute(select(Translation).where(Translation.id == translation_id))
    translation = result.scalar_one_or_none()
    
    if not translation:
        raise HTTPException(status_code=404, detail="Translation not found")
    
    # Trigger regeneration (this will handle both pending and completed cases)
    await TranslationService.trigger_regeneration(db, translation)
    return {"status": "accepted", "message": "Regeneration triggered"}


# 4. GET /translations/{id}: Get status / details
@router.get("/{translation_id}", response_model=TranslationResponse)
async def get_status(translation_id: int, db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(Translation).where(Translation.id == translation_id))
    translation = result.scalar_one_or_none()
    
    if not translation:
        raise HTTPException(status_code=404, detail="Translation not found")
    return translation


# 5. GET /translations/{id}/pdf: Download PDF (with cache in MinIO)
@router.get("/{translation_id}/pdf")
async def download_pdf(translation_id: int, db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(Translation).where(Translation.id == translation_id))
    translation = result.scalar_one_or_none()

    if not translation:
        raise HTTPException(status_code=404, detail="Translation not found")

    # Step A: If the PDF is already generated and stored, serve it directly
    if translation.file_path:
        try:
            # Note: If get_pdf_from_minio is blocking, you could wrap it in a thread
            # or use an asynchronous MinIO client.
            pdf_stream = get_pdf_from_minio(translation.file_path)
            return StreamingResponse(pdf_stream, media_type="application/pdf")
        except Exception:
            pass 

    # Step B: If the translation is still pending, notify the frontend
    if translation.status == "pending":
        raise HTTPException(status_code=202, detail="Still processing...")

    # Step C: If the file is missing, trigger regeneration
    await TranslationService.trigger_regeneration(db, translation)
    raise HTTPException(status_code=202, detail="PDF was missing. Regeneration started.")