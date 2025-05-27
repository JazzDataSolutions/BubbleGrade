from fastapi import APIRouter, UploadFile, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
from typing import List
from uuid import UUID

from ..application.use_cases import ScanUseCases, ExportUseCases, HealthCheckUseCases
from ..domain.services import WebSocketService
from ..presentation.schemas import ScanResponse, ScanCreateResponse, HealthResponse
from ..presentation.dependencies import (
    get_scan_use_cases,
    get_export_use_cases,
    get_health_check_use_cases,
    get_websocket_service
)

# API Routers
scans_router = APIRouter(prefix="/api/scans", tags=["scans"])
exports_router = APIRouter(prefix="/api/exports", tags=["exports"])
health_router = APIRouter(prefix="/health", tags=["health"])
websocket_router = APIRouter(prefix="/ws", tags=["websocket"])


@scans_router.post("", response_model=ScanCreateResponse)
async def upload_scan(
    file: UploadFile,
    scan_use_cases: ScanUseCases = Depends(get_scan_use_cases)
):
    """Upload and process a new bubble sheet scan"""
    try:
        file_content = await file.read()
        scan = await scan_use_cases.create_scan(file.filename, file_content)
        
        return ScanCreateResponse(
            id=str(scan.id),
            filename=scan.filename,
            status=scan.status.value
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing scan: {str(e)}")


@scans_router.get("", response_model=List[ScanResponse])
async def list_scans(scan_use_cases: ScanUseCases = Depends(get_scan_use_cases)):
    """Get list of all scans"""
    try:
        scans = await scan_use_cases.get_all_scans()
        return [
            ScanResponse(
                id=str(scan.id),
                filename=scan.filename,
                status=scan.status.value,
                score=scan.score,
                answers=scan.answers,
                total_questions=scan.total_questions,
                upload_time=scan.upload_time,
                processed_time=scan.processed_time,
                error_message=scan.error_message
            )
            for scan in scans
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving scans: {str(e)}")


@scans_router.get("/{scan_id}", response_model=ScanResponse)
async def get_scan(
    scan_id: UUID,
    scan_use_cases: ScanUseCases = Depends(get_scan_use_cases)
):
    """Get specific scan by ID"""
    try:
        scan = await scan_use_cases.get_scan_by_id(scan_id)
        return ScanResponse(
            id=str(scan.id),
            filename=scan.filename,
            status=scan.status.value,
            score=scan.score,
            answers=scan.answers,
            total_questions=scan.total_questions,
            upload_time=scan.upload_time,
            processed_time=scan.processed_time,
            error_message=scan.error_message
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving scan: {str(e)}")


@exports_router.get("/{scan_id}")
async def export_scan(
    scan_id: UUID,
    export_use_cases: ExportUseCases = Depends(get_export_use_cases)
):
    """Export scan results as Excel file"""
    try:
        excel_data, filename = await export_use_cases.export_scan_to_excel(scan_id)
        
        return Response(
            content=excel_data,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except ValueError as e:
        raise HTTPException(status_code=404 if "not found" in str(e) else 400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting scan: {str(e)}")


@health_router.get("", response_model=HealthResponse)
async def health_check(
    health_use_cases: HealthCheckUseCases = Depends(get_health_check_use_cases)
):
    """Check API and database health"""
    health_status = await health_use_cases.check_database_health()
    
    if health_status["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=health_status)
    
    return HealthResponse(**health_status)


@websocket_router.websocket("")
async def websocket_endpoint(
    websocket: WebSocket,
    websocket_service: WebSocketService = Depends(get_websocket_service)
):
    """WebSocket endpoint for real-time updates"""
    await websocket_service.connect_client(websocket)
    try:
        while True:
            await websocket.receive_text()  # Keep connection alive
    except WebSocketDisconnect:
        websocket_service.disconnect_client(websocket)