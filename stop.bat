@echo off
echo =========================================
echo Stopping Self-RAG Environment...
echo =========================================

echo.
echo Stopping Docker databases...
cd /d "%~dp0"
call docker compose down

echo.
echo Databases stopped successfully!
echo (Remember to close your backend and frontend terminal windows if they are still open)
echo =========================================
pause
