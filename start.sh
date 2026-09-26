#!/bin/bash
set -e

echo "=========================================="
echo "  🚀 Starting AI Interview Platform"
echo "=========================================="

# 1. Setup Virtualenv if not present
if [ ! -d ".venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
else
    source .venv/bin/activate
fi

# 2. Setup client dependencies if needed
if [ ! -d "client/node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    cd client && npm install && cd ..
fi

# 3. Start Backend
echo "🟢 Starting FastAPI Backend on http://localhost:8000..."
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# 4. Start Frontend
echo "🟢 Starting React Frontend on http://localhost:5173..."
cd client && npm run dev &
FRONTEND_PID=$!
cd ..

# Cleanup handler on exit
trap "echo 'Shutting down...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true; exit 0" SIGINT SIGTERM

echo ""
echo "=========================================="
echo "  ✅ App is Live!"
echo "  🌐 Frontend: http://localhost:5173"
echo "  📖 API Docs: http://localhost:8000/docs"
echo "=========================================="
echo "Press Ctrl+C to stop all servers."

wait
