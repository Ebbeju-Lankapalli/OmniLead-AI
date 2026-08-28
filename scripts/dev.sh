#!/bin/bash

set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cleanup() {
    echo
    echo "Stopping OmniLead AI..."
    kill 0
}

trap cleanup SIGINT SIGTERM

echo "========================================"
echo "       OmniLead AI Development"
echo "========================================"
echo
echo "Starting backend:  http://localhost:8000"
echo "Starting frontend: http://localhost:5173"
echo

cd "$ROOT_DIR/backend"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &

cd "$ROOT_DIR/frontend"
npm run dev &

wait
