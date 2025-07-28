@echo off
echo Starting Autonomous Agent...

REM Check if .env file exists
if not exist ".env" (
    echo ERROR: .env file not found!
    echo Please copy .env.example to .env and configure your API keys
    pause
    exit /b 1
)

REM Launch the agent
start /min AutonomousAgent.exe

echo Agent started in background. Check http://localhost:8000/status for monitoring.
