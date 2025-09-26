@echo off
echo 🏈 Starting Fantasy Football Dashboard...
echo ==========================================

REM Check if .env file exists
if not exist .env (
    echo ❌ .env file not found! Please create one with your ESPN and OpenAI API keys.
    pause
    exit /b 1
)

echo ✅ .env file found

REM Start FastAPI server in background
echo 🚀 Starting FastAPI server on port 8000...
start /b uvicorn api.get_roster:app --reload --host 0.0.0.0 --port 8000

REM Wait a moment for API to start
timeout /t 3 /nobreak >nul

REM Start Streamlit app
echo 📊 Starting Streamlit app on port 8501...
streamlit run client.py --server.port 8501 --server.address 0.0.0.0

pause
