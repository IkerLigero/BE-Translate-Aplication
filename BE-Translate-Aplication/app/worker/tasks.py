from app.worker.main import celery_app
from app.services.pdf_service import generate_translation_pdf_bytes
from app.db.session import SessionLocal
from app.models.translation import Translation
from deep_translator import GoogleTranslator

@celery_app.task(name="process_pdf_task")
def process_pdf_task(translation_id: int, pdf_data: dict):
    db = SessionLocal()
    try:
        translation = db.query(Translation).filter(Translation.id == translation_id).first()
        if not translation:
            return "Error: ID not found"

        try:
            # Intentamos traducir
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
            # SI FALLA LA TRADUCCIÓN (TEXTO LARGO)
            print(f"API Error: {e}")
            translation.translated_text = "Error in translation" # <--- ESTO ELIMINA EL PENDING
            translation.status = "error"
            pdf_data["translated_text"] = "Error in translation"

        # Guardamos en la base de datos SÍ O SÍ antes de generar el PDF
        db.commit()

        # Generamos el PDF con los datos actualizados (ya sea el texto o el error)
        generate_translation_pdf_bytes(pdf_data)
        
        return f"Task finished for ID {translation_id}"

    except Exception as e:
        db.rollback()
        return f"System error: {e}"
    finally:
        db.close()