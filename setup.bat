@echo off
echo 🎤 Voice Clone Chat - Quick Setup Script
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js is not installed. Please install Node.js 18 or higher.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
for /f "tokens=*" %%i in ('node --version') do set NODE_VERSION=%%i

echo ✅ Python found: %PYTHON_VERSION%
echo ✅ Node.js found: %NODE_VERSION%
echo.

REM Setup Backend
echo 📦 Setting up Backend...
cd backend

REM Create virtual environment
if not exist "venv" (
    python -m venv venv
    echo ✅ Virtual environment created
)

REM Activate virtual environment and install dependencies
call venv\Scripts\activate
pip install -r requirements.txt
echo ✅ Backend dependencies installed

REM Create .env if it doesn't exist
if not exist ".env" (
    copy .env.example .env
    echo ⚠️  .env file created. Please edit backend\.env and add your API keys!
    echo.
    echo You need:
    echo   - ElevenLabs API Key from: https://elevenlabs.io/app/settings/api-keys
    echo   - OpenAI API Key from: https://platform.openai.com/api-keys
    echo.
)

cd ..

REM Setup Frontend
echo 📦 Setting up Frontend...
cd frontend

npm install
echo ✅ Frontend dependencies installed

cd ..

echo.
echo ==========================================
echo ✅ Setup Complete!
echo ==========================================
echo.
echo Next steps:
echo 1. Edit backend\.env and add your API keys
echo 2. Run the backend: cd backend ^&^& venv\Scripts\activate ^&^& python main.py
echo 3. In a new terminal, run the frontend: cd frontend ^&^& npm run dev
echo 4. Open http://localhost:3000 in your browser
echo.
echo Enjoy! 🎉
pause
