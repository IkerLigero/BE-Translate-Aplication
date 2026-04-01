from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.translation import Translation
from app.schemas.translation import TranslationCreate, TranslationResponse
from app.core.storage import get_pdf_from_minio 
from app.services.translation_service import TranslationService

router = APIRouter()

# 1. LISTAR TODO
@router.get("", response_model=list[TranslationResponse])
def get_all(db: Session = Depends(get_db)):
    return db.query(Translation).order_by(Translation.created_at.desc()).all()

# 2. CREAR TRADUCCIÓN
@router.post("", response_model=TranslationResponse)
def create(payload: TranslationCreate, db: Session = Depends(get_db)):
    return TranslationService.create_translation_process(db, payload)

# 3. FORZAR GENERACIÓN (O REGENERAR)
@router.post("/{translation_id}/generate")
def force_generate(translation_id: int, db: Session = Depends(get_db)):
    translation = db.query(Translation).filter(Translation.id == translation_id).first()
    if not translation:
        raise HTTPException(status_code=404, detail="Translation not found")
    
    TranslationService.trigger_regeneration(db, translation)
    return {"status": "accepted", "message": "Regeneration triggered"}

# 4. VER ESTADO / DETALLE
@router.get("/{translation_id}", response_model=TranslationResponse)
def get_status(translation_id: int, db: Session = Depends(get_db)):
    translation = db.query(Translation).filter(Translation.id == translation_id).first()
    if not translation:
        raise HTTPException(status_code=404, detail="Translation not found")
    return translation

# 5. DESCARGAR PDF (CON CACHÉ EN MINIO)
@router.get("/{translation_id}/pdf")
def download_pdf(translation_id: int, db: Session = Depends(get_db)):
    translation = db.query(Translation).filter(Translation.id == translation_id).first()
    if not translation:
        raise HTTPException(status_code=404, detail="Translation not found")

    # Paso A: Si ya existe en MinIO, se sirve al instante
    if translation.file_path:
        try:
            pdf_stream = get_pdf_from_minio(translation.file_path)
            return StreamingResponse(pdf_stream, media_type="application/pdf")
        except Exception:
            pass # Si falla MinIO, intentamos regenerar abajo

    # Paso B: Si está pendiente, que el front espere
    if translation.status == "pending":
        raise HTTPException(status_code=202, detail="Still processing...")

    # Paso C: Fallback (Si no está o se borró, re-lanzamos el worker)
    TranslationService.trigger_regeneration(db, translation)
    raise HTTPException(status_code=202, detail="PDF was missing. Regeneration started.")