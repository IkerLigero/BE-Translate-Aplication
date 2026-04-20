from fastapi import APIRouter, Depends
from app.api.endpoints import translations, users, login
from app.api.deps import get_current_user

api_router = APIRouter()

# --- RUTAS PÚBLICAS (Sin autenticación) ---
# El login debe ser público para poder obtener el token.
api_router.include_router(login.router, tags=["Auth"])

# El registro de usuarios suele ser público (depende de tu lógica, 
# si solo un admin crea usuarios, muévelo abajo).
api_router.include_router(users.router, prefix="/users", tags=["Usuarios"])


# --- RUTAS PROTEGIDAS (Requieren Token JWT) ---
# Al añadir 'dependencies' aquí, TODOS los endpoints dentro de translations.py
# pasan a ser privados automáticamente.
api_router.include_router(
    translations.router, 
    prefix="/translations", 
    tags=["translations"],
    dependencies=[Depends(get_current_user)]
)