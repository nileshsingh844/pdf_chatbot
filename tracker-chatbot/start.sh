#!/usr/bin/env bash
set -e

echo "Starting PDF Chatbot for Hugging Face Space..."

# Create necessary directories
mkdir -p /app/data/uploads
mkdir -p /app/data/chroma_db

# Function to check if a service is ready
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    echo "Waiting for $service_name to be ready on $host:$port..."
    
    local max_attempts=30
    local attempt=1
    
    while ! nc -z "$host" "$port"; do
        if [ $attempt -ge $max_attempts ]; then
            echo "ERROR: $service_name failed to start after ${max_attempts} attempts"
            exit 1
        fi
        echo "Waiting for $service_name... (attempt $attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    done
    echo "$service_name is ready!"
}

echo "Starting FastAPI backend on :8000..."
cd /app
/app/backend/.venv/bin/uvicorn backend.app.api.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --log-level info &

BACKEND_PID=$!

# Wait for backend to be ready
wait_for_service localhost 8000 "Backend"

echo "Starting Next.js frontend on :7860..."
cd /app/frontend
npm run start -- --port 7860 --hostname 0.0.0.0 &

FRONTEND_PID=$!

# Function to cleanup processes
cleanup() {
    echo "Shutting down services..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    exit 0
}

# Trap signals for graceful shutdown
trap cleanup SIGTERM SIGINT

# Wait for processes
wait $BACKEND_PID $FRONTEND_PID
