@echo off
setlocal ENABLEDELAYEDEXPANSION

echo ==========================================
echo BeyondSight - Inicio rapido para Windows
echo ==========================================

where py >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python Launcher (py) no esta disponible.
    echo Instala Python 3.10+ desde https://www.python.org/downloads/
    exit /b 1
)

if not exist ".venv" (
    echo [INFO] Creando entorno virtual .venv...
    py -m venv .venv
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] No se pudo crear el entorno virtual.
        exit /b 1
    )
)

echo [INFO] Activando entorno virtual...
call .venv\Scripts\activate.bat
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] No se pudo activar el entorno virtual.
    exit /b 1
)

echo [INFO] Actualizando pip...
python -m pip install --upgrade pip
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Error al actualizar pip.
    exit /b 1
)

echo [INFO] Instalando dependencias...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Error al instalar dependencias.
    exit /b 1
)

if not exist ".env" (
    if exist ".env.example" (
        echo [INFO] Creando .env desde .env.example...
        copy /Y .env.example .env >nul
        echo [INFO] Archivo .env creado. Puedes editarlo para agregar tus API keys.
    )
)

echo [INFO] Iniciando BeyondSight en http://localhost:8501 ...
streamlit run app.py
set EXIT_CODE=%ERRORLEVEL%

if %EXIT_CODE% NEQ 0 (
    echo [ERROR] Streamlit termino con codigo %EXIT_CODE%.
    exit /b %EXIT_CODE%
)

endlocal
