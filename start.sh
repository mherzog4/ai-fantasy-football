#!/bin/bash

echo "🏈 Starting Fantasy Football Dashboard..."
echo "=========================================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found! Please create one with your ESPN and OpenAI API keys."
    exit 1
fi

echo "✅ .env file found"

# Start FastAPI server in background
echo "🚀 Starting FastAPI server on port 8000..."
uvicorn api.get_roster:app --reload --host 0.0.0.0 --port 8000 &
API_PID=$!

# Wait a moment for API to start
sleep 3

# Start Streamlit app
echo "📊 Starting Streamlit app on port 8501..."
streamlit run client.py --server.port 8501 --server.address 0.0.0.0

# Cleanup function
cleanup() {
    echo "🛑 Shutting down services..."
    kill $API_PID 2>/dev/null
    exit 0
}

# Trap Ctrl+C
trap cleanup INT

# Wait for background process
wait $API_PID
