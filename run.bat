@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo   VarTex - Portable Environment Launcher/Bootstrapper
echo ===================================================
echo.

REM 1. Check if python is in PATH
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in your system PATH.
    echo Please install Python 3.10 or higher on this computer to run VarTex.
    pause
    exit /b 1
)

REM Get python version and display
for /f "tokens=*" %%i in ('python --version') do set PY_VER=%%i
echo Detected system Python: !PY_VER!

REM Check and setup/fix environment
set "VENV_OK=0"
if exist "venv\" (
    echo [INFO] Verifying existing virtual environment...
    venv\Scripts\python.exe -c "import sys" >nul 2>nul
    if !errorlevel! equ 0 (
        set "VENV_OK=1"
        echo [SUCCESS] Virtual environment is functional.
    ) else (
        echo [WARNING] The virtual environment in 'venv' appears to be broken or configured for another machine/path.
        echo [INFO] Re-creating virtual environment to match this computer's Python installation...
        echo Removing old venv...
        rmdir /s /q venv
    )
)

if "!VENV_OK!" neq "1" (
    echo Creating virtual environment...
    python -m venv venv
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo.
    echo Installing requirements, this may take a minute...
    venv\Scripts\python.exe -m pip install --upgrade pip
    venv\Scripts\pip install -r requirements.txt
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to install dependencies.
        pause
        exit /b 1
    )
    echo [SUCCESS] Virtual environment configured successfully.
    echo.
)

REM Run VarTex with any arguments passed to this batch file
if "%~1"=="" (
    echo To run VarTex, use: run.bat [arguments]
    echo Example: run.bat THYAO.IS
    echo Example: run.bat --portfolio THYAO.IS AAPL --amount 10000
    echo Example: run.bat --no-interactive THYAO.IS
    echo.
    echo Running default test run to check system health...
    echo.
    venv\Scripts\python.exe main.py THYAO.IS --no-interactive
) else (
    venv\Scripts\python.exe main.py %*
)

endlocal
