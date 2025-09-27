@echo off
echo ==========================================
echo  English Learning Platform - Local Development
echo ==========================================
echo.

echo [1/4] Checking API key...
if exist api_key.txt (
    copy api_key.txt backend\api_key.txt >nul 2>&1
    echo ✓ API key found and copied to backend
) else (
    echo ⚠ api_key.txt not found - AI teacher might not work
    echo   Create api_key.txt with your OpenRouter API key
)

echo.
echo [2/4] Installing backend dependencies...
cd backend
echo Checking Flask installation...
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo ⚠ Flask not found! Installing dependencies...
    python -m pip install flask flask-cors requests werkzeug
    if errorlevel 1 (
        echo ❌ Failed to install Flask! Run install-dependencies.bat first
        pause
        exit
    )
)
echo ✅ Backend dependencies ready
cd ..

echo.
echo [3/4] Starting Backend Server on port 5000...
start "English Learning Backend" cmd /k "cd backend && echo Starting Flask backend with 121 assessment questions... && python app.py"
timeout /t 5 /nobreak >nul
echo ✓ Backend server starting...

echo.
echo [4/4] Starting Frontend Server on port 3000...
start "English Learning Frontend" cmd /k "cd frontend && echo Starting frontend server... && python -m http.server 3000"
timeout /t 3 /nobreak >nul

echo.
echo ==========================================
echo ✅ SERVERS STARTED SUCCESSFULLY!
echo ==========================================
echo.
echo 🌐 Frontend: http://localhost:3000
echo 🔧 Backend:  http://localhost:5000
echo 🤖 AI Teacher: ChatGPT-style with memory
echo 📊 Assessment: 121 extreme difficulty questions
echo.
echo ⏰ Wait a few seconds for servers to fully start, then:
echo    1. Open your browser
echo    2. Go to: http://localhost:3000
echo    3. Create an account or login (berkay74/123456)
echo    4. Test the enhanced AI Teacher with chat history!
echo    5. Try the extreme level assessment
echo.
echo 🛑 To stop servers: Close the terminal windows or press Ctrl+C
echo.
echo Production deployment ready for Netlify + Render!
echo ==========================================
pause