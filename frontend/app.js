// EnglishCE - Frontend JavaScript

// Configuration
// Production: Update this to your backend URL
const API_BASE_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:5000/api' 
    : 'https://englishce-backend.onrender.com/api';  // Render deployment URL

// Global state
let currentUser = null;
let authToken = null; // Store authentication token
let currentGame = {
    mode: null,
    question: null,
    score: 0,
    lives: 3,
    timer: null,
    timeLeft: 5,
    recentWords: []
};

// Utility functions
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    
    const container = document.getElementById('toast-container');
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

function showLoading(button) {
    button.classList.add('btn-loading');
    button.disabled = true;
}

function hideLoading(button) {
    button.classList.remove('btn-loading');
    button.disabled = false;
}

async function apiCall(endpoint, method = 'GET', data = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json',
        },
        credentials: 'include'  // Important for session cookies
    };
    
    // Add authorization token if available
    if (authToken) {
        options.headers['Authorization'] = `Bearer ${authToken}`;
    }
    
    if (data) {
        options.body = JSON.stringify(data);
    }
    
    try {
        console.log(`[DEBUG] API Call: ${method} ${API_BASE_URL}${endpoint}`, data);
        
        const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
        
        let result;
        try {
            result = await response.json();
        } catch (e) {
            throw new Error('Invalid response from server');
        }
        
        console.log(`[DEBUG] API Response:`, result);
        
        if (!response.ok) {
            throw new Error(result.error || `HTTP ${response.status}: ${response.statusText}`);
        }
        
        return result;
    } catch (error) {
        console.error('API Error:', error);
        console.error('Full error details:', {
            message: error.message,
            stack: error.stack,
            url: `${API_BASE_URL}${endpoint}`,
            method: method
        });
        
        // Handle specific network errors
        if (error.message.includes('Failed to fetch')) {
            throw new Error(`Backend server bağlantısı kurulamadı. URL: ${API_BASE_URL}${endpoint}`);
        }
        
        throw error;
    }
}

// Restore authentication from localStorage
function restoreAuthState() {
    const storedToken = localStorage.getItem('authToken');
    const storedUser = localStorage.getItem('currentUser');
    
    if (storedToken && storedUser) {
        try {
            authToken = storedToken;
            currentUser = JSON.parse(storedUser);
            console.log('[DEBUG] Auth state restored from localStorage:', currentUser.username);
            return true;
        } catch (error) {
            console.error('[DEBUG] Failed to restore auth state:', error);
            // Clear invalid data
            localStorage.removeItem('authToken');
            localStorage.removeItem('currentUser');
        }
    }
    
    return false;
}

// Check authentication status
async function checkAuth() {
    // First try to restore from localStorage
    if (restoreAuthState()) {
        // Verify token is still valid by making a test API call
        try {
            const result = await apiCall('/auth/check');
            if (result.authenticated) {
                console.log('[DEBUG] Token validation successful');
                return true;
            }
        } catch (error) {
            console.log('[DEBUG] Token validation failed, clearing auth state');
            authToken = null;
            currentUser = null;
            localStorage.removeItem('authToken');
            localStorage.removeItem('currentUser');
        }
    }
    
    // Fall back to session-based check
    try {
        const result = await apiCall('/auth/check');
        console.log('[DEBUG] Auth check result:', result);
        
        if (result.authenticated) {
            currentUser = result.user;
            return true;
        }
        return false;
    } catch (error) {
        console.log('[DEBUG] Auth check failed:', error.message);
        return false;
    }
}

// Ensure user is authenticated before API calls
async function ensureAuthenticated() {
    if (!currentUser) {
        const isAuth = await checkAuth();
        if (!isAuth) {
            showToast('Giriş yapmanız gerekiyor', 'error');
            showLoginScreen();
            return false;
        }
    }
    return true;
}

// Check if current user is a guest user
function isGuestUser() {
    return currentUser && currentUser.is_guest === true;
}

// Show warning for features that require registered account
function checkFeatureAccess(featureName) {
    if (isGuestUser()) {
        showToast(`"${featureName}" özelliği için kayıtlı hesap gerekiyor. Lütfen giriş yapın veya kayıt olun.`, 'error');
        return false;
    }
    return true;
}
function showLogin() {
    document.getElementById('login-form').style.display = 'block';
    document.getElementById('register-form').style.display = 'none';
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-btn')[0].classList.add('active');
}

function showRegister() {
    document.getElementById('login-form').style.display = 'none';
    document.getElementById('register-form').style.display = 'block';
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-btn')[1].classList.add('active');
}

async function handleGuestLogin() {
    const button = document.querySelector('.guest-btn');
    showLoading(button);
    
    try {
        const result = await apiCall('/auth/guest', 'POST');
        
        // Store guest user info and auth token
        currentUser = result.user;
        authToken = result.token;
        
        // Store token in localStorage for persistence
        localStorage.setItem('authToken', authToken);
        localStorage.setItem('currentUser', JSON.stringify(currentUser));
        
        console.log('[DEBUG] Guest login successful');
        
        showToast('Misafir olarak giriş yaptınız! Sınırlı özellikler kullanılabilir.');
        showMainScreen();
        
    } catch (error) {
        showToast(error.message, 'error');
    } finally {
        hideLoading(button);
    }
}

