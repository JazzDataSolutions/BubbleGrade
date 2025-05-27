from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from enum import Enum


class ScanStatus(Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"


@dataclass
class Scan:
    id: UUID
    filename: str
    status: ScanStatus
    upload_time: datetime
    score: Optional[int] = None
    answers: Optional[List[str]] = None
    total_questions: Optional[int] = None
    processed_time: Optional[datetime] = None
    error_message: Optional[str] = None

    def is_completed(self) -> bool:
        return self.status == ScanStatus.COMPLETED

    def is_processing(self) -> bool:
        return self.status == ScanStatus.PROCESSING

    def mark_as_processing(self) -> None:
        self.status = ScanStatus.PROCESSING

    def mark_as_completed(self, score: int, answers: List[str], total_questions: int) -> None:
        self.status = ScanStatus.COMPLETED
        self.score = score
        self.answers = answers
        self.total_questions = total_questions
        self.processed_time = datetime.utcnow()

    def mark_as_error(self, error_message: str) -> None:
        self.status = ScanStatus.ERROR
        self.error_message = error_message


@dataclass
class OMRResult:
    score: int
    answers: List[str]
    total_questions: int


@dataclass
class WebSocketMessage:
    type: str
    scan_id: str
    status: str
    score: Optional[int] = None
    answers: Optional[List[str]] = None
    error: Optional[str] = None