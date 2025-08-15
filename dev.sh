#!/bin/bash

# ToneBridge Development Helper Script
# This script provides convenient commands for development

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Show help
show_help() {
    echo "ToneBridge Development Helper"
    echo "=============================="
    echo ""
    echo "Usage: ./dev.sh [command]"
    echo ""
    echo "Commands:"
    echo "  setup       - Initial project setup"
    echo "  start       - Start all services"
    echo "  stop        - Stop all services"
    echo "  restart     - Restart all services"
    echo "  logs        - View service logs"
    echo "  test        - Run all tests"
    echo "  test-api    - Run API tests only"
    echo "  test-load   - Run load tests"
    echo "  build       - Build all Docker images"
    echo "  clean       - Clean up containers and volumes"
    echo "  db          - Access PostgreSQL shell"
    echo "  redis       - Access Redis CLI"
    echo "  gateway-dev - Run Gateway in development mode"
    echo "  llm-dev     - Run LLM service in development mode"
    echo "  web-dev     - Open Web UI in browser"
    echo "  status      - Check service status"
    echo "  backup      - Backup database"
    echo "  restore     - Restore database from backup"
    echo "  help        - Show this help message"
    echo ""
}

# Setup project
setup_project() {
    print_info "Setting up ToneBridge development environment..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    
    # Create .env if not exists
    if [ ! -f .env ]; then
        cp .env.example .env
        print_warning "Created .env file. Please add your OpenAI API key!"
        read -p "Press Enter after adding your API key..."
    fi
    
    # Install dependencies
    print_info "Installing dependencies..."
    
    if [ -d "services/gateway" ]; then
        cd services/gateway
        go mod download
        cd ../..
        print_success "Go dependencies installed"
    fi
    
    if [ -d "services/llm" ]; then
        cd services/llm
        pip install -r requirements.txt
        cd ../..
        print_success "Python dependencies installed"
    fi
    
    print_success "Setup complete!"
}

# Start services
start_services() {
    print_info "Starting ToneBridge services..."
    cd infrastructure
    docker-compose up -d
    cd ..
    
    print_info "Waiting for services to be ready..."
    sleep 5
    
    check_status
}

# Stop services
stop_services() {
    print_info "Stopping ToneBridge services..."
    cd infrastructure
    docker-compose down
    cd ..
    print_success "Services stopped"
}

# Restart services
restart_services() {
    stop_services
    start_services
}

# View logs
view_logs() {
    cd infrastructure
    docker-compose logs -f
    cd ..
}

# Run tests
run_tests() {
    print_info "Running all tests..."
    
    # API tests
    if [ -f "tests/api_test.sh" ]; then
        print_info "Running API tests..."
        ./tests/api_test.sh
    fi
    
    # Integration tests
    if [ -f "tests/test_integration.py" ]; then
        print_info "Running integration tests..."
        python tests/test_integration.py
    fi
    
    print_success "All tests completed"
}

# Run API tests
run_api_tests() {
    print_info "Running API tests..."
    ./tests/api_test.sh
}

# Run load tests
run_load_tests() {
    print_info "Running load tests..."
    python tests/load_test.py
}

# Build images
build_images() {
    print_info "Building Docker images..."
    cd infrastructure
    docker-compose build
    cd ..
    print_success "Build complete"
}

# Clean up
clean_up() {
    print_warning "This will remove all containers and volumes!"
    read -p "Are you sure? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cd infrastructure
        docker-compose down -v
        docker system prune -f
        cd ..
        print_success "Cleanup complete"
    fi
}

# Database access
access_db() {
    print_info "Accessing PostgreSQL..."
    cd infrastructure
    docker-compose exec postgres psql -U tonebridge -d tonebridge_db
    cd ..
}

# Redis access
access_redis() {
    print_info "Accessing Redis CLI..."
    cd infrastructure
    docker-compose exec redis redis-cli
    cd ..
}

# Run Gateway in dev mode
run_gateway_dev() {
    print_info "Starting Gateway in development mode..."
    cd services/gateway
    go run cmd/api/main.go
}

# Run LLM service in dev mode
run_llm_dev() {
    print_info "Starting LLM service in development mode..."
    cd services/llm
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
}

# Open Web UI
open_web() {
    print_info "Opening Web UI..."
    if command -v open &> /dev/null; then
        open http://localhost:3000
    elif command -v xdg-open &> /dev/null; then
        xdg-open http://localhost:3000
    else
        print_info "Please open http://localhost:3000 in your browser"
    fi
}

# Check status
check_status() {
    print_info "Checking service status..."
    
    # Check Gateway
    if curl -s http://localhost:8080/health > /dev/null 2>&1; then
        print_success "API Gateway: Running at http://localhost:8080"
    else
        print_error "API Gateway: Not responding"
    fi
    
    # Check LLM Service
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        print_success "LLM Service: Running at http://localhost:8000"
    else
        print_error "LLM Service: Not responding"
    fi
    
    # Check Web UI
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        print_success "Web UI: Running at http://localhost:3000"
    else
        print_warning "Web UI: Not running (optional)"
    fi
    
    # Check PostgreSQL
    cd infrastructure
    if docker-compose exec -T postgres pg_isready -U tonebridge > /dev/null 2>&1; then
        print_success "PostgreSQL: Running"
    else
        print_error "PostgreSQL: Not responding"
    fi
    
    # Check Redis
    if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
        print_success "Redis: Running"
    else
        print_error "Redis: Not responding"
    fi
    cd ..
}

# Backup database
backup_db() {
    print_info "Backing up database..."
    
    BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
    cd infrastructure
    docker-compose exec -T postgres pg_dump -U tonebridge tonebridge_db > "../backups/$BACKUP_FILE"
    cd ..
    
    print_success "Database backed up to backups/$BACKUP_FILE"
}

# Restore database
restore_db() {
    if [ -z "$2" ]; then
        print_error "Please specify backup file"
        echo "Usage: ./dev.sh restore backups/backup_file.sql"
        exit 1
    fi
    
    if [ ! -f "$2" ]; then
        print_error "Backup file not found: $2"
        exit 1
    fi
    
    print_warning "This will overwrite the current database!"
    read -p "Are you sure? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Restoring database from $2..."
        cd infrastructure
        docker-compose exec -T postgres psql -U tonebridge tonebridge_db < "../$2"
        cd ..
        print_success "Database restored"
    fi
}

# Main script
case "$1" in
    setup)
        setup_project
        ;;
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    logs)
        view_logs
        ;;
    test)
        run_tests
        ;;
    test-api)
        run_api_tests
        ;;
    test-load)
        run_load_tests
        ;;
    build)
        build_images
        ;;
    clean)
        clean_up
        ;;
    db)
        access_db
        ;;
    redis)
        access_redis
        ;;
    gateway-dev)
        run_gateway_dev
        ;;
    llm-dev)
        run_llm_dev
        ;;
    web-dev)
        open_web
        ;;
    status)
        check_status
        ;;
    backup)
        backup_db
        ;;
    restore)
        restore_db "$@"
        ;;
    help|"")
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac