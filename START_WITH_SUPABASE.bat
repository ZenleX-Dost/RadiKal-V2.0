@echo off
REM RadiKal Backend + Supabase Quick Start Script

echo.
echo ========================================
echo   RadiKal + Supabase Integration
echo ========================================
echo.

REM Check if we're in the right directory
if not exist "backend\main.py" (
    echo ERROR: Please run this script from the RadiKal-V2.0 root directory
    pause
    exit /b 1
)

echo [1/5] Checking Docker Desktop...
docker version >nul 2>&1
if errorlevel 1 (
    echo.
    echo WARNING: Docker Desktop is not running!
    echo.
    echo Supabase requires Docker Desktop to run locally.
    echo.
    echo Please:
    echo   1. Start Docker Desktop
    echo   2. Wait for it to fully start
    echo   3. Run this script again
    echo.
    pause
    exit /b 1
)
echo     Docker Desktop is running!

echo.
echo [2/5] Installing Python dependencies...
cd backend
pip install sqlalchemy==2.0.23 psycopg2-binary==2.9.9 >nul 2>&1
if errorlevel 1 (
    echo     WARNING: Some packages may already be installed
) else (
    echo     Dependencies installed successfully!
)

echo.
echo [3/5] Starting Supabase...
cd ..\frontend-makerkit\apps\web
call pnpm supabase:start
if errorlevel 1 (
    echo.
    echo ERROR: Failed to start Supabase
    echo.
    echo Please check:
    echo   - Docker Desktop is running
    echo   - Ports 54321-54324 are available
    echo   - .env.local file is valid
    echo.
    cd ..\..\..
    pause
    exit /b 1
)

echo.
echo [4/5] Applying RadiKal database schema...
timeout /t 5 /nobreak >nul
call pnpm supabase db reset
if errorlevel 1 (
    echo     WARNING: Migration may have issues, but continuing...
)

echo.
echo [5/5] Testing database connection...
cd ..\..\..
cd backend

python -c "import os; os.environ['DATABASE_TYPE'] = 'supabase'; from db.database import engine, init_db; init_db(); print('Database connection successful!')"
if errorlevel 1 (
    echo.
    echo ERROR: Database connection failed
    echo.
    echo Please check backend\.env configuration
    pause
    exit /b 1
)

echo.
echo ========================================
echo   SUCCESS! Setup Complete
echo ========================================
echo.
echo Supabase is running at:
echo   - Studio UI: http://127.0.0.1:54323
echo   - API: http://127.0.0.1:54321
echo   - Database: postgresql://postgres:postgres@127.0.0.1:54322/postgres
echo.
echo Next steps:
echo   1. Start backend: cd backend ^& python main.py
echo   2. Visit API docs: http://localhost:8000/docs
echo   3. View database: http://127.0.0.1:54323
echo.
pause
