from sqlalchemy.orm import Session, selectinload
from app.database.models import User, Role
from app.schemas.auth import RegistrationDto
import httpx
from fastapi import HTTPException
import requests
from fastapi import HTTPException
from datetime import datetime, timedelta
import random
from fastapi import Depends, HTTPException, status, Request
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


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
http_bearer = HTTPBearer()

def get_user_by_id(db: Session, user_id: str) -> User:
    return db.query(User).filter(User.id == str(user_id)).first()


def get_user_by_email(db: Session, email: str):
    return (
        db.query(User)
        .options(
            selectinload(User.roles).selectinload(Role.permissions)
        )
        .filter(User.email == email)
        .first()
    )
def get_client_ip(request: Request) -> str:
    # Check X-Forwarded-For first (used by proxies/load balancers)
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host

def get_country_from_ip(ip_address: str) -> str:
    """Get country code from IP address"""
    if not ip_address:
        return "OTHERS"
    
    try:
        url = f"http://ip-api.com/json/{ip_address}"
        response = requests.get(url, timeout=5).json()
        if response.get("status") == "success":
            country_code = response.get("countryCode")
            print(country_code)
            return "NG" if country_code == "NG" else "OTHERS"
    except Exception as e:
        print(f"IP lookup failed: {e}")
    return "OTHERS"

def create_user(db: Session, data: RegistrationDto, ip_address: str = None):
    # Check if user already exists
    existing_user = get_user_by_email(db, data.email)
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    # Get country from IP
    country_location = get_country_from_ip(ip_address)

    # Create the user
    db_user = User(
        email=data.email,
        password=data.password, 
        full_name=data.full_name,
        phone_number=data.phone_number,
        country_location=country_location,
        is_active=True,
        terms_agreed=getattr(data, 'terms_agreed', True),
        email_verified=False,
        theme='light',
        language="english",
        login_provider="email",
        is_admin=False,
    )

    # Fetch default role
    default_role = db.query(Role).filter(Role.name == "user").first()
    if default_role:
        db_user.roles.append(default_role)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user



def update_user(db: Session, user: User, ip_address: str = None):
    """
    Commit changes made to the user object and update location if IP is provided
    """
    if ip_address:
        current_country = get_country_from_ip(ip_address)
        user.country_location = current_country

    db.commit()
    db.refresh(user)
    return user