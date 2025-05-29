#!/bin/bash

# BubbleGrade Deployment Script
# Sets up the complete BubbleGrade stack with OCR capabilities

set -e

echo "🚀 Starting BubbleGrade deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.bubblegrade.yml"
ENV_FILE=".env.bubblegrade"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if ports are available
    PORTS=(5173 8080 8090 8100 5433 6379)
    for port in "${PORTS[@]}"; do
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            print_warning "Port $port is already in use. This may cause conflicts."
        fi
    done
    
    print_success "Prerequisites check completed"
}

# Create environment file
create_env_file() {
    print_status "Creating environment configuration..."
    
    cat > $ENV_FILE << EOF
# BubbleGrade Environment Configuration
COMPOSE_PROJECT_NAME=bubblegrade

# Database Configuration
POSTGRES_USER=bubblegrade
POSTGRES_PASSWORD=bubblegrade_secure_password_2024
POSTGRES_DB=bubblegrade

# API Configuration
SECRET_KEY=$(openssl rand -hex 32)
DATABASE_URL=postgresql+asyncpg://bubblegrade:bubblegrade_secure_password_2024@db:5432/bubblegrade
OMR_URL=http://omr:8090
OCR_URL=http://ocr:8100
LOG_LEVEL=INFO

# Frontend Configuration
VITE_API_BASE=/api/v1
VITE_WS_URL=ws://localhost:8080/ws

# Service URLs
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000

# Development flags
DEBUG=false
NODE_ENV=production
EOF
    
    print_success "Environment file created: $ENV_FILE"
}

# Build and start services
deploy_services() {
    print_status "Building and starting BubbleGrade services..."
    
    # Build all services
    docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE build --parallel
    
    # Start database first
    print_status "Starting database..."
    docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE up -d db redis
    
    # Wait for database to be ready
    print_status "Waiting for database to be ready..."
    timeout 60s bash -c 'until docker-compose -f '$COMPOSE_FILE' --env-file '$ENV_FILE' exec -T db pg_isready -U bubblegrade; do sleep 2; done'
    
    # Run database migrations
    print_status "Running database migrations..."
    docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE run --rm api alembic upgrade head
    
    # Start remaining services
    print_status "Starting microservices..."
    docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE up -d omr ocr
    
    # Wait for microservices to be ready
    print_status "Waiting for microservices..."
    timeout 60s bash -c 'until curl -f http://localhost:8090/health; do sleep 2; done'
    timeout 60s bash -c 'until curl -f http://localhost:8100/health; do sleep 2; done'
    
    # Start API and frontend
    print_status "Starting API and frontend..."
    docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE up -d api frontend
    
    print_success "All services started successfully!"
}

# Health check all services
health_check() {
    print_status "Performing health checks..."
    
    SERVICES=(
        "Frontend:http://localhost:5173"
        "API:http://localhost:8080/health"
        "OMR:http://localhost:8090/health"
        "OCR:http://localhost:8100/health"
    )
    
    for service in "${SERVICES[@]}"; do
        name=${service%%:*}
        url=${service#*:}
        
        if curl -f "$url" >/dev/null 2>&1; then
            print_success "$name service is healthy"
        else
            print_error "$name service is not responding"
        fi
    done
}

# Load test data
load_test_data() {
    print_status "Loading test data..."
    
    # Create exam template
    curl -X POST http://localhost:8080/api/v1/templates \
         -H "Content-Type: application/json" \
         -d '{
           "name": "Examen Universitario Estándar",
           "description": "Plantilla para exámenes de 20 preguntas",
           "total_questions": 20,
           "correct_answers": ["A","B","C","D","A","B","C","D","A","B","C","D","A","B","C","D","A","B","C","D"]
         }' >/dev/null 2>&1
    
    print_success "Test data loaded"
}

# Show deployment summary
show_summary() {
    echo ""
    echo "🎉 BubbleGrade deployment completed successfully!"
    echo ""
    echo "📋 Service URLs:"
    echo "   Frontend:  http://localhost:5173"
    echo "   API:       http://localhost:8080"
    echo "   OMR:       http://localhost:8090"
    echo "   OCR:       http://localhost:8100"
    echo "   Database:  localhost:5433"
    echo ""
    echo "📚 API Documentation:"
    echo "   OpenAPI:   http://localhost:8080/docs"
    echo "   ReDoc:     http://localhost:8080/redoc"
    echo ""
    echo "🔧 Management Commands:"
    echo "   View logs: docker-compose -f $COMPOSE_FILE logs -f"
    echo "   Stop:      docker-compose -f $COMPOSE_FILE down"
    echo "   Restart:   docker-compose -f $COMPOSE_FILE restart"
    echo ""
    echo "🧪 Test the system:"
    echo "   1. Open http://localhost:5173"
    echo "   2. Upload a test image"
    echo "   3. Monitor processing in real-time"
    echo ""
}

# Main execution
main() {
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    🫧 BubbleGrade Deployment                 ║"
    echo "║              OCR + OMR Document Processing System            ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    
    check_prerequisites
    create_env_file
    deploy_services
    health_check
    load_test_data
    show_summary
}

# Cleanup function
cleanup() {
    print_status "Cleaning up on exit..."
    docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE down >/dev/null 2>&1 || true
}

# Trap cleanup on script exit
trap cleanup EXIT

# Handle command line arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "test")
        health_check
        ;;
    "clean")
        print_status "Stopping and removing all containers..."
        docker-compose -f $COMPOSE_FILE down -v --remove-orphans
        docker system prune -f
        print_success "Cleanup completed"
        ;;
    "logs")
        docker-compose -f $COMPOSE_FILE logs -f
        ;;
    *)
        echo "Usage: $0 {deploy|test|clean|logs}"
        echo "  deploy - Full deployment (default)"
        echo "  test   - Health check only"
        echo "  clean  - Stop and clean everything"
        echo "  logs   - Show live logs"
        exit 1
        ;;
esac