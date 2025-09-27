@echo off
echo ==========================================
echo  EnglishCE Web Application Setup
echo ==========================================
echo.

echo [1/3] Copying API key to backend...
if exist api_key.txt (
    copy api_key.txt backend\api_key.txt
    echo ✓ API key copied successfully
) else (
    echo ⚠ api_key.txt not found - you'll need to set OPENAI_API_KEY environment variable on Render
)

echo.
echo [2/3] Testing backend setup...
cd backend
python -c "import app; print('✓ Backend dependencies OK')" 2>nul
if errorlevel 1 (
    echo ⚠ Installing backend dependencies...
    pip install -r requirements.txt
)
cd ..

echo.
echo [3/3] Project structure ready!
echo.
echo ==========================================
echo  NEXT STEPS:
echo ==========================================
echo.
echo 🚀 BACKEND DEPLOYMENT:
echo    1. Choose your deployment platform (Heroku, Railway, etc.)
echo    2. Connect your GitHub repository  
echo    3. Set Root Directory: backend
echo    4. Add Environment Variables:
echo       - OPENAI_API_KEY: your_api_key_here
echo       - SECRET_KEY: any_random_secret_here
echo.
echo 🌐 FRONTEND DEPLOYMENT (Netlify):
echo    1. Go to netlify.com and create account
echo    2. Drag and drop the 'frontend' folder
echo    3. Update API_BASE_URL in frontend/app.js
echo       const API_BASE_URL = 'https://your-backend-url.com/api';
echo.
echo 📚 LOCAL TESTING:
echo    Backend:  cd backend ^&^& python app.py
echo    Frontend: cd frontend ^&^& python -m http.server 3000
echo.
echo ==========================================
echo ✅ Setup complete! Check README.md for detailed instructions.
echo ==========================================
pause