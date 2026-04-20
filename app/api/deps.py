from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import SECRET_KEY, ALGORITHM
from app.db.session import get_async_db
from app.models.user import User

# This file contains the dependency to get the current user from the token, ensuring that users can only access their own data.
# It also includes the OAuth2PasswordBearer configuration to specify where the token should be obtained from. 

# This line tells FastAPI that the token will be sent to the /login endpoint.
reusable_oauth2 = OAuth2PasswordBearer(tokenUrl="/login")

# Function to get the current user based on the token.
async def get_current_user(
    db: AsyncSession = Depends(get_async_db),
    token: str = Depends(reusable_oauth2)
) -> User:
    try:
        # 1. Decode the token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        # 2. Validate the token and check if the user_id is present
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Could not validate credentials",
            )
    except (jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or expired token",
        )

    # 3. Fetch the user from the database
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 4. Check if the user is still active
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
        
    return user