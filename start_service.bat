@echo off
echo Starting Chatbot HTTP Service...
echo.
echo This will initialize the chatbot (takes ~10-15 seconds)
echo Service will run on http://localhost:5001
echo.
echo Press Ctrl+C to stop the service
echo.

cd /d %~dp0
python chatbot_service.py

pause

