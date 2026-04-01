from fastapi import APIRouter
from app.api.endpoints import translations

api_router = APIRouter()

# Global router witch includes all the endpoints.
api_router.include_router(
    translations.router, 
    prefix="/translations", # This means that all endpoints defined in translations.py will be under /translations
    tags=["translations"]
)