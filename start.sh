#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

echo "=== LLM Machine Launcher ==="

# Activate venv
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Creating Python venv..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
fi

# Install frontend deps
if [ -d "frontend/node_modules" ]; then
    echo "Frontend deps OK"
else
    echo "Installing frontend deps..."
    cd frontend && npm install && cd ..
fi

# Check Ollama
echo "Checking Ollama..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "Ollama: OK"
else
    echo "WARNING: Ollama is not running. Start it with: ollama serve"
fi

# Start backend server in background
echo "Starting backend server..."
source venv/bin/activate
python backend/server.py &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

# Wait for backend
sleep 2

# Start Electron
echo "Starting Electron app..."
cd frontend
npx electron .
cd ..

# Cleanup
echo "Shutting down..."
kill $BACKEND_PID 2>/dev/null
