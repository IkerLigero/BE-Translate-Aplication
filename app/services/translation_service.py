from sqlalchemy.orm import Session
from app.models.translation import Translation
from app.worker.tasks import process_pdf_task
from zoneinfo import ZoneInfo

class TranslationService:
    @staticmethod
    def get_pdf_data_dict(translation: Translation) -> dict:
        """Centraliza la creación del diccionario que necesita el Worker y Typst"""
        return {
            "id": str(translation.id),
            "source_lang": translation.source_lang,
            "pdf_lang": translation.pdf_lang,
            "target_lang": translation.target_language,
            "original_text": translation.original_text,
            "translated_text": translation.translated_text,
            # Forzamos zona horaria de Madrid/Bruselas para el PDF
            "date": translation.created_at.astimezone(ZoneInfo("Europe/Madrid")).strftime("%Y-%m-%d %H:%M:%S")
        }

    @staticmethod
    def create_translation_process(db: Session, payload) -> Translation:
        """Lógica para el Endpoint 2: Crear en DB y lanzar Worker"""
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
        
        # Lanzar la tarea asíncrona
        pdf_data = TranslationService.get_pdf_data_dict(db_translation)
        process_pdf_task.delay(db_translation.id, pdf_data)
        
        return db_translation

    @staticmethod
    def trigger_regeneration(db: Session, translation: Translation):
        """Lógica para re-lanzar el Worker (Endpoints 3 y 5)"""
        pdf_data = TranslationService.get_pdf_data_dict(translation)
        process_pdf_task.delay(translation.id, pdf_data)