# Mộc Healthy Platform - Local Development Startup Script (PowerShell)
param (
    [switch]$Docker
)

Write-Host "==========================================================" -ForegroundColor Green
Write-Host "  MỘC HEALTHY PLATFORM — LOCAL DEVELOPMENT LAUNCHER" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green

if ($Docker) {
    Write-Host "[1/1] Starting complete stack with Docker Compose..." -ForegroundColor Cyan
    docker compose up --build
} else {
    Write-Host "[1/3] Checking environment..." -ForegroundColor Cyan
    if (-not (Test-Path ".env")) {
        Copy-Item ".env.example" ".env"
        Write-Host "Created .env from .env.example" -ForegroundColor Yellow
    }

    Write-Host "[2/3] Installing workspace dependencies..." -ForegroundColor Cyan
    npm.cmd install

    Write-Host "[3/3] Ready to start individual services:" -ForegroundColor Cyan
    Write-Host "  - API:        uvicorn app.main:app --app-dir apps/api --reload --port 8000" -ForegroundColor White
    Write-Host "  - Admin:      npm.cmd run dev:admin (http://localhost:3000)" -ForegroundColor White
    Write-Host "  - Storefront: npm.cmd run dev:storefront (http://localhost:3001)" -ForegroundColor White
    Write-Host ""
}
