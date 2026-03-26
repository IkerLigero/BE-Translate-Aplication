from app.worker.main import celery_app
from app.services.pdf_service import generate_translation_pdf_bytes
from app.db.session import SessionLocal
from app.models.translation import Translation
from deep_translator import GoogleTranslator

# This Celery task processes the translation data, updates the database record, and generates the PDF using the provided data.
@celery_app.task(name="process_pdf_task")
def process_pdf_task(translation_id: int, pdf_data: dict):
    db = SessionLocal()
    try:
        # Fetch the translation record from the database using the provided ID
        translation = db.query(Translation).filter(Translation.id == translation_id).first()
        if not translation:
            return "Error: ID not found"

        try:
            # Try translating the text using Google Translate API
            translated = GoogleTranslator(
                source=translation.source_lang.lower(), 
                target=translation.target_language.lower()
            ).translate(translation.original_text)
            
            if not translated:
                raise Exception("Empty Result")

            translation.translated_text = translated
            translation.status = "completed"
            pdf_data["translated_text"] = translated

        except Exception as e:
            # If translation fails (e.g., long text)
            print(f"API Error: {e}")
            translation.translated_text = "Error in translation"
            translation.status = "error"
            pdf_data["translated_text"] = "Error in translation"

        # Store the updated translation in the database
        db.commit()

        # Generate the PDF using the provided data
        generate_translation_pdf_bytes(pdf_data)
        
        return f"Task finished for ID {translation_id}"

    except Exception as e:
        db.rollback()
        return f"System error: {e}"
    finally:
        db.close()