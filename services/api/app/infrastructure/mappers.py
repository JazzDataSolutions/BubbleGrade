from ..domain.entities import Scan, ScanStatus
from .database import ScanModel


class ScanMapper:
    @staticmethod
    def to_entity(model: ScanModel) -> Scan:
        """Convert SQLAlchemy model to domain entity"""
        entity = Scan(
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
        # Attach enriched fields if available
        if hasattr(model, 'regions'):
            setattr(entity, 'regions', model.regions)
        if hasattr(model, 'nombre'):
            setattr(entity, 'nombre', model.nombre)
        if hasattr(model, 'curp'):
            setattr(entity, 'curp', model.curp)
        if hasattr(model, 'image_quality'):
            setattr(entity, 'image_quality', model.image_quality)
        return entity

    @staticmethod
    def to_model(entity: Scan) -> ScanModel:
        """Convert domain entity to SQLAlchemy model"""
        model = ScanModel(
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
        # Map enriched fields if present on entity
        if getattr(entity, 'regions', None) is not None:
            model.regions = entity.regions  # type: ignore
        if getattr(entity, 'nombre', None) is not None:
            model.nombre = entity.nombre  # type: ignore
        if getattr(entity, 'curp', None) is not None:
            model.curp = entity.curp  # type: ignore
        if getattr(entity, 'image_quality', None) is not None:
            model.image_quality = entity.image_quality  # type: ignore
        return model