@echo off
REM Warren Bot Docker Build Script for Windows
REM This script builds the Warren Bot Docker image with proper tags

setlocal enabledelayedexpansion

REM Configuration
set IMAGE_NAME=warren-bot
for /f "tokens=3" %%i in ('findstr "^version = " pyproject.toml') do (
    set VERSION=%%i
    set VERSION=!VERSION:"=!
)
if "%DOCKER_REGISTRY%"=="" (
    set REGISTRY=
) else (
    set REGISTRY=%DOCKER_REGISTRY%
)

echo Building Warren Bot Docker Image
echo Version: %VERSION%
echo Image: %IMAGE_NAME%

REM Build the image
echo Building Docker image...
docker build -t "%IMAGE_NAME%:latest" -t "%IMAGE_NAME%:%VERSION%" .
if errorlevel 1 (
    echo Build failed!
    exit /b 1
)

REM If registry is set, also tag for registry
if not "%REGISTRY%"=="" (
    echo Tagging for registry: %REGISTRY%
    docker tag "%IMAGE_NAME%:latest" "%REGISTRY%/%IMAGE_NAME%:latest"
    docker tag "%IMAGE_NAME%:%VERSION%" "%REGISTRY%/%IMAGE_NAME%:%VERSION%"
)

echo Build completed successfully!
echo Available tags:
docker images %IMAGE_NAME%

REM Optional: Run a quick test
echo Testing image...
docker run --rm "%IMAGE_NAME%:latest" python -c "import warren_bot; print('Import test passed')"
if errorlevel 1 (
    echo Import test failed!
    exit /b 1
)

echo Docker build and test completed successfully!
echo.
echo To run the bot:
echo   docker-compose up -d
echo.
echo To push to registry (if configured):
if not "%REGISTRY%"=="" (
    echo   docker push %REGISTRY%/%IMAGE_NAME%:latest
    echo   docker push %REGISTRY%/%IMAGE_NAME%:%VERSION%
) else (
    echo   Set DOCKER_REGISTRY environment variable first
)

pause