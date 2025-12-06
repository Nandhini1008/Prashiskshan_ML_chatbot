#!/bin/bash

# Start SSE-enabled chatbot service with pre-warming

echo "🚀 Starting SSE-enabled chatbot service..."
echo "================================================"

# Set environment variables
export CHATBOT_SERVICE_PORT=5001
export CHATBOT_SERVICE_HOST=0.0.0.0

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3."
    exit 1
fi

# Check if required packages are installed
echo "📦 Checking dependencies..."
python3 -c "import flask" 2>/dev/null || {
    echo "❌ Flask not installed. Run: pip install flask flask-cors"
    exit 1
}

# Start the service
echo "✅ Starting service on port $CHATBOT_SERVICE_PORT..."
echo "================================================"
python3 chatbot_service_sse.py
