.PHONY: help setup dev test clean install-backend install-frontend start-memgraph start-backend start-frontend stop

# Default target
help:
	@echo "OpenTruss Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make setup           - Initialize development environment (install dependencies)"
	@echo "  make install-backend - Install backend dependencies"
	@echo "  make install-frontend - Install frontend dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make dev             - Start all services in development mode"
	@echo "  make start-memgraph  - Start Memgraph database"
	@echo "  make start-backend   - Start backend server"
	@echo "  make start-frontend  - Start frontend server"
	@echo "  make stop            - Stop all Docker services"
	@echo ""
	@echo "Testing:"
	@echo "  make test            - Run all tests (backend + frontend)"
	@echo "  make test-backend    - Run backend tests"
	@echo "  make test-frontend   - Run frontend tests"
	@echo "  make test-e2e        - Run E2E tests"
	@echo ""
	@echo "Data:"
	@echo "  make load-examples   - Load example data to database"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean           - Clean temporary files and caches"
	@echo "  make lint            - Run linters (backend + frontend)"

# Setup: Install all dependencies
setup: install-backend install-frontend
	@echo "✅ Setup complete! Run 'make dev' to start development environment."

# Install backend dependencies
install-backend:
	@echo "📦 Installing backend dependencies..."
	cd backend && \
	if [ ! -d "venv" ]; then \
		python3 -m venv venv; \
	fi && \
	. venv/bin/activate && \
	pip install --upgrade pip && \
	pip install -r requirements.txt && \
	pip install -r requirements-dev.txt
	@echo "✅ Backend dependencies installed"

# Install frontend dependencies
install-frontend:
	@echo "📦 Installing frontend dependencies..."
	cd frontend && npm ci
	@echo "✅ Frontend dependencies installed"

# Development: Start all services
dev: start-memgraph
	@echo "🚀 Starting development environment..."
	@echo "   Backend: http://localhost:8000"
	@echo "   Frontend: http://localhost:3000"
	@echo "   Memgraph: localhost:7687"
	@echo ""
	@echo "   Press Ctrl+C to stop all services"
	@echo ""
	@$(MAKE) start-backend & $(MAKE) start-frontend & wait

# Start Memgraph using Docker Compose
start-memgraph:
	@echo "🗄️  Starting Memgraph database..."
	docker-compose up -d memgraph
	@echo "⏳ Waiting for Memgraph to be ready..."
	@sleep 5
	@echo "✅ Memgraph is ready at localhost:7687"

# Start backend server
start-backend:
	@echo "🔧 Starting backend server..."
	cd backend && \
	if [ -d "venv" ]; then \
		. venv/bin/activate && \
		uvicorn app.main:app --reload --host 0.0.0.0 --port 8000; \
	else \
		echo "⚠️  Virtual environment not found. Run 'make install-backend' first."; \
	fi

# Start frontend server
start-frontend:
	@echo "🎨 Starting frontend server..."
	cd frontend && npm run dev

# Stop all Docker services
stop:
	@echo "🛑 Stopping Docker services..."
	docker-compose down
	@echo "✅ All services stopped"

# Testing
test: test-backend test-frontend
	@echo "✅ All tests completed"

test-backend:
	@echo "🧪 Running backend tests..."
	cd backend && \
	if [ -d "venv" ]; then \
		. venv/bin/activate && \
		pytest tests/ -v; \
	else \
		echo "⚠️  Virtual environment not found. Run 'make install-backend' first."; \
	fi

test-frontend:
	@echo "🧪 Running frontend tests..."
	cd frontend && npm test -- --watchAll=false

test-e2e:
	@echo "🧪 Running E2E tests..."
	cd frontend && npm run test:e2e

# Linting
lint:
	@echo "🔍 Running linters..."
	@$(MAKE) lint-backend
	@$(MAKE) lint-frontend

lint-backend:
	@echo "🔍 Linting backend..."
	@echo "   (Backend linting will be available when tools are configured)"

lint-frontend:
	@echo "🔍 Linting frontend..."
	cd frontend && npm run lint

# Clean temporary files
clean:
	@echo "🧹 Cleaning temporary files..."
	find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -r {} + 2>/dev/null || true
	cd frontend && rm -rf .next node_modules/.cache 2>/dev/null || true
	@echo "✅ Cleanup complete"

