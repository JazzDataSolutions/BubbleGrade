# Development Setup Guide

## Overview

This guide helps developers set up a local development environment for BubbleGrade, including individual service development and debugging.

## Prerequisites

### Required Software

- **Docker Desktop** 4.0+ with Docker Compose
- **Node.js** 18+ and npm (for frontend development)
- **Python** 3.11+ (for API development)
- **Go** 1.22+ (for OMR service development)
- **PostgreSQL** 16+ (optional, for local database)
- **Git** for version control

### Development Tools (Recommended)

- **VS Code** with extensions:
  - Docker
  - Python
  - Go
  - TypeScript and JavaScript
  - REST Client
- **Postman** or **Insomnia** for API testing
- **pgAdmin** or **DBeaver** for database management

## Quick Development Setup

### 1. Clone and Initialize

```bash
# Clone repository
git clone <repository-url>
cd BubbleGrade

# Start all services in development mode
docker compose -f compose.micro.yml up --build
```

### 2. Verify Setup

```bash
# Check all services are running
docker compose ps

# Test API
curl http://localhost:8080/health

# Test OMR service
curl http://localhost:8090/health

# Visit frontend
open http://localhost:5173
```

## Individual Service Development

### Frontend Development

#### Setup

```bash
cd services/frontend
npm install
```

#### Development Server

```bash
# Start development server with hot reload
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

#### Code Structure

```
services/frontend/
├── src/
│   ├── App.tsx              # Main React component
│   ├── App.css              # Styling and animations
│   ├── main.tsx             # Entry point
│   └── vite-env.d.ts        # TypeScript declarations
├── public/                  # Static assets
├── index.html               # HTML template
├── package.json             # Dependencies and scripts
├── tsconfig.json            # TypeScript configuration
├── vite.config.ts           # Vite configuration
└── Dockerfile               # Container build
```

#### Adding New Features

1. **New Components**
   ```typescript
   // src/components/ScanHistory.tsx
   import React from 'react';
   
   interface ScanHistoryProps {
     scans: ScanResult[];
   }
   
   export const ScanHistory: React.FC<ScanHistoryProps> = ({ scans }) => {
     return (
       <div className="scan-history">
         {scans.map(scan => (
           <div key={scan.id} className="scan-item">
             {scan.filename} - {scan.status}
           </div>
         ))}
       </div>
     );
   };
   ```

2. **Styling**
   ```css
   /* src/components/ScanHistory.css */
   .scan-history {
     display: flex;
     flex-direction: column;
     gap: 1rem;
   }
   
   .scan-item {
     padding: 1rem;
     border-radius: 8px;
     background: rgba(255, 255, 255, 0.1);
   }
   ```

#### Testing

```bash
# Run type checking
npm run type-check

# Run linting
npm run lint

# Run tests (if configured)
npm test
```

### API Development

#### Setup

```bash
cd services/api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### Development Server

```bash
# Start with hot reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080

# With debug logging
LOG_LEVEL=DEBUG uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

#### Code Structure

```
services/api/
├── app/
│   ├── main.py              # FastAPI application
│   ├── models.py            # Database models (optional)
│   ├── schemas.py           # Pydantic schemas (optional)
│   └── utils.py             # Utility functions (optional)
├── requirements.txt         # Python dependencies
├── Dockerfile               # Container build
└── tests/                   # Test files
    ├── test_main.py
    └── test_api.py
```

#### Adding New Endpoints

```python
# app/main.py
@app.get("/api/stats")
async def get_statistics():
    async with async_session() as session:
        total_scans = await session.execute(
            select(func.count(Scan.id))
        )
        completed_scans = await session.execute(
            select(func.count(Scan.id)).where(Scan.status == "COMPLETED")
        )
        
        return {
            "total_scans": total_scans.scalar(),
            "completed_scans": completed_scans.scalar(),
            "success_rate": completed_scans.scalar() / total_scans.scalar() * 100
        }
```

#### Database Operations

```python
# Database migration example
async def create_new_table():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Query examples
async def get_recent_scans(limit: int = 10):
    async with async_session() as session:
        result = await session.execute(
            select(Scan)
            .where(Scan.status == "COMPLETED")
            .order_by(Scan.processed_time.desc())
            .limit(limit)
        )
        return result.scalars().all()
