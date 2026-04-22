from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_async_db 
from app.models.user import User
from app.schemas.user import UserCreate, UserOut
from app.core.security import get_password_hash
from app.core.config import settings  # Ensure REGISTRATION_SECRET is defined in your config

router = APIRouter()

@router.post("", response_model=UserOut)
async def create_user_admin(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Creates a new user in the system. 
    Requires a 'registration_secret' within the request body to authorize the operation,
    acting as a master password for administrative user creation.
    """

    # 1. Security Check: Validate the Shared Registration Secret
    # This prevents unauthorized users or clients from creating new accounts
    if user_in.registration_secret != settings.REGISTRATION_SECRET:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid registration secret. Access denied."
        )

    # 2. Check if the user already exists in the database
    # We query by email to ensure unique account constraints
    result = await db.execute(select(User).where(User.email == user_in.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="The email is already registered"
        )

    # 3. Secure Password Storage
    # Hash the plain text password before persisting it to the database
    hashed_pwd = get_password_hash(user_in.password)

    # 4. Object Initialization
    # Mapping the validated input data to the User database model
    new_user = User(
        email=user_in.email,
        hashed_password=hashed_pwd,
        is_active=user_in.is_active
    )

    # 5. Database Persistence
    # Using asynchronous session to add, commit, and refresh the user record
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return new_user