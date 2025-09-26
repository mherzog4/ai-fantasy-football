#!/usr/bin/env python3
"""
Startup script for the FastAPI server
"""
import uvicorn
from api.main import app

if __name__ == "__main__":
    print("🚀 Starting FastAPI server...")
    print("📡 API will be available at: http://localhost:8000")
    print("📚 API docs will be available at: http://localhost:8000/docs")
    print("🔄 Auto-reload enabled for development")
    print("=" * 50)
    
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
