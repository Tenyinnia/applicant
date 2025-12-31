import logging
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import Base
import app.database.models
# from app.api.v1 import authRoutes, userRoutes, walletRoutes, transactionRoutes, apiRoutes, paystackRoutes, Doc
from app.api.v1 import documentRoutes, authRoutes, userRoutes
from fastapi import FastAPI
# from app.database.seeder import DatabaseSeeder
from app.utils import dbSession, engine
from app.config.envconfig import settings
from contextlib import asynccontextmanager
from fastapi import APIRouter
from app.database.repositories import get_current_user
from app.config import initialize_firebase
v1Router = APIRouter(prefix="/api/v1")

# from app.api.v1 import v1Router

@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_firebase()
    
#     """Production-ready lifespan with comprehensive error handling."""
#     startup_success = False
    
#     try:
#         logger.info("=== APPLICATION STARTUP ===")
        
#         # Database seeding (development only)
#         if settings.ENVIRONMENT == "development":
#             logger.info("🌱 Starting database seeding...")
            
#             try:
#                 db = next(dbSession())
#                 seeder = DatabaseSeeder(db)
#                 seeder.seed_all(
#                     create_superuser=settings.CREATE_DEFAULT_SUPERUSER,
#                     superuser_email=settings.DEFAULT_SUPERUSER_EMAIL,
#                     superuser_password=settings.DEFAULT_SUPERUSER_PASSWORD
#                 )
#                 logger.info("✅ Database seeding completed!")
#             except Exception as e:
#                 logger.error(f"❌ Database seeding failed: {e}")
#                 if settings.fail_on_seed_error:  # Add this to your settings
#                     raise
#             finally:
#                 if 'db' in locals():
#                     db.close()
        
#         # Add other startup tasks here
#         logger.info("🚀 Initializing application components...")
        
#         # Example: Initialize external services
#         # await initialize_redis()
#         # await initialize_elasticsearch()
#         # await setup_monitoring()
        
#         startup_success = True
#         logger.info("✅ Application startup completed successfully!")
        
#     except Exception as e:
#         logger.error(f"❌ Application startup failed: {e}")
#         if settings.ENVIRONMENT == "production":
#             raise  # Fail fast in production
#         else:
#             logger.warning("⚠️  Continuing startup despite errors (development mode)")
    
#     # Application running
#     yield
    
#     # Shutdown
#     try:
#         logger.info("=== APPLICATION SHUTDOWN ===")
        
#         if startup_success:
#             logger.info("🔄 Gracefully shutting down services...")
#             # Add cleanup tasks
#             # await cleanup_redis()
#             # await cleanup_elasticsearch()
        
#         logger.info("✅ Application shutdown completed!")
        
#     except Exception as e:
#         logger.error(f"❌ Shutdown error: {e}")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
)

logging.basicConfig()
logging.getLogger("sqlalchemy").setLevel(logging.ERROR)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)
# Create database tables
Base.metadata.create_all(bind=engine)

# # Initialize Firebase Admin SDK
initialize_firebase()
# # Routes
app.include_router(authRoutes.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(
    userRoutes.router,
    prefix="/api/v1/user",
    tags=["User"],
    dependencies=[Depends(get_current_user)],
)
app.include_router(documentRoutes.router, prefix="/api/v1/document", tags=["Document Mgt"], dependencies=[Depends(get_current_user)],)
# app.include_router(walletRoutes.router, prefix="/api/v1/wallet", tags=["Wallet"], dependencies=[Depends(get_current_user)],)
# app.include_router(transactionRoutes.router, prefix="/api/v1/transaction", tags=["Transaction"], dependencies=[Depends(get_current_user)],)
# app.include_router(apiRoutes.router, prefix="/api/v1/api-keys", tags=["API Keys"], dependencies=[Depends(get_current_user)],)
# app.include_router(paystackRoutes.router, prefix="/api/v1/payment-gateway", tags=["PAYMENT"])
# # app.include_router(subscription.router, prefix="/api/v1/subscription", tags=["Subscription"], dependencies=[Depends(get_current_user)],)
# # app.include_router(ipRoutes.router, prefix="/api/v1/ip", tags=["User IP"])

 # Import and include routers

# app.include_router(v1Router)


