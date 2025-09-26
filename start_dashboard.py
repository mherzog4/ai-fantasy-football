#!/usr/bin/env python3
"""
Enhanced startup script for Fantasy Football Dashboard
Properly handles uv environment and error checking
"""
import subprocess
import sys
import time
import threading
import signal
import os
from pathlib import Path

# Global process references for cleanup
api_process = None
streamlit_process = None

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n🛑 Shutting down Fantasy Football Dashboard...")
    
    if api_process:
        api_process.terminate()
    if streamlit_process:
        streamlit_process.terminate()
    
    sys.exit(0)

def start_fastapi():
    """Start the FastAPI server"""
    global api_process
    
    print("🚀 Starting FastAPI server...")
    print("📡 API will be available at: http://localhost:8000")
    print("📚 API docs will be available at: http://localhost:8000/docs")
    
    try:
        # Use uv to run the server
        api_process = subprocess.Popen([
            "uv", "run", "uvicorn", 
            "api.main:app", 
            "--reload", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ])
        
        # Wait for the server to start
        print("⏳ Waiting for FastAPI to start...")
        time.sleep(5)
        
        # Test if server is responding
        test_result = subprocess.run([
            "curl", "-s", "http://localhost:8000/"
        ], capture_output=True, text=True, timeout=5)
        
        if test_result.returncode == 0:
            print("✅ FastAPI server started successfully!")
            return True
        else:
            print("❌ FastAPI server failed to start properly")
            return False
            
    except Exception as e:
        print(f"❌ Error starting FastAPI: {e}")
        return False

def start_streamlit():
    """Start the Streamlit app"""
    global streamlit_process
    
    print("📊 Starting Streamlit app...")
    print("🌐 Dashboard will be available at: http://localhost:8501")
    
    try:
        # Use uv to run streamlit
        streamlit_process = subprocess.Popen([
            "uv", "run", "streamlit", "run", "client.py",
            "--server.port", "8501",
            "--server.address", "0.0.0.0"
        ])
        
        print("✅ Streamlit app started successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error starting Streamlit: {e}")
        return False

def main():
    """Main function to start both services"""
    print("🏈 Fantasy Football Dashboard Starting...")
    print("=" * 60)
    print("🔧 Using uv environment")
    print("=" * 60)
    
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    # Start FastAPI server first
    api_started = start_fastapi()
    if not api_started:
        print("💥 Failed to start FastAPI server. Exiting...")
        return 1
    
    print("-" * 60)
    
    # Start Streamlit app
    streamlit_started = start_streamlit()
    if not streamlit_started:
        print("💥 Failed to start Streamlit app. Exiting...")
        if api_process:
            api_process.terminate()
        return 1
    
    print("-" * 60)
    print("🎉 Fantasy Football Dashboard is ready!")
    print("🌐 Dashboard: http://localhost:8501")
    print("📡 API: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("=" * 60)
    print("Press Ctrl+C to stop the dashboard")
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
            
            # Check if processes are still running
            if api_process and api_process.poll() is not None:
                print("❌ FastAPI server stopped unexpectedly")
                break
                
            if streamlit_process and streamlit_process.poll() is not None:
                print("❌ Streamlit app stopped unexpectedly")
                break
                
    except KeyboardInterrupt:
        pass
    
    return 0

if __name__ == "__main__":
    sys.exit(main())