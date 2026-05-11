from sqlalchemy.ext.asyncio import AsyncSession
from app.models.translation import Translation
from app.models.user import User
from app.worker.tasks import process_pdf_task
from zoneinfo import ZoneInfo

class TranslationService:
    
    @staticmethod
    def get_minimal_pdf_data(translation: Translation) -> dict:
        """
        Prepares a minimal dictionary to trigger the background task.
        Security: We only send the IDs. The Worker will fetch text and emails 
        directly from the Database to prevent data tampering in the message queue.
        """
        return {
            "id": str(translation.id),
            "user_id": translation.user_id, # Used by Worker to cross-check ownership
            # We provide the date as context, but other sensitive fields 
            # like 'original_text' are now handled by the Worker via DB lookup.
            "date": translation.created_at.astimezone(ZoneInfo("Europe/Brussels")).strftime("%Y-%m-%d %H:%M:%S") if translation.created_at else ""
        }

    @staticmethod
    async def create_translation_process(db: AsyncSession, payload, current_user: User) -> Translation:
        """
        Creates a new translation record and triggers the asynchronous processing.
        Links the translation to the current authenticated user.
        """
        # 1. Create the database instance with data from the request payload
        db_translation = Translation(
            original_text=payload.text_to_translate,
            source_lang=payload.source_lang,
            pdf_lang=payload.pdf_lang,
            target_language=payload.target_lang,
            user_id=current_user.id,
            status="pending"
        )
        
        # 2. Persist to database
        db.add(db_translation)
        await db.commit()
        await db.refresh(db_translation)
        
        # 3. Trigger the Celery task
        # We use a minimal data dictionary for better security and smaller message size
        pdf_data = TranslationService.get_minimal_pdf_data(db_translation)
        
        # Task receives the ID as primary key and the dict for security verification
        process_pdf_task.delay(db_translation.id, pdf_data)
        
        return db_translation
    
    @staticmethod
    async def trigger_regeneration(db: AsyncSession, translation: Translation):
        """
        Forces the regeneration of a PDF for an existing translation.
        Used when a file is missing or a retry is manually requested.
        """
        # Update status to pending before re-triggering
        translation.status = "pending"
        await db.commit()

        # Prepare minimal context and send to Worker
        pdf_data = TranslationService.get_minimal_pdf_data(translation)
        process_pdf_task.delay(translation.id, pdf_data)