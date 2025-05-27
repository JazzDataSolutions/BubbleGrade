from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from .presentation.routers import scans_router, exports_router, health_router, websocket_router
from .infrastructure.database import db_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="BubbleGrade API",
    version="2.0.0",
    description="Advanced Microservices OMR System with Clean Architecture"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(scans_router)
app.include_router(exports_router)
app.include_router(health_router)
app.include_router(websocket_router)


@app.on_event("startup")
async def startup():
    """Application startup event"""
    logger.info("🚀 BubbleGrade API v2.0 starting up...")
    logger.info("📊 Built with Clean Architecture and SOLID principles")
    logger.info(f"🗄️ Database URL: {db_config.database_url}")


@app.on_event("shutdown")
async def shutdown():
    """Application shutdown event"""
    logger.info("🛑 BubbleGrade API shutting down...")
    await db_config.close()


# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "BubbleGrade API v2.0",
        "description": "Advanced Microservices OMR System",
        "architecture": "Clean Architecture with SOLID principles",
        "docs": "/docs"
    }