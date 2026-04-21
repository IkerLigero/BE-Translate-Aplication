from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, ExpiredSignatureError, JWTError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import SECRET_KEY, ALGORITHM
from app.db.session import get_async_db
from app.models.user import User

# El tokenUrl debe coincidir con tu nueva ruta refactorizada
reusable_oauth2 = OAuth2PasswordBearer(tokenUrl="/api/v1/login")

async def get_current_user(
    db: AsyncSession = Depends(get_async_db),
    token: str = Depends(reusable_oauth2)
) -> User:
    try:
        # Decode valida automáticamente la firma y la expiración (exp)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalid: subject missing",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
    except ExpiredSignatureError:
        # Caso específico: el token ha caducado
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (JWTError, ValidationError):
        # Otros errores de JWT (firma falsa, formato incorrecto)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Buscar usuario en DB
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
        
    return user