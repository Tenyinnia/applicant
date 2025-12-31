import uuid
import enum
from sqlalchemy import Column, String, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from app.database import Base


class OtpTypeEnum(enum.Enum):
    VERIFY = "verify"
    RESET = "reset"


class UserOtp(Base):
    __tablename__ = "user_otps"

    id            = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    user_id       = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    otp           = Column(String(255))
    otp_type      = Column(Enum(OtpTypeEnum), nullable=False)
    expiry_date   = Column(DateTime, nullable=True)

    user          = relationship("User", back_populates="user_otps")

