from pydantic import BaseModel, EmailStr
from typing import Optional

# Lo que recibimos del Admin
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    is_active: Optional[bool] = True

# Lo que devolvemos al mundo (sin la contraseña)
class UserOut(BaseModel):
    id: int
    email: EmailStr
    is_active: bool

    class Config:
        from_attributes = True