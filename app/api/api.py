from fastapi import APIRouter
from app.api.endpoints import translations

api_router = APIRouter()

# Aquí unimos el fichero de traducciones al router global
api_router.include_router(
    translations.router, 
    prefix="/translations", 
    tags=["translations"]
)