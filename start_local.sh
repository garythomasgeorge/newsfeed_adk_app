#!/bin/bash

# Function to kill background processes on exit
cleanup() {
    echo "Stopping servers..."
    kill $(jobs -p) 2>/dev/null
}
trap cleanup EXIT

echo "=== Starting Batch-Processed AI News Aggregator (Local) ==="

# 1. Backend Setup
echo "[Backend] Checking dependencies..."
if [ ! -d "backend/.venv" ]; then
    echo "[Backend] Creating virtual environment..."
    python3 -m venv backend/.venv
fi

source backend/.venv/bin/activate
pip install -r backend/requirements.txt

echo "[Backend] Starting FastAPI server..."
uvicorn backend.main:app --reload --port 8080 &
BACKEND_PID=$!

# 2. Frontend Setup
echo "[Frontend] Installing dependencies..."
cd frontend
if [ ! -d "node_modules" ]; then
    npm install
fi

echo "[Frontend] Starting Vite dev server..."
npm run dev &
FRONTEND_PID=$!

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
