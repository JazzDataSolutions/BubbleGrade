from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from .entities import Scan


class ScanRepository(ABC):
    @abstractmethod
    async def create(self, scan: Scan) -> Scan:
        """Create a new scan record"""
        pass

    @abstractmethod
    async def get_by_id(self, scan_id: UUID) -> Optional[Scan]:
        """Get scan by ID"""
        pass

    @abstractmethod
    async def get_all(self) -> List[Scan]:
        """Get all scans ordered by upload time"""
        pass

    @abstractmethod
    async def update(self, scan: Scan) -> Scan:
        """Update scan record"""
        pass

    @abstractmethod
    async def delete(self, scan_id: UUID) -> bool:
        """Delete scan record"""
        pass