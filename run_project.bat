@echo off
SETLOCAL EnableDelayedExpansion

echo ============================================================
echo   Precision Oncology AI - Distributed HDFS Startup
echo ============================================================
echo.

:: 1. Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not running. 
    echo Please start Docker Desktop and try again.
    pause
    exit /b
)

:: 2. Start the Cluster
echo [1/3] Launching Docker Containers...
docker-compose up -d --build

if %errorlevel% neq 0 (
    echo [ERROR] Failed to start Docker containers.
    pause
    exit /b
)

:: 3. Run HDFS Initialization (wait for nodes and set 1GB quota)
echo [2/3] Initializing Distributed HDFS Layer...
echo (This will wait for the NameNode to be fully ready)
docker-compose exec api python init_hdfs.py

if %errorlevel% neq 0 (
    echo [ERROR] HDFS Initialization failed.
    pause
    exit /b
)

:: 4. Final Status
echo.
echo [3/3] Project is LIVE!
echo.
echo  - Frontend UI:  http://localhost:5173
echo  - API Docs:     http://localhost:8000/docs
echo  - Hadoop UI:    http://localhost:9870
echo.
echo.
echo NOTE: Synthetic data generation is NOT run by default.
echo To fill the 1GB quota with gene data, run:
echo docker-compose exec api python scripts/generate_gene_data_hdfs.py
echo.
pause
