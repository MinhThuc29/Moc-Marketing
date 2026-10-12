#!/usr/bin/env bash
set -e

echo "=========================================================="
echo "  MỘC HEALTHY PLATFORM — LOCAL DEVELOPMENT LAUNCHER"
echo "=========================================================="

if [ "$1" == "--docker" ]; then
    echo "[1/1] Starting complete stack with Docker Compose..."
    docker compose up --build
else
    echo "[1/3] Checking environment..."
    if [ ! -f ".env" ]; then
        cp .env.example .env
        echo "Created .env from .env.example"
    fi

    echo "[2/3] Installing workspace dependencies..."
    npm install

    echo "[3/3] Ready to start individual services:"
    echo "  - API:        uvicorn app.main:app --app-dir apps/api --reload --port 8000"
    echo "  - Admin:      npm run dev:admin (http://localhost:3000)"
    echo "  - Storefront: npm run dev:storefront (http://localhost:3001)"
    echo ""
fi
