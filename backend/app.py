"""
English Learning Web Application - Backend API
Flask server with comprehensive API endpoints for the English learning platform
"""

import os
import json
import random
import urllib.request
import urllib.error
import sqlite3
import hashlib
import uuid
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, session, make_response
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'englishce-secret-key-change-in-production')

# Rate limiting to protect API
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["1000 per hour"],  # Genel limit: saatte 1000 istek
    storage_uri="memory://"
)

# Configure for local development and production
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Changed from 'None' to 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = False  # Allow JavaScript access for debugging
app.config['SESSION_PERMANENT'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour

# Enable CORS for frontend communication - OPEN FOR TESTING
CORS(app, 
     origins="*",  # Allow all origins for testing
     supports_credentials=False,  # Disable credentials for broader access
     allow_headers=["Content-Type", "Authorization", "Accept", "Origin", "X-Requested-With"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
     expose_headers=["*"])

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, 'users.db')
WORDS_PATH = os.path.join(BASE_DIR, 'words.txt')
MISTAKES_PATH = os.path.join(BASE_DIR, 'mistakes.json')
CHAT_HISTORY_PATH = os.path.join(BASE_DIR, 'chat_history.json')

# Database connection lock
db_lock = threading.Lock()

@contextmanager
def get_db_connection(timeout=30, retries=3):
    """Get database connection with proper locking and retry logic"""
    conn = None
    for attempt in range(retries):
        try:
            with db_lock:
                conn = sqlite3.connect(DATABASE_PATH, timeout=timeout)
                # Enable WAL mode for better concurrency
                conn.execute('PRAGMA journal_mode=WAL')
                conn.execute('PRAGMA synchronous=NORMAL')
                conn.execute('PRAGMA cache_size=1000')
                conn.execute('PRAGMA temp_store=MEMORY')
                conn.row_factory = sqlite3.Row
                yield conn
                break
        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower() and attempt < retries - 1:
                print(f"[DEBUG] Database locked, retrying in {0.5 * (attempt + 1)} seconds...")
                time.sleep(0.5 * (attempt + 1))
                continue
            else:
                print(f"[ERROR] Database error after {attempt + 1} attempts: {e}")
                raise
        except Exception as e:
            print(f"[ERROR] Unexpected database error: {e}")
            raise
        finally:
            if conn:
                try:
                    conn.close()
                except:
                    pass

def read_api_key():
    """Read API key from file or environment variable - Now returns empty since users provide their own keys"""
    # No server-side API key anymore - users provide their own
    print("[DEBUG] Server-side API key disabled - users provide their own")
    return None

# Load words data
def load_words():
    """Load English-Turkish word pairs from words.txt file"""
    pairs = []
    if not os.path.exists(WORDS_PATH):
        return pairs
    
    with open(WORDS_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # Handle potential numbering format like "1→a\tbir"
            if '→' in line:
                try:
                    _, line = line.split('→', 1)
                    line = line.strip()
                except ValueError:
                    pass
            parts = line.split('\t')
            if len(parts) >= 2:
                en = parts[0].strip()
                tr = parts[1].strip()
                if en and tr:
                    pairs.append({'en': en, 'tr': tr})
    
    # Remove duplicates
    seen = set()
    unique_pairs = []
    for p in pairs:
        if p['en'] not in seen:
            unique_pairs.append(p)
            seen.add(p['en'])
    
    return unique_pairs

def load_words_with_levels():
    """Load words with CEFR level classification"""
    try:
        with open(os.path.join(BASE_DIR, 'words_with_levels.json'), 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("[WARNING] words_with_levels.json not found, using basic words")
        return []

def load_level_test_questions():
    """Load level assessment test questions"""
    questions = []
    
    # Load basic questions
    try:
        with open(os.path.join(BASE_DIR, 'level_test_questions.json'), 'r', encoding='utf-8') as f:
            basic_questions = json.load(f)
            questions.extend(basic_questions)
    except FileNotFoundError:
        print("[WARNING] level_test_questions.json not found")
    
    # Load enhanced questions
    try:
        with open(os.path.join(BASE_DIR, 'enhanced_test_questions.json'), 'r', encoding='utf-8') as f:
            enhanced_questions = json.load(f)
            questions.extend(enhanced_questions)
            print(f"[DEBUG] Loaded {len(enhanced_questions)} enhanced questions")
    except FileNotFoundError:
        print("[WARNING] enhanced_test_questions.json not found")
    
    # Load advanced questions
    try:
        with open(os.path.join(BASE_DIR, 'advanced_assessment_questions.json'), 'r', encoding='utf-8') as f:
            advanced_questions = json.load(f)
            questions.extend(advanced_questions)
            print(f"[DEBUG] Loaded {len(advanced_questions)} advanced questions")
    except FileNotFoundError:
        print("[WARNING] advanced_assessment_questions.json not found")
    
    # Load ultra-advanced questions
    try:
        with open(os.path.join(BASE_DIR, 'ultra_advanced_questions.json'), 'r', encoding='utf-8') as f:
            ultra_questions = json.load(f)
            questions.extend(ultra_questions)
            print(f"[DEBUG] Loaded {len(ultra_questions)} ultra-advanced questions")
    except FileNotFoundError:
        print("[WARNING] ultra_advanced_questions.json not found")
    
    # Load extreme challenge questions
    try:
        with open(os.path.join(BASE_DIR, 'extreme_challenge_questions.json'), 'r', encoding='utf-8') as f:
            extreme_questions = json.load(f)
            questions.extend(extreme_questions)
            print(f"[DEBUG] Loaded {len(extreme_questions)} extreme challenge questions")
    except FileNotFoundError:
        print("[WARNING] extreme_challenge_questions.json not found")
    
    print(f"[DEBUG] Total assessment questions loaded: {len(questions)}")
    return questions

# Global words data
WORDS_DATA = load_words()
WORDS_WITH_LEVELS = load_words_with_levels()
LEVEL_TEST_QUESTIONS = load_level_test_questions()

# Simple token storage (in production, use Redis or database)
active_tokens = {}

def generate_token(user_id, username):
    """Generate a new authentication token"""
    token = str(uuid.uuid4())
    expires_at = datetime.now() + timedelta(hours=24)
    active_tokens[token] = {
        'user_id': user_id,
        'username': username,
        'expires_at': expires_at
    }
    return token

def get_user_from_token(token):
    """Get user info from token"""
    if not token or token not in active_tokens:
        return None
    
    token_data = active_tokens[token]
    if datetime.now() > token_data['expires_at']:
        # Token expired, remove it
        del active_tokens[token]
        return None
    
    return token_data

def invalidate_token(token):
    """Remove token from active tokens"""
    if token in active_tokens:
        del active_tokens[token]

def get_current_user():
    """Get current user from either session or token"""
    # First try session authentication
    if 'user_id' in session:
        return {
            'user_id': session['user_id'],
            'username': session['username'],
            'level': session['level']
        }
    
    # Then try token authentication
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        token_data = get_user_from_token(token)
        if token_data:
            return {
                'user_id': token_data['user_id'],
                'username': token_data['username'],
                'level': 'UNSET'  # Default level for token auth
            }
    
    return None

def require_auth():
    """Decorator-like function to check authentication (supports both registered users and guests)"""
    user = get_current_user()
    if not user:
        return False, jsonify({'error': 'Not authenticated'}), 401
    return True, user, None

def require_registered_user():
    """Decorator-like function that requires registered user (no guests)"""
    user = get_current_user()
    if not user:
        return False, jsonify({'error': 'Not authenticated'}), 401
    
    # Check if user is guest
    if str(user['user_id']).startswith('guest_'):
        return False, jsonify({'error': 'Registered account required for this feature'}), 403
    
    return True, user, None

# Database initialization
def init_database():
    """Initialize SQLite database for user management"""
    try:
        print(f"[DEBUG] Initializing database at: {DATABASE_PATH}")
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    level TEXT DEFAULT 'UNSET',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    level_test_scores TEXT DEFAULT '{}'
                )
            ''')
            
            # Create chat history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    message TEXT NOT NULL,
                    response TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            conn.commit()
        print("[DEBUG] Database initialized successfully")
    except Exception as e:
        print(f"[ERROR] Database initialization failed: {e}")

# Helper functions
def get_user_by_username(username):
    """Get user data by username"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        
        if user:
            return {
                'id': user[0],
                'username': user[1],
                'password_hash': user[2],
                'level': user[3],
                'created_at': user[4],
                'last_login': user[5],
                'level_test_scores': user[6]
            }
        return None

def create_user(username, password):
    """Create a new user"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            password_hash = generate_password_hash(password)
            cursor.execute(
                'INSERT INTO users (username, password_hash) VALUES (?, ?)',
                (username, password_hash)
            )
            conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def update_user_login(username):
    """Update user's last login timestamp"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE username = ?',
            (username,)
        )
        conn.commit()

def load_chat_history(user_id):
    """Load user's chat history from database"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT message, response, created_at FROM chat_history 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT 10
            ''', (user_id,))
            
            conversations = cursor.fetchall()
            return [{
                'message': conv[0],
                'response': conv[1],
                'timestamp': conv[2]
            } for conv in conversations]
    except Exception as e:
        print(f"[ERROR] Failed to load chat history: {e}")
        return []

def save_chat_message(user_id, message, response):
    """Save chat message and response to database"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO chat_history (user_id, message, response, created_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, message, response))
            conn.commit()
            print(f"[DEBUG] Saved chat message for user {user_id}")
    except Exception as e:
        print(f"[ERROR] Failed to save chat message: {e}")

def load_mistakes():
    """Load user mistakes from JSON file"""
    try:
        with open(MISTAKES_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_mistakes(mistakes):
    """Save user mistakes to JSON file"""
    try:
        with open(MISTAKES_PATH, 'w', encoding='utf-8') as f:
            json.dump(mistakes, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving mistakes: {e}")

def pick_random_word(recent_words=None, mode='practice', mistakes=None, user_level=None):
    """Pick a random word with smart selection logic"""
    # Use level-appropriate words if available and user has a level
    if WORDS_WITH_LEVELS and user_level and user_level != 'UNSET':
        # Get words for user's level and one level above
        level_order = ['A1', 'A2', 'B1', 'B2', 'C1']
        try:
            current_level_index = level_order.index(user_level)
            target_levels = [user_level]
            # Add next level for challenge (70% current level, 30% next level)
            if current_level_index < len(level_order) - 1:
                target_levels.append(level_order[current_level_index + 1])
        except ValueError:
            target_levels = [user_level]
        
        # Filter words by target levels
        level_words = [w for w in WORDS_WITH_LEVELS if w['level'] in target_levels]
        
        if level_words:
            # Weight words: 70% current level, 30% next level
            if len(target_levels) > 1:
                current_level_words = [w for w in level_words if w['level'] == target_levels[0]]
                next_level_words = [w for w in level_words if w['level'] == target_levels[1]]
                
                if random.random() < 0.7 and current_level_words:
                    available_words = current_level_words
                elif next_level_words:
                    available_words = next_level_words
                else:
                    available_words = level_words
            else:
                available_words = level_words
        else:
            # Fallback to all words
            available_words = WORDS_DATA
    else:
        # Fallback to original word list
        available_words = WORDS_DATA
    
    if not available_words:
        return None
    
    # Avoid recent words when possible
    recent_set = set(recent_words or [])
    filtered_words = [w for w in available_words if w['en'] not in recent_set]
    
    if not filtered_words:
        filtered_words = available_words
    
    # In mistakes mode, prefer words with more mistakes
    if mode == 'mistakes' and mistakes:
        mistake_words = []
        for word in filtered_words:
            if word['en'] in mistakes:
                mistake_words.extend([word] * min(mistakes[word['en']], 5))  # Weight by mistake count
        
        if mistake_words:
            return random.choice(mistake_words)
    
    # In race mode, 10% chance to pick from mistakes
    if mode == 'race' and mistakes and random.random() < 0.1:
        mistake_words = [w for w in filtered_words if w['en'] in mistakes]
        if mistake_words:
            weights = [min(mistakes[w['en']], 5) for w in mistake_words]
            return random.choices(mistake_words, weights=weights)[0]
    
    return random.choice(filtered_words)

def generate_question(word_pair, recent_words=None, mode='TR_PROMPT'):
    """Generate a multiple choice question"""
    if mode == 'TR_PROMPT':
        # Show Turkish, options are English
        question = word_pair['tr']
        correct_answer = word_pair['en']
        
        # Generate distractors
        other_words = [w for w in WORDS_DATA if w['en'] != word_pair['en']]
        distractors = random.sample(other_words, min(2, len(other_words)))
        options = [correct_answer] + [d['en'] for d in distractors]
    else:
        # Show English, options are Turkish
        question = word_pair['en']
        correct_answer = word_pair['tr']
        
        # Generate distractors
        other_words = [w for w in WORDS_DATA if w['tr'] != word_pair['tr']]
        distractors = random.sample(other_words, min(2, len(other_words)))
        options = [correct_answer] + [d['tr'] for d in distractors]
    
    random.shuffle(options)
    correct_index = options.index(correct_answer)
    
    return {
        'question': question,
        'options': options,
        'correct_index': correct_index,
        'word_pair': word_pair,
        'mode': mode
    }

def call_ai_api(messages, api_key):
    """Call OpenRouter AI API"""
    try:
        url = 'https://openrouter.ai/api/v1/chat/completions'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }
        
        data = {
            'model': 'deepseek/deepseek-chat-v3.1:free',  # Deepseek V3.1 free model
            'messages': messages,
            'max_tokens': 1000,
            'temperature': 0.7
        }
        
        print(f"[DEBUG] Making AI API request to {url}")
        print(f"[DEBUG] API Key exists: {api_key is not None}")
        print(f"[DEBUG] API Key preview: {api_key[:10] + '...' if api_key else 'None'}")
        
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers=headers,
            method='POST'
        )
        
        with urllib.request.urlopen(req) as response:
            response_data = json.loads(response.read().decode('utf-8'))
            
            if 'choices' not in response_data or not response_data['choices']:
                raise ValueError('Invalid API response')
                
            choice = response_data['choices'][0]
            if 'message' in choice and 'content' in choice['message']:
                return choice['message']['content'].strip()
            elif 'text' in choice:
                return choice['text'].strip()
            else:
                raise ValueError('Cannot parse API response')
                
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"[ERROR] HTTP Error {e.code}: {e.reason}")
        print(f"[ERROR] Response body: {error_body}")
        raise Exception(f"HTTP Error {e.code}: {e.reason} - {error_body}")
    except Exception as e:
        print(f"[ERROR] AI API Error: {e}")
        raise

# API Routes

@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "*")
        response.headers.add('Access-Control-Allow-Methods', "*")
        return response

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,Accept,Origin,X-Requested-With')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS,HEAD')
    return response

@app.route('/api/health', methods=['GET', 'OPTIONS'])
def health_check():
    """Health check endpoint"""
    api_key = read_api_key()
    return jsonify({
        'status': 'healthy', 
        'words_count': len(WORDS_DATA),
        'api_key_configured': api_key is not None,
        'api_key_preview': api_key[:10] + '...' if api_key else 'Not found'
    })

@app.route('/api/auth/guest', methods=['POST'])
@limiter.limit("20 per hour")  # Guest token'ları sınırla
def get_guest_token():
    """Get a temporary guest token for anonymous users"""
    try:
        # Guest kullanıcılar için özel token oluştur
        guest_id = f"guest_{int(time.time())}_{random.randint(1000, 9999)}"
        token = generate_token(guest_id, "guest")
        
        return jsonify({
            'token': token,
            'user': {
                'username': 'Guest',
                'level': 'A1',  # Varsayılan seviye
                'is_guest': True
            },
            'message': 'Guest access granted - limited features available'
        })
    except Exception as e:
        print(f"[ERROR] Guest token error: {e}")
        return jsonify({'error': 'Failed to create guest access'}), 500

@app.route('/api/auth/register', methods=['POST'])
def register():
    """User registration endpoint"""
    try:
        data = request.get_json()
        print(f"[DEBUG] Registration request: {data}")
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        
        if len(password) < 4:
            return jsonify({'error': 'Password must be at least 4 characters'}), 400
        
        if create_user(username, password):
            print(f"[DEBUG] User {username} created successfully")
            return jsonify({'message': 'User created successfully'})
        else:
            print(f"[DEBUG] Username {username} already exists")
            return jsonify({'error': 'Username already exists'}), 400
    except Exception as e:
        print(f"[ERROR] Registration error: {e}")
        return jsonify({'error': 'Registration failed'}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        print(f"[DEBUG] Login request: {data}")
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        
        user = get_user_by_username(username)
        print(f"[DEBUG] User found: {user is not None}")
        
        if user and check_password_hash(user['password_hash'], password):
            # Generate authentication token
            token = generate_token(user['id'], user['username'])
            
            # Also maintain session for backward compatibility
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['level'] = user['level']
            session['auth_token'] = token
            update_user_login(username)
            
            print(f"[DEBUG] Login successful for {username}, token: {token[:10]}...")
            return jsonify({
                'message': 'Login successful',
                'token': token,
                'user': {
                    'username': user['username'],
                    'level': user['level'],
                    'needs_level_assessment': user['level'] == 'UNSET'
                }
            })
        else:
            print(f"[DEBUG] Invalid credentials for {username}")
            return jsonify({'error': 'Invalid credentials'}), 401
    except Exception as e:
        print(f"[ERROR] Login error: {e}")
        return jsonify({'error': 'Login failed'}), 500

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """User logout endpoint"""
    # Invalidate token if present
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        invalidate_token(token)
    
    # Clear session
    session.clear()
    return jsonify({'message': 'Logged out successfully'})

@app.route('/api/auth/check', methods=['GET'])
def check_auth():
    """Check authentication status"""
    is_authenticated, user_or_response, status_code = require_auth()
    if not is_authenticated:
        return user_or_response, status_code
    
    user = user_or_response
    print(f"[DEBUG] Auth check successful - User: {user['username']}")
    
    return jsonify({
        'authenticated': True,
        'user': {
            'username': user['username'],
            'level': user['level'],
            'user_id': user['user_id']
        }
    })

@app.route('/api/user/profile', methods=['GET'])
def get_profile():
    """Get current user profile"""
    is_authenticated, user_or_response, status_code = require_auth()
    if not is_authenticated:
        return user_or_response, status_code
    
    user = user_or_response
    
    return jsonify({
        'username': user['username'],
        'level': user['level'],
        'needs_level_assessment': user['level'] == 'UNSET'
    })

@app.route('/api/game/question', methods=['POST'])
def get_question():
    """Get a new question for the word game"""
    is_authenticated, user_or_response, status_code = require_auth()
    if not is_authenticated:
        return user_or_response, status_code
    
    user = user_or_response
    print(f"[DEBUG] Game question request - User: {user['username']}")
    
    data = request.get_json()
    mode = data.get('mode', 'practice')  # practice, race, mistakes
    recent_words = data.get('recent_words', [])
    question_mode = data.get('question_mode', random.choice(['TR_PROMPT', 'EN_PROMPT']))
    
    # Load user's mistakes
    mistakes = load_mistakes()
    user_mistakes = mistakes.get(user['username'], {})
    
    # Pick a word based on user's level
    word_pair = pick_random_word(recent_words, mode, user_mistakes, user.get('level', 'UNSET'))
    if not word_pair:
        return jsonify({'error': 'No words available'}), 404
    
    # Generate question
    question_data = generate_question(word_pair, recent_words, question_mode)
    
    return jsonify(question_data)

@app.route('/api/game/answer', methods=['POST'])
def submit_answer():
    """Submit an answer and get feedback"""
    is_authenticated, user_or_response, status_code = require_auth()
    if not is_authenticated:
        return user_or_response, status_code
    
    user = user_or_response
    
    data = request.get_json()
    selected_index = data.get('selected_index')
    correct_index = data.get('correct_index')
    word_pair = data.get('word_pair')
    
    is_correct = selected_index == correct_index
    
    # Record mistake if wrong
    if not is_correct and word_pair:
        mistakes = load_mistakes()
        username = user['username']
        
        if username not in mistakes:
            mistakes[username] = {}
        
        en_word = word_pair['en']
        mistakes[username][en_word] = mistakes[username].get(en_word, 0) + 1
        save_mistakes(mistakes)
    
    return jsonify({
        'correct': is_correct,
        'message': 'Doğru!' if is_correct else 'Yanlış!'
    })

@app.route('/api/mistakes', methods=['GET'])
def get_mistakes():
    """Get user's mistakes for review"""
    is_authenticated, user_or_response, status_code = require_auth()
    if not is_authenticated:
        return user_or_response, status_code
    
    user = user_or_response
    print(f"[DEBUG] Mistakes request - User: {user['username']}")
    
    mistakes = load_mistakes()
    user_mistakes = mistakes.get(user['username'], {})
    
    # Convert to list with word pairs
    mistake_words = []
    words_dict = {w['en']: w for w in WORDS_DATA}
    
    for en_word, count in user_mistakes.items():
        if en_word in words_dict:
            word_data = words_dict[en_word].copy()
            word_data['mistake_count'] = count
            mistake_words.append(word_data)
    
    # Sort by mistake count (most mistakes first)
    mistake_words.sort(key=lambda x: x['mistake_count'], reverse=True)
    
    return jsonify(mistake_words)

@app.route('/api/ai/chat', methods=['POST'])
@limiter.limit("5 per minute")  # AI chat'i sınırla: dakikada 5 mesaj
def ai_chat():
    """Enhanced AI teacher chat endpoint with memory and comprehensive responses"""
    is_authenticated, user_or_response, status_code = require_auth()  # Tüm giriş yapmış kullanıcılar
    if not is_authenticated:
        return user_or_response, status_code
    
    user = user_or_response
    data = request.get_json()
    message = data.get('message', '').strip()
    language = data.get('language', 'AUTO')  # EN, TR, AUTO
    user_api_key = data.get('user_api_key', '').strip()  # User-provided API key
    
    if not message:
        return jsonify({'error': 'Message required'}), 400
    
    # Use user-provided API key if available, otherwise fallback to server key
    api_key = user_api_key if user_api_key else read_api_key()
    
    if not api_key:
        # No API key provided - require user to enter one
        return jsonify({
            'error': 'API key gerekli! Lütfen OpenRouter API key’inizi girin.',
            'demo_mode': False,
            'requires_api_key': True
        }), 400
    
    try:
        # Load user's chat history for context
        chat_history = load_chat_history(user['user_id'])
        
        # Build context from recent conversations
        context_messages = []
        for chat in reversed(chat_history[-3:]):  # Last 3 conversations for context
            context_messages.append({'role': 'user', 'content': chat['message']})
            context_messages.append({'role': 'assistant', 'content': chat['response']})
        
        # Enhanced system message for comprehensive teaching
        system_msg = f"""
You are an expert English teacher with a warm, encouraging personality. Your student's current level is {user.get('level', 'beginner')}.

TEACHING STYLE:
📚 Always provide comprehensive, detailed explanations
🎯 Break complex topics into clear sections with headers
📝 Include multiple examples for each concept
🌟 Use emojis to make learning engaging
💡 Provide practical tips and mnemonics
📊 Create simple visual representations when helpful
🔄 Always recap key points at the end

FORMAT YOUR RESPONSES:
1. **Topic Overview** 📋 - Brief introduction
2. **Key Rules** 📏 - Main grammar rules or concepts
3. **Examples** 📝 - Multiple clear examples
4. **Practice Tips** 💪 - How to practice and remember
5. **Common Mistakes** ⚠️ - What to avoid
6. **Quick Recap** 🔄 - Summary of main points

LANGUAGE PREFERENCE:
- If user writes in Turkish, respond in Turkish
- If user writes in English, respond in English
- Always be encouraging and supportive
- Adapt explanations to the student's level

Remember: Be like ChatGPT - detailed, structured, helpful, and conversational!
"""
        
        # Build complete message chain
        messages = [{'role': 'system', 'content': system_msg}]
        messages.extend(context_messages)
        messages.append({'role': 'user', 'content': message})
        
        response = call_ai_api(messages, api_key)
        
        # Save this conversation to memory
        save_chat_message(user['user_id'], message, response)
        
        return jsonify({
            'response': response,
            'detected_language': 'TR' if any(char in message.lower() for char in 'çğıöşü') else 'EN',
            'has_context': len(chat_history) > 0
        })
        
    except Exception as e:
        return jsonify({'error': f'AI service error: {str(e)}'}), 500

@app.route('/api/ai/chat/history', methods=['GET'])
def get_chat_history():
    """Get user's chat history"""
    is_authenticated, user_or_response, status_code = require_auth()
    if not is_authenticated:
        return user_or_response, status_code
    
    user = user_or_response
    
    try:
        # Get chat history with limit
        limit = request.args.get('limit', 20, type=int)
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT message, response, created_at FROM chat_history 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (user['user_id'], limit))
            
            conversations = cursor.fetchall()
            
            return jsonify({
                'conversations': [{
                    'user_message': conv[0],
                    'ai_response': conv[1],
                    'timestamp': conv[2]
                } for conv in conversations],
                'total_count': len(conversations)
            })
            
    except Exception as e:
        print(f"[ERROR] Failed to get chat history: {e}")
        return jsonify({'error': 'Failed to load chat history'}), 500

