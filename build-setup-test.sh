#!/bin/bash
# =============================================================================
# ERP System - Build, Setup & Test Automation Script
# =============================================================================
# Usage: ./build-setup-test.sh [option]
# Options:
#   --install     Install all dependencies
#   --migrate     Run database migrations
#   --test        Run test suite with coverage
#   --lint        Run code quality checks
#   --all         Run complete pipeline (install + migrate + test + lint)
#   --clean       Clean cache and build artifacts
#   --help        Show this help message
# =============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="${PROJECT_ROOT}/src"
VENV_DIR="${PROJECT_ROOT}/venv"
PYTHON_CMD="python3"
PIP_CMD="pip3"
export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH:-}"

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo ""
    echo "============================================================================="
    echo "  $1"
    echo "============================================================================="
    echo ""
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed. Please install Python 3.8+ first."
        exit 1
    fi
    
    if ! command -v pip3 &> /dev/null; then
        log_error "pip3 is not installed. Please install pip first."
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    log_info "Found Python ${PYTHON_VERSION}"
    
    if ! command -v git &> /dev/null; then
        log_warning "Git is not installed. Some features may not work."
    fi
}

# Create virtual environment
setup_venv() {
    if [ ! -d "$VENV_DIR" ]; then
        log_info "Creating virtual environment..."
        python3 -m venv "$VENV_DIR"
        source "${VENV_DIR}/bin/activate"
        log_success "Virtual environment created at ${VENV_DIR}"
    else
        source "${VENV_DIR}/bin/activate"
        log_info "Virtual environment activated"
    fi
    
    # Upgrade pip
    pip install --upgrade pip setuptools wheel > /dev/null 2>&1
}

# Install dependencies
install_dependencies() {
    print_header "Installing Dependencies"
    
    if [ ! -f "${PROJECT_ROOT}/requirements.txt" ]; then
        log_error "requirements.txt not found!"
        exit 1
    fi
    
    log_info "Installing production dependencies..."
    pip install -r "${PROJECT_ROOT}/requirements.txt"
    
    if [ -f "${PROJECT_ROOT}/requirements-dev.txt" ]; then
        log_info "Installing development dependencies..."
        pip install -r "${PROJECT_ROOT}/requirements-dev.txt"
    fi
    
    log_success "All dependencies installed successfully"
}

# Run database migrations
run_migrations() {
    print_header "Running Database Migrations"
    
    cd "$SRC_DIR"
    
    log_info "Creating database if not exists..."
    python manage.py check || exit 1
    
    log_info "Making migrations..."
    python manage.py makemigrations --no-input
    
    log_info "Applying migrations..."
    python manage.py migrate --no-input
    
    log_success "Database migrations completed"
    cd "$PROJECT_ROOT"
}

# Run tests
run_tests() {
    print_header "Running Tests"
    
    cd "$PROJECT_ROOT"
    
    log_info "Running pytest with coverage..."
    python -m pytest \
        --cov=src \
        --cov-report=term-missing \
        --cov-report=html:tests/htmlcov \
        --cov-fail-under=70 \
        -v \
        --tb=short
    
    TEST_EXIT_CODE=$?
    
    if [ $TEST_EXIT_CODE -eq 0 ]; then
        log_success "All tests passed! Coverage report: file://${PROJECT_ROOT}/tests/htmlcov/index.html"
    else
        log_error "Some tests failed. Exit code: ${TEST_EXIT_CODE}"
    fi
    
    return $TEST_EXIT_CODE
}

# Run linting and code quality checks
run_linting() {
    print_header "Running Code Quality Checks"
    
    cd "$SRC_DIR"
    
    log_info "Running flake8..."
    flake8 . --config="${PROJECT_ROOT}/setup.cfg" || true
    
    log_info "Running black (check mode)..."
    black --check . || true
    
    log_info "Running isort (check mode)..."
    isort --check-only . || true
    
    log_info "Running mypy..."
    mypy . --ignore-missing-imports || true
    
    log_success "Code quality checks completed"
    cd "$PROJECT_ROOT"
}

# Clean build artifacts
clean_artifacts() {
    print_header "Cleaning Build Artifacts"
    
    log_info "Removing __pycache__ directories..."
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    
    log_info "Removing .pyc files..."
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    
    log_info "Removing .pytest_cache..."
    rm -rf .pytest_cache 2>/dev/null || true
    
    log_info "Removing htmlcov..."
    rm -rf tests/htmlcov 2>/dev/null || true
    
    log_info "Removing .mypy_cache..."
    rm -rf .mypy_cache 2>/dev/null || true
    
    log_info "Removing dist and build directories..."
    rm -rf dist build 2>/dev/null || true
    
    log_success "Cleanup completed"
}

# Show help
show_help() {
    cat << EOF
ERP System - Build, Setup & Test Automation

Usage: $(basename "$0") [OPTION]

Options:
  --install     Install all dependencies in virtual environment
  --migrate     Run database migrations
  --test        Run test suite with coverage reporting
  --lint        Run code quality checks (flake8, black, isort, mypy)
  --all         Run complete pipeline (install + migrate + test + lint)
  --clean       Clean cache and build artifacts
  --help        Show this help message

Examples:
  $(basename "$0") --install      # Install dependencies only
  $(basename "$0") --test         # Run tests only
  $(basename "$0") --all          # Run complete setup and test pipeline
  $(basename "$0") --clean        # Clean all build artifacts

EOF
}

# Main execution
main() {
    check_prerequisites
    
    case "${1:-}" in
        --install)
            setup_venv
            install_dependencies
            ;;
        --migrate)
            run_migrations
            ;;
        --test)
            run_tests
            ;;
        --lint)
            run_linting
            ;;
        --all)
            setup_venv
            install_dependencies
            run_migrations
            run_tests
            run_linting
            print_header "Complete Pipeline Finished Successfully"
            ;;
        --clean)
            clean_artifacts
            ;;
        --help|-h|"")
            show_help
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
