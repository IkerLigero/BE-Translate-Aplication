from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import translations

app = FastAPI(title="TMS - Translation Management System")

# --- CONFIGURACIÓN DE CORS (El puente para Ibai) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow any Frontend to connect. In production, change to the real URL.
    allow_credentials=True,
    allow_methods=["*"], # Allow GET, POST, PUT, DELETE, etc.
    allow_headers=["*"], # Allow all headers.
)

app.include_router(translations.router, prefix="/translations", tags=["Translations"])

@app.get("/")
def read_root():
    return {"message": "Translation API is ready and open for the Frontend"}