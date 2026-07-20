@echo off
title Local Utility & Plugin Hub Launcher

:: Auto-detect Python environment
set PYTHON_CMD=python
where python >nul 2>nul
if %errorlevel% neq 0 (
    if exist "E:\environment\Miniconda3\python.exe" (
        set PYTHON_CMD="E:\environment\Miniconda3\python.exe"
    ) else if exist "E:\language\Python\python.exe" (
        set PYTHON_CMD="E:\language\Python\python.exe"
    ) else (
        echo [ERROR] Python not found in PATH or standard paths.
        echo Please install Python, or edit this run.bat to specify python.exe path.
        pause
        exit /b 1
    )
)

:: Support drag and drop folder
if "%~1" neq "" (
    echo [INFO] Direct organizing dropped directory: "%~1"
    %PYTHON_CMD% "%~dp0main.py" "%~1"
    echo.
    echo [INFO] Done. dashboard.html generated.
    pause
    exit /b 0
)

:menu
cls
echo ===================================================
  echo     Local Plugin Hub & Utility Platform (Launcher)
echo ===================================================
echo  [Tips] You can configure Environment in .env file.
echo  [Drag] You can drag any folder onto run.bat icon.
echo.
echo  [1] Run Sandbox Verification (Test integration for all plugins)
echo  [2] Start Graphical Control Console (GUI Platform)
echo  [3] Setup Messy Test Directory
echo  [4] Exit
echo ===================================================
echo.
set /p opt="Please select option (1-4): "

if "%opt%"=="1" (
    echo.
    echo Running sandbox integration tests...
    %PYTHON_CMD% "%~dp0main.py" --test-all
    pause
    goto menu
)

if "%opt%"=="2" (
    echo.
    echo Launching Graphical Console...
    %PYTHON_CMD% "%~dp0main.py"
    goto menu
)

if "%opt%"=="3" (
    echo.
    echo Generating mock files for local testing...
    %PYTHON_CMD% "%~dp0main.py" --setup-test
    pause
    goto menu
)

if "%opt%"=="4" (
    exit /b 0
)

goto menu
