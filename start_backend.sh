#!/bin/bash

# Fantasy Football Backend Starter
# This script activates the virtual environment and starts the backend

echo "🚀 Starting Fantasy Football Backend..."

# Check if virtual environment exists
if [ -d ".venv" ]; then
    echo "📦 Activating virtual environment..."
    source .venv/bin/activate
elif [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
fi

# Start the FastAPI server using uvicorn
echo "🌟 Starting FastAPI server with uvicorn..."
if command -v python3 &> /dev/null; then
    echo "Using python3..."
    python3 -m uvicorn api.main:app --reload --port 8000
elif command -v python &> /dev/null; then
    echo "Using python..."
    python -m uvicorn api.main:app --reload --port 8000
else
    echo "❌ No Python installation found!"
    echo "Please install Python 3.9+ and try again."
    exit 1
fi