async function handleLogin(event) {
    event.preventDefault();
    const button = event.target.querySelector('button[type="submit"]');
    showLoading(button);
    
    try {
        const username = document.getElementById('login-username').value;
        const password = document.getElementById('login-password').value;
        
        const result = await apiCall('/auth/login', 'POST', { username, password });
        
        // Store both user info and auth token
        currentUser = result.user;
        authToken = result.token;
        
        // Store token in localStorage for persistence
        localStorage.setItem('authToken', authToken);
        localStorage.setItem('currentUser', JSON.stringify(currentUser));
        
        console.log('[DEBUG] Login successful, token stored:', authToken?.substr(0, 10) + '...');
        
        showToast('Giriş başarılı!');
        showMainScreen();
        
    } catch (error) {
        showToast(error.message, 'error');
    } finally {
        hideLoading(button);
    }
}

async function handleRegister(event) {
    event.preventDefault();
    const button = event.target.querySelector('button[type="submit"]');
    showLoading(button);
    
    try {
        const username = document.getElementById('register-username').value;
        const password = document.getElementById('register-password').value;
        const confirm = document.getElementById('register-confirm').value;
        
        if (password !== confirm) {
            throw new Error('Şifreler eşleşmiyor');
        }
        
        await apiCall('/auth/register', 'POST', { username, password });
        
        showToast('Kayıt başarılı! Şimdi giriş yapabilirsiniz.');
        showLogin();
        
    } catch (error) {
        showToast(error.message, 'error');
    } finally {
        hideLoading(button);
    }
}

async function logout() {
    try {
        await apiCall('/auth/logout', 'POST');
        
        // Clear all authentication data
        currentUser = null;
        authToken = null;
        localStorage.removeItem('authToken');
        localStorage.removeItem('currentUser');
        
        // Clear API key from session
        localStorage.removeItem('openrouter_api_key');
        
        showLoginScreen();
        showToast('Çıkış yapıldı');
    } catch (error) {
        showToast('Çıkış yaparken hata oluştu', 'error');
        
        // Clear local data anyway
        currentUser = null;
        authToken = null;
        localStorage.removeItem('authToken');
        localStorage.removeItem('currentUser');
        
        // Clear API key from session
        localStorage.removeItem('openrouter_api_key');
        
        showLoginScreen();
    }
}

// Screen management
function showLoginScreen() {
    document.getElementById('loading-screen').style.display = 'none';
    document.getElementById('login-screen').style.display = 'block';
    document.getElementById('main-screen').style.display = 'none';
}

function showMainScreen() {
    document.getElementById('loading-screen').style.display = 'none';
    document.getElementById('login-screen').style.display = 'none';
    document.getElementById('main-screen').style.display = 'block';
    
    // Update user info
    document.getElementById('username').textContent = currentUser.username;
    updateUserLevelDisplay();
    
    // Load mistake count
    loadMistakeCount();
    showSection('menu');
}

function showSection(sectionName) {
    // Hide all sections
    document.querySelectorAll('.section').forEach(section => {
        section.style.display = 'none';
    });
    
    // Show target section
    document.getElementById(`${sectionName}-section`).style.display = 'block';
    
    // Update navigation
    document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));
    const targetBtn = Array.from(document.querySelectorAll('.nav-btn')).find(btn => 
        btn.onclick && btn.onclick.toString().includes(`'${sectionName}'`)
    );
    if (targetBtn) targetBtn.classList.add('active');
    
    // Initialize section-specific content
    if (sectionName === 'ai-teacher') {
        initAITeacher();
    } else if (sectionName === 'reading') {
        initReading();
    } else if (sectionName === 'mistakes') {
        loadMistakes();
    } else if (sectionName === 'level-assessment') {
        // Level assessment initialization is handled by startLevelAssessment()
    }
}

// Game functions
async function startGame(mode) {
    currentGame.mode = mode;
    currentGame.score = 0;
    currentGame.lives = mode === 'race' ? 3 : Infinity;
    currentGame.recentWords = [];
    
    showSection('game');
    
    // Show/hide game elements based on mode
    const timerStat = document.getElementById('timer-stat');
    const livesStat = document.getElementById('lives-stat');
    
    if (mode === 'race') {
        timerStat.style.display = 'block';
        livesStat.style.display = 'block';
        document.getElementById('lives-display').textContent = currentGame.lives;
    } else {
        timerStat.style.display = 'none';
        livesStat.style.display = 'none';
    }
    
    await loadNextQuestion();
}

async function loadNextQuestion() {
    // Check authentication first
    if (!(await ensureAuthenticated())) {
        return;
    }
    
    try {
        const questionData = await apiCall('/game/question', 'POST', {
            mode: currentGame.mode,
            recent_words: currentGame.recentWords,
            question_mode: Math.random() > 0.5 ? 'TR_PROMPT' : 'EN_PROMPT'
        });
        
        currentGame.question = questionData;
        
        // Update UI
        document.getElementById('question-text').textContent = questionData.question;
        document.getElementById('question-counter').textContent = currentGame.score + 1;
        
        // Update options
        const optionBtns = document.querySelectorAll('.option-btn');
        optionBtns.forEach((btn, index) => {
            btn.querySelector('.option-text').textContent = questionData.options[index];
            btn.className = 'option-btn';
            btn.disabled = false;
        });
        
        // Clear feedback
        document.getElementById('feedback').textContent = '';
        document.getElementById('next-btn').style.display = 'none';
        
        // Start timer for race mode
        if (currentGame.mode === 'race') {
            startTimer();
        }
        
        // Track recent word
        if (questionData.word_pair) {
            currentGame.recentWords.push(questionData.word_pair.en);
            if (currentGame.recentWords.length > 10) {
                currentGame.recentWords.shift();
            }
        }
        
    } catch (error) {
        showToast('Soru yüklenirken hata oluştu: ' + error.message, 'error');
    }
}

