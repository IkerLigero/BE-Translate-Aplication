import asyncio
from fastapi import APIRouter, Depends, HTTPException, logger
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from datetime import timedelta
from app.core.storage import s3_client
from app.core.storage import s3_presigned_client
import os

from app.db.session import get_async_db
from app.models.translation import Translation
from app.schemas.translation import TranslationCreate, TranslationResponse
from app.core.storage import get_pdf_from_minio 
from app.services.translation_service import TranslationService

from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()


# 1. GET /translations: List all translations
@router.get("", response_model=List[TranslationResponse])
async def get_translations(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user) # Lo mantenemos porque usamos su ID
    ):
    # List only translations that belong to the current user, ordered by creation date
    result = await db.execute(
        select(Translation)
        .where(Translation.user_id == current_user.id)
        .order_by(Translation.created_at.desc())
    )
    return result.scalars().all()


# 2. POST /translations: Create a new translation
@router.post("", response_model=TranslationResponse)
# Now this endpoint also requires the current user, so we can link the translation to them
async def create(
    payload: TranslationCreate, 
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user) # Security added to link translation to user
    ):
    # Calls the function that creates the translation and starts the background process, passing the current user's ID
    return await TranslationService.create_translation_process(db, payload, current_user)


# 3. POST /translations/{id}/generate: Force generation (only owner)
@router.post("/{translation_id}/generate")
async def force_generate(
    translation_id: int, 
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user) # Security added
    ):
    
    # Search for the translation ensuring it belongs to the user
    result = await db.execute(
        select(Translation)
        .where(Translation.id == translation_id)
        .where(Translation.user_id == current_user.id)
    )
    # If not found, return 404 (either it doesn't exist or doesn't belong to the user)
    translation = result.scalar_one_or_none()
    
    if not translation:
        raise HTTPException(status_code=404, detail="Translation not found or you do not have permission")
    
    # Trigger the regeneration using the service function, which will handle the logic to call the Celery task
    await TranslationService.trigger_regeneration(db, translation)
    return {"status": "accepted", "message": "Regeneration triggered"}


# 4. GET /translations/{id}: Get details (only owner)
@router.get("/{translation_id}", response_model=TranslationResponse)
async def get_status(
    translation_id: int, 
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user) # Security added
):
    result = await db.execute(
        select(Translation)
        .where(Translation.id == translation_id)
        .where(Translation.user_id == current_user.id) # <--- Owner filter
    )
    translation = result.scalar_one_or_none()
    
    if not translation:
        raise HTTPException(status_code=404, detail="Translation not found")
    return translation


# 5. GET /translations/{id}/pdf: Download PDF (only owner)
@router.get("/{translation_id}/pdf")
async def download_pdf(
    translation_id: int, 
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Translation).where(
        Translation.id == translation_id,
        Translation.user_id == current_user.id
    )
    result = await db.execute(query)
    translation = result.scalar_one_or_none()

    # If not found, return 404 (either it doesn't exist or doesn't belong to the user)
    if not translation:
        raise HTTPException(status_code=404, detail="Translation not found")

    try:
        # Attempt to retrieve the file from MinIO
        file_stream = get_pdf_from_minio(translation.file_path)
        return StreamingResponse(
            file_stream,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=translation_{translation_id}.pdf"}
        )
        
    except Exception:
        # IF MINIO FAILS (File manually deleted):
        # 1. Change the status in the DB to 'pending' again
        translation.status = "pending"
        await db.commit()
        
        # 2. Trigger the regeneration (your existing function)
        await TranslationService.trigger_regeneration(db, translation)
        
        # 3. Inform the frontend that regeneration is in progress
        raise HTTPException(
            status_code=202, 
            detail="File was missing in storage. Regeneration triggered automatically. Please wait."
        )