@app.route('/api/ai/chat/clear', methods=['POST'])
def clear_chat_history():
    """Clear user's chat history"""
    is_authenticated, user_or_response, status_code = require_auth()
    if not is_authenticated:
        return user_or_response, status_code
    
    user = user_or_response
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM chat_history WHERE user_id = ?', (user['user_id'],))
            conn.commit()
            
            return jsonify({'message': 'Chat history cleared successfully'})
            
    except Exception as e:
        print(f"[ERROR] Failed to clear chat history: {e}")
        return jsonify({'error': 'Failed to clear chat history'}), 500

@app.route('/api/translate', methods=['POST'])
@limiter.limit("10 per minute")  # Çeviri'yi sınırla: dakikada 10 istek
def translate_text():
    """Translate text using AI"""
    is_authenticated, user_or_response, status_code = require_auth()  # Tüm giriş yapmış kullanıcılar
    if not is_authenticated:
        return user_or_response, status_code
    
    data = request.get_json()
    text = data.get('text', '').strip()
    
    if not text:
        return jsonify({'error': 'Text required'}), 400
    
    # Check if it's a single word in our dictionary first
    text_lower = text.lower()
    words_dict = {w['en'].lower(): w['tr'] for w in WORDS_DATA}
    
    if text_lower in words_dict:
        return jsonify({
            'translation': words_dict[text_lower],
            'source': 'dictionary'
        })
    
    # Use AI for translation
    api_key = read_api_key()
    if not api_key:
        return jsonify({'error': 'Translation service not configured'}), 503
    
    try:
        # Detect source language
        turkish_chars = set('çğıöşü')
        is_turkish = any(ch in turkish_chars for ch in text.lower())
        
        if is_turkish:
            system_msg = f"Translate this Turkish text to English. Only provide the translation: '{text}'"
        else:
            system_msg = f"Translate this English text to Turkish. Only provide the translation: '{text}'"
        
        messages = [{'role': 'user', 'content': system_msg}]
        response = call_ai_api(messages, api_key)
        
        return jsonify({
            'translation': response,
            'source': 'ai'
        })
        
    except Exception as e:
        return jsonify({'error': f'Translation error: {str(e)}'}), 500

