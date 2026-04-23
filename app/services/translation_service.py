from sqlalchemy.ext.asyncio import AsyncSession
from app.models.translation import Translation
from app.models.user import User
from app.worker.tasks import process_pdf_task
from zoneinfo import ZoneInfo


class TranslationService:
    @staticmethod
    # This function prepares a dictionary with all the necessary data to generate the PDF, which will be sent to the Celery task.
    def get_pdf_data_dict(translation: Translation) -> dict:
        return {
            "id": str(translation.id),
            "user_id": translation.user_id, # User ID for reference
            "source_lang": translation.source_lang,
            "user_email": translation.owner.email if translation.owner else "N/A",
            "pdf_lang": translation.pdf_lang,
            "target_lang": translation.target_language,
            "original_text": translation.original_text,
            "translated_text": translation.translated_text,
            "date": translation.created_at.astimezone(ZoneInfo("Europe/Brussels")).strftime("%Y-%m-%d %H:%M:%S") if translation.created_at else ""
        }

    # This function creates a new translation record in the database, starts the PDF generation process asynchronously, and returns the created translation.
    @staticmethod
    async def create_translation_process(db: AsyncSession, payload, current_user: User) -> Translation:
        db_translation = Translation(
            original_text=payload.text_to_translate,
            source_lang=payload.source_lang,
            pdf_lang=payload.pdf_lang,
            target_language=payload.target_lang,
            user_id=current_user.id,
            status="pending"
        )
        
        db.add(db_translation)
        await db.commit()
        await db.refresh(db_translation)
        
        pdf_data = TranslationService.get_pdf_data_dict(db_translation)
        # Call the Celery task to process the PDF in the background, passing the translation ID and the prepared data dictionary.
        process_pdf_task.delay(db_translation.id, pdf_data)
        
        return db_translation
    
    
    @staticmethod
    # This function can be called to force the regeneration of the PDF for a given translation, and it will also ensure that only the owner can trigger this action.
    async def trigger_regeneration(db: AsyncSession, translation: Translation):
        """Asynchronous logic to force regeneration"""
        pdf_data = TranslationService.get_pdf_data_dict(translation)
        process_pdf_task.delay(translation.id, pdf_data)