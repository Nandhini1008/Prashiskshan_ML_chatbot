@echo off
REM Start SSE-enabled chatbot service with pre-warming

echo Starting SSE-enabled chatbot service...
echo ================================================

REM Set environment variables
set CHATBOT_SERVICE_PORT=5001
set CHATBOT_SERVICE_HOST=0.0.0.0

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Python not found. Please install Python 3.
    exit /b 1
)

REM Start the service
echo Starting service on port %CHATBOT_SERVICE_PORT%...
echo ================================================
python chatbot_service_sse.py