```

#### Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html
```

### OMR Service Development

#### Setup

```bash
cd services/omr

# Download dependencies
go mod download

# Install OpenCV (for local development)
# On macOS:
brew install opencv

# On Ubuntu:
sudo apt-get update
sudo apt-get install libopencv-dev
```

#### Development

```bash
# Run service locally
go run main.go

# Build binary
go build -o omr main.go

# Run tests
go test ./...

# Run with race detection
go test -race ./...
```

#### Code Structure

```
services/omr/
├── main.go                  # Main application
├── internal/                # Internal packages
│   ├── detector/            # Bubble detection logic
│   ├── processor/           # Image processing
│   └── models/              # Data structures
├── pkg/                     # Public packages
├── go.mod                   # Go module definition
├── go.sum                   # Dependency checksums
├── Dockerfile               # Container build
└── test-data/               # Sample images for testing
    ├── sample1.jpg
    └── sample2.png
```

#### Adding New Detection Algorithms

```go
// internal/detector/advanced.go
package detector

import (
    "gocv.io/x/gocv"
    "image"
)

type AdvancedDetector struct {
    minRadius int
    maxRadius int
    threshold float64
}

func (d *AdvancedDetector) DetectBubbles(img gocv.Mat) []Circle {
    // Implement advanced detection algorithm
    gray := gocv.NewMat()
    defer gray.Close()
    
    gocv.CvtColor(img, &gray, gocv.ColorBGRToGray)
    
    // Apply adaptive thresholding
    thresh := gocv.NewMat()
    defer thresh.Close()
    gocv.AdaptiveThreshold(gray, &thresh, 255, 
        gocv.AdaptiveThresholdMean, gocv.ThresholdBinary, 11, 2)
    
    // Find contours and filter by area
    contours := gocv.FindContours(thresh, gocv.RetrievalExternal, 
        gocv.ChainApproxSimple)
    
    var circles []Circle
    for _, contour := range contours {
        area := gocv.ContourArea(contour)
        if area > 100 && area < 1000 {
            // Convert contour to circle
            circle := d.contourToCircle(contour)
            circles = append(circles, circle)
        }
    }
    
    return circles
}
```

#### Testing with Sample Images

```go
// main_test.go
package main

import (
    "testing"
    "gocv.io/x/gocv"
)

func TestBubbleDetection(t *testing.T) {
    // Load test image
    img := gocv.IMRead("test-data/sample1.jpg", gocv.IMReadColor)
    if img.Empty() {
        t.Fatal("Could not load test image")
    }
    defer img.Close()
    
    // Run detection
    bubbles := detectBubbles(img)
    
    // Verify results
    if len(bubbles) == 0 {
        t.Error("No bubbles detected in test image")
    }
    
    // Check for reasonable number of bubbles
    if len(bubbles) > 100 {
        t.Error("Too many bubbles detected - possible false positives")
    }
}
```

## Database Development

### Local PostgreSQL Setup

```bash
# Option 1: Use Docker
docker run --name bubblegrade-db \
  -e POSTGRES_USER=omr \
  -e POSTGRES_PASSWORD=omr \
  -e POSTGRES_DB=omr \
  -p 5432:5432 \
  -d postgres:16-alpine

# Option 2: Local installation
# macOS
brew install postgresql
brew services start postgresql

# Ubuntu
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
```

### Database Schema Development

```sql
-- migrations/001_initial_schema.sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE scans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'QUEUED',
    score INTEGER,
    answers JSONB,
    total_questions INTEGER,
    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_time TIMESTAMP,
    
    CONSTRAINT valid_status CHECK (status IN ('QUEUED', 'PROCESSING', 'COMPLETED', 'ERROR')),
    CONSTRAINT valid_score CHECK (score >= 0 AND score <= 100)
);

CREATE INDEX idx_scans_status ON scans(status);
CREATE INDEX idx_scans_upload_time ON scans(upload_time);
CREATE INDEX idx_scans_status_time ON scans(status, upload_time);
```

### Database Testing

