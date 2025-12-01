@echo off
REM Git Setup Script for E-Nose Project

echo ========================================
echo Git Repository Setup
echo ========================================
echo.

REM Set Git path
set GIT="D:\Program Files\Git\bin\git.exe"

REM Configure Git user (ganti dengan info Anda)
echo [1/6] Configuring Git user...
%GIT% config --global user.name "ASUS"
%GIT% config --global user.email "your.email@example.com"
echo Done!
echo.

REM Initialize repository
echo [2/6] Initializing Git repository...
%GIT% init
echo Done!
echo.

REM Add all files
echo [3/6] Adding files to Git...
%GIT% add .
echo Done!
echo.

REM Create initial commit
echo [4/6] Creating initial commit...
%GIT% commit -m "Initial commit: E-Nose system with Edge Impulse integration"
echo Done!
echo.

echo ========================================
echo Repository initialized successfully!
echo ========================================
echo.
echo Next steps:
echo 1. Create a new repository on GitHub: https://github.com/new
echo 2. Copy the repository URL
echo 3. Run: setup_github_remote.bat
echo.
pause
