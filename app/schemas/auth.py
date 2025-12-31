from pydantic import BaseModel, EmailStr, Field, model_validator, StringConstraints
from typing import Literal, Optional, List, Annotated

class TokenResponse(BaseModel):
    access: str
    refresh: str
    
class RegistrationDto(BaseModel):
    email:              EmailStr
    password:           str
    full_name:          str
    phone_number:       str
    terms_agreed:       bool = True

   
    
    class Config:
        # Example values for API documentation
        json_schema_extra = {
            "example": {
                "full_name": "John Doe",
                "email": "user@example.com",
                "password": "securepassword123",
                "phone_number": "+2348066575743",
                "terms_agreed": True,
            }
        }


class SocialAuthDto(BaseModel):
    social_type:        Literal["google","facebook"]
    id_token:           str

class LoginDto(BaseModel):
    email:      EmailStr
    password:   str


class VerifyEmailOtpDto(BaseModel):
    email:  EmailStr
    otp:    str
    

class ResendEmailOtpDto(BaseModel):
    email:      EmailStr
    otp_type:   Literal["verify", "reset"]


class RequestPasswordResetDto(BaseModel):
    email:  EmailStr


class SetNewPasswordDto(BaseModel):
    email:          EmailStr
    otp:            str
    new_password:   str
    


class TwoFactorVerifyRequest(BaseModel):
    temp_token: str
    code: str
    
class AdminCreationDto(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    terms_agreed: bool = True
    phone_number: Optional[str] = str
    language: Optional[str] = "english"
    make_admin: bool = Field(False, description="Only super-admins may flip this")
    role_ids: Optional[List[int]] = Field(None, description="Assign roles if make_admin is True")

    @model_validator(mode="before")
    def check_roles_for_admin(cls, values):
        make_admin = values.get("make_admin")
        role_ids = values.get("role_ids")
        if make_admin and not role_ids:
            raise ValueError("role_ids must be provided when make_admin is True")
        return values

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123",
                "full_name": "John Doe",
                "terms_agreed": True,
                "phone_number": "+2348066666666",
                "language": "english",
                "make_admin": True,
                "role_ids": [1, 2]  # Admin can assign multiple roles
            }
        }
        


class ResetPasswordDto(BaseModel):
    new_password: Annotated[str, StringConstraints(min_length=8)]
    confirm_password: Annotated[str, StringConstraints(min_length=8)]