@app.route('/api/words/search', methods=['GET'])
def search_words():
    """Search words in the dictionary"""
    query = request.args.get('q', '').strip().lower()
    
    if not query:
        return jsonify([])
    
    # Search in both English and Turkish
    results = []
    for word in WORDS_DATA:
        if (query in word['en'].lower() or 
            query in word['tr'].lower()):
            results.append(word)
    
    # Limit results
    results = results[:20]
    
    return jsonify(results)

@app.route('/api/reading/stories', methods=['GET'])
def get_stories():
    """Get available reading stories"""
    stories = [
        {
            'id': 'little_prince',
            'title': 'The Little Prince',
            'description': 'A classic tale about friendship and discovery',
            'level': 'Intermediate'
        },
        {
            'id': 'beach_day',
            'title': 'A Day at the Beach',
            'description': 'A family enjoys a perfect summer day',
            'level': 'Beginner'
        },
        {
            'id': 'magic_garden',
            'title': 'The Magic Garden',
            'description': 'A mysterious garden that brings joy to a village',
            'level': 'Intermediate'
        },
        {
            'id': 'learning_english',
            'title': 'Learning English',
            'description': 'Emma\'s journey to master the English language',
            'level': 'Beginner'
        },
        {
            'id': 'weekend_plans',
            'title': 'Weekend Plans',
            'description': 'Mike\'s perfect weekend routine in Portland',
            'level': 'Advanced'
        }
    ]
    
    return jsonify(stories)

