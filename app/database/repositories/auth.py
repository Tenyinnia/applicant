from datetime import datetime, timedelta
import random
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from jose import jwt, JWTError, ExpiredSignatureError
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from app.config.envconfig import settings
from app.utils import dbSession
from app.database.models import User, Role, Permission
import string
import secrets
from uuid import UUID
from app.utils import verify_jwt, verify_password
from .user import get_user_by_email, get_user_by_id

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
http_bearer = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
    db: Session = Depends(dbSession),
) -> User:
    token_data = verify_jwt(credentials.credentials, db)
    
    # Get 'sub' from token and validate
    user_id = token_data.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token: missing sub")
    
    try:
        user_uuid = UUID(user_id)  # Validate UUID format
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token: bad UUID")
    
    # Fetch user from DB
    user = get_user_by_id(db, user_uuid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check token version
    if token_data.get("token_version") != user.token_version:
        raise HTTPException(status_code=401, detail="Token revoked")
    
    return user


def require_authenticated():
    """Just require any authenticated user."""
    def _guard(user: User = Depends(get_current_user)):
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account Logged Out, Login and Try again"
            )
        return user
    return _guard

def authenticate_user(email: str, password: str, db: Session) -> User | None:
    """Authenticate user with email and password"""
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password):
        return None
    return user