```python
# tests/test_database.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import Scan, Base

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_scan_creation(db_session):
    scan = Scan(
        filename="test.jpg",
        status="QUEUED"
    )
    db_session.add(scan)
    db_session.commit()
    
    assert scan.id is not None
    assert scan.filename == "test.jpg"
    assert scan.status == "QUEUED"
```

## Debugging and Troubleshooting

### VS Code Debug Configuration

Create `.vscode/launch.json`:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Debug FastAPI",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/services/api/app/main.py",
            "console": "integratedTerminal",
            "env": {
                "DATABASE_URL": "postgresql+asyncpg://omr:omr@localhost/omr"
            }
        },
        {
            "name": "Debug Go OMR",
            "type": "go",
            "request": "launch",
            "mode": "auto",
            "program": "${workspaceFolder}/services/omr/main.go",
            "env": {
                "PORT": "8090"
            }
        }
    ]
}
```

### Logging Configuration

#### API Debugging

```python
# app/main.py
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url} - {response.status_code} - {process_time:.4f}s")
    return response
```

#### OMR Service Debugging

```go
// main.go
import (
    "log"
    "os"
)

func init() {
    if os.Getenv("DEBUG") == "true" {
        log.SetFlags(log.LstdFlags | log.Lshortfile)
    }
}

func detectBubbles(img gocv.Mat) []Circle {
    log.Printf("Processing image of size %dx%d", img.Cols(), img.Rows())
    
    // ... detection logic ...
    
    log.Printf("Detected %d potential bubbles", len(bubbles))
    return bubbles
}
```

### Common Issues and Solutions

#### 1. CORS Issues
```javascript
// Frontend can't connect to API
// Solution: Check CORS configuration in API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### 2. Database Connection Issues
```python
# Check database connectivity
async def test_db_connection():
    try:
        async with async_session() as session:
            result = await session.execute(text("SELECT 1"))
            print("Database connected successfully")
    except Exception as e:
        print(f"Database connection failed: {e}")
```

#### 3. OpenCV Issues
```bash
# On macOS with M1/M2 chips
export CGO_CPPFLAGS="-I/opt/homebrew/include"
export CGO_LDFLAGS="-L/opt/homebrew/lib -lopencv_core -lopencv_imgproc -lopencv_imgcodecs"

# On Linux with missing libraries
sudo apt-get install libopencv-dev pkg-config
```

## Code Quality and Standards

### Pre-commit Hooks

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 22.12.0
    hooks:
      - id: black
        files: ^services/api/

  - repo: https://github.com/eslint/eslint
    rev: v8.32.0
    hooks:
      - id: eslint
        files: ^services/frontend/
```

### Code Formatting

```bash
# Python formatting
cd services/api
black app/
isort app/

# JavaScript/TypeScript formatting
cd services/frontend
npm run format

# Go formatting
cd services/omr
go fmt ./...
```

## Performance Optimization

### Frontend Optimization

```typescript
// Lazy loading components
const ScanHistory = lazy(() => import('./components/ScanHistory'));

// Memoize expensive calculations
const processedScans = useMemo(() => 
  scans.filter(scan => scan.status === 'COMPLETED'),
  [scans]
);

// Debounce API calls
const debouncedSearch = useCallback(
  debounce((query: string) => {
    searchScans(query);
  }, 300),
  []
);
```

### API Optimization

```python
# Database query optimization
@app.get("/api/scans")
async def list_scans(
    limit: int = 10,
    offset: int = 0,
    status: Optional[str] = None
):
    query = select(Scan).order_by(Scan.upload_time.desc())
    
    if status:
        query = query.where(Scan.status == status)
    
    query = query.offset(offset).limit(limit)
    
    async with async_session() as session:
        result = await session.execute(query)
        return result.scalars().all()
```

### OMR Service Optimization

```go
// Parallel processing for multiple images
func processImages(images []gocv.Mat) []Result {
    results := make([]Result, len(images))
    var wg sync.WaitGroup
    
    for i, img := range images {
        wg.Add(1)
        go func(idx int, image gocv.Mat) {
            defer wg.Done()
            results[idx] = processImage(image)
        }(i, img)
    }
    
    wg.Wait()
    return results
}
```

This development guide provides comprehensive setup instructions and best practices for contributing to the BubbleGrade project. Follow these guidelines to ensure consistent, maintainable, and high-quality code.