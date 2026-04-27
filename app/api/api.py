from fastapi import APIRouter, Depends
from app.api.endpoints import translations, users, login
from app.api.deps import get_current_user

api_router = APIRouter()
# This file is responsible for defining the main API router and including all the endpoint routers (translations, users, login).
# It also sets up the dependencies for protected routes, ensuring that only authenticated users can access certain


# --- Public Routes ---
# Public routers uses the endpoints without the get_current_user dependency, allowing access without a token.
# Login must be public to obtain the token.
api_router.include_router(login.router, tags=["Auth"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])


# --- Protected Routes (Require JWT Token) ---
# By adding 'dependencies' here, ALL endpoints within translations.py
# become private automatically.
api_router.include_router(
    translations.router, 
    prefix="/translations", 
    tags=["translations"],
    dependencies=[Depends(get_current_user)]
)