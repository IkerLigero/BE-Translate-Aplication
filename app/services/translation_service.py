from sqlalchemy.orm import Session
from app.models.translation import Translation
from app.worker.tasks import process_pdf_task
from zoneinfo import ZoneInfo


class TranslationService:
    # Convert a SQLAlchemy Translation object into the dictionary.
    @staticmethod
    def get_pdf_data_dict(translation: Translation) -> dict:
        """Centralizes the creation of the dictionary needed by the Worker and Typst"""
        return {
            "id": str(translation.id),
            "source_lang": translation.source_lang,
            "pdf_lang": translation.pdf_lang,
            "target_lang": translation.target_language,
            "original_text": translation.original_text,
            "translated_text": translation.translated_text,
            "date": translation.created_at.astimezone(ZoneInfo("Europe/Madrid")).strftime("%Y-%m-%d %H:%M:%S")
        }


    # This method is executed when someone makes a POST request to create a new translation.
    @staticmethod
    def create_translation_process(db: Session, payload) -> Translation:
        """Logic for Endpoint 2: Create in DB and launch Worker"""
        # 1. Create the DB entry with status "pending"
        db_translation = Translation(
            original_text=payload.text_to_translate,
            source_lang=payload.source_lang,
            pdf_lang=payload.pdf_lang,
            target_language=payload.target_lang,
            status="pending"
        )
        db.add(db_translation)
        db.commit()
        db.refresh(db_translation)
        
        # 2. Call the previous method to have the data ready.
        pdf_data = TranslationService.get_pdf_data_dict(db_translation)
        # 3. Launch the Worker task asynchronously with the translation ID and the data dictionary.
        process_pdf_task.delay(db_translation.id, pdf_data)
        
        return db_translation


    # This method is executed when someone makes a POST request to force regeneration.
    @staticmethod
    def trigger_regeneration(db: Session, translation: Translation):
        """Logic for Endpoint 3: Force regeneration (or regenerate)"""
        pdf_data = TranslationService.get_pdf_data_dict(translation)
        process_pdf_task.delay(translation.id, pdf_data)