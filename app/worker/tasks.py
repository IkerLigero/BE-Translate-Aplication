import logging
import celery
from app.worker.main import celery_app
from app.services.pdf_service import generate_translation_pdf_bytes
from app.db.session import SessionLocal
from app.models.translation import Translation
# Mandatory import to avoid SQLAlchemy "Mapper[Translation] failed to locate a name 'User'" error
from app.models.user import User  
from deep_translator import GoogleTranslator
from app.core.storage import upload_pdf_to_minio
from sqlalchemy.orm import joinedload
# Embedding
from app.core.vectors import get_embedding

# Configure logging to see errors in Celery logs
logger = logging.getLogger(__name__)

@celery_app.task(
    name="process_pdf_task",
    bind=True,                # Allows access to task instance (self)
    max_retries=3,            # Retry up to 3 times if it fails
    default_retry_delay=2     # Wait 2 seconds between retries
)

def process_pdf_task(self, translation_id: int, pdf_data: dict):
    """
    Background task to handle text translation, PDF generation, 
    storage in MinIO organized by user folders, and semantic embedding generation.
    Reinforced with database-side security validation.
    """
    db = SessionLocal()
    translation = None
    
    try:
        # 1. FETCH AND VALIDATE DATA (Source of Truth)
        # We load the owner relationship to get the email securely from the DB
        translation = db.query(Translation).options(
            joinedload(Translation.owner)
        ).filter(Translation.id == translation_id).first()
        
        # SECURITY CHECK: Ensure the translation exists before proceeding
        if not translation:
            logger.error(f"CRITICAL: Translation ID {translation_id} not found in database.")
            return "Error: ID not found"

        # SECURITY CHECK: Compare user_id from message with DB to prevent unauthorized access
        # This prevents metadata manipulation in the task queue
        if pdf_data.get("user_id") != translation.user_id:
            logger.error(f"SECURITY ALERT: User mismatch for Translation ID {translation_id}. "
                         f"Message User: {pdf_data.get('user_id')}, DB User: {translation.user_id}")
            translation.status = "error"
            db.commit()
            return "Error: Security validation failed"

        # 2. SYNCHRONIZE METADATA
        # We use the DB data to populate the PDF context, ignoring potentially stale/malicious message data
        real_user_id = translation.user_id
        user_email = translation.owner.email if translation.owner else "N/A"
        
        # We RECONSTRUCT pdf_data using the fresh data from the DB
        pdf_data.update({
            "id": str(translation.id),            # Required by some PDF templates
            "user_email": user_email,
            "original_text": translation.original_text,
            "pdf_lang": translation.pdf_lang,
            "target_lang": translation.target_language,
            "source_lang": translation.source_lang, # <-- THIS WAS MISSING AND CAUSED THE ERROR
            "user_id": real_user_id,
            "date": translation.created_at.strftime("%Y-%m-%d %H:%M:%S") if translation.created_at else ""
        })

        # 3. GENERATE SEMANTIC EMBEDDING
        # Every new or regenerated document gets its vector stored for semantic search
        if translation.embedding is None:
            try:
                logger.info(f"Generating embedding for ID {translation_id}...")
                vector = get_embedding(translation.original_text)
                if vector:
                    translation.embedding = vector
                    db.commit() # Save vector immediately
                else:
                    logger.warning(f"Embedding generation returned None for ID {translation_id}")
            except Exception as e:
                logger.error(f"Non-critical Error: Could not generate embedding for ID {translation_id}: {e}")
                # We do not raise here to allow the main translation/PDF flow to finish

        # 4. TRANSLATION LOGIC
        # We only call the external API if the translation is missing or previously failed
        try:
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
                db.commit() 
            else:
                logger.info(f"Reusing existing translation for ID {translation_id}")
                pdf_data["translated_text"] = translation.translated_text
            
        except Exception as e:
            logger.warning(f"Translation API failed for ID {translation_id}: {e}")
            translation.status = "error"
            translation.translated_text = "Translation Service Unavailable"
            db.commit() 
            # Raise for Celery to trigger the retry mechanism
            raise self.retry(exc=e)

        # 5. PDF GENERATION & SECURE STORAGE
        try:
            # Generate the PDF file bytes using the synchronized data
            pdf_bytes = generate_translation_pdf_bytes(pdf_data)
        
            # SECURE PATH: Files are organized in MinIO by user ID folders obtained from DB
            file_name = f"user_{real_user_id}/translation_{translation_id}.pdf"
            
            # Upload the generated bytes to MinIO
            upload_pdf_to_minio(pdf_bytes, file_name)
            
            # Update final record status
            translation.file_path = file_name 
            translation.status = "completed"
            db.commit()
            
        except Exception as e:
            logger.error(f"Storage or PDF generation error for ID {translation_id}: {e}")
            translation.status = "error"
            db.commit()
            raise e 

        return f"Task finished successfully for ID {translation_id}"

    except Exception as e:
        db.rollback()
        # Ensure Celery internal Retry exception is passed correctly to the worker
        if isinstance(e, celery.exceptions.Retry):
            raise e
            
        # Update DB status if a fatal unhandled error occurs
        if translation:
            translation.status = "error"
            db.commit()
        raise e 
    finally:
        # Prevent database connection leaks
        db.close()