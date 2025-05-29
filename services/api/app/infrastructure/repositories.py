from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from ..domain.entities import Scan, ScanStatus
from ..domain.repositories import ScanRepository
from .database import ScanModel
from .mappers import ScanMapper


class SQLAlchemyScanRepository(ScanRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, scan: Scan) -> Scan:
        scan_model = ScanMapper.to_model(scan)
        self.session.add(scan_model)
        await self.session.commit()
        await self.session.refresh(scan_model)
        return ScanMapper.to_entity(scan_model)

    async def get_by_id(self, scan_id: UUID) -> Optional[Scan]:
        result = await self.session.execute(
            select(ScanModel).where(ScanModel.id == scan_id)
        )
        scan_model = result.scalar_one_or_none()
        return ScanMapper.to_entity(scan_model) if scan_model else None

    async def get_all(self) -> List[Scan]:
        result = await self.session.execute(
            select(ScanModel).order_by(ScanModel.upload_time.desc())
        )
        scan_models = result.scalars().all()
        return [ScanMapper.to_entity(model) for model in scan_models]

    async def update(self, scan: Scan) -> Scan:
        # Update basic and enriched fields
        await self.session.execute(
            update(ScanModel)
            .where(ScanModel.id == scan.id)
            .values(
                status=scan.status.value,
                score=scan.score,
                answers=scan.answers,
                total_questions=scan.total_questions,
                processed_time=scan.processed_time,
                error_message=scan.error_message,
                regions=getattr(scan, 'regions', None),
                nombre=getattr(scan, 'nombre', None),
                curp=getattr(scan, 'curp', None),
                image_quality=getattr(scan, 'image_quality', None)
            )
        )
        await self.session.commit()
        return scan

    async def delete(self, scan_id: UUID) -> bool:
        result = await self.session.execute(
            select(ScanModel).where(ScanModel.id == scan_id)
        )
        scan_model = result.scalar_one_or_none()
        if scan_model:
            await self.session.delete(scan_model)
            await self.session.commit()
            return True
        return False
    
# Alias for v2 orchestrator
ProcessedScanRepository = SQLAlchemyScanRepository