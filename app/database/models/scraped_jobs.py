# app/models/document.py
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy import Column, String, JSON, DateTime, Boolean, Float, Text
from sqlalchemy.orm import relationship
from app.database import Base
from sqlalchemy.sql import func
from sqlalchemy import DateTime
from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
import uuid

class Job(Base):
    __tablename__ = "jobs"

    id            = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title         = Column(String, nullable=False)
    company       = Column(String, nullable=False)
    location      = Column(String)
    description   = Column(Text)
    url           = Column(String, unique=True, nullable=False)
    external_id   = Column(String)          # board-specific id
    board       = Column(String, index=True)  # "remote_ok", "github", etc.
    posted_at     = Column(DateTime)
    raw_payload   = Column(JSONB)           # full ad as json
    created_at    = Column(DateTime, server_default=func.now())