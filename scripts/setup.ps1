# OpenTruss Development Environment Setup Script (PowerShell)
# This script helps set up and manage the OpenTruss development environment on Windows

param(
    [Parameter(Position=0)]
    [ValidateSet('setup', 'dev', 'backend', 'frontend', 'memgraph', 'test')]
    [string]$Command = 'setup'
)

$ErrorActionPreference = "Stop"

$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$PROJECT_ROOT = Split-Path -Parent $SCRIPT_DIR

# Helper functions
function Write-Info {
    param([string]$Message)
    Write-Host "ℹ️  $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

function Test-Command {
    param([string]$CommandName)
    $null -ne (Get-Command $CommandName -ErrorAction SilentlyContinue)
}

# Setup backend environment
function Setup-Backend {
    Write-Info "Setting up backend environment..."
    Set-Location "$PROJECT_ROOT\backend"
    
    # Create virtual environment if it doesn't exist
    if (-not (Test-Path "venv")) {
        Write-Info "Creating Python virtual environment..."
        python -m venv venv
    }
    
    # Activate virtual environment
    & ".\venv\Scripts\Activate.ps1"
    
    # Upgrade pip
    Write-Info "Upgrading pip..."
    python -m pip install --upgrade pip
    
    # Install dependencies
    Write-Info "Installing backend dependencies..."
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
    
    Write-Info "✅ Backend environment setup complete"
}

# Setup frontend environment
function Setup-Frontend {
    Write-Info "Setting up frontend environment..."
    Set-Location "$PROJECT_ROOT\frontend"
    
    # Check if Node.js is installed
    if (-not (Test-Command "node")) {
        Write-Error "Node.js is not installed. Please install Node.js 18.0+ first."
        exit 1
    }
    
    # Install dependencies
    Write-Info "Installing frontend dependencies..."
    npm ci
    
    Write-Info "✅ Frontend environment setup complete"
}

# Start Memgraph database
function Start-Memgraph {
    Write-Info "Starting Memgraph database..."
    Set-Location $PROJECT_ROOT
    
    if (-not (Test-Command "docker")) {
        Write-Error "Docker is not installed. Please install Docker Desktop first."
        exit 1
    }
    
    docker-compose up -d memgraph
    
    Write-Info "⏳ Waiting for Memgraph to be ready..."
    Start-Sleep -Seconds 5
    
    Write-Info "✅ Memgraph is ready at localhost:7687"
}

# Start backend server
function Start-Backend {
    Write-Info "Starting backend server..."
    Set-Location "$PROJECT_ROOT\backend"
    
    if (-not (Test-Path "venv")) {
        Write-Error "Virtual environment not found. Run '.\scripts\setup.ps1 setup' first."
        exit 1
    }
    
    & ".\venv\Scripts\Activate.ps1"
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
}

# Start frontend server
function Start-Frontend {
    Write-Info "Starting frontend server..."
    Set-Location "$PROJECT_ROOT\frontend"
    
    npm run dev
}

# Start development environment (all services)
function Start-Dev {
    Write-Info "🚀 Starting development environment..."
    Write-Info "   Backend: http://localhost:8000"
    Write-Info "   Frontend: http://localhost:3000"
    Write-Info "   Memgraph: localhost:7687"
    Write-Host ""
    
    # Start Memgraph
    Start-Memgraph
    
    # Note: PowerShell job management for parallel processes
    Write-Warning "Starting backend and frontend servers..."
    Write-Warning "Press Ctrl+C to stop all services"
    Write-Host ""
    
    # Start backend in background job
    $backendJob = Start-Job -ScriptBlock {
        Set-Location $using:PROJECT_ROOT\backend
        & ".\venv\Scripts\Activate.ps1"
        uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    }
    
    # Start frontend (blocking)
    Start-Frontend
    
    # Cleanup job on exit
    $backendJob | Stop-Job
    $backendJob | Remove-Job
}

# Run tests
function Run-Tests {
    Write-Info "Running all tests..."
    
    # Backend tests
    if (Test-Path "$PROJECT_ROOT\backend\venv") {
        Write-Info "Running backend tests..."
        Set-Location "$PROJECT_ROOT\backend"
        & ".\venv\Scripts\Activate.ps1"
        pytest tests/ -v
    } else {
        Write-Warning "Backend virtual environment not found. Skipping backend tests."
    }
    
    # Frontend tests
    Write-Info "Running frontend tests..."
    Set-Location "$PROJECT_ROOT\frontend"
    npm test -- --watchAll=false
}

# Main execution
try {
    switch ($Command) {
        'setup' {
            Write-Info "Setting up OpenTruss development environment..."
            Setup-Backend
            Setup-Frontend
            Write-Info "✅ Setup complete! Run '.\scripts\setup.ps1 dev' to start development environment."
        }
        'dev' {
            Start-Dev
        }
        'backend' {
            Start-Backend
        }
        'frontend' {
            Start-Frontend
        }
        'memgraph' {
            Start-Memgraph
        }
        'test' {
            Run-Tests
        }
    }
} catch {
    Write-Error "An error occurred: $_"
    exit 1
}

