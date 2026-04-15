from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_async_db # Tu dependencia de sesión
from app.models.user import User
from app.schemas.user import UserCreate, UserOut
from app.core.security import get_password_hash

router = APIRouter()

@router.post("", response_model=UserOut)
async def create_user_admin(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_async_db)
):
    # 1. Verificar si el usuario ya existe
    result = await db.execute(select(User).where(User.email == user_in.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Este email ya está registrado")

    # 2. HASEAR la contraseña (La magia ocurre aquí)
    hashed_pwd = get_password_hash(user_in.password)

    # 3. Crear el objeto con el hash, no con la password plana
    new_user = User(
        email=user_in.email,
        hashed_password=hashed_pwd,
        is_active=user_in.is_active
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return new_user