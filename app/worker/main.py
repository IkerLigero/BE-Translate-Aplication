from celery import Celery

# Celery configuration for the worker that processes PDF generation tasks in the background.
celery_app = Celery(
    "pdf_worker",
    broker="redis://127.0.0.1:6379/0", 
    backend="redis://127.0.0.1:6379/0"
)

# Autodiscover tasks in the 'app.worker' module
celery_app.autodiscover_tasks(['app.worker'], force=True) 

# This setting ensures that if the Redis broker is not available when the worker starts, it will keep trying to connect instead of crashing immediately.
celery_app.conf.update(
    broker_connection_retry_on_startup=True
)