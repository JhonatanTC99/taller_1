@echo off
title Orquestador Dollarcity AI - Módulo 3
color 0A

echo ========================================================
echo   INICIANDO ECOSISTEMA AGENTICO DOLLARCITY (MODULO 3)
echo ========================================================
echo.

echo [1/3] Navegando al directorio del backend...
cd backend || (
    echo [ERROR] No se encontro la carpeta 'backend'. Asegurate de que este archivo .bat este en la raiz del proyecto.
    pause
    exit /b
)

echo.
echo [2/3] Levantando infraestructura (PostgreSQL) con Docker...
docker compose up -d
echo Esperando 5 segundos a que el motor de BD inicialice...
timeout /t 5 /nobreak > NUL
echo.

echo [3/3] Iniciando Servidor de Produccion (FastAPI)...
echo.
echo --------------------------------------------------------
echo RECORDATORIOS PARA LA SUSTENTACION:
echo 1. Recuerda tener ngrok corriendo en otra terminal: 
echo    ngrok http 8000
echo 2. Tu N8N debe apuntar al endpoint:
echo    https://[tu-url-ngrok]/api/channel/chat
echo --------------------------------------------------------
echo.
echo [ INFO ] Presiona CTRL+C para detener el servidor.
echo.

:: Lanza FastAPI con uv
uv run python main.py --server

pause