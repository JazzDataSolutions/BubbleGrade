# API Documentation

## Overview

The BubbleGrade API is built with FastAPI and provides RESTful endpoints for managing bubble sheet scans, real-time WebSocket communication, and Excel export functionality.

## Base URL

```
http://localhost:8080/api
```

## Authentication

Currently, the API does not require authentication for development purposes. In production, implement proper authentication mechanisms.

## Endpoints

### Upload Scan

**POST** `/api/v1/scans`

Upload a bubble sheet image for processing.

**Request:**
- Content-Type: `multipart/form-data`
- Body: Form data with file field

```bash
curl -X POST "http://localhost:8080/api/v1/scans" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@bubble_sheet.jpg"
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "QUEUED",
  "filename": "bubble_sheet.jpg"
}
```

### List All Scans

**GET** `/api/scans`

Retrieve all scans ordered by upload time (newest first).

**Response:**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "filename": "bubble_sheet.jpg",
    "status": "COMPLETED",
    "score": 85,
    "answers": ["A", "B", "C", "D", "A"],
    "total_questions": 5,
    "upload_time": "2023-12-01T10:30:00",
    "processed_time": "2023-12-01T10:30:15",
    "regions": {
      "omr": {"x": 124, "y": 870, "width": 1800, "height": 2000},
      "nombre": {"x": 200, "y": 50, "width": 1800, "height": 300},
      "curp": {"x": 200, "y": 350, "width": 1800, "height": 300}
    },
    "nombre": {
      "value": "Juan Perez",
      "confidence": 0.92,
      "needsReview": false,
      "correctedBy": null,
      "correctedAt": null
    },
    "curp": {
      "value": "PEPJ800101HMCRRN09",
      "confidence": 0.98,
      "needsReview": false,
      "correctedBy": null,
      "correctedAt": null
    },
    "image_quality": {
      "resolution": {"width": 2480, "height": 3508},
      "clarity": 123.45,
      "skew": 2.5
    }
  }
]
``` 

### Get Specific Scan

**GET** `/api/scans/{scan_id}`

Retrieve details for a specific scan.

**Parameters:**
- `scan_id` (string): UUID of the scan

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "bubble_sheet.jpg",
  "status": "COMPLETED",
  "score": 85,
  "answers": ["A", "B", "C", "D", "A"],
  "total_questions": 5,
  "upload_time": "2023-12-01T10:30:00",
  "processed_time": "2023-12-01T10:30:15",
  "regions": {
    "omr": {"x": 124, "y": 870, "width": 1800, "height": 2000},
    "nombre": {"x": 200, "y": 50, "width": 1800, "height": 300},
    "curp": {"x": 200, "y": 350, "width": 1800, "height": 300}
  },
  "nombre": {
    "value": "Juan Perez",
    "confidence": 0.92,
    "needsReview": false,
    "correctedBy": null,
    "correctedAt": null
  },
  "curp": {
    "value": "PEPJ800101HMCRRN09",
    "confidence": 0.98,
    "needsReview": false,
    "correctedBy": null,
    "correctedAt": null
  },
  "image_quality": {
    "resolution": {"width": 2480, "height": 3508},
    "clarity": 123.45,
    "skew": 2.5
  }
}
``` 

### Export Scan Results

**GET** `/api/exports/{scan_id}`

Download Excel file with detailed scan results.

**Parameters:**
- `scan_id` (string): UUID of the scan

**Response:**
- Content-Type: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- File download with formatted Excel report

### Health Check

**GET** `/health`

Check API and database connectivity.

**Response:**
```json
{
  "status": "healthy",
  "service": "api",
  "database": "connected"
}
```

## WebSocket Communication

### Connection

Connect to the WebSocket endpoint for real-time updates:

```
ws://localhost:8080/ws
```

### Message Types

#### Scan Update
```json
{
  "type": "scan_update",
  "scan_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "PROCESSING"
}
```

#### Scan Complete
```json
{
  "type": "scan_complete",
  "scan_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "COMPLETED",
  "score": 85,
  "answers": ["A", "B", "C", "D", "A"]
}
```

#### Scan Error
```json
{
  "type": "scan_error",
  "scan_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "ERROR",
  "error": "Processing failed: Invalid image format"
}
```

## Status Values

| Status | Description |
|--------|-------------|
| `QUEUED` | Scan uploaded, waiting for processing |
| `PROCESSING` | Currently being processed by OMR service |
| `COMPLETED` | Processing finished successfully |
| `ERROR` | Processing failed due to an error |

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid file format. Supported formats: JPG, PNG"
}
```

### 404 Not Found
```json
{
  "detail": "Scan not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error occurred during processing"
}
```

## Rate Limiting

Currently no rate limiting is implemented. Consider implementing rate limiting for production use.

## CORS Configuration

The API is configured to accept requests from any origin during development. Restrict origins in production:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

## Database Schema

### Scans Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key, auto-generated |
| `filename` | VARCHAR(255) | Original filename |
| `status` | VARCHAR(50) | Current processing status |
| `score` | INTEGER | Final score percentage |
| `answers` | JSONB | Array of detected answers |
| `total_questions` | INTEGER | Number of questions processed |
| `upload_time` | TIMESTAMP | When scan was uploaded |
| `processed_time` | TIMESTAMP | When processing completed |