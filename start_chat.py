#!/usr/bin/env python3
"""
Enhanced startup script for Fantasy Football AI Chat Interface
Starts both API and the new chat interface
"""
import subprocess
import sys
import time
import signal
import os

# Global process references for cleanup
api_process = None
chat_process = None

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n🛑 Shutting down Fantasy Football AI Chat...")
    
    if api_process:
        api_process.terminate()
    if chat_process:
        chat_process.terminate()
    
    sys.exit(0)

def start_fastapi():
    """Start the FastAPI server"""
    global api_process
    
    print("🚀 Starting FastAPI server...")
    print("📡 API will be available at: http://localhost:8000")
    print("📚 API docs will be available at: http://localhost:8000/docs")
    
    try:
        # Use uv to run the server if available, fallback to python
        try:
            api_process = subprocess.Popen([
                "uv", "run", "uvicorn", 
                "api.main:app", 
                "--reload", 
                "--host", "0.0.0.0", 
                "--port", "8000"
            ])
        except FileNotFoundError:
            # Fallback to regular python
            api_process = subprocess.Popen([
                sys.executable, "-m", "uvicorn", 
                "api.main:app", 
                "--reload", 
                "--host", "0.0.0.0", 
                "--port", "8000"
            ])
        
        # Wait for the server to start
        print("⏳ Waiting for FastAPI to start...")
        time.sleep(5)
        
        print("✅ FastAPI server started successfully!")
        return True
            
    except Exception as e:
        print(f"❌ Error starting FastAPI: {e}")
        return False

def start_chat_interface():
    """Start the AI Chat interface"""
    global chat_process
    
    print("🤖 Starting AI Chat Interface...")
    print("💬 Chat will be available at: http://localhost:8501")
    
    try:
        # Use uv to run streamlit if available, fallback to python
        try:
            chat_process = subprocess.Popen([
                "uv", "run", "streamlit", "run", "main_client.py",
                "--server.port", "8501",
                "--server.address", "0.0.0.0"
            ])
        except FileNotFoundError:
            # Fallback to regular python
            chat_process = subprocess.Popen([
                sys.executable, "-m", "streamlit", "run", "main_client.py",
                "--server.port", "8501",
                "--server.address", "0.0.0.0"
            ])
        
        print("✅ AI Chat Interface started successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error starting Chat Interface: {e}")
        return False

def main():
    """Main function to start both services"""
    print("🤖 Fantasy Football AI Chat Starting...")
    print("=" * 60)
    print("🔧 Initializing services...")
    print("=" * 60)
    
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    # Start FastAPI server first
    api_started = start_fastapi()
    if not api_started:
        print("💥 Failed to start FastAPI server. Exiting...")
        return 1
    
    print("-" * 60)
    
    # Start Chat Interface
    chat_started = start_chat_interface()
    if not chat_started:
        print("💥 Failed to start Chat Interface. Exiting...")
        if api_process:
            api_process.terminate()
        return 1
    
    print("-" * 60)
    print("🎉 Fantasy Football AI Chat is ready!")
    print("🤖 AI Chat: http://localhost:8501")
    print("📡 API: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("=" * 60)
    print("💬 Start chatting with your AI fantasy assistant!")
    print("Press Ctrl+C to stop the services")
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
            
            # Check if processes are still running
            if api_process and api_process.poll() is not None:
                print("❌ FastAPI server stopped unexpectedly")
                break
                
            if chat_process and chat_process.poll() is not None:
                print("❌ Chat Interface stopped unexpectedly")
                break
                
    except KeyboardInterrupt:
        pass
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