function startTimer() {
    currentGame.timeLeft = 5;
    document.getElementById('timer-display').textContent = currentGame.timeLeft;
    
    currentGame.timer = setInterval(() => {
        currentGame.timeLeft--;
        document.getElementById('timer-display').textContent = currentGame.timeLeft;
        
        if (currentGame.timeLeft <= 0) {
            clearInterval(currentGame.timer);
            handleTimeout();
        }
    }, 1000);
}

function stopTimer() {
    if (currentGame.timer) {
        clearInterval(currentGame.timer);
        currentGame.timer = null;
    }
}

async function selectAnswer(index) {
    stopTimer();
    
    // Disable all buttons
    document.querySelectorAll('.option-btn').forEach(btn => btn.disabled = true);
    
    try {
        const result = await apiCall('/game/answer', 'POST', {
            selected_index: index,
            correct_index: currentGame.question.correct_index,
            word_pair: currentGame.question.word_pair
        });
        
        // Update UI based on result
        const optionBtns = document.querySelectorAll('.option-btn');
        const selectedBtn = optionBtns[index];
        const correctBtn = optionBtns[currentGame.question.correct_index];
        
        if (result.correct) {
            selectedBtn.classList.add('correct');
            document.getElementById('feedback').innerHTML = '✅ Doğru!';
            document.getElementById('feedback').style.color = 'var(--success-color)';
            currentGame.score++;
        } else {
            selectedBtn.classList.add('incorrect');
            correctBtn.classList.add('correct');
            document.getElementById('feedback').innerHTML = '❌ Yanlış! Doğru cevap yeşil renkte gösterildi.';
            document.getElementById('feedback').style.color = 'var(--error-color)';
            
            if (currentGame.mode === 'race') {
                currentGame.lives--;
                document.getElementById('lives-display').textContent = currentGame.lives;
                
                if (currentGame.lives <= 0) {
                    showGameOver();
                    return;
                }
            }
        }
        
        // Show next button
        document.getElementById('next-btn').style.display = 'block';
        
        // Auto-advance in race mode
        if (currentGame.mode === 'race') {
            setTimeout(() => {
                nextQuestion();
            }, result.correct ? 800 : 1200);
        }
        
    } catch (error) {
        showToast('Cevap gönderilirken hata oluştu: ' + error.message, 'error');
    }
}

function handleTimeout() {
    // Show correct answer
    const correctBtn = document.querySelectorAll('.option-btn')[currentGame.question.correct_index];
    correctBtn.classList.add('correct');
    
    document.getElementById('feedback').innerHTML = '⏰ Süre doldu! Doğru cevap yeşil renkte gösterildi.';
    document.getElementById('feedback').style.color = 'var(--error-color)';
    
    // Disable all buttons
    document.querySelectorAll('.option-btn').forEach(btn => btn.disabled = true);
    
    // Lose life
    currentGame.lives--;
    document.getElementById('lives-display').textContent = currentGame.lives;
    
    if (currentGame.lives <= 0) {
        showGameOver();
    } else {
        setTimeout(() => {
            nextQuestion();
        }, 1200);
    }
}

function nextQuestion() {
    loadNextQuestion();
}

function showGameOver() {
    showToast(`Oyun bitti! ${currentGame.score} soru doğru cevapladın.`, 'info');
    showSection('menu');
}

// AI Teacher functions
function initAITeacher() {
    // Check if API key is already set in localStorage (persistent)
    const persistentApiKey = localStorage.getItem('openrouter_api_key');
    if (persistentApiKey) {
        showChatInterface();
        loadChatHistory();
    } else {
        showApiKeyInput();
    }
}

function showApiKeyInput() {
    document.getElementById('api-key-section').style.display = 'block';
    document.getElementById('chat-messages').style.display = 'none';
    document.getElementById('chat-input-container').style.display = 'none';
}

function showChatInterface() {
    document.getElementById('api-key-section').style.display = 'none';
    document.getElementById('chat-messages').style.display = 'block';
    document.getElementById('chat-input-container').style.display = 'block';
    
    // Initialize chat if needed
    const messagesContainer = document.getElementById('chat-messages');
    if (messagesContainer.children.length === 1) {
        // Only welcome message exists
        loadChatHistory();
    }
}

function setApiKey() {
    const apiKeyInput = document.getElementById('api-key-input');
    const apiKey = apiKeyInput.value.trim();
    
    if (!apiKey) {
        alert('Lütfen API key girin!');
        return;
    }
    
    if (!apiKey.startsWith('sk-or-v1-')) {
        alert('Geçersiz API key formatı! OpenRouter API key "sk-or-v1-" ile başlamalı.');
        return;
    }
    
    // Store in localStorage (persistent across sessions)
    localStorage.setItem('openrouter_api_key', apiKey);
    
    // Clear input for security
    apiKeyInput.value = '';
    
    // Show chat interface
    showChatInterface();
    
    // Add welcome message
    addMessage('🎉 API key başarıyla kaydedildi! Artık her zaman AI öğretmeni kullanabilirsin.', 'bot');
}

function changeApiKey() {
    // Clear current API key
    localStorage.removeItem('openrouter_api_key');
    
    // Show API key input again
    showApiKeyInput();
    
    // Add instruction message
    addMessage('🔑 API key değiştirmek için yeni key’inizi girin.', 'bot');
}

