from app.worker.main import celery_app
from app.services.pdf_service import generate_translation_pdf_bytes
from app.db.session import SessionLocal
from app.models.translation import Translation
# 1. Cambiamos el import
from deep_translator import GoogleTranslator 

@celery_app.task(name="process_pdf_task")
def process_pdf_task(translation_id: int, pdf_data: dict):
    db = SessionLocal()
    try:
        translation = db.query(Translation).filter(Translation.id == translation_id).first()
        if not translation:
            return f"Error: Translation {translation_id} not found"

        # 2. Nueva lógica con GoogleTranslator (Sin API Key)
        texto_traducido = GoogleTranslator(
            source=translation.source_lang.lower(), 
            target=translation.target_language.lower()
        ).translate(translation.original_text)
        
        # 3. Guardar en DB
        translation.translated_text = texto_traducido
        pdf_data["translated_text"] = texto_traducido

        # 4. Generar PDF (Doble check)
        generate_translation_pdf_bytes(pdf_data)

        # 5. Finalizar
        translation.status = "completed"
        db.commit()
        
        return f"Success: ID {translation_id} translated with Google."

    except Exception as e:
        db.rollback()
        # Imprimimos el error en la terminal del worker para que lo veas
        print(f"DEBUG ERROR: {str(e)}")
        return f"Error in the process: {str(e)}"
    finally:
        db.close()