# Docker Deployment Guide

This guide explains how to run the Application Registry Service using Docker and Docker Compose.

## 🐳 Quick Start

### Option 1: One-Command Start
```bash
./docker-start.sh
```

### Option 2: Manual Docker Compose
```bash
# Simple deployment
docker-compose -f docker-compose.simple.yml up -d

# Full deployment with nginx
docker-compose up -d
```

## 📦 What's Included

### Docker Files
- `Dockerfile` - Multi-stage Python application container
- `docker-compose.yml` - Full production setup with nginx
- `docker-compose.simple.yml` - Simple single-service deployment
- `docker-start.sh` - Automated startup script
- `nginx.conf` - Nginx reverse proxy configuration
- `.dockerignore` - Optimized build context

### Container Features
- ✅ Python 3.11 slim base image
- ✅ Non-root user for security
- ✅ Health checks
- ✅ Persistent data storage
- ✅ Production-ready Gunicorn server
- ✅ Automatic database initialization

## 🚀 Deployment Options

### Simple Deployment (Recommended for Development)
```bash
# Start service
docker-compose -f docker-compose.simple.yml up -d

# View logs
docker-compose -f docker-compose.simple.yml logs -f

# Stop service
docker-compose -f docker-compose.simple.yml down
```

**Access:** `http://localhost:5000`

### Full Production Deployment
```bash
# Start with nginx reverse proxy
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

**Access:** 
- Direct API: `http://localhost:5000`
- Via Nginx: `http://localhost:80`

## 🔧 Configuration

### Environment Variables
Edit `docker.env` or set in docker-compose.yml:

```bash
FLASK_APP=app.py
FLASK_ENV=production
DATABASE_URL=sqlite:///data/app_registry.db
SECRET_KEY=your-production-secret-key
```

### Data Persistence
- SQLite database stored in `./data/app_registry.db`
- Automatically created on first run
- Persists across container restarts

### Port Configuration
- **5000**: Application port
- **80**: Nginx proxy port (full deployment)
- **443**: HTTPS port (nginx, requires SSL setup)

## 🧪 Testing the Deployment

### Health Check
```bash
curl http://localhost:5000/health
```

### Register an Application
```bash
curl -X POST http://localhost:5000/api/applications \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Docker Test App",
    "version": "1.0.0",
    "developer": "Docker User",
    "contact_email": "docker@example.com"
  }'
```

### List Applications
```bash
curl http://localhost:5000/api/applications
```

## 📊 Monitoring & Logs

### View Container Status
```bash
docker ps
```

### View Application Logs
```bash
# Simple deployment
docker-compose -f docker-compose.simple.yml logs -f app-registry

# Full deployment
docker-compose logs -f app-registry
docker-compose logs -f nginx
```

### Container Health
```bash
docker inspect app-registry-service --format='{{.State.Health.Status}}'
```

## 🔒 Security Features

### Application Security
- Non-root user execution
- Minimal base image (Python slim)
- Security headers via nginx
- Rate limiting (nginx)
- Health checks

### Network Security
- Isolated Docker network
- Internal service communication
- Configurable CORS origins

## 🛠️ Troubleshooting

### Container Won't Start
```bash
# Check build logs
docker-compose -f docker-compose.simple.yml build --no-cache

# Check container logs
docker-compose -f docker-compose.simple.yml logs app-registry
```

### Database Issues
```bash
# Reset database
docker-compose -f docker-compose.simple.yml down
rm -rf ./data
docker-compose -f docker-compose.simple.yml up -d
```

### Port Conflicts
```bash
# Check what's using port 5000
lsof -i :5000

# Change port in docker-compose.yml
ports:
  - "5001:5000"  # Use port 5001 instead
```

## 🔄 Updates & Maintenance

### Update Application
```bash
# Rebuild and restart
docker-compose -f docker-compose.simple.yml build --no-cache
docker-compose -f docker-compose.simple.yml up -d
```

### Backup Database
```bash
# Copy database file
cp ./data/app_registry.db ./backup/app_registry_$(date +%Y%m%d).db
```

### Scale Service
```bash
# Run multiple instances (requires load balancer)
docker-compose -f docker-compose.simple.yml up -d --scale app-registry=3
```

## 📈 Production Considerations

### Resource Limits
Add to docker-compose.yml:
```yaml
services:
  app-registry:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
```

### SSL/HTTPS Setup
1. Obtain SSL certificates
2. Mount certificates in nginx container
3. Update nginx.conf for HTTPS

### External Database
Replace SQLite with PostgreSQL:
```yaml
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: app_registry
      POSTGRES_USER: appuser
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  app-registry:
    environment:
      - DATABASE_URL=postgresql://appuser:secure_password@postgres:5432/app_registry
```

## 📋 Quick Reference

| Command | Purpose |
|---------|---------|
| `./docker-start.sh` | One-command startup |
| `docker-compose -f docker-compose.simple.yml up -d` | Start simple deployment |
| `docker-compose -f docker-compose.simple.yml down` | Stop deployment |
| `docker-compose -f docker-compose.simple.yml logs -f` | View logs |
| `docker-compose -f docker-compose.simple.yml restart` | Restart service |
| `curl http://localhost:5000/health` | Health check |

The Docker deployment provides a complete, production-ready environment that eliminates dependency issues and ensures consistent deployment across different systems!
