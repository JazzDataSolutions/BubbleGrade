# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## System Overview

BubbleGrade is a microservices-based Optical Mark Recognition (OMR) system for automated grading of bubble sheets. It follows Clean Architecture principles with SOLID design patterns and uses a domain-driven approach.

### Service Architecture

- **Frontend**: React 18 + TypeScript + Vite (port 5173)
- **API**: FastAPI + SQLAlchemy + AsyncPG (port 8080) 
- **OMR**: Go + OpenCV for image processing (port 8090)
- **Database**: PostgreSQL 16 (port 5432)

All services run in Docker containers orchestrated via `compose.micro.yml`.

## Development Commands

### Full System
```bash
# Start all services
docker compose -f compose.micro.yml up --build

# View logs
docker compose -f compose.micro.yml logs -f

# Stop all services
docker compose -f compose.micro.yml down
```

### Frontend Development
```bash
cd services/frontend
npm install
npm run dev          # Development server at localhost:5173
npm run build        # Production build
npm run lint         # ESLint checking
npm run preview      # Preview production build
```

### API Development
```bash
cd services/api
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

### OMR Service Development
```bash
cd services/omr
go mod download
go run main.go       # Standalone service
go test ./...        # Run tests
```

## Code Architecture

### Clean Architecture Implementation

The API service follows Clean Architecture with clear separation:

- **Domain Layer** (`app/domain/`): Core business entities and interfaces
  - `entities.py`: Domain models (Scan, OMRResult, WebSocketMessage)
  - `repositories.py`: Repository interfaces
  - `services.py`: Domain service interfaces

- **Application Layer** (`app/application/`): Use cases and business logic
  - `use_cases.py`: Business use cases (ScanUseCases, ExportUseCases)

- **Infrastructure Layer** (`app/infrastructure/`): External adapters
  - `database.py`: SQLAlchemy models and database setup
  - `repositories.py`: Database repository implementations
  - `external_services.py`: HTTP clients for OMR service
  - `websocket_manager.py`: WebSocket connection management

- **Presentation Layer** (`app/presentation/`): API endpoints and schemas
  - `routers.py`: FastAPI route handlers
  - `schemas.py`: Pydantic request/response models
  - `dependencies.py`: Dependency injection setup

### Key Design Patterns

1. **Repository Pattern**: Database access abstracted through repository interfaces
2. **Dependency Injection**: Services injected through FastAPI dependencies
3. **Domain Events**: WebSocket messages for real-time updates
4. **Clean Error Handling**: Structured error responses and logging

## Important Notes

### Database
- Uses SQLAlchemy async ORM with PostgreSQL
- Database URL: `postgresql+asyncpg://omr:omr@db/omr`
- Scan results stored in `scans` table with JSONB for answers

### WebSocket Communication
- Real-time updates for scan processing status
- Connection manager handles multiple client connections
- Message types: `scan_update`, `scan_complete`, `scan_error`

### File Processing Pipeline
1. File upload to `/api/scans`
2. Database record creation with QUEUED status
3. Background task sends file to Go OMR service
4. OMR processes image using OpenCV circle detection
5. Results stored in database with COMPLETED status
6. WebSocket notification sent to frontend

### Environment Variables
- `DATABASE_URL`: PostgreSQL connection string
- `OMR_URL`: Go service endpoint (default: http://omr:8090/grade)
- `SECRET_KEY`: Application secret key

### Ports and Services
- Frontend: localhost:5173
- API: localhost:8080 
- OMR: localhost:8090
- Database: localhost:5433 (mapped from container 5432)

## Testing Strategy

The system currently uses the main.py file directly. For Clean Architecture testing approach:
- Unit tests for domain entities and use cases
- Integration tests for repository implementations  
- API tests for endpoints and WebSocket functionality
- E2E tests for full processing pipeline

When implementing tests, follow the existing Clean Architecture structure and test each layer independently.