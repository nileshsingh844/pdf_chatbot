#!/usr/bin/env bash
set -e

echo "Starting PDF Chatbot for Hugging Face Space..."

# Debug GROQ_API_KEY presence
echo "DEBUG: GROQ_API_KEY present? -> ${GROQ_API_KEY:+YES}"
echo "DEBUG: GROQ_API_KEY length -> ${#GROQ_API_KEY}"

# Debug Python environment
python -c "import os; print('PY DEBUG GROQ_API_KEY:', repr(os.getenv('GROQ_API_KEY')))"

# Export GROQ_API_KEY explicitly for Python processes
export GROQ_API_KEY="${GROQ_API_KEY}"

# Create data directories
mkdir -p ./data/uploads ./data/chroma_db

# Function to wait for service
wait_for_service() {
    local url=$1
    local max_attempts=30
    local attempt=1
    
    echo "Waiting for service at $url..."
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "$url" > /dev/null 2>&1; then
            echo "Service is ready!"
            return 0
        fi
        echo "Attempt $attempt/$max_attempts: Service not ready, waiting 2 seconds..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "Service failed to start after $max_attempts attempts"
    return 1
}

# Start backend
echo "Starting FastAPI backend..."
python -m uvicorn backend.app.api.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --log-level info &
BACKEND_PID=$!

# Wait for backend to be ready
wait_for_service "http://localhost:8000/api/health"

# Start frontend
echo "Starting Next.js frontend..."
cd frontend
npm run start &
FRONTEND_PID=$!

# Wait for frontend to be ready
wait_for_service "http://localhost:7860"

# Function to handle graceful shutdown
cleanup() {
    echo "Shutting down services..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

# Keep script running
wait $BACKEND_PID $FRONTEND_PID
