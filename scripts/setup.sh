#!/bin/bash
# OpenTruss Development Environment Setup Script
# This script helps set up and manage the OpenTruss development environment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Print colored message
print_info() {
    echo -e "${GREEN}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Setup backend environment
setup_backend() {
    print_info "Setting up backend environment..."
    cd "$PROJECT_ROOT/backend"
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        print_info "Creating Python virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    print_info "Upgrading pip..."
    pip install --upgrade pip
    
    # Install dependencies
    print_info "Installing backend dependencies..."
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
    
    print_info "✅ Backend environment setup complete"
}

# Setup frontend environment
setup_frontend() {
    print_info "Setting up frontend environment..."
    cd "$PROJECT_ROOT/frontend"
    
    # Check if Node.js is installed
    if ! command_exists node; then
        print_error "Node.js is not installed. Please install Node.js 18.0+ first."
        exit 1
    fi
    
    # Install dependencies
    print_info "Installing frontend dependencies..."
    npm ci
    
    print_info "✅ Frontend environment setup complete"
}

# Start Memgraph database
start_memgraph() {
    print_info "Starting Memgraph database..."
    cd "$PROJECT_ROOT"
    
    if ! command_exists docker; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    docker-compose up -d memgraph
    
    print_info "⏳ Waiting for Memgraph to be ready..."
    sleep 5
    
    print_info "✅ Memgraph is ready at localhost:7687"
}

# Start backend server
start_backend() {
    print_info "Starting backend server..."
    cd "$PROJECT_ROOT/backend"
    
    if [ ! -d "venv" ]; then
        print_error "Virtual environment not found. Run './scripts/setup.sh setup' first."
        exit 1
    fi
    
    source venv/bin/activate
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
}

# Start frontend server
start_frontend() {
    print_info "Starting frontend server..."
    cd "$PROJECT_ROOT/frontend"
    
    npm run dev
}

# Start development environment (all services)
start_dev() {
    print_info "🚀 Starting development environment..."
    print_info "   Backend: http://localhost:8000"
    print_info "   Frontend: http://localhost:3000"
    print_info "   Memgraph: localhost:7687"
    echo ""
    
    # Start Memgraph
    start_memgraph
    
    # Start backend and frontend in background
    start_backend &
    BACKEND_PID=$!
    
    start_frontend &
    FRONTEND_PID=$!
    
    # Wait for processes
    trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
    wait
}

# Run tests
run_tests() {
    print_info "Running all tests..."
    
    # Backend tests
    if [ -d "$PROJECT_ROOT/backend/venv" ]; then
        print_info "Running backend tests..."
        cd "$PROJECT_ROOT/backend"
        source venv/bin/activate
        pytest tests/ -v
    else
        print_warning "Backend virtual environment not found. Skipping backend tests."
    fi
    
    # Frontend tests
    print_info "Running frontend tests..."
    cd "$PROJECT_ROOT/frontend"
    npm test -- --watchAll=false
}

# Main function
main() {
    case "${1:-setup}" in
        setup)
            print_info "Setting up OpenTruss development environment..."
            setup_backend
            setup_frontend
            print_info "✅ Setup complete! Run './scripts/setup.sh dev' to start development environment."
            ;;
        dev)
            start_dev
            ;;
        backend)
            start_backend
            ;;
        frontend)
            start_frontend
            ;;
        memgraph)
            start_memgraph
            ;;
        test)
            run_tests
            ;;
        *)
            echo "Usage: $0 {setup|dev|backend|frontend|memgraph|test}"
            echo ""
            echo "Commands:"
            echo "  setup     - Initialize development environment (install dependencies)"
            echo "  dev       - Start all services in development mode"
            echo "  backend   - Start backend server only"
            echo "  frontend  - Start frontend server only"
            echo "  memgraph  - Start Memgraph database only"
            echo "  test      - Run all tests"
            exit 1
            ;;
    esac
}

main "$@"