@app.route('/api/reading/story/<story_id>', methods=['GET'])
def get_story_content(story_id):
    """Get content of a specific story"""
    stories_content = {
        'little_prince': """Once upon a time, there was a little prince who lived on a small planet called Asteroid B-612. His planet was so small that he could watch forty-four sunsets in a single day by simply moving his chair. The little prince loved to watch the sunset every day because it made him feel peaceful and happy. He took care of his planet by regularly cleaning out the baobab seeds that threatened to grow too large.""",
        
        'beach_day': """Sarah and her family woke up early on a beautiful sunny Saturday morning in July. They had been planning this beach trip for weeks, and everyone was excited about spending the day by the ocean. Her mother packed a large picnic basket filled with sandwiches, fresh fruit, cold drinks, and homemade cookies. Her father loaded the car with beach chairs, umbrellas, towels, and a cooler full of ice.""",
        
        'magic_garden': """In a small village nestled between rolling hills and a quiet river, there was a mysterious garden that captivated everyone's imagination. The garden was located at the edge of the village, surrounded by an old stone wall covered in ivy and climbing roses. Nobody in the village knew who owned the garden or who took care of it, but it was always perfectly maintained.""",
        
        'learning_english': """Emma Rodriguez was a bright ten-year-old girl living in Madrid, Spain, when she first discovered her passion for the English language. Her journey began when her family hosted an exchange student named Jennifer from California for the summer. Jennifer was friendly and patient, and she spent hours teaching Emma basic English words and phrases.""",
        
        'weekend_plans': """Mike Thompson, a 28-year-old graphic designer living in Portland, Oregon, absolutely loves weekends because they offer him the perfect opportunity to relax and recharge. After working long hours during the week creating advertisements and website designs, he looks forward to his two days of freedom. Mike's weekend routine has developed over several years and reflects his personality and interests perfectly."""
    }
    
    if story_id not in stories_content:
        return jsonify({'error': 'Story not found'}), 404
    
    # Split into sentences
    content = stories_content[story_id]
    sentences = [s.strip() + '.' for s in content.split('.') if s.strip()]
    
    return jsonify({
        'content': content,
        'sentences': sentences
    })

