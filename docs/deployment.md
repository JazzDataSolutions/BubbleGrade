# Deployment Guide

## Overview

This guide covers deploying BubbleGrade in various environments, from development to production.

## Quick Local Deployment

### Prerequisites

- Docker Desktop 4.0+ with Docker Compose
- 4GB+ available RAM
- Ports 5173, 8080, 8090, 5432 available

### Basic Deployment

```bash
# Clone repository
git clone <repository-url>
cd BubbleGrade

# Start all services
docker compose -f compose.micro.yml up --build

# Verify services are running
docker compose -f compose.micro.yml ps
```

## Development Environment

### Hot Reload Setup

Create `compose.dev.yml`:

```yaml
version: "3.9"

services:
  frontend:
    volumes:
      - ./services/frontend/src:/app/src
    command: npm run dev -- --host 0.0.0.0

  api:
    volumes:
      - ./services/api:/app
    command: uvicorn app.main:app --reload --host 0.0.0.0 --port 8080

  omr:
    volumes:
      - ./services/omr:/app
```

Run with development overrides:
```bash
docker compose -f compose.micro.yml -f compose.dev.yml up
```

## Production Deployment

### Environment Configuration

Create `.env.production`:

```env
# API Configuration
SECRET_KEY=your-super-secret-production-key
DATABASE_URL=postgresql+asyncpg://bubblegrade_user:secure_password@db/bubblegrade_prod
OMR_URL=http://omr:8090/grade
LOG_LEVEL=WARNING

# Database Configuration
POSTGRES_USER=bubblegrade_user
POSTGRES_PASSWORD=secure_password
POSTGRES_DB=bubblegrade_prod

# OMR Configuration
OMR_THREADS=8
OPENCV_LOG_LEVEL=ERROR

# Frontend Configuration
VITE_API_BASE=https://api.yourdomain.com/api
VITE_WS_URL=wss://api.yourdomain.com/ws
```

### Production Docker Compose

Create `compose.prod.yml`:

```yaml
version: "3.9"

services:
  frontend:
    restart: unless-stopped
    environment:
      - VITE_API_BASE=https://api.yourdomain.com/api
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.frontend.rule=Host(`yourdomain.com`)"

  api:
    restart: unless-stopped
    env_file: .env.production
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: "1.0"
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.api.rule=Host(`api.yourdomain.com`)"

  omr:
    restart: unless-stopped
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 4G
          cpus: "2.0"

  db:
    restart: unless-stopped
    env_file: .env.production
    volumes:
      - db_data:/var/lib/postgresql/data
      - ./backups:/backups
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: "1.0"

volumes:
  db_data:
    driver: local
```

## Cloud Deployment

### AWS ECS Deployment

1. **Build and Push Images**

```bash
# Build images
docker build -t your-registry/bubblegrade-frontend services/frontend
docker build -t your-registry/bubblegrade-api services/api
docker build -t your-registry/bubblegrade-omr services/omr

# Push to registry
docker push your-registry/bubblegrade-frontend
docker push your-registry/bubblegrade-api
docker push your-registry/bubblegrade-omr
```

2. **Create ECS Task Definition**

```json
{
  "family": "bubblegrade",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "2048",
  "memory": "4096",
  "containerDefinitions": [
    {
      "name": "frontend",
      "image": "your-registry/bubblegrade-frontend",
      "portMappings": [{"containerPort": 80}],
      "essential": true
    },
    {
      "name": "api",
      "image": "your-registry/bubblegrade-api",
      "portMappings": [{"containerPort": 8080}],
      "environment": [
        {"name": "DATABASE_URL", "value": "postgresql+asyncpg://..."}
      ],
      "essential": true
    },
    {
      "name": "omr",
      "image": "your-registry/bubblegrade-omr",
      "portMappings": [{"containerPort": 8090}],
      "essential": true
    }
  ]
}
```

### Google Cloud Run

1. **Deploy Frontend**

```bash
gcloud run deploy bubblegrade-frontend \
  --image your-registry/bubblegrade-frontend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

2. **Deploy API**

```bash
gcloud run deploy bubblegrade-api \
  --image your-registry/bubblegrade-api \
  --platform managed \
  --region us-central1 \
  --set-env-vars DATABASE_URL="postgresql+asyncpg://..." \
  --allow-unauthenticated
```

### Kubernetes Deployment

Create `k8s/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: bubblegrade-frontend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: bubblegrade-frontend
  template:
    metadata:
      labels:
        app: bubblegrade-frontend
    spec:
      containers:
      - name: frontend
        image: your-registry/bubblegrade-frontend
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"

---
apiVersion: v1
kind: Service
metadata:
  name: bubblegrade-frontend-service
spec:
  selector:
    app: bubblegrade-frontend
  ports:
  - port: 80
    targetPort: 80
  type: LoadBalancer
```

## Database Setup

### PostgreSQL Configuration

For production, use managed database services:

#### AWS RDS
```bash
aws rds create-db-instance \
  --db-instance-identifier bubblegrade-prod \
  --db-instance-class db.t3.medium \
  --engine postgres \
  --master-username bubblegrade_admin \
  --master-user-password your-secure-password \
  --allocated-storage 100
```

#### Google Cloud SQL
```bash
gcloud sql instances create bubblegrade-prod \
  --database-version=POSTGRES_14 \
  --tier=db-g1-small \
  --region=us-central1
```

### Database Migration

```bash
# Run initial migration
docker compose exec api python -c "
from app.main import engine, Base
import asyncio
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
asyncio.run(create_tables())
"
```

## Monitoring and Logging

### Health Checks

Configure health check endpoints:

```yaml
services:
  api:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  omr:
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:8090/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Logging Configuration

Add logging configuration to `services/api/app/main.py`:

```python
import logging
from pythonjsonlogger import jsonlogger

# Configure structured logging
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)
```

### Prometheus Metrics

Add metrics collection:

```python
from prometheus_client import Counter, Histogram, generate_latest

# Metrics
scan_counter = Counter('bubblegrade_scans_total', 'Total scans processed')
processing_time = Histogram('bubblegrade_processing_seconds', 'Time spent processing scans')

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

## Security Considerations

### HTTPS Configuration

Use Traefik or nginx for SSL termination:

```yaml
# traefik.yml
services:
  traefik:
    image: traefik:v2.9
    command:
      - "--api.insecure=true"
      - "--providers.docker=true"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.myresolver.acme.tlschallenge=true"
      - "--certificatesresolvers.myresolver.acme.email=your-email@domain.com"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - "/var/run/docker.sock:/var/run/docker.sock:ro"
      - "./acme.json:/acme.json"
```

### Environment Variables Security

Never commit secrets to version control:

```bash
# Use external secret management
docker run -d \
  --env-file /secure/path/.env \
  your-registry/bubblegrade-api
```

## Backup and Recovery

### Database Backups

```bash
# Automated backup script
#!/bin/bash
BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

docker compose exec db pg_dump -U bubblegrade_user bubblegrade_prod > \
  "${BACKUP_DIR}/bubblegrade_backup_${TIMESTAMP}.sql"

# Retain only last 7 days
find $BACKUP_DIR -name "bubblegrade_backup_*.sql" -mtime +7 -delete
```

### Volume Backups

```bash
# Backup database volume
docker run --rm \
  -v bubblegrade_db_data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/db_data_backup.tar.gz -C /data .
```

## Performance Optimization

### Scaling OMR Service

```bash
# Scale OMR service for high load
docker compose -f compose.micro.yml up -d --scale omr=5
```

### Database Optimization

```sql
-- Add indexes for better performance
CREATE INDEX CONCURRENTLY idx_scans_status_upload_time ON scans(status, upload_time);
CREATE INDEX CONCURRENTLY idx_scans_processed_time ON scans(processed_time) WHERE status = 'COMPLETED';
```

### Caching

Add Redis for caching:

```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

## Troubleshooting

### Common Issues

1. **Out of Memory**
   - Increase Docker memory limits
   - Reduce OMR service replicas

2. **Database Connection Issues**
   - Check network connectivity
   - Verify credentials
   - Ensure database is ready before API starts

3. **OpenCV Processing Errors**
   - Verify image formats
   - Check OMR service logs
   - Ensure sufficient CPU resources

### Debug Commands

```bash
# View service logs
docker compose logs -f api
docker compose logs -f omr

# Check service health
curl http://localhost:8080/health
curl http://localhost:8090/health

# Database connection test
docker compose exec db psql -U omr -d omr -c "SELECT 1;"
```