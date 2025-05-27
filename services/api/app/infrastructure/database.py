from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import DateTime, String, Integer
from datetime import datetime
from uuid import uuid4
import os


class Base(DeclarativeBase):
    pass


class ScanModel(Base):
    __tablename__ = "scans"
    
    id: Mapped[UUID] = mapped_column(UUID, primary_key=True, default=uuid4)
    filename: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50), default="QUEUED")
    score: Mapped[int] = mapped_column(Integer, nullable=True)
    answers: Mapped[dict] = mapped_column(JSONB, nullable=True)
    total_questions: Mapped[int] = mapped_column(Integer, nullable=True)
    upload_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    processed_time: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[str] = mapped_column(String(500), nullable=True)


class DatabaseConfig:
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://omr:omr@db/omr")
        self.engine = create_async_engine(self.database_url, echo=True)
        self.async_session = async_sessionmaker(self.engine, expire_on_commit=False)

    async def get_session(self) -> AsyncSession:
        async with self.async_session() as session:
            yield session

    async def close(self):
        await self.engine.dispose()


# Global database configuration
db_config = DatabaseConfig()