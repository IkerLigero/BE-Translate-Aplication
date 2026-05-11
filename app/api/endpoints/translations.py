import asyncio
from fastapi import APIRouter, Depends, status,HTTPException, logger
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
from app.schemas.translation import TranslationCreate, TranslationResponse, DuplicateRequest
from app.core.storage import get_pdf_from_minio 
from app.services.translation_service import TranslationService

from app.api.deps import get_current_user
from app.models.user import User

from app.core.vectors import search_similar_translations



router = APIRouter()


# 0. GET /translations/search?q=: Search in history with semantic similarity (only owner)   
@router.get("/search", response_model=List[TranslationResponse])
async def search_history(
    q: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search in the user's history using semantic similarity (OpenAI Embeddings).
    Returns the top 5 most relevant documents based on the original text.
    """
    # 1. Validate that the query is not empty
    if not q or not q.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Search query cannot be empty"
        )
        
    # 2. Call the business logic to perform the vector search
    results = await search_similar_translations(
        db=db, 
        user_id=current_user.id,  # Ensure we only search within the current user's translations
        query_text=q,             # The text we want to find similar documents to
        limit=5                   # Limit to top 5 results for relevance and performance
    )
    
    return results


# 1. GET /translations: List all translations
@router.get("", response_model=List[TranslationResponse])
async def get_translations(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
    ):
    # List only translations that belong to the current user, ordered by creation date
    result = await db.execute(
        select(Translation)
        .where(
            Translation.user_id == current_user.id,
            Translation.is_active == True  # Only active translations
        )
        .order_by(Translation.created_at.desc())
    )
    return result.scalars().all()


# 2. POST /translations: Create a new translation
@router.post("", response_model=TranslationResponse)
# Now this endpoint also requires the current user, so we can link the translation to them
async def create(
    payload: TranslationCreate, 
    db: AsyncSession = Depends(get_async_db), # We need the DB session to create the translation record and start the background process
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


# 5. DELETE /translations/{id}: Soft delete (only owner)
@router.delete("/{translation_id}", status_code=status.HTTP_200_OK)
async def delete_translation(
    translation_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Search for the translation ensuring it belongs to the user
    result = await db.execute(
        select(Translation).where(
            Translation.id == translation_id, 
            Translation.user_id == current_user.id
        )
    )
    translation = result.scalar_one_or_none()

    # 2. If not found, return 404 (either it doesn't exist or doesn't belong to the user)
    if not translation:
        raise HTTPException(status_code=404, detail="Translation not found")

    # 3. Soft delete
    translation.is_active = False
    
    # 4. Commit the change to the database
    await db.commit()
    return {"message": "Translation moved to trash"}


# 6. PATCH /translations/{id}/restore: Restore soft-deleted translation (only owner)
@router.patch("/{translation_id}/restore", status_code=status.HTTP_200_OK)
async def restore_translation(
    translation_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Restore a soft-deleted translation by setting is_active back to True.
    """
    # 1. Search for the translation (specifically looking for inactive ones)
    result = await db.execute(
        select(Translation).where(
            Translation.id == translation_id, 
            Translation.user_id == current_user.id,
            Translation.is_active == False  # Safety: only restore what is actually deleted
        )
    )
    translation = result.scalar_one_or_none()

    # 2. If it's not there, it's either active, belongs to someone else, or doesn't exist
    if not translation:
        raise HTTPException(
            status_code=404, 
            detail="Translation not found in trash or already active"
        )

    # 3. Restore
    translation.is_active = True
    
    # 4. Save changes
    await db.commit()
    await db.refresh(translation)

    return {
        "message": "Translation restored successfully",
        "translation_id": translation.id,
        "is_active": translation.is_active
    }


# 7. POST /translations/{id}/duplicate: Duplicate translation (only owner)
@router.post("/{translation_id}/duplicate", response_model=TranslationResponse)
async def duplicate_translation(
    translation_id: int,
    request: DuplicateRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Search for the original translation to clone its data
    result = await db.execute(
        select(Translation).where(
            Translation.id == translation_id, 
            Translation.user_id == current_user.id
        )
    )
    original = result.scalar_one_or_none()

    # If the original translation doesn't exist or doesn't belong to the user, return 404
    if not original:
        raise HTTPException(status_code=404, detail="Original translation not found")

    # 2. Create the new instance (duplicate)
    # Using the new target language from the request while keeping original text and source language
    new_translation = Translation(
        user_id=current_user.id,
        original_text=original.original_text,
        source_lang=original.source_lang,
        target_language=request.new_target_lang, # New language chosen by user
        pdf_lang=original.pdf_lang,
        status="pending", # Reset status for the new process
        is_active=True
    )

    db.add(new_translation)
    await db.flush() # Generate the new ID without closing the transaction
    await db.commit()
    await db.refresh(new_translation)

    # 3. Prepare data and trigger the Celery task
    try:
        # Import the actual task name from your tasks.py
        from app.worker.tasks import process_pdf_task
        
        # Prepare the pdf_data dictionary required by your process_pdf_task
        pdf_data = {
            "user_id": current_user.id,
            "original_text": original.original_text,
            "source_lang": original.source_lang,
            "target_lang": request.new_target_lang,
            "pdf_lang": original.pdf_lang
        }
        
        # Send task to Celery with both required arguments: translation_id and pdf_data
        process_pdf_task.delay(new_translation.id, pdf_data)
        
    except ImportError:
        # Fallback in case of absolute import issues in certain environments
        import app.worker.tasks as worker_tasks
        
        pdf_data = {
            "user_id": current_user.id,
            "original_text": original.original_text,
            "source_lang": original.source_lang,
            "target_lang": request.new_target_lang,
            "pdf_lang": original.pdf_lang
        }
        worker_tasks.process_pdf_task.delay(new_translation.id, pdf_data)

    return new_translation


# 8. GET /translations/{id}/pdf: Download PDF (only owner)
@router.get("/{translation_id}/pdf")
async def download_pdf(
    translation_id: int, 
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    # First, we check if the translation exists and belongs to the user. This ensures that only the owner can attempt to download the PDF.
    query = select(Translation).where(
        Translation.id == translation_id,
        Translation.user_id == current_user.id
    )
    # If the translation doesn't exist or doesn't belong to the user, we return a 404 error.
    result = await db.execute(query)
    translation = result.scalar_one_or_none()

    # If not found, return 404 (either it doesn't exist or doesn't belong to the user)
    if not translation:
        raise HTTPException(status_code=404, detail="Translation not found")

    try:
        # Attempt to retrieve the file from MinIO
        file_stream = get_pdf_from_minio(translation.file_path)
        # If the file is successfully retrieved, we return it as a streaming response with the appropriate headers for downloading.
        return StreamingResponse(
            file_stream,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=translation_{translation_id}.pdf"}
        )
        
    except Exception:
        # IF MINIO FAILS (File manually deleted or corrupted):
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
        
