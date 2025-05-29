"""
Repository interfaces for domain entities.
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from .entities import Scan

class ScanRepository(ABC):
    """Interface for scan persistence operations"""
    @abstractmethod
    async def create(self, scan: Scan) -> Scan:
        ...

    @abstractmethod
    async def get_by_id(self, scan_id: UUID) -> Optional[Scan]:
        ...

    @abstractmethod
    async def get_all(self) -> List[Scan]:
        ...

    @abstractmethod
    async def update(self, scan: Scan) -> Scan:
        ...

    @abstractmethod
    async def delete(self, scan_id: UUID) -> bool:
        ...