from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import translations

app = FastAPI(title="TMS - Translation Management System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    translations.router, 
    prefix="/translations", 
    tags=["Translations"]
)

@app.get("/")
def read_root():
    return {"message": "Translation API is ready and open for the Frontend"}