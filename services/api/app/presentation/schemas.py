from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID


class ScanResponse(BaseModel):
    id: str
    filename: str
    status: str
    score: Optional[int] = None
    answers: Optional[List[str]] = None
    total_questions: Optional[int] = None
    upload_time: datetime
    processed_time: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class ScanCreateResponse(BaseModel):
    id: str
    filename: str
    status: str


class HealthResponse(BaseModel):
    status: str
    service: str
    database: str
    error: Optional[str] = None


class ErrorResponse(BaseModel):
    detail: str