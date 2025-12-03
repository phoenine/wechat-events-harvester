# WeRSS Supabase Migration Guide

This guide documents the migration from the original architecture to Plan A: minimal changes with Supabase PostgreSQL.

## Overview

Implements the minimal changes required to migrate from the original architecture to use Supabase PostgreSQL while maintaining the existing SQLAlchemy ORM layer.

## Changes Made

### 1. Database Configuration
- **Connection String**: Updated to use PostgreSQL connection to Supabase
- **Connection Pool**: Optimized for Supabase cloud database (pool_size=5, max_overflow=10)
- **Connection Parameters**: Added PostgreSQL-specific settings (connect_timeout, application_name, statement_timeout)

### 2. Docker Configuration
- **Backend Dockerfile**: Fixed incorrect path references (`ws-supabase/backend/` → `./`)
- **Frontend Dockerfile**: Updated to use correct paths and package manager (pnpm)
- **Docker Compose**: Added proper environment variables and health checks

### 3. Database Compatibility
- **Type Mapping**: Enhanced data_sync.py to handle PostgreSQL type conversions
- **Permissions**: Added database permission checks for PostgreSQL
- **Connection Handling**: Improved connection management for cloud databases

### 4. CORS Configuration
- **Cross-Origin**: Already configured to allow all origins with credentials
- **Headers**: Proper headers set for API access

### 5. CI/CD Pipeline
- **GitHub Actions**: Created workflow for building and deploying both services
- **Container Registry**: Configured for GitHub Container Registry
- **Multi-architecture**: Support for different architectures

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Supabase      │
│   (Vue 3)       │◄──►│   (FastAPI)     │◄──►│   (PostgreSQL)  │
│   Port: 3000    │    │   Port: 38001   │    │   Port: 5432    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Web Scraping Capabilities

The backend includes comprehensive web scraping support:

- **Playwright**: Modern browser automation framework
- **Firefox Browser**: Installed for headless browsing
- **Multi-architecture Support**: Works on both AMD64 and ARM64
- **Stealth Mode**: Includes playwright-stealth for anti-detection
- **System Dependencies**: All required libraries for browser automation

## Deployment

### Prerequisites
- Docker and Docker Compose installed
- Supabase instance running (local or cloud)
- Environment variables configured

### Quick Start

1. **Configure Environment**
   ```bash
   # Copy and edit .env file
   cp .env.example .env
   # Edit .env with your Supabase credentials
   ```

2. **Deploy Services**
   ```bash
   # Run deployment script
   ./deploy.sh
   ```

3. **Verify Deployment**
   ```bash
   # Check service status
   docker-compose ps

   # View logs
   docker-compose logs -f

   # Test API
   curl http://localhost:38001/api/docs
   ```

### Manual Deployment

1. **Build Services**
   ```bash
   docker-compose build
   ```

2. **Start Services**
   ```bash
   docker-compose up -d
   ```

3. **Initialize Database**
   ```bash
   docker-compose exec backend python init_sys.py
   ```

## Configuration

### Environment Variables

#### Database Configuration
```bash
POSTGRES_PASSWORD=your-super-secret-and-long-postgres-password
POSTGRES_HOST=localhost          # or your Supabase host
POSTGRES_PORT=5432
POSTGRES_DB=postgres
```

#### Application Configuration
```bash
APP_NAME=we-mp-rss
SERVER_NAME=we-mp-rss
WEB_NAME=WeRSS微信公众号订阅助手
SECRET_KEY_BASE=your-secret-key
USERNAME=admin
PASSWORD=admin@123
ENABLE_JOB=true
THREADS=4
PORT=38001
DEBUG=false
```

### Docker Compose Services

#### Backend Service
- **Image**: Built from `./backend/Dockerfile`
- **Port**: 38001
- **Environment**: All backend configuration
- **Volumes**: `./data:/app/data` for persistent storage
- **Health Check**: API documentation endpoint
- **Features**: Multi-architecture support, Playwright for web scraping, Firefox browser

#### Frontend Service
- **Image**: Built from `./frontend/Dockerfile`
- **Port**: 3000
- **Environment**: `VITE_API_BASE_URL` for API endpoint
- **Dependencies**: Depends on backend service
- **Health Check**: Root endpoint

## Database Schema

The application uses SQLAlchemy models that are automatically synchronized with the database. Key tables include:

- **users**: User authentication and management
- **articles**: RSS article content
- **feeds**: RSS feed configurations
- **message_tasks**: Background task management
- **tags**: Content tagging system

## Monitoring and Maintenance

### Health Checks
Both services include health checks that monitor:
- Service availability
- API endpoint responsiveness
- Database connectivity

### Logging
- Application logs are available via `docker-compose logs`
- Database logs can be accessed through Supabase dashboard
- Structured logging with different levels (INFO, WARNING, ERROR)

### Backup and Recovery
- Database backups should be configured through Supabase
- Application data in `./data` directory should be backed up regularly
- Container images are versioned and stored in registry

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check Supabase credentials in `.env`
   - Verify network connectivity to Supabase
   - Check PostgreSQL service status

2. **Build Failures**
   - Ensure Docker has sufficient resources
   - Check network connectivity for package downloads
   - Verify all dependencies are available

3. **Service Startup Issues**
   - Check service logs: `docker-compose logs [service-name]`
   - Verify environment variables are set correctly
   - Check port availability (38001, 3000, 5432)

### Performance Optimization

1. **Database Performance**
   - Monitor connection pool usage
   - Optimize query performance
   - Consider indexing strategies

2. **Application Performance**
   - Monitor response times
   - Optimize static asset delivery
   - Consider caching strategies

## Security Considerations

1. **Database Security**
   - Use strong passwords for database access
   - Configure proper network access controls
   - Enable SSL/TLS for database connections

2. **Application Security**
   - Keep dependencies updated
   - Use secure configuration practices
   - Monitor for security vulnerabilities

3. **Container Security**
   - Use minimal base images
   - Scan images for vulnerabilities
   - Follow container security best practices

## Next Steps

After successful deployment with Plan A, consider:

1. **Plan B Implementation**: Full Supabase integration with Auth and Storage
2. **Performance Monitoring**: Add application performance monitoring
3. **Scaling**: Configure auto-scaling for production workloads
4. **Disaster Recovery**: Implement comprehensive backup strategies

## Support

For issues and questions:
- Check application logs
- Review Supabase documentation
- Consult the migration plan document
- Check GitHub issues for known problems