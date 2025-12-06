#!/bin/bash
# Deployment script for EC2 instance
# This script:
# 1. Pulls code from GitHub
# 2. Builds Docker image locally on EC2
# 3. Deploys the service using docker-compose
# No Docker Hub required - everything is built on EC2

set -e  # Exit on error

echo "=========================================="
echo "Chatbot Service Deployment Script"
echo "=========================================="

# Configuration
REPO_URL="${GITHUB_REPO_URL:-https://github.com/yourusername/yourrepo.git}"
BRANCH="${GITHUB_BRANCH:-main}"
SERVICE_DIR="/opt/chatbot-service"
COMPOSE_FILE="docker-compose.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed and determine which command to use
DOCKER_COMPOSE_CMD=""
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker-compose"
    print_info "Using docker-compose (v1)"
elif docker compose version &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker compose"
    print_info "Using docker compose (v2)"
else
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create service directory if it doesn't exist
if [ ! -d "$SERVICE_DIR" ]; then
    print_info "Creating service directory: $SERVICE_DIR"
    sudo mkdir -p "$SERVICE_DIR"
    sudo chown $USER:$USER "$SERVICE_DIR"
fi

cd "$SERVICE_DIR"

# Clone or update repository
if [ -d ".git" ]; then
    print_info "Updating existing repository..."
    git fetch origin
    git checkout "$BRANCH"
    git pull origin "$BRANCH"
else
    print_info "Cloning repository from $REPO_URL..."
    git clone -b "$BRANCH" "$REPO_URL" .
fi

# Find chatbot directory (try multiple possible paths)
CHATBOT_DIR=""

# First, check if current directory has the required files
if [ -f "docker-compose.yml" ] && [ -f "chatbot_service_sse.py" ]; then
    CHATBOT_DIR="."
    print_info "Found chatbot files in current directory"
else
    # Try common subdirectory paths
    POSSIBLE_PATHS=(
        "Prashiskshan_ml/chatbot"
        "chatbot"
        "Prashiskshan_ML_chatbot"
        "Prashiskshan_ML_chatbot/chatbot"
        "Prashiskshan_ML_chatbot/Prashiskshan_ml/chatbot"
    )

    print_info "Looking for chatbot directory in subdirectories..."
    for path in "${POSSIBLE_PATHS[@]}"; do
        if [ -d "$path" ] && [ -f "$path/docker-compose.yml" ] && [ -f "$path/chatbot_service_sse.py" ]; then
            CHATBOT_DIR="$path"
            print_info "Found chatbot directory at: $path"
            break
        fi
    done

    # If not found, try to find any directory with docker-compose.yml and chatbot_service_sse.py
    if [ -z "$CHATBOT_DIR" ]; then
        print_warn "Chatbot directory not found in common locations. Searching..."
        CHATBOT_DIR=$(find . -name "docker-compose.yml" -type f -exec dirname {} \; | while read dir; do
            if [ -f "$dir/chatbot_service_sse.py" ]; then
                echo "$dir"
                break
            fi
        done | head -1)
        if [ -n "$CHATBOT_DIR" ]; then
            print_info "Found chatbot directory at: $CHATBOT_DIR"
        fi
    fi
fi

# Final check
if [ -z "$CHATBOT_DIR" ] || [ ! -f "$CHATBOT_DIR/docker-compose.yml" ]; then
    print_error "Chatbot directory not found. Please check the repository structure."
    print_error "Looking for a directory containing docker-compose.yml and chatbot_service_sse.py"
    print_error ""
    print_error "Current directory: $(pwd)"
    print_error "Current directory structure:"
    ls -la | head -20
    print_error ""
    print_error "Searching for docker-compose.yml files..."
    find . -name "docker-compose.yml" -type f 2>/dev/null | head -5
    print_error ""
    print_error "Searching for chatbot_service_sse.py files..."
    find . -name "chatbot_service_sse.py" -type f 2>/dev/null | head -5
    print_error ""
    print_error "Please either:"
    print_error "  1. Navigate to the chatbot directory manually and run: $DOCKER_COMPOSE_CMD up -d"
    print_error "  2. Or update the script with the correct path"
    exit 1
fi

cd "$CHATBOT_DIR"
print_info "Working directory: $(pwd)"

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_warn ".env file not found. Creating from template..."
    if [ -f "env_template.txt" ]; then
        cp env_template.txt .env
        print_warn "Please update .env file with your configuration before continuing."
        print_info "Required configuration:"
        print_info "  - API Keys (OPENROUTER_API_KEY, GEMINI_API_KEY)"
        print_info ""
        print_info "Note: Qdrant and Redis are self-hosted and will be configured automatically."
        read -p "Press Enter after updating .env file..."
    else
        print_error ".env file not found and no template available."
        exit 1
    fi
fi


# Validate API keys
if grep -q "your_openrouter_api_key_here" .env 2>/dev/null || grep -q "your_gemini_api_key_here" .env 2>/dev/null; then
    print_warn "API keys may not be configured. Please verify in .env file."
fi

# Stop existing containers
print_info "Stopping existing containers..."
$DOCKER_COMPOSE_CMD down || true

# Build Docker image locally on EC2 (no Docker Hub needed)
print_info "Building Docker image locally on EC2..."
print_info "This may take a few minutes on first build..."
$DOCKER_COMPOSE_CMD build --no-cache

# Start services
print_info "Starting services..."
$DOCKER_COMPOSE_CMD up -d

# Wait for service to be healthy
print_info "Waiting for service to be healthy..."
sleep 10

# Check service health
MAX_RETRIES=30
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -f http://localhost/health > /dev/null 2>&1; then
        print_info "Service is healthy!"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo -n "."
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    print_error "Service failed to become healthy. Check logs with: $DOCKER_COMPOSE_CMD logs"
    exit 1
fi

# Show service status
print_info "Service deployment completed!"
echo ""
echo "=========================================="
echo "Service Information"
echo "=========================================="
EC2_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo 'localhost')
echo "Service URL: http://${EC2_IP}"
echo "Health Check: http://${EC2_IP}/health"
echo ""
echo "Services Running:"
echo "  - Chatbot Service (Nginx): Port 80"
echo "  - Qdrant (Vector DB): Port 6333"
echo "  - Redis (Conversation Storage): Port 6379"
echo ""
echo "Useful commands:"
echo "  View logs:        $DOCKER_COMPOSE_CMD logs -f"
echo "  View chatbot logs: $DOCKER_COMPOSE_CMD logs -f chatbot"
echo "  View Qdrant logs:  $DOCKER_COMPOSE_CMD logs -f qdrant"
echo "  View Redis logs:   $DOCKER_COMPOSE_CMD logs -f redis"
echo "  Stop service:     $DOCKER_COMPOSE_CMD down"
echo "  Restart:          $DOCKER_COMPOSE_CMD restart"
echo "  Status:           $DOCKER_COMPOSE_CMD ps"
echo ""
echo "Qdrant Management:"
echo "  Qdrant Dashboard: http://${EC2_IP}:6333/dashboard"
echo "  Qdrant Health:    http://${EC2_IP}:6333/health"
echo "=========================================="

