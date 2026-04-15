from datetime import datetime, timedelta
from typing import Union, Any
from jose import jwt
from passlib.context import CryptContext

# --- CONFIGURACIÓN ---
# En el futuro, estos valores irán a tu archivo .env
SECRET_KEY = "tu_llave_secreta_super_segura_para_el_tms" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 horas

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# --- FUNCIONES DE CONTRASEÑA ---
def get_password_hash(password: str) -> str:
    """Transforma la contraseña plana en un hash para la DB."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Compara una contraseña plana con el hash de la DB."""
    return pwd_context.verify(plain_password, hashed_password)


# --- FUNCIONES DE TOKEN (JWT) ---
def create_access_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # El 'sub' (subject) suele ser el ID del usuario
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt