.PHONY: help build up down logs clean test lint setup

# Default target
help:
	@echo "ToneBridge Development Commands"
	@echo "================================"
	@echo "make setup      - Initial project setup"
	@echo "make build      - Build all Docker images"
	@echo "make up         - Start all services"
	@echo "make down       - Stop all services"
	@echo "make logs       - View service logs"
	@echo "make clean      - Clean up containers and volumes"
	@echo "make test       - Run all tests"
	@echo "make lint       - Run linters"
	@echo "make gateway    - Start only Gateway service"
	@echo "make llm        - Start only LLM service"
	@echo "make db         - Access PostgreSQL shell"
	@echo "make redis-cli  - Access Redis CLI"

# Initial setup
setup:
	@echo "Setting up ToneBridge development environment..."
	@cp .env.example .env
	@echo "Please edit .env file with your configuration (especially OPENAI_API_KEY)"
	@cd services/gateway && go mod download
	@cd services/llm && pip install -r requirements.txt
	@echo "Setup complete!"

# Docker commands
build:
	@echo "Building Docker images..."
	@cd infrastructure && docker-compose build

up:
	@echo "Starting all services..."
	@cd infrastructure && docker-compose up -d
	@echo "Waiting for services to be ready..."
	@sleep 5
	@make health-check

down:
	@echo "Stopping all services..."
	@cd infrastructure && docker-compose down

logs:
	@cd infrastructure && docker-compose logs -f

clean:
	@echo "Cleaning up containers and volumes..."
	@cd infrastructure && docker-compose down -v
	@docker system prune -f

# Service-specific commands
gateway:
	@echo "Starting Gateway service..."
	@cd services/gateway && go run cmd/api/main.go

llm:
	@echo "Starting LLM service..."
	@cd services/llm && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Database access
db:
	@echo "Accessing PostgreSQL..."
	@cd infrastructure && docker-compose exec postgres psql -U tonebridge -d tonebridge_db

redis-cli:
	@echo "Accessing Redis CLI..."
	@cd infrastructure && docker-compose exec redis redis-cli

# Testing
test:
	@echo "Running tests..."
	@echo "Testing Gateway..."
	@cd services/gateway && go test ./...
	@echo "Testing LLM Service..."
	@cd services/llm && pytest

test-gateway:
	@cd services/gateway && go test -v ./...

test-llm:
	@cd services/llm && pytest -v

# Linting
lint:
	@echo "Running linters..."
	@echo "Linting Gateway..."
	@cd services/gateway && golangci-lint run
	@echo "Linting LLM Service..."
	@cd services/llm && flake8 app/

lint-gateway:
	@cd services/gateway && golangci-lint run

lint-llm:
	@cd services/llm && flake8 app/

# Health checks
health-check:
	@echo "Checking service health..."
	@curl -s http://localhost:8082/health | jq '.' || echo "Gateway is not responding"
	@curl -s http://localhost:8003/health | jq '.' || echo "LLM Service is not responding"

# Development utilities
watch-gateway:
	@cd services/gateway && air

watch-llm:
	@cd services/llm && uvicorn app.main:app --reload

# API testing
test-transform:
	@echo "Testing transformation endpoint..."
	@curl -X POST http://localhost:8082/api/v1/transform \
		-H "Content-Type: application/json" \
		-d '{"text": "Fix the bug ASAP", "transformation_type": "tone", "target_tone": "warm"}' | jq '.'

test-analyze:
	@echo "Testing analysis endpoint..."
	@curl -X POST http://localhost:8082/api/v1/analyze \
		-H "Content-Type: application/json" \
		-d '{"text": "Critical bug in production environment needs immediate attention"}' | jq '.'

# Docker utilities
docker-clean-all:
	@docker stop $$(docker ps -aq) 2>/dev/null || true
	@docker rm $$(docker ps -aq) 2>/dev/null || true
	@docker rmi $$(docker images -q) 2>/dev/null || true
	@docker volume rm $$(docker volume ls -q) 2>/dev/null || true
	@docker network prune -f

# Production build
build-prod:
	@echo "Building for production..."
	@cd services/gateway && CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o main cmd/api/main.go
	@cd infrastructure && docker-compose -f docker-compose.prod.yml build

# Deployment
deploy:
	@echo "Deploying to production..."
	@echo "Not implemented yet"