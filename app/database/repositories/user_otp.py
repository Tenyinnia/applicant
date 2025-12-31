from datetime import datetime, timedelta
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.database.models import User, UserOtp


def get_otp_by_type(db: Session, email: str, otp: str, otp_type: str):
    db_user = db.query(User).filter(User.email == email).first()
    if not db_user:
        return None
    return (
        db.query(UserOtp)
        .filter(
            UserOtp.user_id == db_user.id,
            UserOtp.otp == otp,
            UserOtp.otp_type == otp_type,
        )
        .first()
    )


def create_otp(
    db: Session, strategy: str, otp: str, otp_type: str, expiry_time: int = 15
):
    db_user = db.query(User).filter(User.email == strategy).first()
    if not db_user:
        return None
    db_otp = UserOtp(
        user_id=db_user.id,
        otp=otp,
        otp_type=otp_type,
        expiry_date=datetime.now() + timedelta(minutes=expiry_time),
    )
    db.add(db_otp)
    db.commit()
    db.refresh(db_otp)
    return db_otp


def delete_otp(db: Session, otp_id: str):
    db_otp = db.query(UserOtp).filter(UserOtp.id == otp_id).first()
    if db_otp:
        db.delete(db_otp)
        db.commit()
        return True
    return False


def delete_otp_by_type(db: Session, user_id: str, otp_type: str):
    deleted_count = (
        db.query(UserOtp)
        .filter(UserOtp.user_id == user_id, UserOtp.otp_type == otp_type)
        .delete()
    )
    db.commit()
    return deleted_count > 0
