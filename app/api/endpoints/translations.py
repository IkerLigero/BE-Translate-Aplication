import asyncio
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from datetime import timedelta
from app.core.storage import s3_client
import os

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

    if translation.file_path:
        try:
            # 2. Usamos s3_client de boto3 para generar la URL firmada
            bucket = os.getenv("MINIO_BUCKET_NAME", "translations")
            url = s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': bucket,
                    'Key': translation.file_path
                },
                ExpiresIn=900 # 15 minutos (900 segundos)
            )
            # 3. Devolvemos el JSON con la URL como te pidió el jefe
            return {"download_url": url}
            
        except Exception as e:
            # Si algo falla con S3, logeamos y lanzamos error
            print(f"Error generando URL: {e}")
            raise HTTPException(status_code=500, detail="Could not generate download link")

    # Si sigue procesando
    if translation.status == "pending":
        raise HTTPException(status_code=202, detail="Still processing...")

    # Si el archivo no está pero debería, regeneramos
    await TranslationService.trigger_regeneration(db, translation)
    raise HTTPException(status_code=202, detail="PDF was missing. Regeneration started.")