@echo off
REM Setup script for Autonomous Research & Execution Agent (Windows)

echo === Autonomous Research ^& Execution Agent Setup ===
echo.

REM Check Python version
echo Checking Python version...
python --version 2>nul
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    exit /b 1
)
echo Python found
echo.

REM Create virtual environment
echo Creating virtual environment...
if exist venv (
    echo Virtual environment already exists. Skipping...
) else (
    python -m venv venv
    echo Virtual environment created
)
echo.

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo Virtual environment activated
echo.

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip
echo pip upgraded
echo.

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
echo Dependencies installed
echo.

REM Install Playwright browsers
echo Installing Playwright browsers...
playwright install
echo Playwright browsers installed
echo.

REM Create required directories
echo Creating required directories...
if not exist data mkdir data
if not exist logs mkdir logs
if not exist outputs mkdir outputs
echo Directories created: data\, logs\, outputs\
echo.

REM Copy .env.example to .env if it doesn't exist
if exist .env (
    echo .env file already exists. Skipping...
) else (
    echo Creating .env file from template...
    copy .env.example .env
    echo .env file created
    echo.
    echo WARNING: Please edit .env and set your OPENROUTER_API_KEY
)
echo.

echo === Setup Complete ===
echo.
echo Next steps:
echo 1. Activate the virtual environment: venv\Scripts\activate.bat
echo 2. Edit .env and set your OPENROUTER_API_KEY
echo 3. Run the application: python main.py (when implemented)
echo 4. Run tests: pytest
echo.
pause
