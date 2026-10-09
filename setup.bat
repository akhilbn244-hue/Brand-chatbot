@echo off
REM ================================================================
REM  setup.bat - double-click ONCE to install everything.
REM  1. Checks Python is installed
REM  2. Creates a private "virtual environment" (.venv) for this project,
REM     so its toolboxes don't clash with other projects
REM  3. Installs the toolboxes listed in requirements.txt
REM  4. Creates your .env file and opens it so you can paste your key
REM ================================================================
cd /d "%~dp0"
title Brand Knowledge Chatbot - Setup

echo.
echo  Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  Python was not found. Reinstall it from python.org and tick
    echo  "Add Python to PATH" during installation. Then run this again.
    pause
    exit /b 1
)

echo  Creating the project environment (.venv)...
if not exist ".venv" python -m venv .venv

echo  Installing toolboxes - this takes 2-5 minutes the first time...
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo.
    echo  Installing failed. Check your internet connection and run setup.bat again.
    pause
    exit /b 1
)

if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo.
    echo  Opening .env - paste your Gemini key after GEMINI_API_KEY= then save and close.
    notepad ".env"
)

echo.
echo  ==============================================
echo   Setup finished. Now double-click run.bat
echo  ==============================================
pause
