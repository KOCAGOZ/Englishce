# 🚀 English Learning App - Deployment Guide

## 📋 Project Structure (Production Ready)

```
englishcekopya/
├── frontend/                 # Frontend files for Netlify
│   ├── index.html           # Main HTML file
│   ├── app.js              # JavaScript application
│   ├── styles.css          # CSS styles
│   ├── manifest.json       # PWA manifest
│   └── netlify.toml        # Netlify configuration
├── backend/                 # Backend files for Render
│   ├── app.py              # Main Flask application
│   ├── requirements.txt    # Python dependencies
│   ├── Procfile           # Render process configuration
│   ├── api_key.txt        # OpenRouter API key (add this manually)
│   ├── words.txt          # English-Turkish word pairs
│   ├── words_with_levels.json # CEFR level classified words
│   └── *.json             # Assessment question files
├── README.md              # Project documentation
├── DEPLOYMENT.md          # This deployment guide
└── start-local.bat        # Local development script
```

## 🚀 **HIZLI DEPLOYMENT**

### **Backend (Render)**
1. GitHub'a push yap
2. Render.com'a git
3. "New Web Service" → GitHub repo'yu seç
4. Environment variables:
   - `OPENAI_API_KEY`: (Remove this - users now provide their own API keys)
   - `SECRET_KEY`: random string
   - `FLASK_ENV`: production
5. Deploy!

### **Frontend (Netlify)**
1. Netlify.com'a git
2. "Add new site" → GitHub repo'yu seç
3. Publish directory: `frontend`
4. Deploy!

### **Son Adım**
Render URL'ini frontend/app.js'te güncelle!

---

1. **Choose Your Platform**: You can use any cloud platform like:
   - Heroku
   - Railway
   - PythonAnywhere
   - DigitalOcean App Platform
   - AWS Elastic Beanstalk

2. **Create New Web Service**:
   - Connect your GitHub repository
   - Select the `backend` folder as root directory
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python app.py` or `gunicorn app:app`

3. **Environment Variables** (Add in your platform's dashboard):
   ```
   SECRET_KEY=your-secret-key-for-sessions
   ```
   
   **Note**: No API key needed here - users provide their own!

4. **Deploy**: Your backend will be available at your platform's provided URL

### Frontend Deployment (Netlify)

1. **Update API URL**: Before deploying, update the backend URL in `frontend/app.js`:
   ```javascript
   const API_BASE_URL = window.location.hostname === 'localhost' 
       ? 'http://localhost:5000/api' 
       : 'https://your-backend-url.com/api';  // ← Update this URL
   ```

2. **Deploy to Netlify**:
   - Go to [netlify.com](https://netlify.com) and sign up
   - Drag and drop the `frontend` folder to Netlify
   - Or connect your GitHub repository and set build folder to `frontend`

3. **Update CORS**: After getting your deployment URL, update CORS in `backend/app.py`:
   ```python
   origins=[
       "https://your-app-name.netlify.app",  # ← Add your actual Netlify URL
       # ... other origins
   ]
   ```

## 🔑 API Key Setup

1. **Get OpenRouter API Key**:
   - Go to [openrouter.ai](https://openrouter.ai)
   - Create account and get API key
   - Add to Render environment variables

2. **Local Development**:
   - Create `backend/api_key.txt` with your API key
   - This file is ignored by git for security

## 🗃️ Database

- Uses SQLite database (automatically created)
- Stores user accounts, chat history, assessment results
- Database file created automatically on first run
- No additional setup required

## ✅ Features Included

### 🎮 Game Modes
- **Practice Mode**: Unlimited time word learning
- **Race Mode**: Fast-paced 5-second challenges
- **Mistakes Review**: Practice words you got wrong

### 🎓 Level Assessment
- **Extreme Difficulty Test**: 121 questions, A1-C1 levels
- **Time Pressure**: Short time limits for advanced questions
- **Academic Vocabulary**: Native-level proficiency testing
- **Ultra-Strict Scoring**: 95% accuracy needed for C1

### 🤖 AI Teacher (ChatGPT-Style)
- **Comprehensive Responses**: Detailed explanations with structure
- **Chat Memory**: Remembers conversation history
- **Contextual Teaching**: References previous discussions
- **Multiple Languages**: Auto-detects Turkish/English

### 📚 Additional Features
- **Reading Stories**: Interactive text with word translations
- **Mistake Tracking**: Analytics on learning progress
- **User Authentication**: Secure account system
- **Progress Tracking**: Level progression and statistics

## 🛠️ Technical Stack

- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Backend**: Python Flask with SQLite
- **AI**: OpenRouter API (GPT-3.5-turbo)
- **Hosting**: Netlify (frontend) + Render (backend)
- **Database**: SQLite with WAL mode for concurrency

## 🔒 Security Features

- **Password Hashing**: Werkzeug secure password storage
- **Session Management**: Token-based authentication
- **Database Locking**: Thread-safe database operations
- **CORS Protection**: Configured for production domains
- **Input Validation**: Sanitized user inputs

## 📱 PWA Support

- Responsive design for all devices
- Offline-capable service worker ready
- Mobile-first approach
- Touch-friendly interface

## 🚀 Performance

- **Database**: Optimized SQLite with connection pooling
- **Frontend**: Minimal dependencies, fast loading
- **API**: Efficient endpoint design
- **Caching**: Browser caching optimized

## 📞 Support

If you need help with deployment:
1. Check the Render/Netlify deployment logs
2. Verify environment variables are set correctly
3. Ensure API key is valid and has credits
4. Check CORS configuration matches your domain

---

**Ready for Production!** 🎉

Your English learning platform is now ready to help students worldwide improve their English skills with advanced AI-powered teaching!