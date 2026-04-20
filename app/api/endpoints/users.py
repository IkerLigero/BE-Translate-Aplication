from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_async_db # Tu dependencia de sesión
from app.models.user import User
from app.schemas.user import UserCreate, UserOut
from app.core.security import get_password_hash

router = APIRouter()

# This file contains the endpoint for creating users, which is necessary for testing and for the overall functionality of the app.
# It includes password hashing and checks for existing users to prevent duplicates.

# Endpoint for creating a new user, which will be used for testing and also allows for user management in the future.
@router.post("", response_model=UserOut)
async def create_user_admin(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_async_db)
):
    # 1. Check if the user already exists
    result = await db.execute(select(User).where(User.email == user_in.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="The email is already registered")

    # 2. Hash the password before saving it to the database
    hashed_pwd = get_password_hash(user_in.password)

    # 3. Create the user object with the hashed password, not the plain password
    new_user = User(
        email=user_in.email,
        hashed_password=hashed_pwd,
        is_active=user_in.is_active
    )

    # 4. Save the new user to the database
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return new_user