// AI Teacher functions - Enhanced with ChatGPT-style features
async function sendMessage() {
    // Check authentication first
    if (!(await ensureAuthenticated())) {
        return;
    }
    
    // Check if API key is set
    const apiKey = localStorage.getItem('openrouter_api_key');
    if (!apiKey) {
        showApiKeyInput();
        addMessage('⚠️ API key gerekli! Lütfen önce API key’inizi girin.', 'error');
        return;
    }
    
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Clear input
    input.value = '';
    
    // Add user message to chat
    addMessage(message, 'user');
    
    // Show typing indicator
    showTypingIndicator();
    
    try {
        const language = document.getElementById('chat-language').value;
        const result = await apiCall('/ai/chat', 'POST', { 
            message, 
            language,
            user_api_key: apiKey  // Send API key with request
        });
        
        // Remove typing indicator
        hideTypingIndicator();
        
        // Add AI response with context indicator
        addMessage(result.response, 'bot', result.has_context);
        
    } catch (error) {
        // Remove typing indicator
        hideTypingIndicator();
        
        // Handle 401 errors (invalid API key)
        if (error.message.includes('401') || error.message.includes('Unauthorized')) {
            localStorage.removeItem('openrouter_api_key');
            showApiKeyInput();
            addMessage('⚠️ API key geçersiz veya süresi dolmuş! Lütfen yeni bir API key girin.', 'error');
        } else {
            // Show error message
            addMessage('⚠️ Üzgünüm, bir hata oluştu: ' + error.message, 'error');
        }
    }
}

