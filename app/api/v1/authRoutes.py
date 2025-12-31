from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from firebase_admin.auth import verify_id_token
from app.schemas.auth import (
    RegistrationDto,
    SocialAuthDto,
    LoginDto,
    VerifyEmailOtpDto,
    ResendEmailOtpDto,
    RequestPasswordResetDto,
    SetNewPasswordDto,
)
from app.database.models import OtpTypeEnum, User
from app.database.repositories import (
    get_user_by_email,create_user, create_otp,
    get_otp_by_type, delete_otp_by_type
    
    
)
from app.utils import (
   create_jwt, verify_jwt, 
    verify_password, generate_temp_password, 
    get_password_hash, create_access_token, 
    create_temp_token
    )
from app.database.repositories import get_current_user
from app.utils.mail import send_account_verification_email, send_reset_email
from app.utils import dbSession, apiResponse
from fastapi import Request, HTTPException
from ipaddress import ip_address as ip
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
import httpx
from app.database.repositories import get_client_ip, get_country_from_ip
from sqlalchemy.orm import Session
from app.utils.security import (
    create_jwt, generate_otp, verify_password
)

router = APIRouter()
@router.post("/register")
async def register_user(
    payload: RegistrationDto, 
    request: Request, 
    db: Session = Depends(dbSession)
    ):
    try:
        # Check if user exists
        existing_user = get_user_by_email(db, payload.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        # Get client IP address
        ip_address = get_client_ip(request)
        print
        # Hash password and create user
        payload.password = get_password_hash(payload.password)
        new_user = create_user(db, payload, ip_address)

        if not new_user:
            raise HTTPException(status_code=500, detail="User creation failed")

        # Create wallet automatically for the new user
        # try:
        #     wallet_service = WalletService(db)
        #     wallet = wallet_service.get_or_create_wallet(str(new_user.id))
           
        # except Exception as wallet_error:
        #     print(f"WARNING: Failed to create wallet for user {new_user.id}: {str(wallet_error)}")

        # Generate and send OTP
        otp = generate_otp()
        create_otp(db, new_user.email, otp, OtpTypeEnum.VERIFY)
        send_account_verification_email(new_user.email, otp)

        # Create JWT token
        access_token = create_jwt({
            "sub": str(new_user.id),            # unique immutable identifier
            "email": new_user.email,            # optional, for convenience
            "token_version": new_user.token_version  # optional, for revocation
        })

        return apiResponse(
               "success",
                "User registered successfully",
                {
                    "user": new_user.non_sensitive(),
                    "ip":ip_address,
                    "token": access_token
                },
                )

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/social")
async def register_user(payload: SocialAuthDto, request: Request, db: Session = Depends(dbSession)):
    try:
        decoded_token = verify_id_token(payload.id_token)
        if not decoded_token["uid"]:
            raise HTTPException(status_code=401, detail="Authentication failed")

        user = get_user_by_email(db, decoded_token["email"])
        is_new_user = False
        
        if not user:
            # Get client IP and determine country code
            ip_address = get_client_ip(request)
            print(ip_address)
            # Create new user
            user = create_user(db, payload, ip_address)
            is_new_user = True

        # Create wallet for new users (social auth users might not have wallets)
        # if is_new_user:
        #     try:
        #         wallet_service = WalletService(db)
        #         wallet = wallet_service.get_or_create_wallet(str(user.id))
        #         print(f"DEBUG: Wallet created for social auth user {user.id} with currency {wallet.currency}")
        #     except Exception as wallet_error:
        #         print(f"WARNING: Failed to create wallet for social auth user {user.id}: {str(wallet_error)}")
        #         # Don't fail authentication if wallet creation fails

        access_token = create_jwt({"email": user.email, "user_id": str(user.id), "token_version": user.token_version})

        return apiResponse(
            "success",
            "User authenticated successfully.",
            {"user": user.non_sensitive(), "ip":ip_address, "token": access_token},
            )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/login")
async def login_user(payload: LoginDto, db: Session = Depends(dbSession)):
    try:
        user = get_user_by_email(db, payload.email)
        if not user or not verify_password(payload.password, user.password):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        access_token = create_jwt({"email": user.email, "sub": str(user.id), "token_version": user.token_version})

        return apiResponse(
            "success",
            "User login successful.",
            {"user": user.non_sensitive(), "token": access_token},
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/verify-email")
async def verify_email_otp(
    payload: VerifyEmailOtpDto,
    user: User = Depends(get_current_user),
    db: Session = Depends(dbSession),
):
    try:
        otp_record = get_otp_by_type(db, payload.email, payload.otp, OtpTypeEnum.VERIFY)
        if not user or not otp_record:
            raise HTTPException(status_code=400, detail="Invalid otp")

        if otp_record.expiry_date < datetime.now() - timedelta(minutes=15):
            raise HTTPException(status_code=400, detail="Token expired")

        delete_otp_by_type(db, user.id, OtpTypeEnum.VERIFY)

        user.email_verified = True
        db.commit()
        db.refresh(user)

        return apiResponse("success", "Email verified successfully.", {})
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/resend-email-otp")
async def resend_email_otp(
    payload: ResendEmailOtpDto,
    user: User = Depends(get_current_user),
    db: Session = Depends(dbSession),
):
    try:
        delete_otp_by_type(db, user.id, OtpTypeEnum.VERIFY)

        otp = generate_otp()
        create_otp(db, user.email, otp, OtpTypeEnum.VERIFY)

        send_account_verification_email(user.email, otp)

        return apiResponse("success", "Otp resent successfully.", {})
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/password-reset/initiate")
async def initiate_password_reset(
    payload: RequestPasswordResetDto, db: Session = Depends(dbSession)
):
    try:
        user = get_user_by_email(db, payload.email)
        if not user:
            raise HTTPException(status_code=400, detail="User not found")

        otp = generate_otp()
        create_otp(db, user.email, otp, OtpTypeEnum.RESET)

        send_reset_email(payload.email, otp)

        return apiResponse("success", "Otp resent successfully.", {})
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/password-reset/finalize")
async def finalize_password_reset(
    payload: SetNewPasswordDto, db: Session = Depends(dbSession)
):
    try:
        user = get_user_by_email(db, payload.email)
        otp_record = get_otp_by_type(db, payload.email, payload.otp, OtpTypeEnum.RESET)

        if not user or not otp_record:
            raise HTTPException(status_code=400, detail="Invalid otp")

        if otp_record["expiry_date"] < datetime.now():
            raise HTTPException(status_code=400, detail="Token expired")

        user.password = get_password_hash(payload.new_password)
        db.commit()
        db.refresh(user)

        delete_otp_by_type(db, user.id, OtpTypeEnum.RESET)

        return apiResponse(
            "success",
            "Password Reset Successfully.",
            {})
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


