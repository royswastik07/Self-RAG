@echo off
echo =========================================
echo Starting Self-RAG Environment...
echo =========================================

echo.
echo Starting Docker databases (Qdrant & PostgreSQL)...
cd /d "%~dp0"
call docker compose up -d

echo.
echo Starting Backend (FastAPI)...
start cmd /k "cd /d %~dp0backend && uv run uvicorn api.main:app --reload"

echo.
echo Starting Frontend (React)...
start cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo All services started! You can close this window.
echo (The backend and frontend are running in separate terminal windows)
echo =========================================
pause