function addMessage(content, sender, hasContext = false) {
    const messagesContainer = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    
    messageDiv.className = `message ${sender}-message`;
    
    if (sender === 'user') {
        messageDiv.innerHTML = `
            <div class="message-avatar">👤</div>
            <div class="message-content">
                <div class="message-header">
                    <span class="sender-name">Sen</span>
                    <span class="message-time">${getCurrentTime()}</span>
                </div>
                <div class="message-text">${escapeHtml(content)}</div>
            </div>
        `;
    } else if (sender === 'bot') {
        const contextIndicator = hasContext ? '<span class="context-indicator" title="Önceki sohbetlerimizi hatırlıyorum">🧠</span>' : '';
        
        messageDiv.innerHTML = `
            <div class="message-avatar">🤖</div>
            <div class="message-content">
                <div class="message-header">
                    <span class="sender-name">AI Öğretmen ${contextIndicator}</span>
                    <span class="message-time">${getCurrentTime()}</span>
                </div>
                <div class="message-text">${formatAIResponse(content)}</div>
            </div>
        `;
    } else if (sender === 'error') {
        messageDiv.innerHTML = `
            <div class="message-avatar">⚠️</div>
            <div class="message-content">
                <div class="message-text error-text">${escapeHtml(content)}</div>
            </div>
        `;
    }
    
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function formatAIResponse(content) {
    // Format the AI response to look more structured like ChatGPT
    let formatted = content
        // Convert **bold** to <strong>
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        // Convert *italic* to <em>
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        // Convert numbered lists
        .replace(/^(\d+\.)\s(.+)$/gm, '<div class="ai-list-item"><span class="list-number">$1</span>$2</div>')
        // Convert bullet points
        .replace(/^[•·-]\s(.+)$/gm, '<div class="ai-bullet-item"><span class="bullet">•</span>$1</div>')
        // Convert headers with emojis (look for emoji + text pattern)
        .replace(/^(.{1,2})\s\*\*(.+?)\*\*/gm, '<div class="ai-section-header">$1 <strong>$2</strong></div>')
        // Convert line breaks
        .replace(/\n/g, '<br>');
    
    return formatted;
}

function showTypingIndicator() {
    const messagesContainer = document.getElementById('chat-messages');
    const typingDiv = document.createElement('div');
    typingDiv.id = 'typing-indicator';
    typingDiv.className = 'message bot-message typing';
    typingDiv.innerHTML = `
        <div class="message-avatar">🤖</div>
        <div class="message-content">
            <div class="typing-dots">
                <span></span><span></span><span></span>
            </div>
        </div>
    `;
    
    messagesContainer.appendChild(typingDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function hideTypingIndicator() {
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

function sendSuggestion(suggestion) {
    document.getElementById('chat-input').value = suggestion;
    sendMessage();
}

function addMessageToChat(message, isUser) {
    // Legacy function for backward compatibility
    addMessage(message, isUser ? 'user' : 'bot');
}

function getCurrentTime() {
    return new Date().toLocaleTimeString('tr-TR', { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

async function loadChatHistory() {
    try {
        const result = await apiCall('/ai/chat/history?limit=10');
        
        if (result.error) {
            addMessage('⚠️ Geçmiş yüklenirken hata: ' + result.error, 'error');
            return;
        }
        
        if (result.conversations && result.conversations.length > 0) {
            // Clear current messages except welcome message
            const messagesContainer = document.getElementById('chat-messages');
            const welcomeMessage = messagesContainer.firstElementChild;
            messagesContainer.innerHTML = '';
            messagesContainer.appendChild(welcomeMessage);
            
            // Add history messages (in reverse order since they come newest first)
            result.conversations.reverse().forEach(conv => {
                addMessage(conv.user_message, 'user');
                addMessage(conv.ai_response, 'bot', true);
            });
            
            addMessage(`📚 ${result.conversations.length} önceki sohbet yüklendi!`, 'bot');
        } else {
            addMessage('📝 Henüz sohbet geçmişin yok. İlk sorunu sor!', 'bot');
        }
    } catch (error) {
        addMessage('⚠️ Geçmiş yüklenirken hata: ' + error.message, 'error');
    }
}

function clearChatHistory() {
    if (!confirm('Tüm sohbet geçmişini silmek istediğinden emin misin?')) {
        return;
    }
    
    fetch(`${API_BASE_URL}/ai/chat/clear`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${authToken}`
        },
        credentials: 'include'
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            addMessage('⚠️ Geçmiş silinirken hata: ' + data.error, 'error');
        } else {
            // Clear chat messages except welcome
            const messagesContainer = document.getElementById('chat-messages');
            const welcomeMessage = messagesContainer.firstElementChild;
            messagesContainer.innerHTML = '';
            messagesContainer.appendChild(welcomeMessage);
            
            addMessage('🗑️ Sohbet geçmişi temizlendi!', 'bot');
        }
    })
    .catch(error => {
        addMessage('⚠️ Geçmiş silinirken hata: ' + error.message, 'error');
    });
}

// Reading functions
async function initReading() {
    try {
        const stories = await apiCall('/reading/stories');
        const select = document.getElementById('story-select');
        
        // Clear existing options except first
        select.innerHTML = '<option value="">Hikaye seçin...</option>';
        
        stories.forEach(story => {
            const option = document.createElement('option');
            option.value = story.id;
            option.textContent = `${story.title} (${story.level})`;
            select.appendChild(option);
        });
        
    } catch (error) {
        showToast('Hikayeler yüklenirken hata oluştu: ' + error.message, 'error');
    }
}

async function loadStory() {
    const select = document.getElementById('story-select');
    const storyId = select.value;
    
    if (!storyId) {
        document.getElementById('story-title').textContent = '';
        document.getElementById('story-content').innerHTML = '<p class="reading-instruction">Yukarıdan bir hikaye seçin. Kelimelerin üzerine tıklayarak çevirisini görebilirsiniz.</p>';
        return;
    }
    
    try {
        const storyData = await apiCall(`/reading/story/${storyId}`);
        const selectedOption = select.options[select.selectedIndex];
        const title = selectedOption.textContent.split(' (')[0];
        
        document.getElementById('story-title').textContent = title;
        
        // Create interactive content
        const contentDiv = document.getElementById('story-content');
        contentDiv.innerHTML = '';
        
        storyData.sentences.forEach(sentence => {
            const p = document.createElement('p');
            p.style.marginBottom = '1rem';
            p.style.textAlign = 'center'; // User prefers centered text
            
            // Split sentence into words and make them interactive
            const words = sentence.split(/(\s+)/);
            words.forEach(word => {
                if (word.trim()) {
                    const span = document.createElement('span');
                    span.textContent = word;
                    span.className = 'interactive-word';
                    span.style.position = 'relative';
                    span.onclick = () => translateWord(word.replace(/[^\w]/g, ''));
                    
                    // Add hover button (hidden by default, shown on hover per user preference)
                    const addBtn = document.createElement('button');
                    addBtn.textContent = '+';
                    addBtn.className = 'word-add-btn';
                    addBtn.onclick = (e) => {
                        e.stopPropagation();
                        saveWordToVocabulary(word.replace(/[^\w]/g, ''));
                    };
                    
                    span.appendChild(addBtn);
                    p.appendChild(span);
                } else {
                    p.appendChild(document.createTextNode(word));
                }
            });
            
            contentDiv.appendChild(p);
        });
        
    } catch (error) {
        showToast('Hikaye yüklenirken hata oluştu: ' + error.message, 'error');
    }
}

async function translateWord(word) {
    try {
        const result = await apiCall('/translate', 'POST', { text: word });
        showTranslationModal(word, result.translation);
    } catch (error) {
        showToast('Çeviri yapılırken hata oluştu: ' + error.message, 'error');
    }
}

function showTranslationModal(original, translation) {
    document.getElementById('original-text').textContent = original;
    document.getElementById('translated-text').textContent = translation;
    document.getElementById('translation-modal').style.display = 'flex';
}

function closeTranslationModal() {
    document.getElementById('translation-modal').style.display = 'none';
}

function saveWordToVocabulary(word) {
    // This would save word to user's vocabulary
    showToast(`"${word}" kelimesi kaydedildi!`);
}

// Mistakes functions
async function loadMistakeCount() {
    try {
        const mistakes = await apiCall('/mistakes');
        document.getElementById('mistake-count').textContent = `📊 ${mistakes.length} kelime`;
    } catch (error) {
        console.error('Error loading mistake count:', error);
    }
}

async function loadMistakes() {
    try {
        const mistakes = await apiCall('/mistakes');
        const container = document.getElementById('mistakes-content');
        
        if (mistakes.length === 0) {
            container.innerHTML = '<p class="text-center">Henüz yanlış yaptığın kelime yok. Oyunlarda yanlış yapınca burada görünecek.</p>';
            return;
        }
        
        container.innerHTML = '';
        
        mistakes.forEach(mistake => {
            const card = document.createElement('div');
            card.className = 'mistake-card';
            card.style.cssText = `
                background: white;
                padding: 1rem;
                border-radius: 0.5rem;
                box-shadow: var(--shadow-sm);
                margin-bottom: 1rem;
                display: flex;
                justify-content: space-between;
                align-items: center;
            `;
            
            card.innerHTML = `
                <div>
                    <strong>${mistake.en}</strong> → ${mistake.tr}
                    <div style="font-size: 0.875rem; color: var(--gray-600);">
                        ${mistake.mistake_count} kez yanlış yapıldı
                    </div>
                </div>
                <button class="btn btn-primary btn-sm" onclick="practiceWord('${mistake.en}')">
                    Çalış
                </button>
            `;
            
            container.appendChild(card);
        });
        
    } catch (error) {
        showToast('Yanlışlar yüklenirken hata oluştu: ' + error.message, 'error');
    }
}

function practiceWord(word) {
    // Start mistakes mode and focus on this word
    startGame('mistakes');
}

// Window resize handler for responsive text centering (user preference)
window.addEventListener('resize', () => {
    // Re-center text elements when window is resized
    const storyContent = document.getElementById('story-content');
    if (storyContent) {
        const paragraphs = storyContent.querySelectorAll('p');
        paragraphs.forEach(p => {
            p.style.textAlign = 'center';
        });
    }
});

// Event listeners
document.addEventListener('DOMContentLoaded', async () => {
    // Hide loading screen
    setTimeout(async () => {
        document.getElementById('loading-screen').style.display = 'none';
        
        // Check if user is already logged in
        const isAuthenticated = await checkAuth();
        
        if (isAuthenticated) {
            console.log('[DEBUG] User already authenticated, showing main screen');
            showMainScreen();
        } else {
            console.log('[DEBUG] User not authenticated, showing login screen');
            showLoginScreen();
        }
    }, 1000);
    
    // Form event listeners
    document.getElementById('login-form').addEventListener('submit', handleLogin);
    document.getElementById('register-form').addEventListener('submit', handleRegister);
    
    // Chat input enter key
    document.getElementById('chat-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
    // API key input enter key
    const apiKeyInput = document.getElementById('api-key-input');
    if (apiKeyInput) {
        apiKeyInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                setApiKey();
            }
        });
    }
    
    // Modal click outside to close
    document.getElementById('translation-modal').addEventListener('click', (e) => {
        if (e.target.id === 'translation-modal') {
            closeTranslationModal();
        }
    });
});

// Level Assessment Functions
let currentLevelTest = {
    testId: null,
    currentQuestion: 0,
    totalQuestions: 30,
    answers: [],
    questionTimer: null,
    questionStartTime: null,
    timeLimit: 60,  // default time limit in seconds
    timeRemaining: 60
};

async function startLevelAssessment() {
    showSection('level-assessment');
    
    // Reset assessment state
    document.getElementById('assessment-instructions').style.display = 'block';
    document.getElementById('assessment-test').style.display = 'none';
    document.getElementById('assessment-results').style.display = 'none';
    
    // Clear any existing timer
    if (currentLevelTest.questionTimer) {
        clearInterval(currentLevelTest.questionTimer);
    }
    
    currentLevelTest = {
        testId: null,
        currentQuestion: 0,
        totalQuestions: 30,
        answers: [],
        questionTimer: null,
        questionStartTime: null,
        timeLimit: 60,
        timeRemaining: 60
    };
}

async function startAssessmentTest() {
    if (!await ensureAuthenticated()) return;
    
    try {
        showToast('Seviye belirleme sınavı başlatılıyor...', 'info');
        
        const result = await apiCall('/level/test/start', 'POST');
        
        currentLevelTest.testId = result.test_id;
        currentLevelTest.totalQuestions = result.total_questions;
        currentLevelTest.currentQuestion = result.current_question;
        
        // Hide instructions, show test
        document.getElementById('assessment-instructions').style.display = 'none';
        document.getElementById('assessment-test').style.display = 'block';
        
        // Display first question
        displayTestQuestion(result.question);
        updateTestProgress();
        
    } catch (error) {
        console.error('Level test start error:', error);
        showToast(error.message, 'error');
    }
}

function displayTestQuestion(question) {
    // Store question start time
    currentLevelTest.questionStartTime = Date.now();
    
    // Set time limit based on question type and level
    const timeLimit = question.time_limit || 60; // Default 60 seconds
    currentLevelTest.timeLimit = timeLimit;
    currentLevelTest.timeRemaining = timeLimit;
    
    // Update question display
    document.getElementById('test-question-text').textContent = question.question;
    
    // Show question type and difficulty indicator
    const questionHeader = document.querySelector('.question-header');
    const difficultyBadge = `<span class="difficulty-badge difficulty-${question.level?.toLowerCase() || 'a1'}">${question.level || 'A1'}</span>`;
    const typeBadge = question.type ? `<span class="type-badge">${getQuestionTypeLabel(question.type)}</span>` : '';
    questionHeader.innerHTML = `
        <span class="question-label">Soru:</span>
        ${difficultyBadge}
        ${typeBadge}
        <span class="timer-display" id="question-timer">⏱️ ${timeLimit}s</span>
    `;
    
    // Update options
    const optionButtons = document.querySelectorAll('.test-option-btn');
    optionButtons.forEach((btn, index) => {
        if (index < question.options.length) {
            btn.style.display = 'flex';
            btn.querySelector('.test-option-text').textContent = question.options[index];
            btn.classList.remove('selected', 'correct', 'incorrect', 'timeout');
            btn.disabled = false;
        } else {
            btn.style.display = 'none';
        }
    });
    
    // Hide next button and feedback
    document.getElementById('test-next-btn').style.display = 'none';
    document.getElementById('test-feedback').textContent = '';
    
    // Start countdown timer
    startQuestionTimer();
}

function getQuestionTypeLabel(type) {
    const labels = {
        'translation': '🔤 Çeviri',
        'grammar': '📝 Gramer',
        'phrasal_verb': '🔗 Phrasal Verb',
        'vocabulary': '📚 Kelime',
        'context': '🎯 Bağlam',
        'reading_comprehension': '📖 Okuduğunu Anlama',
        'advanced_grammar': '📝 İleri Gramer',
        'idioms': '💬 Deyimler',
        'contextual_vocabulary': '🎯 Bağlamsal Kelime',
        'register': '🎩 Üslup'
    };
    return labels[type] || '📝 Soru';
}

function startQuestionTimer() {
    // Clear existing timer
    if (currentLevelTest.questionTimer) {
        clearInterval(currentLevelTest.questionTimer);
    }
    
    // Start new timer
    currentLevelTest.questionTimer = setInterval(() => {
        currentLevelTest.timeRemaining--;
        
        const timerDisplay = document.getElementById('question-timer');
        if (timerDisplay) {
            timerDisplay.textContent = `⏱️ ${currentLevelTest.timeRemaining}s`;
            
            // Add warning colors
            if (currentLevelTest.timeRemaining <= 10) {
                timerDisplay.style.color = 'var(--error-color)';
                timerDisplay.style.fontWeight = 'bold';
            } else if (currentLevelTest.timeRemaining <= 20) {
                timerDisplay.style.color = 'var(--warning-color)';
            }
        }
        
        // Time's up!
        if (currentLevelTest.timeRemaining <= 0) {
            handleQuestionTimeout();
        }
    }, 1000);
}

function handleQuestionTimeout() {
    // Clear timer
    if (currentLevelTest.questionTimer) {
        clearInterval(currentLevelTest.questionTimer);
        currentLevelTest.questionTimer = null;
    }
    
    // Disable all buttons and mark as timeout
    const optionButtons = document.querySelectorAll('.test-option-btn');
    optionButtons.forEach(btn => {
        btn.disabled = true;
        btn.classList.add('timeout');
    });
    
    // Show timeout feedback
    const feedback = document.getElementById('test-feedback');
    feedback.innerHTML = '⏰ <strong>Süre doldu!</strong> Bu soru yanlış sayılacak.';
    feedback.style.color = 'var(--error-color)';
    
    // Auto-submit timeout answer (wrong answer)
    setTimeout(() => {
        submitTimeoutAnswer();
    }, 2000);
}

async function submitTimeoutAnswer() {
    if (!currentLevelTest.testId) return;
    
    try {
        const timeTaken = Math.round((Date.now() - currentLevelTest.questionStartTime) / 1000);
        
        const result = await apiCall('/level/test/answer', 'POST', {
            test_id: currentLevelTest.testId,
            selected_index: -1, // Special value for timeout
            time_taken: timeTaken
        });
        
        // Handle timeout response
        currentLevelTest.answers.push({
            selected: -1,
            correct: false,
            timeout: true
        });
        
        if (result.test_completed) {
            setTimeout(() => {
                showAssessmentResults(result);
            }, 1000);
        } else {
            currentLevelTest.currentQuestion = result.current_question;
            currentLevelTest.nextQuestion = result.question;
            document.getElementById('test-next-btn').style.display = 'block';
        }
        
    } catch (error) {
        console.error('Timeout answer error:', error);
        showToast('Süre doldu, sonraki soruya geçiliyor...', 'warning');
    }
}

function updateTestProgress() {
    const progress = (currentLevelTest.currentQuestion / currentLevelTest.totalQuestions) * 100;
    
    document.getElementById('test-question-counter').textContent = 
        `Soru ${currentLevelTest.currentQuestion} / ${currentLevelTest.totalQuestions}`;
    document.getElementById('test-progress-percent').textContent = `${Math.round(progress)}%`;
    document.getElementById('test-progress-fill').style.width = `${progress}%`;
}

async function selectTestAnswer(selectedIndex) {
    if (!currentLevelTest.testId) return;
    
    // Stop the timer
    if (currentLevelTest.questionTimer) {
        clearInterval(currentLevelTest.questionTimer);
        currentLevelTest.questionTimer = null;
    }
    
    // Calculate time taken
    const timeTaken = Math.round((Date.now() - currentLevelTest.questionStartTime) / 1000);
    
    // Mark selected option
    const optionButtons = document.querySelectorAll('.test-option-btn');
    optionButtons.forEach((btn, index) => {
        btn.classList.remove('selected');
        if (index === selectedIndex) {
            btn.classList.add('selected');
        }
        btn.disabled = true;
    });
    
    try {
        const result = await apiCall('/level/test/answer', 'POST', {
            test_id: currentLevelTest.testId,
            selected_index: selectedIndex,
            time_taken: timeTaken
        });
        
        // Show feedback with time performance
        const isCorrect = result.previous_correct;
        const feedback = document.getElementById('test-feedback');
        
        let timePerformance = '';
        if (timeTaken <= currentLevelTest.timeLimit * 0.25) {
            timePerformance = ' ⚡ Çok hızlı!';
        } else if (timeTaken <= currentLevelTest.timeLimit * 0.5) {
            timePerformance = ' 🏃 Hızlı!';
        } else if (timeTaken >= currentLevelTest.timeLimit * 0.8) {
            timePerformance = ' 🐌 Yavaş';
        }
        
        if (isCorrect) {
            feedback.innerHTML = `✅ <strong>Doğru!</strong>${timePerformance} (${timeTaken}s)`;
            feedback.style.color = 'var(--success-color)';
            optionButtons[selectedIndex].classList.add('correct');
        } else {
            feedback.innerHTML = `❌ <strong>Yanlış</strong>${timePerformance} (${timeTaken}s)`;
            feedback.style.color = 'var(--error-color)';
            optionButtons[selectedIndex].classList.add('incorrect');
            
            // Show correct answer
            if (result.correct_index !== undefined) {
                optionButtons[result.correct_index]?.classList.add('correct');
            }
        }
        
        currentLevelTest.answers.push({
            selected: selectedIndex,
            correct: isCorrect,
            timeTaken: timeTaken
        });
        
        if (result.test_completed) {
            // Show final results
            setTimeout(() => {
                showAssessmentResults(result);
            }, 1500);
        } else {
            // Show next question
            currentLevelTest.currentQuestion = result.current_question;
            document.getElementById('test-next-btn').style.display = 'block';
            
            // Store next question for later display
            currentLevelTest.nextQuestion = result.question;
        }
        
    } catch (error) {
        console.error('Test answer error:', error);
        showToast(error.message, 'error');
        
        // Re-enable buttons on error
        optionButtons.forEach(btn => {
            btn.disabled = false;
        });
        
        // Restart timer on error
        if (currentLevelTest.questionStartTime) {
            const elapsed = Math.round((Date.now() - currentLevelTest.questionStartTime) / 1000);
            currentLevelTest.timeRemaining = Math.max(0, currentLevelTest.timeLimit - elapsed);
            if (currentLevelTest.timeRemaining > 0) {
                startQuestionTimer();
            }
        }
    }
}

function nextTestQuestion() {
    if (currentLevelTest.nextQuestion) {
        displayTestQuestion(currentLevelTest.nextQuestion);
        updateTestProgress();
        currentLevelTest.nextQuestion = null;
    }
}

function showAssessmentResults(results) {
    // Hide test, show results
    document.getElementById('assessment-test').style.display = 'none';
    document.getElementById('assessment-results').style.display = 'block';
    
    // Update final level badge
    const levelBadge = document.getElementById('final-level-badge');
    levelBadge.textContent = results.final_level;
    
    // Update level description
    const levelDescriptions = {
        'A1': {
            title: 'Başlangıç Seviyesi',
            description: 'Temel İngilizce kelime ve ifadeleri anlayabilirsin. Günlük hayatta sık kullanılan basit cümleler kurabilirsin.'
        },
        'A2': {
            title: 'Temel Seviye',
            description: 'Temel konularda basit iletişim kurabilirsin. Kişisel bilgiler ve günlük rutinler hakkında konuşabilirsin.'
        },
        'B1': {
            title: 'Orta Seviye',
            description: 'Tanıdık konularda ana fikirleri anlayabilirsin. Seyahat, hobiler ve deneyimler hakkında konuşabilirsin.'
        },
        'B2': {
            title: 'Orta-Üst Seviye',
            description: 'Karmaşık metinlerin ana fikirlerini anlayabilirsin. Çeşitli konularda detaylı tartışmalar yapabilirsin.'
        },
        'C1': {
            title: 'İleri Seviye',
            description: 'Uzun ve karmaşık metinleri anlayabilirsin. Akıcı ve spontane şekilde kendini ifade edebilirsin.'
        }
    };
    
    const levelInfo = levelDescriptions[results.final_level] || levelDescriptions['A1'];
    document.getElementById('level-title').textContent = levelInfo.title;
    document.getElementById('level-description').textContent = levelInfo.description;
    
    // Update summary stats
    document.getElementById('correct-count').textContent = results.correct_answers;
    document.getElementById('total-questions').textContent = results.total_questions;
    document.getElementById('success-rate').textContent = 
        `${Math.round((results.correct_answers / results.total_questions) * 100)}%`;
    
    // Update level breakdown
    const breakdown = document.getElementById('level-breakdown');
    breakdown.innerHTML = '<h4 style="margin-bottom: 1rem; color: var(--gray-800);">Seviye Bazında Performans</h4>';
    
    if (results.test_summary && results.test_summary.level_breakdown) {
        Object.entries(results.test_summary.level_breakdown).forEach(([level, stats]) => {
            const accuracy = Math.round((stats.correct / stats.total) * 100);
            const item = document.createElement('div');
            item.className = 'breakdown-item';
            item.innerHTML = `
                <span class="breakdown-level">${level} Seviyesi</span>
                <span class="breakdown-stats">${stats.correct}/${stats.total} (%${accuracy})</span>
            `;
            breakdown.appendChild(item);
        });
    }
    
    // Update user level in current user object
    if (currentUser) {
        currentUser.level = results.final_level;
        localStorage.setItem('currentUser', JSON.stringify(currentUser));
        updateUserLevelDisplay();
    }
    
    showToast(`Tebrikler! Seviyeniz belirlendi: ${results.final_level}`, 'success');
}

function updateUserLevelDisplay() {
    const levelBadge = document.getElementById('user-level');
    if (currentUser && currentUser.level && currentUser.level !== 'UNSET') {
        levelBadge.textContent = currentUser.level;
        levelBadge.style.display = 'inline-block';
    } else {
        levelBadge.style.display = 'none';
    }
}