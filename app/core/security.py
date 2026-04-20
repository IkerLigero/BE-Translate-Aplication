from datetime import datetime, timedelta
from typing import Union, Any
from jose import jwt
from passlib.context import CryptContext

# --- Initial configuration ---
# In the future, these values will go to your .env file
SECRET_KEY = "your_super_secure_secret_key_for_tms" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# The password hashing uses bcrypt, which is a secure algorithm for storing passwords.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# --- PASSWORD FUNCTIONS ---
def get_password_hash(password: str) -> str:
    """Transforms a plain password into a hash for the DB."""
    return pwd_context.hash(password)

# This function will be used to verify the password during login, comparing the plain password with the hashed one stored in the database.
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Compare a plain password with the hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


# --- TOKEN FUNCTIONS (JWT [JSON Web Token]) ---
# This function creates a JWT token that includes the user ID (or any subject) and an expiration time.
def create_access_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # The 'sub' (subject) is usually the user ID
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt