"""
BubbleGrade FastAPI - Orchestration service for OMR + OCR processing
Handles image preprocessing, region detection, and coordinates microservices
"""

import asyncio
import cv2
import numpy as np
import httpx
import aiofiles
from fastapi import FastAPI, UploadFile, HTTPException, BackgroundTasks, Depends, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select, update
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
import json
import logging
import os
from uuid import uuid4

from .domain.entities import ProcessedScan, ScanStatus, RegionBoundingBox
from .infrastructure.database import ProcessedScanModel, TemplateModel
from .infrastructure.repositories import ProcessedScanRepository
from .services.image_processing import ImageProcessor
from .services.microservice_client import MicroserviceClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="BubbleGrade API", version="2.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://omr:omr@db/omr")
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)

# Service URLs
OMR_SERVICE_URL = os.getenv("OMR_URL", "http://omr:8090")
OCR_SERVICE_URL = os.getenv("OCR_URL", "http://ocr:8100")

# Initialize services
image_processor = ImageProcessor()
microservice_client = MicroserviceClient(
    omr_url=OMR_SERVICE_URL,
    ocr_url=OCR_SERVICE_URL,
    timeout=60.0
)

async def get_scan_repository() -> ProcessedScanRepository:
    """Dependency injection for scan repository"""
    return ProcessedScanRepository(async_session)

class DocumentOrchestrator:
    """Orchestrates the complete document processing pipeline"""
    
    def __init__(self):
        self.omr_client = microservice_client
        self.image_processor = image_processor

    async def process_document(
        self,
        scan_id: str,
        file_content: bytes,
        filename: str,
        scan_repository: ProcessedScanRepository
    ) -> ProcessedScan:
        """
        Complete document processing pipeline:
        1. Image preprocessing and quality analysis
        2. Region detection and segmentation  
        3. Parallel OMR and OCR processing
        4. Results validation and storage
        """
        # scan_id provided by caller
        
        try:
            # Create initial scan record
            scan = ProcessedScan(
                id=scan_id,
                filename=filename,
                status=ScanStatus.PROCESSING,
                upload_time=datetime.utcnow()
            )
            await scan_repository.create(scan)

            # Step 1: Preprocess image and detect regions
            logger.info(f"Starting image preprocessing for scan {scan_id}")
            processed_image, regions = await self._preprocess_and_detect_regions(file_content)
            
            # Update scan with detected regions
            scan.regions = regions
            await scan_repository.update(scan)

            # Step 2: Extract region images (for optional use)
            # region_images = await self._extract_region_images(processed_image, regions)

            # Step 3: Unified OMR + OCR processing via local module
            from .omr_ocr import grade_scan
            logger.info(f"Starting unified OMR/OCR processing for scan {scan_id}")
            merged_result = await asyncio.get_running_loop().run_in_executor(
                None, grade_scan, processed_image, regions
            )

            omr_result = {
                'score': merged_result.get('score', 0),
                'answers': merged_result.get('answers', []),
                'total': merged_result.get('total', 0)
            }
            nombre_result = {
                'text': merged_result.get('nombre_text', '').strip(),
                'confidence': merged_result.get('nombre_confidence', 0.0)
            }
            curp_result = {
                'text': merged_result.get('curp_text', '').strip(),
                'confidence': merged_result.get('curp_confidence', 0.0)
            }

            # Step 4: Validate and update scan results
            scan = await self._finalize_scan_results(
                scan, omr_result, nombre_result, curp_result, scan_repository
            )

            logger.info(f"Document processing completed for scan {scan_id}")
            return scan

        except Exception as e:
            logger.error(f"Document processing failed for scan {scan_id}: {e}")
            # Update scan status to error
            scan.status = ScanStatus.ERROR
            scan.error_message = str(e)
            await scan_repository.update(scan)
            raise

    async def _preprocess_and_detect_regions(
        self, 
        file_content: bytes
    ) -> tuple[np.ndarray, Dict[str, RegionBoundingBox]]:
        """Preprocess image and detect document regions using OpenCV"""
        
        # Decode image
        nparr = np.frombuffer(file_content, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise ValueError("Failed to decode image")

        # Step 1: Image quality enhancement
        processed = await self.image_processor.enhance_document_image(image)
        
        # Step 2: Detect document regions
        regions = await self.image_processor.detect_document_regions(processed)
        
        return processed, regions

    async def _extract_region_images(
        self, 
        image: np.ndarray, 
        regions: Dict[str, RegionBoundingBox]
    ) -> Dict[str, np.ndarray]:
        """Extract individual region images from the main document"""
        
        region_images = {'original': image}
        
        for region_name, bbox in regions.items():
            if region_name == 'omr':
                continue  # OMR uses full image
                
            # Extract region with padding
            x, y, w, h = bbox.x, bbox.y, bbox.width, bbox.height
            padding = 10  # Add padding for better OCR
            
            x_start = max(0, x - padding)
            y_start = max(0, y - padding)
            x_end = min(image.shape[1], x + w + padding)
            y_end = min(image.shape[0], y + h + padding)
            
            region_img = image[y_start:y_end, x_start:x_end]
            
            # Additional preprocessing for OCR
            if region_name == 'nombre':
                region_img = await self.image_processor.optimize_for_handwriting(region_img)
            elif region_name == 'curp':
                region_img = await self.image_processor.optimize_for_print_text(region_img)
            
            region_images[region_name] = region_img
            
        return region_images

    async def _process_omr(
        self, 
        image: np.ndarray, 
        regions: Dict[str, RegionBoundingBox]
    ) -> Dict[str, Any]:
        """Process OMR section using Go microservice"""
        
        # Encode image as JPEG for transmission
        _, buffer = cv2.imencode('.jpg', image)
        image_bytes = buffer.tobytes()
        
        # Call OMR service
        result = await self.omr_client.process_omr(image_bytes, 'processed_image.jpg')
        return result

    async def _process_ocr_region(
        self, 
        region_image: np.ndarray, 
        region_type: str,
        bbox: RegionBoundingBox
    ) -> Dict[str, Any]:
        """Process individual OCR region using Node.js microservice"""
        
        # Encode region image
        _, buffer = cv2.imencode('.jpg', region_image)
        image_bytes = buffer.tobytes()
        
        # Prepare OCR request
        ocr_request = {
            'region': region_type,
            'boundingBox': {
                'x': bbox.x,
                'y': bbox.y,
                'width': bbox.width,
                'height': bbox.height
            },
            'preprocessing': {
                'denoise': True,
                'sharpen': region_type == 'curp',  # Sharpen for printed CURP
                'contrast': 1.2 if region_type == 'nombre' else 1.0,
                'brightness': 0.1 if region_type == 'nombre' else 0.0
            }
        }
        
        # Call OCR service
        result = await self.omr_client.process_ocr(image_bytes, ocr_request)
        return result

    async def _finalize_scan_results(
        self,
        scan: ProcessedScan,
        omr_result: Dict[str, Any],
        nombre_result: Dict[str, Any],
        curp_result: Dict[str, Any],
        repository: ProcessedScanRepository
    ) -> ProcessedScan:
        """Finalize scan with all processing results"""
        
        # Update OMR results
        scan.score = omr_result.get('score', 0)
        scan.answers = omr_result.get('answers', [])
        scan.total_questions = omr_result.get('total', 0)
        
        # Update OCR results
        scan.nombre = {
            'value': nombre_result.get('text', '').strip(),
            'confidence': nombre_result.get('confidence', 0.0),
            'needsReview': nombre_result.get('confidence', 0.0) < 0.8,
            'correctedBy': None,
            'correctedAt': None
        }
        
        scan.curp = {
            'value': curp_result.get('text', '').strip(),
            'confidence': curp_result.get('confidence', 0.0),
            'needsReview': curp_result.get('confidence', 0.0) < 0.9 or not self._is_valid_curp_format(curp_result.get('text', '')),
            'correctedBy': None,
            'correctedAt': None
        }
        
        # Update image quality metrics
        scan.image_quality = omr_result.get('quality', {})
        
        # Determine final status
        needs_review = (
            scan.nombre['needsReview'] or 
            scan.curp['needsReview'] or
            scan.score == 0
        )
        
        scan.status = ScanStatus.NEEDS_REVIEW if needs_review else ScanStatus.COMPLETED
        scan.processed_time = datetime.utcnow()
        
        # Save final results
        await repository.update(scan)
        return scan

    def _is_valid_curp_format(self, curp: str) -> bool:
        """Basic CURP format validation"""
        import re
        curp_pattern = r'^[A-Z]{4}\d{6}[HM][A-Z]{5}\d{2}$'
        return bool(re.match(curp_pattern, curp.strip()))

# Initialize orchestrator
orchestrator = DocumentOrchestrator()

# API Endpoints
# ----------------
class TemplateCreate(BaseModel):
    name: str
    description: str
    total_questions: int
    correct_answers: List[str]

class TemplateResponse(BaseModel):
    id: str
    name: str
    description: str
    total_questions: int
    correct_answers: List[str]

@app.post("/api/v1/templates", response_model=TemplateResponse)
async def create_template(
    template: TemplateCreate
):
    """Create a new exam template"""
    async with async_session() as session:
        tm = TemplateModel(
            name=template.name,
            description=template.description,
            total_questions=template.total_questions,
            correct_answers=template.correct_answers
        )
        session.add(tm)
        await session.commit()
        await session.refresh(tm)
        return TemplateResponse(
            id=str(tm.id),
            name=tm.name,
            description=tm.description,
            total_questions=tm.total_questions,
            correct_answers=tm.correct_answers
        )

@app.get("/api/v1/templates", response_model=List[TemplateResponse])
async def list_templates():
    """List all exam templates"""
    async with async_session() as session:
        result = await session.execute(select(TemplateModel))
        tms = result.scalars().all()
        return [
            TemplateResponse(
                id=str(tm.id),
                name=tm.name,
                description=tm.description,
                total_questions=tm.total_questions,
                correct_answers=tm.correct_answers
            ) for tm in tms
        ]
@app.post("/api/v1/scans", response_model=dict)
async def upload_scan(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    template_id: Optional[str] = Form(None),
    repository: ProcessedScanRepository = Depends(get_scan_repository)
):
    """Upload and process a document scan"""
    
    if not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=400, 
            detail="Invalid file type. Only images are supported."
        )
    
    try:
        # Generate scan identifier
        scan_id = str(uuid4())
        # Read file content
        file_content = await file.read()
        
        if len(file_content) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(
                status_code=400,
                detail="File too large. Maximum size is 10MB."
            )
        
        # Start background processing with provided scan_id
        background_tasks.add_task(
            orchestrator.process_document,
            scan_id,
            file_content,
            file.filename or "unknown.jpg",
            repository
        )
        return {
            "id": scan_id,
            "message": "Document uploaded successfully and processing started",
            "filename": file.filename,
            "status": "PROCESSING"
        }
        
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/api/v1/scans")
async def list_scans(
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    repository: ProcessedScanRepository = Depends(get_scan_repository)
):
    """List processed scans with optional filtering and pagination"""
    # Retrieve all scans
    all_scans = await repository.get_all()
    # Optional status filtering
    if status:
        all_scans = [s for s in all_scans if s.status.value == status]
    total = len(all_scans)
    # Apply pagination
    sliced = all_scans[offset: offset + limit]
    return {
        "scans": [scan.to_dict() for scan in sliced],
        "total": total,
        "limit": limit,
        "offset": offset
    }

@app.get("/api/v1/scans/{scan_id}")
async def get_scan(
    scan_id: str,
    repository: ProcessedScanRepository = Depends(get_scan_repository)
):
    """Get detailed scan information"""
    
    scan = await repository.get_by_id(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    return scan.to_dict()

@app.patch("/api/v1/scans/{scan_id}")
async def update_scan(
    scan_id: str,
    updates: dict,
    repository: ProcessedScanRepository = Depends(get_scan_repository)
):
    """Update scan data (for manual corrections)"""
    
    scan = await repository.get_by_id(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    # Apply manual corrections
    if 'nombre' in updates:
        scan.nombre.update(updates['nombre'])
        scan.nombre['correctedBy'] = 'user'  # Would be actual user ID
        scan.nombre['correctedAt'] = datetime.utcnow().isoformat()
        
    if 'curp' in updates:
        scan.curp.update(updates['curp'])
        scan.curp['correctedBy'] = 'user'
        scan.curp['correctedAt'] = datetime.utcnow().isoformat()
    
    # Update status if all corrections are complete
    if not scan.nombre.get('needsReview') and not scan.curp.get('needsReview'):
        scan.status = ScanStatus.COMPLETED
    
    await repository.update(scan)
    return scan.to_dict()

@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    # Check database connectivity
    try:
        async with async_session() as session:
            await session.execute(select(1))
        return {"status": "healthy"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)