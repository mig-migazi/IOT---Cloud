#!/bin/bash

echo "🐳 Deploying Application Registry Service with Docker..."

# Create data directory with proper permissions
echo "📁 Setting up data directory..."
mkdir -p ./data
chmod 777 ./data

# Clean up any existing containers and images
echo "🧹 Cleaning up existing deployment..."
docker compose -f docker/docker-compose.simple.yml down 2>/dev/null || true
docker rm -f app-registry-service 2>/dev/null || true
docker rmi app-registry-service 2>/dev/null || true

# Build and start the service using Docker Compose
echo "📦 Building and starting service..."
docker compose -f docker/docker-compose.simple.yml up -d --build

if [ $? -ne 0 ]; then
    echo "❌ Docker deployment failed!"
    exit 1
fi

# Wait for service to be ready
echo "⏳ Waiting for service to be ready..."
sleep 15

# Test the service
echo "🧪 Testing service health..."
if curl -f http://localhost:5001/health >/dev/null 2>&1; then
    echo "✅ Service deployed successfully!"
    echo ""
    echo "🌐 Service available at: http://localhost:5001"
    echo "📋 API Documentation: docs/README.md"
    echo ""
    echo "🧪 Quick test:"
    echo "  curl http://localhost:5001/health"
    echo "  curl http://localhost:5001/api/applications"
    echo ""
    echo "🔧 Management commands:"
    echo "  docker compose -f docker/docker-compose.simple.yml logs -f    # View logs"
    echo "  docker compose -f docker/docker-compose.simple.yml down      # Stop service"
    echo "  docker compose -f docker/docker-compose.simple.yml restart   # Restart service"
else
    echo "❌ Service health check failed. Checking logs..."
    docker compose -f docker/docker-compose.simple.yml logs
    echo ""
    echo "🔍 Troubleshooting:"
    echo "1. Check container status: docker ps"
    echo "2. Check logs: docker compose -f docker/docker-compose.simple.yml logs"
    echo "3. Check port conflicts: lsof -i :5001"
fi
