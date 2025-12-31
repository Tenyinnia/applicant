from pydantic_settings import BaseSettings
from pydantic import Field
from typing import ClassVar, Dict

class Settings(BaseSettings):
    APP_NAME: str
    APP_ENV: str
    BASE_URL: str

    DATABASE_URL: str

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    JWT_EXPIRATION_TIME: int
    JWT_AUDIENCE: str
    JWT_ISSUER: str

    EMAIL_HOST: str
    EMAIL_PORT: int
    EMAIL_USER: str
    EMAIL_PASSWORD: str
    DEFAULT_FROM_EMAIL: str
    EMAIL_USE_TLS: bool=True
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        description="Access token expiration time in minutes"
    )
    TEMP_TOKEN_EXPIRE_MINUTES: int= Field(        
        default=5,
        description="Temporary Access token expiration time in minutes"
        )
    # FIREBASE_CREDENTIALS: str

    # ZIGATEXT_ACCESS_KEY: str
    # ZIGATEXT_BASE_URL: str
    # ZIGATEXT_SENDER_NAME: str

    # PAYSTACK_BASE_URL: str
    # PAYSTACK_SECRET_KEY: str
    # PAYSTACK_PUBLIC_KEY: str
    # FRONTEND_PAY_URL: str
    ENVIRONMENT: str = Field("development", pattern="^(development|staging|production)$")
    # CREATE_DEFAULT_SUPERUSER: bool = False
    # DEFAULT_SUPERUSER_EMAIL: str
    # DEFAULT_SUPERUSER_PASSWORD: str
    SCRAPEOPS_API_KEY: str
    SCRAPEOPS_PROXY_ENABLED: bool=True


    @property
    def is_production(self):
        return self.ENVIRONMENT == "production"
    
    class Config:
        env_file = ".env"


settings = Settings()
