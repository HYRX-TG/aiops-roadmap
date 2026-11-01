@echo off
chcp 65001 >nul
title AIOps Knowledge Map - Dev Server
cd /d D:\aiops-roadmap
echo ================================================
echo   AIOps Knowledge Map  (infra-roadmap fork)
echo   URL: http://localhost:3000
echo   Keep this window OPEN while using.
echo ================================================
start /b cmd /c "timeout /t 8 /nobreak >nul && start "" http://localhost:3000"
call "C:\Users\tang\.workbuddy\binaries\node\versions\22.22.2-3\npm.cmd" run dev
echo.
echo Server stopped. Press any key to close.
pause >nul