# Level Assessment Endpoints

@app.route('/api/level/test/start', methods=['POST'])
def start_level_test():
    """Start a new level assessment test"""
    is_authenticated, user_or_response, status_code = require_auth()
    if not is_authenticated:
        return user_or_response, status_code
    
    user = user_or_response
    
    try:
        # Generate 30 random questions from different levels
        if not LEVEL_TEST_QUESTIONS:
            return jsonify({'error': 'Level test questions not available'}), 503
        
        # Select questions progressively: start easy, get harder
        selected_questions = []
        
        # Group questions by level
        questions_by_level = {}
        for q in LEVEL_TEST_QUESTIONS:
            level = q['level']
            if level not in questions_by_level:
                questions_by_level[level] = []
            questions_by_level[level].append(q)
        
        # Enhanced question selection algorithm
        selected_questions = []
        
        # Group questions by level and type
        questions_by_level = {}
        questions_by_type = {}
        
        for q in LEVEL_TEST_QUESTIONS:
            level = q['level']
            q_type = q.get('type', 'translation')
            
            if level not in questions_by_level:
                questions_by_level[level] = []
            if q_type not in questions_by_type:
                questions_by_type[q_type] = []
                
            questions_by_level[level].append(q)
            questions_by_type[q_type].append(q)
        
        # ULTIMATE CHALLENGE question distribution 
        # This will be extremely difficult - most people will get A1 or A2
        question_plan = [
            # Phase 1: Quick basic assessment (questions 1-6)
            ('A1', 1), ('A2', 2), ('B1', 3),
            # Phase 2: Intermediate challenge (questions 7-14) 
            ('A2', 1), ('B1', 3), ('B2', 4),
            # Phase 3: Advanced challenge (questions 15-24)
            ('B2', 4), ('C1', 6),
            # Phase 4: EXTREME challenge (questions 25-30)
            ('C1', 6)  # Final 6 questions all C1 level!
        ]
        
        # Select questions with maximum difficulty preference
        for level, count in question_plan:
            level_questions = questions_by_level.get(level, [])
            if level_questions:
                # For C1 questions, prioritize extreme and ultra-advanced types
                if level == 'C1':
                    extreme_types = ['extreme_challenge', 'ultra_reading', 'ultra_grammar', 
                                   'ultra_vocabulary', 'ultra_collocations', 'ultra_logic', 'ultra_academic']
                    extreme_qs = [q for q in level_questions if q.get('type') in extreme_types]
                    if extreme_qs:
                        level_questions = extreme_qs
                # For B2 questions, prefer advanced types
                elif level == 'B2':
                    advanced_types = ['ultra_reading', 'ultra_grammar', 'ultra_vocabulary',
                                    'reading_comprehension', 'advanced_grammar', 'contextual_vocabulary']
                    advanced_qs = [q for q in level_questions if q.get('type') in advanced_types]
                    if advanced_qs:
                        level_questions = advanced_qs
                
                selected_count = min(count, len(level_questions))
                selected = random.sample(level_questions, selected_count)
                selected_questions.extend(selected)
        
        # Fill remaining slots if needed
        if len(selected_questions) < 30:
            remaining_questions = [q for q in LEVEL_TEST_QUESTIONS if q not in selected_questions]
            needed = 30 - len(selected_questions)
            if remaining_questions:
                additional = random.sample(remaining_questions, min(needed, len(remaining_questions)))
                selected_questions.extend(additional)
        
        # Shuffle but maintain general difficulty progression
        # Group into 3 phases and shuffle within each phase
        phase1 = selected_questions[:10]
        phase2 = selected_questions[10:20] 
        phase3 = selected_questions[20:30]
        
        random.shuffle(phase1)
        random.shuffle(phase2) 
        random.shuffle(phase3)
        
        test_questions = phase1 + phase2 + phase3
        
        # Create test session
        test_session = {
            'test_id': str(uuid.uuid4()),
            'user_id': user['user_id'],
            'username': user['username'],
            'questions': test_questions,
            'current_question': 0,
            'answers': [],
            'start_time': datetime.now().isoformat(),
            'status': 'active'
        }
        
        # Store test session (in production, use Redis or database)
        if not hasattr(app, 'test_sessions'):
            app.test_sessions = {}
        app.test_sessions[test_session['test_id']] = test_session
        
        # Return first question
        if test_questions:
            first_question = test_questions[0].copy()
            # Remove correct answer info from response
            first_question.pop('correct_index', None)
            first_question.pop('word', None)
            
            return jsonify({
                'test_id': test_session['test_id'],
                'total_questions': len(test_questions),
                'current_question': 1,
                'question': first_question
            })
        else:
            return jsonify({'error': 'No questions available'}), 503
            
    except Exception as e:
        print(f"[ERROR] Level test start error: {e}")
        return jsonify({'error': 'Failed to start level test'}), 500

