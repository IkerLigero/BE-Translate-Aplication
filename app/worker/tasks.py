from app.worker.main import celery_app
from app.services.pdf_service import generate_translation_pdf_bytes
from app.db.session import SessionLocal
from app.models.translation import Translation
from deep_translator import GoogleTranslator
from app.core.storage import upload_pdf_to_minio # Importing the new storage utility

# This Celery task processes the translation data, updates the database, 
# generates a PDF, and stores it in MinIO.
@celery_app.task(name="process_pdf_task")
def process_pdf_task(translation_id: int, pdf_data: dict):
    db = SessionLocal()
    try:
        translation = db.query(Translation).filter(Translation.id == translation_id).first()
        if not translation:
            return "Error: ID not found"

        # 1. Aseguramos que pdf_lang esté en el diccionario para el PDF
        pdf_data["pdf_lang"] = translation.pdf_lang        # "fr"
        pdf_data["target_lang"] = translation.target_language # "en"

        try:
            # 2. Usamos source_lang para la traducción (ya lo tienes bien)
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
            print(f"API Error: {e}")
            translation.translated_text = "Error in translation"
            translation.status = "error"
            pdf_data["translated_text"] = "Error in translation"

        # 3. Generar el PDF pasándole el pdf_data que ahora tiene pdf_lang
        pdf_bytes = generate_translation_pdf_bytes(pdf_data)

        file_name = f"translation_{translation_id}.pdf"
        upload_pdf_to_minio(pdf_bytes, file_name)

        translation.file_path = file_name
        db.commit()
        
        return f"Task finished and file stored for ID {translation_id}"

    except Exception as e:
        db.rollback()
        return f"System error: {e}"
    finally:
        db.close()