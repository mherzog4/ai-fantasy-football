import subprocess
import sys
import time
import threading
import webbrowser
from pathlib import Path

def start_fastapi():
    """Start the FastAPI server"""
    print("🚀 Starting FastAPI server...")
    
    # Try using uv first since you have a uv environment
    try:
        result = subprocess.run([
            "uv", "run", "uvicorn", 
            "api.main:app", 
            "--reload", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ], check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback to direct python/pip
        print("uv not found, falling back to direct python...")
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "api.main:app", 
            "--reload", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ])

def start_streamlit():
    """Start the AI Chat Interface"""
    print("🤖 Starting AI Chat Interface...")
    time.sleep(5)  # Give FastAPI more time to start properly
    
    try:
        subprocess.run([
            "uv", "run", "streamlit", "run", "main_client.py",
            "--server.port", "8501",
            "--server.address", "0.0.0.0"
        ], check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("uv not found, falling back to direct python...")
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "main_client.py",
            "--server.port", "8501",
            "--server.address", "0.0.0.0"
        ])

def main():
    print("🤖 Fantasy Football AI Chat Starting...")
    print("=" * 50)
    
    # Start FastAPI in a separate thread
    api_thread = threading.Thread(target=start_fastapi, daemon=True)
    api_thread.start()
    
    # Start Streamlit in the main thread
    start_streamlit()

if __name__ == "__main__":
    main()
