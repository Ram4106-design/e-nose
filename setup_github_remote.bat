@echo off
REM GitHub Remote Setup Script

echo ========================================
echo GitHub Remote Setup
echo ========================================
echo.

REM Set Git path
set GIT="D:\Program Files\Git\bin\git.exe"

REM Ask for GitHub repository URL
set /p REPO_URL="Enter your GitHub repository URL (e.g., https://github.com/username/enose.git): "

echo.
echo [1/3] Adding remote origin...
%GIT% remote add origin %REPO_URL%
echo Done!
echo.

echo [2/3] Setting branch to main...
%GIT% branch -M main
echo Done!
echo.

echo [3/3] Pushing to GitHub...
%GIT% push -u origin main
echo Done!
echo.

echo ========================================
echo Successfully pushed to GitHub!
echo ========================================
echo.
echo Your repository is now available at:
echo %REPO_URL%
echo.
pause
