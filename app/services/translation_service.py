from sqlalchemy.ext.asyncio import AsyncSession
from app.models.translation import Translation
from app.models.user import User # Importamos el modelo User
from app.worker.tasks import process_pdf_task
from zoneinfo import ZoneInfo

class TranslationService:
    @staticmethod
    def get_pdf_data_dict(translation: Translation) -> dict:
        return {
            "id": str(translation.id),
            "user_id": translation.user_id, # Añadimos el user_id para el worker
            "source_lang": translation.source_lang,
            "pdf_lang": translation.pdf_lang,
            "target_lang": translation.target_language,
            "original_text": translation.original_text,
            "translated_text": translation.translated_text,
            "date": translation.created_at.astimezone(ZoneInfo("Europe/Madrid")).strftime("%Y-%m-%d %H:%M:%S") if translation.created_at else ""
        }

    @staticmethod
    async def create_translation_process(db: AsyncSession, payload, current_user: User) -> Translation:
        """Ahora recibe 'current_user' para vincular la traducción"""
        db_translation = Translation(
            original_text=payload.text_to_translate,
            source_lang=payload.source_lang,
            pdf_lang=payload.pdf_lang,
            target_language=payload.target_lang,
            user_id=current_user.id,  # <--- Vinculación automática
            status="pending"
        )
        
        db.add(db_translation)
        await db.commit()
        await db.refresh(db_translation)
        
        pdf_data = TranslationService.get_pdf_data_dict(db_translation)
        process_pdf_task.delay(db_translation.id, pdf_data)
        
        return db_translation
    
    # ... trigger_regeneration se queda igual pero usará el nuevo dict con user_id
    @staticmethod
    async def trigger_regeneration(db: AsyncSession, translation: Translation):
        """Asynchronous logic to force regeneration"""
        pdf_data = TranslationService.get_pdf_data_dict(translation)
        process_pdf_task.delay(translation.id, pdf_data)