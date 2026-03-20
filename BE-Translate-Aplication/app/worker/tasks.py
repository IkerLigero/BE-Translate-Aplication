from app.worker.main import celery_app
from app.services.pdf_service import generate_translation_pdf_bytes
from app.db.session import SessionLocal
from app.models.translation import Translation

# Celery task to process PDF generation in the background
@celery_app.task(name="process_pdf_task")
def process_pdf_task(translation_id: int, pdf_data: dict):
    try:
        pdf_bytes = generate_translation_pdf_bytes(pdf_data)
        
        db = SessionLocal()
        translation = db.query(Translation).filter(Translation.id == translation_id).first()
        if translation:
            translation.status = "completed"
            db.commit()
        db.close()
        
        return f"PDF {translation_id} processed successfully."
    except Exception as e:
        return f"Error in the worker: {str(e)}"