@app.route('/api/level/test/answer', methods=['POST'])
def submit_level_test_answer():
    """Submit an answer for level test"""
    is_authenticated, user_or_response, status_code = require_auth()
    if not is_authenticated:
        return user_or_response, status_code
    
    data = request.get_json()
    test_id = data.get('test_id')
    selected_index = data.get('selected_index')
    
    if not test_id or selected_index is None:
        return jsonify({'error': 'Missing test_id or selected_index'}), 400
    
    # Get test session
    if not hasattr(app, 'test_sessions') or test_id not in app.test_sessions:
        return jsonify({'error': 'Test session not found'}), 404
    
    test_session = app.test_sessions[test_id]
    
    if test_session['status'] != 'active':
        return jsonify({'error': 'Test is not active'}), 400
    
    current_q_index = test_session['current_question']
    if current_q_index >= len(test_session['questions']):
        return jsonify({'error': 'No more questions'}), 400
    
    current_question = test_session['questions'][current_q_index]
    is_correct = selected_index == current_question['correct_index']
    
    # Record answer
    answer_record = {
        'question_id': current_question['id'],
        'level': current_question['level'],
        'selected_index': selected_index,
        'correct_index': current_question['correct_index'],
        'is_correct': is_correct,
        'answered_at': datetime.now().isoformat()
    }
    test_session['answers'].append(answer_record)
    test_session['current_question'] += 1
    
    # Check if test is complete
    if test_session['current_question'] >= len(test_session['questions']):
        # Calculate final level
        test_session['status'] = 'completed'
        test_session['end_time'] = datetime.now().isoformat()
        
        final_level = calculate_user_level(test_session['answers'])
        test_session['final_level'] = final_level
        
        # Update user level in database
        update_user_level(test_session['user_id'], final_level)
        
        return jsonify({
            'test_completed': True,
            'final_level': final_level,
            'correct_answers': sum(1 for a in test_session['answers'] if a['is_correct']),
            'total_questions': len(test_session['questions']),
            'test_summary': get_test_summary(test_session['answers'])
        })
    
    # Return next question
    next_question = test_session['questions'][test_session['current_question']].copy()
    next_question.pop('correct_index', None)
    next_question.pop('word', None)
    
    return jsonify({
        'test_completed': False,
        'current_question': test_session['current_question'] + 1,
        'total_questions': len(test_session['questions']),
        'question': next_question,
        'previous_correct': is_correct
    })

