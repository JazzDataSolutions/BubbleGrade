from abc import ABC, abstractmethod
from typing import List

from .entities import OMRResult, WebSocketMessage


class OMRService(ABC):
    @abstractmethod
    async def process_image(self, file_path: str, filename: str) -> OMRResult:
        """Process bubble sheet image and return results"""
        pass


class WebSocketService(ABC):
    @abstractmethod
    async def broadcast_message(self, message: WebSocketMessage) -> None:
        """Broadcast message to all connected WebSocket clients"""
        pass

    @abstractmethod
    async def connect_client(self, websocket) -> None:
        """Add new WebSocket connection"""
        pass

    @abstractmethod
    def disconnect_client(self, websocket) -> None:
        """Remove WebSocket connection"""
        pass


class ExcelExportService(ABC):
    @abstractmethod
    async def create_report(self, scan_id: str, filename: str, score: int, 
                           answers: List[str], correct_answers: List[str]) -> bytes:
        """Generate Excel report for scan results"""
        pass


class FileStorageService(ABC):
    @abstractmethod
    async def save_upload(self, file_content: bytes, filename: str) -> str:
        """Save uploaded file and return file path"""
        pass

    @abstractmethod
    async def delete_file(self, file_path: str) -> None:
        """Delete temporary file"""
        pass