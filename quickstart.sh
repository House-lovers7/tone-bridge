#!/bin/bash

# ToneBridge Quick Start Script
# This script helps you quickly set up and run the ToneBridge platform

set -e

echo "========================================="
echo "  ToneBridge Quick Start Setup"
echo "========================================="
echo ""

# Check prerequisites
echo "Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi
echo "✅ Docker is installed"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    echo "   Visit: https://docs.docker.com/compose/install/"
    exit 1
fi
echo "✅ Docker Compose is installed"

# Check if .env file exists
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Please edit the .env file and add your OpenAI API key"
    echo "   File location: $(pwd)/.env"
    echo ""
    read -p "Press Enter after you've added your OpenAI API key to continue..."
fi

# Build Docker images
echo ""
echo "Building Docker images..."
cd infrastructure
docker-compose build

# Start services
echo ""
echo "Starting services..."
docker-compose up -d

# Wait for services to be ready
echo ""
echo "Waiting for services to be ready..."
sleep 10

# Health check
echo ""
echo "Performing health checks..."

# Check Gateway
if curl -s http://localhost:8082/health > /dev/null 2>&1; then
    echo "✅ API Gateway is running at http://localhost:8082"
else
    echo "❌ API Gateway is not responding"
fi

# Check LLM Service
if curl -s http://localhost:8003/health > /dev/null 2>&1; then
    echo "✅ LLM Service is running at http://localhost:8003"
else
    echo "❌ LLM Service is not responding"
fi

# Check PostgreSQL
if docker-compose exec -T postgres pg_isready -U tonebridge > /dev/null 2>&1; then
    echo "✅ PostgreSQL is running"
else
    echo "❌ PostgreSQL is not responding"
fi

# Check Redis
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is running"
else
    echo "❌ Redis is not responding"
fi

echo ""
echo "========================================="
echo "  ToneBridge is ready!"
echo "========================================="
echo ""
echo "API Gateway: http://localhost:8082"
echo "LLM Service: http://localhost:8003"
echo "Health Check: http://localhost:8082/health"
echo ""
echo "Next steps:"
echo "1. Register a user: POST http://localhost:8082/api/v1/auth/register"
echo "2. Login: POST http://localhost:8082/api/v1/auth/login"
echo "3. Transform text: POST http://localhost:8082/api/v1/transform"
echo ""
echo "To view logs: cd infrastructure && docker-compose logs -f"
echo "To stop services: cd infrastructure && docker-compose down"
echo ""
echo "For more information, see README.md"