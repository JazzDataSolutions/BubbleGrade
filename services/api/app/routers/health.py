from fastapi import APIRouter
from sqlalchemy import select
from fastapi import HTTPException

from ..main_bubblegrade import async_session, logger

router = APIRouter()

@router.get("/health")
async def health_check():
    """Comprehensive health check: database connectivity (best-effort)"""
    try:
        async with async_session() as session:
            await session.execute(select(1))
    except Exception as e:
        logger.warning(f"Health check: DB unreachable: {e}")
    return {"status": "healthy"}