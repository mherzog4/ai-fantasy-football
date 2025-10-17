#!/bin/bash

# Fantasy Football Dashboard - Next.js Frontend Launcher
# This script starts the Next.js frontend server

echo "🏈 Starting Fantasy Football Dashboard (Next.js)..."

cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Start the development server
echo "🚀 Starting Next.js development server on http://localhost:3000"
npm run dev
