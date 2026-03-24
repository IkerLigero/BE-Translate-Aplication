from celery import Celery

celery_app = Celery(
    "pdf_worker",
    broker="redis://127.0.0.1:6379/0",
    backend="redis://127.0.0.1:6379/0"
)
# Autodiscover tasks in the 'app.worker' module
celery_app.autodiscover_tasks(['app.worker'], force=True) 


celery_app.conf.update(
    broker_connection_retry_on_startup=True
)