from app.worker.main import celery_app
from app.services.pdf_service import generate_translation_pdf_bytes
from app.db.session import SessionLocal
from app.models.translation import Translation
from deep_translator import GoogleTranslator
from app.core.storage import upload_pdf_to_minio
import logging

# Configure logging to see errors in Celery logs
logger = logging.getLogger(__name__)

@celery_app.task(
    name="process_pdf_task",
    bind=True,                # Allows access to task instance (self)
    max_retries=3,            # Retry up to 3 times if it fails
    default_retry_delay=2     # Wait 2 seconds between retries
)

# The task processes the translation and PDF generation, with robust error handling and retries for transient issues.
def process_pdf_task(self, translation_id: int, pdf_data: dict):
    db = SessionLocal()
    try:
        translation = db.query(Translation).filter(Translation.id == translation_id).first()
        if not translation:
            logger.error(f"Translation ID {translation_id} not found in database.")
            return "Error: ID not found"

        # 1. Sync data
        pdf_data["pdf_lang"] = translation.pdf_lang
        pdf_data["target_lang"] = translation.target_language

        # 2. Smart translation logic with retry for transient errors (like API issues)
        try:
            # If we don't have the translated text yet, call the API
            if not translation.translated_text or translation.translated_text == "Translation Service Unavailable":
                logger.info(f"Translating ID {translation_id} via Google API...")
                translator = GoogleTranslator(
                    source=translation.source_lang.lower(), 
                    target=translation.target_language.lower()
                )
                translated = translator.translate(translation.original_text)
                
                if not translated:
                    raise ValueError("Translation returned empty result")

                translation.translated_text = translated
                pdf_data["translated_text"] = translated
                # Save the translation immediately so it's available if the PDF fails later
                db.commit() 
            
            else:
                # If it already exists in DB, reuse it (saves time and API calls)
                logger.info(f"Reusing existing translation for ID {translation_id}")
                pdf_data["translated_text"] = translation.translated_text
            
        except Exception as e:
            logger.warning(f"Translation failed for ID {translation_id}: {e}")
            translation.status = "error"
            translation.translated_text = "Translation Service Unavailable"
            db.commit() 
            raise self.retry(exc=e)

        # 3. PDF Generation & MinIO (This always runs if there's no file)
        try:
            pdf_bytes = generate_translation_pdf_bytes(pdf_data)
            file_name = f"translation_{translation_id}.pdf"
            
            upload_pdf_to_minio(pdf_bytes, file_name)
            
            translation.file_path = file_name
            translation.status = "completed"
            db.commit()
            
        except Exception as e:
            logger.error(f"PDF/Storage error for ID {translation_id}: {e}")
            # If the PDF fails, mark it as error but the translated text is already saved above
            translation.status = "error"
            db.commit()
            raise e 

        return f"Task finished successfully for ID {translation_id}"

    except Exception as e:
        db.rollback()
        # Only mark as error if it's not a scheduled retry by Celery
        if not isinstance(e, self.retry_backoff_base):
            if translation:
                translation.status = "error"
                db.commit()
        raise e # It's important to re-raise the exception so Celery can handle the retry
    finally:
        db.close()