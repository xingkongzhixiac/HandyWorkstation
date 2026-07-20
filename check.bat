@echo off
setlocal EnableDelayedExpansion
title HandyWorkstation Workflow & Quality Gate Checker
chcp 65001 >nul

echo ===================================================
echo   HandyWorkstation Workflow & Quality Gate Checker
echo ===================================================
echo.

:: Detect Python
set PYTHON_CMD=python
where python >nul 2>nul
if !errorlevel! neq 0 (
    if exist "E:\environment\Miniconda3\python.exe" (
        set PYTHON_CMD="E:\environment\Miniconda3\python.exe"
    ) else if exist "E:\language\Python\python.exe" (
        set PYTHON_CMD="E:\language\Python\python.exe"
    ) else (
        echo [ERROR] Python environment not detected.
        pause
        exit /b 1
    )
)

%PYTHON_CMD% "%~dp0check.py"
pause
