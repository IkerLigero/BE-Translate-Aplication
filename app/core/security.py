from datetime import datetime, timedelta, timezone
from typing import Union, Any
from jose import jwt
from passlib.context import CryptContext

# --- Configuration ---
SECRET_KEY = "your_super_secure_secret_key_for_tms" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours default

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- PASSWORD FUNCTIONS ---
def get_password_hash(password: str) -> str:
    """Transforms a plain password into a hash for the DB."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Compare a plain password with the hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

# --- TOKEN FUNCTIONS ---
def create_access_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str:
    """
    Creates a JWT token with an expiration time (exp).
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt