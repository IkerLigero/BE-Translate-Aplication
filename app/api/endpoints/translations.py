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

from app.api.deps import get_current_user # Importamos la dependencia
from app.models.user import User

router = APIRouter()

# 1. GET /translations: List all translations
@router.get("", response_model=List[TranslationResponse])
async def get_translations(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user) # Inyectamos seguridad
):
    result = await db.execute(
        select(Translation)
        .where(Translation.user_id == current_user.id) # <--- Filtro de privacidad
        .order_by(Translation.created_at.desc())
    )
    return result.scalars().all()


# 2. POST /translations: Create a new translation
@router.post("", response_model=TranslationResponse)
async def create(
    payload: TranslationCreate, 
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user) # Inyectamos seguridad
):
    return await TranslationService.create_translation_process(db, payload, current_user)

# 3. POST /translations/{id}/generate: Forzar generación (solo dueño)
@router.post("/{translation_id}/generate")
async def force_generate(
    translation_id: int, 
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user) # Seguridad añadida
):
    # Buscamos la traducción verificando que pertenezca al usuario
    result = await db.execute(
        select(Translation)
        .where(Translation.id == translation_id)
        .where(Translation.user_id == current_user.id) # <--- Filtro de dueño
    )
    translation = result.scalar_one_or_none()
    
    if not translation:
        raise HTTPException(status_code=404, detail="Traducción no encontrada o no tiene permisos")
    
    await TranslationService.trigger_regeneration(db, translation)
    return {"status": "accepted", "message": "Regeneration triggered"}


# 4. GET /translations/{id}: Obtener detalles (solo dueño)
@router.get("/{translation_id}", response_model=TranslationResponse)
async def get_status(
    translation_id: int, 
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user) # Seguridad añadida
):
    result = await db.execute(
        select(Translation)
        .where(Translation.id == translation_id)
        .where(Translation.user_id == current_user.id) # <--- Filtro de dueño
    )
    translation = result.scalar_one_or_none()
    
    if not translation:
        raise HTTPException(status_code=404, detail="Traducción no encontrada")
    return translation


# 5. GET /translations/{id}/pdf: Descargar PDF (solo dueño)
@router.get("/{translation_id}/pdf")
async def download_pdf(
    translation_id: int, 
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user) # Seguridad añadida
):
    # Verificamos que la traducción existe Y es del usuario
    result = await db.execute(
        select(Translation)
        .where(Translation.id == translation_id)
        .where(Translation.user_id == current_user.id) # <--- Filtro de dueño
    )
    translation = result.scalar_one_or_none()

    if not translation:
        raise HTTPException(status_code=404, detail="Archivo no encontrado o acceso denegado")

    if translation.file_path:
        try:
            bucket = os.getenv("MINIO_BUCKET_NAME", "translations")
            url = s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': bucket,
                    'Key': translation.file_path # Ya incluirá el prefijo user_X/
                },
                ExpiresIn=900 
            )
            return {"download_url": url}
            
        except Exception as e:
            print(f"Error generando URL: {e}")
            raise HTTPException(status_code=500, detail="Could not generate download link")

    # Si sigue procesando
    if translation.status == "pending":
        raise HTTPException(status_code=202, detail="Still processing...")

    # Si el archivo falta por alguna razón, regeneramos (manteniendo el contexto del usuario)
    await TranslationService.trigger_regeneration(db, translation)
    raise HTTPException(status_code=202, detail="PDF was missing. Regeneration started.")