@app.route('/api/level/current', methods=['GET'])
def get_current_level():
    """Get user's current level"""
    is_authenticated, user_or_response, status_code = require_auth()
    if not is_authenticated:
        return user_or_response, status_code
    
    user = user_or_response
    
    return jsonify({
        'current_level': user.get('level', 'UNSET'),
        'needs_assessment': user.get('level', 'UNSET') == 'UNSET'
    })

def calculate_user_level(answers):
    """Calculate user level based on test answers with enhanced algorithm including time pressure"""
    if not answers:
        return 'A1'
    
    # Enhanced scoring system
    level_scores = {'A1': 0, 'A2': 0, 'B1': 0, 'B2': 0, 'C1': 0}
    level_weights = {'A1': 1, 'A2': 2, 'B1': 3, 'B2': 4, 'C1': 5}
    
    total_weighted_score = 0
    max_possible_score = 0
    
    # Count correct answers by level with weighted scoring
    level_stats = {}
    consecutive_correct = 0
    consecutive_wrong = 0
    
    for i, answer in enumerate(answers):
        level = answer['level']
        is_correct = answer['is_correct']
        weight = level_weights[level]
        time_taken = answer.get('time_taken', 0)  # Time in seconds
        time_limit = answer.get('time_limit', 60)  # Default 60 seconds
        question_type = answer.get('type', 'translation')
        
        if level not in level_stats:
            level_stats[level] = {'correct': 0, 'total': 0, 'weighted_score': 0}
        
        level_stats[level]['total'] += 1
        max_possible_score += weight
        
        if is_correct:
            level_stats[level]['correct'] += 1
            score = weight
            
            # Time bonus for quick correct answers (answered in first 25% of time limit)
            if time_taken > 0 and time_taken <= time_limit * 0.25:
                score += weight * 0.15  # 15% bonus for very quick answers
            elif time_taken > 0 and time_taken <= time_limit * 0.5:
                score += weight * 0.05  # 5% bonus for quick answers
            
            # Bonus for difficult question types (increased bonuses for extreme difficulty)
            if question_type == 'extreme_challenge':
                score += weight * 0.5  # 50% bonus for extreme challenge questions!
            elif question_type in ['ultra_reading', 'ultra_grammar', 'ultra_vocabulary', 
                               'ultra_collocations', 'ultra_logic', 'ultra_academic']:
                score += weight * 0.25  # 25% bonus for ultra-advanced questions
            elif question_type in ['reading_comprehension', 'advanced_grammar', 'contextual_vocabulary']:
                score += weight * 0.15  # 15% bonus for advanced question types
            elif question_type in ['grammar', 'phrasal_verb', 'vocabulary', 'context']:
                score += weight * 0.08  # 8% bonus for enhanced questions
            
            level_stats[level]['weighted_score'] += score
            total_weighted_score += score
            consecutive_correct += 1
            consecutive_wrong = 0
            
            # Bonus for consecutive correct answers
            if consecutive_correct >= 3:
                total_weighted_score += weight * 0.1  # 10% bonus
                
        else:
            consecutive_correct = 0
            consecutive_wrong += 1
            
            # EXTREME penalties for wrong answers
            penalty = 0
            
            # Massive penalties for wrong answers on extreme/advanced questions
            if question_type == 'extreme_challenge':
                penalty += weight * 0.5  # 50% penalty for wrong extreme challenge answers!
            elif question_type in ['ultra_reading', 'ultra_grammar', 'ultra_vocabulary', 
                               'ultra_collocations', 'ultra_logic', 'ultra_academic']:
                penalty += weight * 0.35  # 35% penalty for wrong ultra-advanced answers
            elif question_type in ['reading_comprehension', 'advanced_grammar', 'contextual_vocabulary']:
                penalty += weight * 0.25  # 25% penalty for wrong advanced answers
            
            # Time penalty for taking too long on wrong answers (increased)
            if time_taken > time_limit * 0.7:  # Took more than 70% of time limit
                penalty += weight * 0.25  # 25% penalty for slow wrong answers
            
            # Consecutive wrong answer penalties (more severe)
            if consecutive_wrong >= 2 and weight >= 3:  # B1, B2, C1 levels
                penalty += weight * 0.2  # 20% penalty for consecutive wrong answers
            if consecutive_wrong >= 3:  # Any level
                penalty += weight * 0.15  # Additional 15% penalty for 3+ wrong in a row
            
            total_weighted_score -= penalty
    
    # Ensure score doesn't go negative
    total_weighted_score = max(0, total_weighted_score)
    
    # Calculate overall accuracy with time and difficulty factors
    overall_accuracy = total_weighted_score / max_possible_score if max_possible_score > 0 else 0
    
    # INSANELY STRICT thresholds - this will be extremely difficult
    level_thresholds = {
        'C1': 0.95,  # 95% accuracy needed for C1 (almost impossible!)
        'B2': 0.88,  # 88% accuracy needed for B2 (very difficult)
        'B1': 0.78,  # 78% accuracy needed for B1 (challenging)
        'A2': 0.65,  # 65% accuracy needed for A2 (moderate)
        'A1': 0.0    # Default to A1
    }
    
    # Check level-specific performance with ultra-strict requirements
    user_level = 'A1'
    for level in ['C1', 'B2', 'B1', 'A2']:
        if level in level_stats:
            level_accuracy = level_stats[level]['correct'] / level_stats[level]['total']
            
            # INSANELY strict level-specific thresholds
            if level == 'C1':
                level_threshold = 0.90  # Need 90% on C1 questions specifically!
            elif level == 'B2':
                level_threshold = 0.80  # Need 80% on B2 questions specifically
            elif level == 'B1':
                level_threshold = 0.70  # Need 70% on B1 questions
            else:
                level_threshold = 0.60  # Need 60% on A2 questions
            
            # Additional requirements: must answer more questions at that level
            min_questions_required = 4 if level in ['C1', 'B2'] else 3
            
            # Must meet ALL criteria for level assignment
            if (overall_accuracy >= level_thresholds[level] and 
                level_accuracy >= level_threshold and 
                level_stats[level]['total'] >= min_questions_required):
                user_level = level
                break
    
    print(f"[DEBUG] Enhanced level calculation: overall_accuracy={overall_accuracy:.2f}, final_level={user_level}")
    return user_level

