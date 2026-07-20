@echo off
setlocal EnableDelayedExpansion
title HandyWorkstation Product Executable Builder
chcp 65001 >nul

echo ===================================================
echo   HandyWorkstation Product Executable Builder
echo ===================================================
echo.

:: Detect Python Environment
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

:: Check PyInstaller
echo [*] Checking PyInstaller...
%PYTHON_CMD% -m PyInstaller --version >nul 2>nul
if !errorlevel! neq 0 (
    echo [*] PyInstaller not found. Installing PyInstaller via pip...
    %PYTHON_CMD% -m pip install pyinstaller
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to install PyInstaller.
        pause
        exit /b 1
    )
)

echo [*] Cleaning previous build artifacts...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

echo [*] Building Portable Single Executable Product...
%PYTHON_CMD% -m PyInstaller HandyWorkstation.spec --noconfirm

if !errorlevel! neq 0 (
    echo.
    echo [ERROR] Build failed! Check errors above.
    pause
    exit /b 1
)

echo.
echo ===================================================
echo  [SUCCESS] HandyWorkstation packaged successfully!
echo  [Product Executable] dist\HandyWorkstation.exe
echo ===================================================
echo.
pause
