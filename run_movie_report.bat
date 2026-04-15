@echo off
title IMDb Movie Report Generator
color 0E

echo ╔══════════════════════════════════════════════════════╗
echo ║         ⭐ IMDb Movie Report Generator ⭐          ║
echo ║                                                      ║
echo ║  This tool fetches IMDb data for your video files    ║
echo ║  and generates a beautiful HTML report + a batch     ║
echo ║  file to rename files with IMDb ratings.             ║
echo ╚══════════════════════════════════════════════════════╝
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python from https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Install requests if not available
echo [INFO] Checking dependencies...
python -c "import requests" 2>nul
if %errorlevel% neq 0 (
    echo [INFO] Installing 'requests' library...
    pip install requests
    echo.
)

:: Run the script
echo [INFO] Launching IMDb Report Generator...
echo.
python "%~dp0generate_movie_report.py"

:: Keep window open if there was an error
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Script exited with an error.
    pause
)
