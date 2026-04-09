from sqlalchemy.ext.asyncio import AsyncSession # Cambiado de Session
from app.models.translation import Translation
from app.worker.tasks import process_pdf_task
from zoneinfo import ZoneInfo
from sqlalchemy import select

class TranslationService:
    @staticmethod
    def get_pdf_data_dict(translation: Translation) -> dict:
        """Mantiene la lógica de formato de datos para el Worker"""
        return {
            "id": str(translation.id),
            "source_lang": translation.source_lang,
            "pdf_lang": translation.pdf_lang,
            "target_lang": translation.target_language,
            "original_text": translation.original_text,
            "translated_text": translation.translated_text,
            # Asegúrate de que created_at no sea None antes de llamar a astimezone
            "date": translation.created_at.astimezone(ZoneInfo("Europe/Madrid")).strftime("%Y-%m-%d %H:%M:%S") if translation.created_at else ""
        }

    @staticmethod
    async def create_translation_process(db: AsyncSession, payload) -> Translation:
        """Lógica asíncrona para crear en DB y lanzar Worker"""
        # 1. Crear la entrada en la DB
        db_translation = Translation(
            original_text=payload.text_to_translate,
            source_lang=payload.source_lang,
            pdf_lang=payload.pdf_lang,
            target_language=payload.target_lang,
            status="pending"
        )
        
        db.add(db_translation)
        # En AsyncSession, commit y refresh DEBEN ser await
        await db.commit()
        await db.refresh(db_translation)
        
        # 2. Preparar datos para el worker
        pdf_data = TranslationService.get_pdf_data_dict(db_translation)
        
        # 3. Lanzar Celery (esto sigue siendo .delay(), no necesita await)
        process_pdf_task.delay(db_translation.id, pdf_data)
        
        return db_translation

    @staticmethod
    async def trigger_regeneration(db: AsyncSession, translation: Translation):
        """Lógica asíncrona para forzar regeneración"""
        pdf_data = TranslationService.get_pdf_data_dict(translation)
        process_pdf_task.delay(translation.id, pdf_data)