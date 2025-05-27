from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..infrastructure.database import db_config
from ..infrastructure.repositories import SQLAlchemyScanRepository
from ..infrastructure.external_services import (
    HttpOMRService,
    LocalFileStorageService,
    OpenpyxlExcelExportService
)
from ..infrastructure.websocket_manager import FastAPIWebSocketService
from ..application.use_cases import ScanUseCases, ExportUseCases, HealthCheckUseCases
from ..domain.repositories import ScanRepository
from ..domain.services import OMRService, WebSocketService, ExcelExportService, FileStorageService


# Database dependency
async def get_database_session() -> AsyncSession:
    async with db_config.async_session() as session:
        yield session


# Repository dependencies
def get_scan_repository(session: AsyncSession = Depends(get_database_session)) -> ScanRepository:
    return SQLAlchemyScanRepository(session)


# Service dependencies
def get_omr_service() -> OMRService:
    return HttpOMRService()


def get_file_storage_service() -> FileStorageService:
    return LocalFileStorageService()


def get_excel_export_service() -> ExcelExportService:
    return OpenpyxlExcelExportService()


# Global WebSocket service instance (singleton)
_websocket_service = FastAPIWebSocketService()


def get_websocket_service() -> WebSocketService:
    return _websocket_service


# Use case dependencies
def get_scan_use_cases(
    scan_repository: ScanRepository = Depends(get_scan_repository),
    omr_service: OMRService = Depends(get_omr_service),
    websocket_service: WebSocketService = Depends(get_websocket_service),
    file_storage_service: FileStorageService = Depends(get_file_storage_service)
) -> ScanUseCases:
    return ScanUseCases(scan_repository, omr_service, websocket_service, file_storage_service)


def get_export_use_cases(
    scan_repository: ScanRepository = Depends(get_scan_repository),
    excel_export_service: ExcelExportService = Depends(get_excel_export_service)
) -> ExportUseCases:
    return ExportUseCases(scan_repository, excel_export_service)


def get_health_check_use_cases(
    scan_repository: ScanRepository = Depends(get_scan_repository)
) -> HealthCheckUseCases:
    return HealthCheckUseCases(scan_repository)