#!/bin/bash

# WeRSS Supabase Migration Validation Script
# This script validates the migration configuration without requiring Docker builds

set -e

echo "🔍 Starting WeRSS Supabase Migration Validation"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    case $status in
        "success")
            echo -e "${GREEN}✅ $message${NC}"
            ;;
        "error")
            echo -e "${RED}❌ $message${NC}"
            ;;
        "warning")
            echo -e "${YELLOW}⚠️  $message${NC}"
            ;;
        "info")
            echo -e "ℹ️  $message"
            ;;
    esac
}

# Function to check file existence
check_file() {
    local file=$1
    local description=$2
    if [ -f "$file" ]; then
        print_status "success" "$description found: $file"
        return 0
    else
        print_status "error" "$description not found: $file"
        return 1
    fi
}

# Function to check directory existence
check_directory() {
    local dir=$1
    local description=$2
    if [ -d "$dir" ]; then
        print_status "success" "$description found: $dir"
        return 0
    else
        print_status "error" "$description not found: $dir"
        return 1
    fi
}

# Function to validate Dockerfiles
validate_dockerfile() {
    local dockerfile=$1
    local service=$2

    if [ ! -f "$dockerfile" ]; then
        print_status "error" "$service Dockerfile not found: $dockerfile"
        return 1
    fi

    print_status "info" "Validating $service Dockerfile..."

    # Check for common issues
    if grep -q "ws-supabase" "$dockerfile"; then
        print_status "error" "$service Dockerfile contains incorrect path references"
        return 1
    fi

    if grep -q "web_ui" "$dockerfile"; then
        print_status "error" "$service Dockerfile contains old path references"
        return 1
    fi

    # Check for required instructions
    if ! grep -q "FROM" "$dockerfile"; then
        print_status "error" "$service Dockerfile missing FROM instruction"
        return 1
    fi

    if ! grep -q "EXPOSE" "$dockerfile"; then
        print_status "warning" "$service Dockerfile missing EXPOSE instruction"
    fi

    print_status "success" "$service Dockerfile validation passed"
    return 0
}

# Function to validate Python code
validate_python() {
    local file=$1
    local description=$2

    if [ ! -f "$file" ]; then
        print_status "error" "$description not found: $file"
        return 1
    fi

    print_status "info" "Validating $description..."

    # Check for Python syntax errors
    if python3 -m py_compile "$file" 2>/dev/null; then
        print_status "success" "$description syntax is valid"
    else
        print_status "error" "$description has syntax errors"
        return 1
    fi

    return 0
}

# Function to validate configuration files
validate_config() {
    local file=$1
    local description=$2

    if [ ! -f "$file" ]; then
        print_status "error" "$description not found: $file"
        return 1
    fi

    print_status "info" "Validating $description..."

    # Check for required environment variables
    if [[ "$file" == *.env* ]]; then
        local required_vars=("POSTGRES_PASSWORD" "POSTGRES_HOST" "POSTGRES_PORT" "POSTGRES_DB")
        for var in "${required_vars[@]}"; do
            if grep -q "^$var=" "$file"; then
                print_status "success" "Environment variable $var is set"
            else
                print_status "warning" "Environment variable $var is missing"
            fi
        done
    fi

    # Check for YAML syntax
    if [[ "$file" == *.yaml ]] || [[ "$file" == *.yml ]]; then
        if command -v yq >/dev/null 2>&1; then
            if yq eval '.' "$file" >/dev/null 2>&1; then
                print_status "success" "$description YAML syntax is valid"
            else
                print_status "error" "$description has YAML syntax errors"
                return 1
            fi
        else
            print_status "warning" "yq not found, skipping YAML validation"
        fi
    fi

    return 0
}

# Main validation function
main() {
    echo "🚀 Starting validation process..."

    local errors=0

    # Check project structure
    print_status "info" "Checking project structure..."

    check_directory "backend" "Backend directory" || ((errors++))
    check_directory "frontend" "Frontend directory" || ((errors++))
    check_directory ".github/workflows" "GitHub workflows directory" || ((errors++))

    # Check configuration files
    print_status "info" "Checking configuration files..."

    check_file ".env" "Environment file" || ((errors++))
    check_file "docker-compose.yaml" "Docker Compose file" || ((errors++))
    check_file "backend/config.example.yaml" "Backend config example" || ((errors++))

    # Validate Dockerfiles
    print_status "info" "Validating Dockerfiles..."

    validate_dockerfile "backend/Dockerfile" "Backend" || ((errors++))
    validate_dockerfile "frontend/Dockerfile" "Frontend" || ((errors++))

    # Validate Docker Compose
    print_status "info" "Validating Docker Compose configuration..."

    if [ -f "docker-compose.yaml" ]; then
        # Check for required services and port configuration
        if grep -q "backend:" "docker-compose.yaml"; then
            print_status "success" "Backend service defined"

            # Check for port 38001
            if grep -q "38001:38001" "docker-compose.yaml"; then
                print_status "success" "Backend port 38001 configured"
            else
                print_status "error" "Backend port 38001 not configured"
                ((errors++))
            fi
        else
            print_status "error" "Backend service not defined"
            ((errors++))
        fi

        if grep -q "frontend:" "docker-compose.yaml"; then
            print_status "success" "Frontend service defined"
        else
            print_status "error" "Frontend service not defined"
            ((errors++))
        fi

        # Check for environment variables
        if grep -q "DB=" "docker-compose.yaml"; then
            print_status "success" "Database configuration found"
        else
            print_status "error" "Database configuration missing"
            ((errors++))
        fi

        # Check for API base URL
        if grep -q "VITE_API_BASE_URL.*38001" "docker-compose.yaml"; then
            print_status "success" "API base URL configured for port 38001"
        else
            print_status "error" "API base URL not configured for port 38001"
            ((errors++))
        fi
    fi

    # Validate Python code
    print_status "info" "Validating Python code..."

    validate_python "backend/core/db.py" "Database module" || ((errors++))
    validate_python "backend/data_sync.py" "Data synchronization module" || ((errors++))
    validate_python "backend/web.py" "Web application" || ((errors++))

    # Validate environment configuration
    print_status "info" "Validating environment configuration..."

    if [ -f ".env" ]; then
        validate_config ".env" "Environment file" || ((errors++))
    fi

    # Check for GitHub Actions workflow
    print_status "info" "Checking CI/CD configuration..."

    if [ -f ".github/workflows/build-and-deploy.yml" ]; then
        print_status "success" "GitHub Actions workflow found"
        validate_config ".github/workflows/build-and-deploy.yml" "CI/CD workflow" || ((errors++))
    else
        print_status "warning" "GitHub Actions workflow not found"
    fi

    # Summary
    echo ""
    echo "📋 Validation Summary:"
    echo "====================="

    if [ $errors -eq 0 ]; then
        print_status "success" "All validations passed! 🎉"
        echo ""
        echo "✨ Your WeRSS Supabase migration is ready for deployment!"
        echo ""
        echo "🚀 Next steps:"
        echo "  1. Review the migration guide: MIGRATION_GUIDE.md"
        echo "  2. Update .env with your Supabase credentials"
        echo "  3. Run deployment: ./deploy.sh"
        echo "  4. Access your application at:"
        echo "     - Frontend: http://localhost:30000"
        echo "     - Backend API: http://localhost:38001"
        echo "     - API Documentation: http://localhost:38001/api/docs"
        return 0
    else
        print_status "error" "Validation failed with $errors error(s)"
        echo ""
        echo "🔧 Please fix the issues above before proceeding with deployment."
        return 1
    fi
}

# Run main function
main "$@"
