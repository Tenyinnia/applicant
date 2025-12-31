from datetime import datetime, timedelta, timezone
import random
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer
from passlib.context import CryptContext
from jose import jwt, JWTError, ExpiredSignatureError
from sqlalchemy.orm import Session
from app.config.envconfig import settings
import string
import secrets


pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
http_bearer = HTTPBearer()


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def generate_temp_password(length: int = 12) -> str:
    """
    Generate a strong temporary password.
    
    Args:
        length (int): Length of the password. Default is 12 characters.
        
    Returns:
        str: A randomly generated password containing letters, digits, and symbols.
    """
    if length < 8:
        raise ValueError("Password length should be at least 8 characters for security.")

    # Define character sets
    alphabet = string.ascii_letters + string.digits + string.punctuation

    # Generate a secure random password
    temp_password = ''.join(secrets.choice(alphabet) for _ in range(length))

    return temp_password

def create_jwt(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.JWT_EXPIRATION_TIME)
    )
    to_encode.update(
        {
        "exp": expire,
        "iss": settings.JWT_ISSUER,    # who issued this token
        "aud": settings.JWT_AUDIENCE,  # who the token is intended for
        }
        )
    return jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )

def verify_jwt(token: str, db: Session) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            issuer=settings.JWT_ISSUER,
            audience=settings.JWT_AUDIENCE 
        )
        return payload
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def create_access_token(data: dict) -> str:
    return create_jwt(
        data=data,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
def create_temp_token(data: dict) -> str:
    return create_jwt(data, expires_delta=timedelta(minutes=settings.TEMP_TOKEN_EXPIRE_MINUTES))  # 5 minutes for security

def decode_temp_token(token: str, db: Session) -> dict:
    return verify_jwt(token, db)


def generate_otp() -> str:
    return f"{random.randint(100000, 999999)}"





