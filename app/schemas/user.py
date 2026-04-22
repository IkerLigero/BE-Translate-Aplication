from pydantic import BaseModel, EmailStr
from typing import Optional

# What we receive from the Frontend when creating a user
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    is_active: Optional[bool] = True
    registration_secret: str

# What we return to the Frontend when we create a user or when we fetch user data
class UserOut(BaseModel):
    id: int
    email: EmailStr
    is_active: bool

    class Config:
        from_attributes = True