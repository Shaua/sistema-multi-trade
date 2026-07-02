@echo off
title Sistema 3 Multi Trade - Iniciando Servidores

echo ================================================
echo   Sistema 3 Multi Trade - Iniciando Servidores
echo ================================================
echo.

:: Inicia o backend em uma nova janela
echo [1/2] Iniciando Backend (FastAPI)...
start "Backend - FastAPI" cmd /k "cd /d "%~dp0backend" && venv\Scripts\activate && uvicorn app.main:app --reload"

:: Aguarda 2 segundos para o backend subir primeiro
timeout /t 2 /nobreak >nul

:: Inicia o frontend em uma nova janela
echo [2/2] Iniciando Frontend (Vite)...
start "Frontend - Vite" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo.
echo ================================================
echo   Servidores iniciados!
echo   Backend:  http://127.0.0.1:8000
echo   Frontend: http://localhost:5173
echo ================================================
echo.
echo Esta janela pode ser fechada.
pause
