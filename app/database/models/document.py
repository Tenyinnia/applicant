# app/models/document.py
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy import Column, String, JSON, DateTime, Boolean, Float
from sqlalchemy.orm import relationship
from app.database import Base
from sqlalchemy.sql import func
from sqlalchemy import DateTime
from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
import uuid

class Document(Base):
    __tablename__ = "documents"

    id                  = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    user_id             = Column(PG_UUID(as_uuid=True),ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    file_name           = Column(String, nullable=False)
    file_type           = Column(String, nullable=False, index=True)  # 'cv', 'cover_letter', 'certificate'
    file_path           = Column(String, nullable=False)  # path on disk or cloud

    user                = relationship("User", back_populates="documents")
    parsed_profile      = relationship("ParsedProfile", back_populates="document", uselist=False, cascade="all, delete-orphan",)
    
class ParsedProfile(Base):
    __tablename__ = "parsed_profiles"

    id                  = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id             = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    document_id         = Column(PG_UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), unique=True)

    payload             = Column(JSONB, nullable=False)          # canonical structure
    created_at          = Column(DateTime, default=func.now())
    updated_at          = Column(DateTime, default=func.now(), onupdate=func.now())

    document            = relationship("Document", back_populates="parsed_profile") 
    

class UserParsedCV(Base):
    __tablename__ = "user_parsed_cv"

    user_id             = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    document_id         = Column(PG_UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), unique=True)
    parsed_at           = Column(DateTime, default=func.now())

    document            = relationship("Document", backref="current_parse")

