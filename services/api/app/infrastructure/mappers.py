from ..domain.entities import Scan, ScanStatus
from .database import ScanModel


class ScanMapper:
    @staticmethod
    def to_entity(model: ScanModel) -> Scan:
        """Convert SQLAlchemy model to domain entity"""
        return Scan(
            id=model.id,
            filename=model.filename,
            status=ScanStatus(model.status),
            upload_time=model.upload_time,
            score=model.score,
            answers=model.answers,
            total_questions=model.total_questions,
            processed_time=model.processed_time,
            error_message=model.error_message
        )

    @staticmethod
    def to_model(entity: Scan) -> ScanModel:
        """Convert domain entity to SQLAlchemy model"""
        return ScanModel(
            id=entity.id,
            filename=entity.filename,
            status=entity.status.value,
            score=entity.score,
            answers=entity.answers,
            total_questions=entity.total_questions,
            upload_time=entity.upload_time,
            processed_time=entity.processed_time,
            error_message=entity.error_message
        )