def get_test_summary(answers):
    """Get detailed test summary"""
    total = len(answers)
    correct = sum(1 for a in answers if a['is_correct'])
    
    level_breakdown = {}
    for answer in answers:
        level = answer['level']
        if level not in level_breakdown:
            level_breakdown[level] = {'correct': 0, 'total': 0}
        
        level_breakdown[level]['total'] += 1
        if answer['is_correct']:
            level_breakdown[level]['correct'] += 1
    
    return {
        'total_questions': total,
        'correct_answers': correct,
        'accuracy': round((correct / total) * 100, 1) if total > 0 else 0,
        'level_breakdown': level_breakdown
    }

def update_user_level(user_id, level):
    """Update user's level in database"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE users SET level = ? WHERE id = ?',
                (level, user_id)
            )
            conn.commit()
            print(f"[DEBUG] Updated user {user_id} level to {level}")
    except Exception as e:
        print(f"[ERROR] Failed to update user level: {e}")

# Initialize database on startup
init_database()

if __name__ == '__main__':
    # Get port from environment variable (for Render deployment) or default to 5000
    port = int(os.environ.get('PORT', 5000))
    print(f"[DEBUG] Starting Flask app on port {port}")
    print(f"[DEBUG] Environment: {os.environ.get('FLASK_ENV', 'development')}")
    app.run(host='0.0.0.0', port=port, debug=False)
