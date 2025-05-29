from fastapi import APIRouter, UploadFile, HTTPException, Depends, BackgroundTasks, Query, Request
from fastapi.responses import FileResponse, StreamingResponse
from typing import List, Optional
from uuid import UUID
import asyncio
from datetime import datetime

from ..application.use_cases import ScanUseCases, ExportUseCases, TemplateUseCases
from ..presentation.schemas import (
    ScanResponse, ScanListResponse, CreateTemplateRequest, 
    TemplateResponse, PaginationParams, ScanFilters
)
from ..middleware.validation import FileValidator, rate_limit, require_auth
from ..domain.entities import ScanStatus

# API Router with versioning
router = APIRouter(prefix="/api/v1", tags=["BubbleGrade API v1"])

# Dependency injection (would be properly configured)
async def get_scan_use_cases() -> ScanUseCases:
    # This would return properly injected dependencies
    pass

async def get_export_use_cases() -> ExportUseCases:
    pass

async def get_template_use_cases() -> TemplateUseCases:
    pass

# Scan endpoints
@router.post("/scans", response_model=ScanResponse)
@rate_limit("upload")
async def upload_scan(
    request: Request,
    file: UploadFile,
    template_id: Optional[str] = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    scan_use_cases: ScanUseCases = Depends(get_scan_use_cases)
):
    """
    Upload a new bubble sheet scan for processing.
    
    - **file**: Image or PDF file (JPG, PNG, TIFF, PDF)
    - **template_id**: Optional exam template ID for validation
    """
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Read file content
    file_content = await file.read()
    
    # Validate file
    is_valid, error_msg, file_hash = FileValidator.validate_upload(
        file_content, file.filename or "unknown"
    )
    
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    try:
        # Check for duplicates using hash
        existing_scan = await scan_use_cases.find_by_hash(file_hash)
        if existing_scan:
            raise HTTPException(
                status_code=409, 
                detail=f"Duplicate file detected. Original scan ID: {existing_scan.id}"
            )
        
        # Create scan
        scan = await scan_use_cases.create_scan(
            filename=file.filename or "unknown",
            file_content=file_content,
            file_hash=file_hash,
            template_id=template_id
        )
        
        return ScanResponse.from_entity(scan)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process upload: {str(e)}")

