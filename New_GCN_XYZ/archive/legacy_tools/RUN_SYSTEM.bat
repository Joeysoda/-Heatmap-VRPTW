@echo off
REM AGV Scheduling System Startup Script
REM This script ensures proper Python environment and runs the system

echo ======================================================================
echo   AGV Scheduling System - Startup Script
echo ======================================================================
echo.

REM Check if numpy is installed
python -c "import numpy" 2>nul
if errorlevel 1 (
    echo [INFO] Installing required packages: numpy, openpyxl...
    pip install numpy openpyxl
    echo.
)

REM Check if openpyxl is installed
python -c "import openpyxl" 2>nul
if errorlevel 1 (
    echo [INFO] Installing openpyxl...
    pip install openpyxl
    echo.
)

echo [INFO] Starting AGV Scheduling System...
echo [INFO] Press Ctrl+C to stop the system
echo.

REM Run the system
python "%~dp0anylogic_file_bridge.py"

pause
