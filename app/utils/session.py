from sqlalchemy import create_engine, Column, DateTime
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.orm import sessionmaker, Query
from sqlalchemy.sql import func
from app.config import settings
from typing import Literal
from app.schemas import ApiResponse

# SQLAlchemy engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # live connections check
) 

# Session maker for managing database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def dbSession():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def apiResponse(
    status: Literal["success", "error"],
    message: str,
    data: dict = None,
) -> ApiResponse:
    """
    Function to create a standardized API response.

    Args:
        status (Literal["success", "error"]): status type.
        message (str): Message to be included in the response.
        data (dict, optional): Data to be included in the response. Defaults to None.

    Returns:
        dict: Standardized API response.
    """
    return {"status": status, "message": message, "data": data}