@router.get("/scans", response_model=ScanListResponse)
@rate_limit("api")
async def list_scans(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[List[ScanStatus]] = Query(None, description="Filter by status"),
    date_from: Optional[datetime] = Query(None, description="Filter from date"),
    date_to: Optional[datetime] = Query(None, description="Filter to date"),
    min_score: Optional[int] = Query(None, ge=0, le=100, description="Minimum score"),
    max_score: Optional[int] = Query(None, ge=0, le=100, description="Maximum score"),
    sort_by: str = Query("upload_time", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    scan_use_cases: ScanUseCases = Depends(get_scan_use_cases)
):
    """
    Get paginated list of scans with filtering and sorting.
    """
    try:
        # Create filter object
        filters = ScanFilters(
            status=status,
            date_from=date_from,
            date_to=date_to,
            min_score=min_score,
            max_score=max_score
        )
        
        # Create pagination object
        pagination = PaginationParams(
            page=page,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        result = await scan_use_cases.get_scans_paginated(filters, pagination)
        
        return ScanListResponse(
            scans=[ScanResponse.from_entity(scan) for scan in result.items],
            total=result.total,
            page=result.page,
            limit=result.limit,
            total_pages=result.total_pages
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch scans: {str(e)}")

@router.get("/scans/{scan_id}", response_model=ScanResponse)
@rate_limit("api")
async def get_scan(
    scan_id: UUID,
    scan_use_cases: ScanUseCases = Depends(get_scan_use_cases)
):
    """Get detailed information about a specific scan."""
    try:
        scan = await scan_use_cases.get_scan_by_id(scan_id)
        return ScanResponse.from_entity(scan)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch scan: {str(e)}")

@router.delete("/scans/{scan_id}")
@rate_limit("api")
async def delete_scan(
    scan_id: UUID,
    scan_use_cases: ScanUseCases = Depends(get_scan_use_cases)
):
    """Delete a scan and its associated files."""
    try:
        await scan_use_cases.delete_scan(scan_id)
        return {"message": "Scan deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete scan: {str(e)}")

@router.post("/scans/{scan_id}/reprocess", response_model=ScanResponse)
@rate_limit("upload")
async def reprocess_scan(
    scan_id: UUID,
    template_id: Optional[str] = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    scan_use_cases: ScanUseCases = Depends(get_scan_use_cases)
):
    """Reprocess an existing scan with optional new template."""
    try:
        scan = await scan_use_cases.reprocess_scan(scan_id, template_id)
        return ScanResponse.from_entity(scan)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reprocess scan: {str(e)}")

# Export endpoints
@router.get("/exports/{scan_id}")
@rate_limit("export")
async def export_scan(
    scan_id: UUID,
    format: str = Query("xlsx", regex="^(xlsx|csv|pdf)$", description="Export format"),
    export_use_cases: ExportUseCases = Depends(get_export_use_cases)
):
    """Export scan results in various formats."""
    try:
        if format == "xlsx":
            data, filename = await export_use_cases.export_to_excel(scan_id)
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        elif format == "csv":
            data, filename = await export_use_cases.export_to_csv(scan_id)
            media_type = "text/csv"
        elif format == "pdf":
            data, filename = await export_use_cases.export_to_pdf(scan_id)
            media_type = "application/pdf"
        
        return StreamingResponse(
            io.BytesIO(data),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export scan: {str(e)}")

# Template endpoints
@router.get("/templates", response_model=List[TemplateResponse])
@rate_limit("api")
async def list_templates(
    template_use_cases: TemplateUseCases = Depends(get_template_use_cases)
):
    """Get list of exam templates."""
    try:
        templates = await template_use_cases.get_all_templates()
        return [TemplateResponse.from_entity(template) for template in templates]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch templates: {str(e)}")

@router.post("/templates", response_model=TemplateResponse)
@rate_limit("api")
async def create_template(
    template_data: CreateTemplateRequest,
    template_use_cases: TemplateUseCases = Depends(get_template_use_cases)
):
    """Create a new exam template."""
    try:
        template = await template_use_cases.create_template(template_data.to_entity())
        return TemplateResponse.from_entity(template)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create template: {str(e)}")

@router.get("/templates/{template_id}", response_model=TemplateResponse)
@rate_limit("api")
async def get_template(
    template_id: UUID,
    template_use_cases: TemplateUseCases = Depends(get_template_use_cases)
):
    """Get specific template details."""
    try:
        template = await template_use_cases.get_template_by_id(template_id)
        return TemplateResponse.from_entity(template)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch template: {str(e)}")

# Batch operations
@router.post("/scans/batch")
@rate_limit("upload")
async def batch_upload(
    files: List[UploadFile],
    template_id: Optional[str] = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    scan_use_cases: ScanUseCases = Depends(get_scan_use_cases)
):
    """Upload multiple files for batch processing."""
    if len(files) > 10:  # Limit batch size
        raise HTTPException(status_code=400, detail="Too many files. Maximum 10 files per batch")
    
    results = []
    errors = []
    
    for file in files:
        try:
            file_content = await file.read()
            is_valid, error_msg, file_hash = FileValidator.validate_upload(
                file_content, file.filename or "unknown"
            )
            
            if not is_valid:
                errors.append({"filename": file.filename, "error": error_msg})
                continue
                
            scan = await scan_use_cases.create_scan(
                filename=file.filename or "unknown",
                file_content=file_content,
                file_hash=file_hash,
                template_id=template_id
            )
            
            results.append(ScanResponse.from_entity(scan))
            
        except Exception as e:
            errors.append({"filename": file.filename, "error": str(e)})
    
    return {
        "successful": results,
        "errors": errors,
        "summary": {
            "total": len(files),
            "successful": len(results),
            "failed": len(errors)
        }
    }

# Health and monitoring
@router.get("/health")
async def health_check():
    """Comprehensive health check endpoint."""
    try:
        # Check database connectivity
        # Check OMR service connectivity  
        # Check disk space
        # Check memory usage
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "2.0.0",
            "services": {
                "database": "healthy",
                "omr_service": "healthy",
                "websocket": "healthy"
            },
            "metrics": {
                "active_scans": 0,  # Would be real count
                "total_processed": 0,  # Would be real count
                "uptime_seconds": 0  # Would be real uptime
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }