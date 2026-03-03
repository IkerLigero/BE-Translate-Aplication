from fastapi import FastAPI
from app.api.endpoints import translations

# Creamos la instancia principal de la API
app = FastAPI(
    title="TMS - Translation Management System",
    description="API for managing translations. Create translation requests and retrieve their status.",
    version="1.0.0"
)

# Incluimos las rutas del archivo translations.py
# El prefix "/translations" significa que todas sus rutas empezarán por ahí
app.include_router(translations.router, prefix="/translations", tags=["Translations"])

# Un endpoint de cortesía para saber que el servidor está vivo
@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "Bienvenido a la API de Traducción",
        "docs": "/docs"
    }