from typing import List
from uuid import UUID, uuid4
from datetime import datetime
import logging

from ..domain.entities import Scan, ScanStatus, OMRResult, WebSocketMessage
from ..domain.repositories import ScanRepository
from ..domain.services import OMRService, WebSocketService, ExcelExportService, FileStorageService

logger = logging.getLogger(__name__)


class ScanUseCases:
    def __init__(
        self,
        scan_repository: ScanRepository,
        omr_service: OMRService,
        websocket_service: WebSocketService,
        file_storage_service: FileStorageService
    ):
        self.scan_repository = scan_repository
        self.omr_service = omr_service
        self.websocket_service = websocket_service
        self.file_storage_service = file_storage_service

    async def create_scan(self, filename: str, file_content: bytes) -> Scan:
        """Create a new scan and initiate processing"""
        scan_id = uuid4()
        scan = Scan(
            id=scan_id,
            filename=filename,
            status=ScanStatus.QUEUED,
            upload_time=datetime.utcnow()
        )
        
        # Save to database
        created_scan = await self.scan_repository.create(scan)
        
        # Save file for processing
        file_path = await self.file_storage_service.save_upload(file_content, filename)
        
        # Start background processing (this would be done via task queue in production)
        await self._process_scan_async(created_scan, file_path)
        
        return created_scan

    async def get_scan_by_id(self, scan_id: UUID) -> Scan:
        """Get scan by ID"""
        scan = await self.scan_repository.get_by_id(scan_id)
        if not scan:
            raise ValueError(f"Scan with ID {scan_id} not found")
        return scan

    async def get_all_scans(self) -> List[Scan]:
        """Get all scans"""
        return await self.scan_repository.get_all()

    async def _process_scan_async(self, scan: Scan, file_path: str) -> None:
        """Process scan asynchronously"""
        try:
            # Update status to processing
            scan.mark_as_processing()
            await self.scan_repository.update(scan)
            
            # Notify via WebSocket
            await self.websocket_service.broadcast_message(
                WebSocketMessage(
                    type="scan_update",
                    scan_id=str(scan.id),
                    status=scan.status.value
                )
            )
            
            # Process with OMR service
            result = await self.omr_service.process_image(file_path, scan.filename)
            
            # Update scan with results
            scan.mark_as_completed(result.score, result.answers, result.total_questions)
            await self.scan_repository.update(scan)
            
            # Notify completion via WebSocket
            await self.websocket_service.broadcast_message(
                WebSocketMessage(
                    type="scan_complete",
                    scan_id=str(scan.id),
                    status=scan.status.value,
                    score=scan.score,
                    answers=scan.answers
                )
            )
            
            logger.info(f"Scan {scan.id} completed successfully with score {scan.score}")
            
        except Exception as e:
            logger.error(f"Error processing scan {scan.id}: {e}")
            
            # Update scan with error
            scan.mark_as_error(str(e))
            await self.scan_repository.update(scan)
            
            # Notify error via WebSocket
            await self.websocket_service.broadcast_message(
                WebSocketMessage(
                    type="scan_error",
                    scan_id=str(scan.id),
                    status=scan.status.value,
                    error=str(e)
                )
            )
            
        finally:
            # Clean up temporary file
            await self.file_storage_service.delete_file(file_path)


class ExportUseCases:
    def __init__(
        self,
        scan_repository: ScanRepository,
        excel_export_service: ExcelExportService
    ):
        self.scan_repository = scan_repository
        self.excel_export_service = excel_export_service

    async def export_scan_to_excel(self, scan_id: UUID) -> tuple[bytes, str]:
        """Export scan results to Excel format"""
        scan = await self.scan_repository.get_by_id(scan_id)
        if not scan:
            raise ValueError(f"Scan with ID {scan_id} not found")
        
        if not scan.is_completed():
            raise ValueError("Scan is not completed yet")
        
        # Hardcoded correct answers for demo (would be configurable in real app)
        correct_answers = ["A", "B", "C", "D", "A", "B", "C", "D", "A", "B"]
        
        excel_data = await self.excel_export_service.create_report(
            scan_id=str(scan_id),
            filename=scan.filename,
            score=scan.score,
            answers=scan.answers,
            correct_answers=correct_answers
        )
        
        filename = f"{scan.filename}_{scan_id}_results.xlsx"
        return excel_data, filename


class HealthCheckUseCases:
    def __init__(self, scan_repository: ScanRepository):
        self.scan_repository = scan_repository

    async def check_database_health(self) -> dict:
        """Check if database connection is healthy"""
        try:
            # Try to get any scan to test database connection
            await self.scan_repository.get_all()
            return {"status": "healthy", "service": "api", "database": "connected"}
        except Exception as e:
            return {"status": "unhealthy", "service": "api", "database": "disconnected", "error": str(e)}