#!/bin/bash

# WeRSS Supabase Migration Deployment Script
# This script helps deploy the application with Supabase integration

set -e

echo "🚀 Starting WeRSS Supabase Migration Deployment"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please create one based on .env.example"
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

echo "📋 Configuration Summary:"
echo "  - Database Host: ${POSTGRES_HOST:-localhost}"
echo "  - Database Port: ${POSTGRES_PORT:-5432}"
echo "  - Database Name: ${POSTGRES_DB:-postgres}"
echo "  - Backend Port: ${PORT:-38001}"
echo ""

# Function to check if Supabase is accessible
check_supabase() {
    echo "🔍 Checking Supabase connection..."
    if command -v pg_isready &> /dev/null; then
        if pg_isready -h "${POSTGRES_HOST:-localhost}" -p "${POSTGRES_PORT:-5432}" -U postgres; then
            echo "✅ Supabase PostgreSQL is accessible"
            return 0
        else
            echo "❌ Cannot connect to Supabase PostgreSQL"
            return 1
        fi
    else
        echo "⚠️  pg_isready not found, skipping connection check"
        return 0
    fi
}

# Function to build and start services
deploy_services() {
    echo "🔨 Building and starting services..."

    # Stop existing services
    echo "🛑 Stopping existing services..."
    docker-compose down || true

    # Build and start services
    echo "🏗️  Building services..."
    docker-compose build --no-cache

    echo "🚀 Starting services..."
    docker-compose up -d

    # Wait for services to be ready
    echo "⏳ Waiting for services to be ready..."
    sleep 30

    # Check service health
    echo "🏥 Checking service health..."
    if curl -f http://localhost:38001/api/docs > /dev/null 2>&1; then
        echo "✅ Backend service is healthy"
    else
        echo "❌ Backend service is not responding"
        echo "📋 Backend logs:"
        docker-compose logs backend
        return 1
    fi

    if curl -f http://localhost:30000 > /dev/null 2>&1; then
        echo "✅ Frontend service is healthy"
    else
        echo "❌ Frontend service is not responding"
        echo "📋 Frontend logs:"
        docker-compose logs frontend
        return 1
    fi
}

# Function to run database initialization
init_database() {
    echo "🗄️  Initializing database..."

    # Run initialization using Supabase
    docker-compose exec -T backend python -c "
from core.config import cfg
import sys

try:
    # Run initialization
    from init_sys import init
    init()
    print('✅ Database initialization completed')

except Exception as e:
    print(f'❌ Database initialization failed: {e}')
    sys.exit(1)
"
}

# Main deployment flow
main() {
    echo "🎯 Starting deployment process..."

    # Check Supabase connection
    if ! check_supabase; then
        echo "⚠️  Supabase connection check failed, but continuing with deployment"
    fi

    # Deploy services
    if deploy_services; then
        echo "✅ Services deployed successfully"

        # Initialize database
        if init_database; then
            echo "✅ Database initialized successfully"
        else
            echo "⚠️  Database initialization failed, but services are running"
        fi

        echo ""
        echo "🎉 Deployment completed successfully!"
        echo ""
        echo "📋 Service URLs:"
        echo "  - Frontend: http://localhost:30000"
        echo "  - Backend API: http://localhost:38001"
        echo "  - API Documentation: http://localhost:38001/api/docs"
        echo ""
        echo "🔧 Management commands:"
        echo "  - View logs: docker-compose logs -f"
        echo "  - Stop services: docker-compose down"
        echo "  - Restart services: docker-compose restart"
        echo "  - Shell access: docker-compose exec backend bash"

    else
        echo "❌ Deployment failed"
        echo "📋 Service logs:"
        docker-compose logs
        exit 1
    fi
}

# Run main function
main "$@"
