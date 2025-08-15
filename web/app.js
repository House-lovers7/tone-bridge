// ToneBridge Web UI JavaScript

const API_BASE_URL = 'http://localhost:8082/api/v1';
let authToken = null;
let userEmail = null;
let isPreviewMode = false;

// DOM Elements
const loginSection = document.getElementById('loginSection');
const appSection = document.getElementById('appSection');
const loginForm = document.getElementById('loginForm');
const registerBtn = document.getElementById('registerBtn');
const logoutBtn = document.getElementById('logoutBtn');
const transformBtn = document.getElementById('transformBtn');
const analyzeBtn = document.getElementById('analyzeBtn');
const loadHistoryBtn = document.getElementById('loadHistoryBtn');
const copyBtn = document.getElementById('copyBtn');
const transformationType = document.getElementById('transformationType');
const toneOptions = document.getElementById('toneOptions');
const loadingIndicator = document.getElementById('loadingIndicator');
const errorMessage = document.getElementById('errorMessage');
const errorText = document.getElementById('errorText');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
    setupEventListeners();
});

// Setup Event Listeners
function setupEventListeners() {
    loginForm.addEventListener('submit', handleLogin);
    registerBtn.addEventListener('click', handleRegister);
    logoutBtn.addEventListener('click', handleLogout);
    transformBtn.addEventListener('click', handleTransform);
    analyzeBtn.addEventListener('click', handleAnalyze);
    loadHistoryBtn.addEventListener('click', loadHistory);
    copyBtn.addEventListener('click', copyTransformedText);
    
    transformationType.addEventListener('change', (e) => {
        toneOptions.style.display = e.target.value === 'tone' ? 'block' : 'none';
    });

    // Preview mode event listeners
    const previewBtn = document.getElementById('previewBtn');
    const exitPreviewBtn = document.getElementById('exitPreviewBtn');
    const previewTransformBtn = document.getElementById('previewTransformBtn');
    const previewInputText = document.getElementById('previewInputText');
    const previewCopyBtn = document.getElementById('previewCopyBtn');
    const upgradeBtn = document.getElementById('upgradeBtn');
    
    if (previewBtn) {
        previewBtn.addEventListener('click', enterPreviewMode);
    }
    if (exitPreviewBtn) {
        exitPreviewBtn.addEventListener('click', exitPreviewMode);
    }
    if (previewTransformBtn) {
        previewTransformBtn.addEventListener('click', handlePreviewTransform);
    }
    if (previewInputText) {
        previewInputText.addEventListener('input', updateCharCount);
    }
    if (previewCopyBtn) {
        previewCopyBtn.addEventListener('click', copyPreviewText);
    }
    if (upgradeBtn) {
        upgradeBtn.addEventListener('click', () => {
            exitPreviewMode();
            document.getElementById('registerBtn').click();
        });
    }
}

// Authentication Functions
function checkAuth() {
    const token = localStorage.getItem('authToken');
    const email = localStorage.getItem('userEmail');
    
    if (token && email) {
        authToken = token;
        userEmail = email;
        showApp();
    } else {
        showLogin();
    }
}

async function handleLogin(e) {
    e.preventDefault();
    
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    
    showLoading();
    
    try {
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        });
        
        if (response.ok) {
            const data = await response.json();
            authToken = data.access_token;
            userEmail = email;
            
            localStorage.setItem('authToken', authToken);
            localStorage.setItem('userEmail', userEmail);
            
            showApp();
            showSuccess('ログインに成功しました');
        } else {
            const error = await response.json();
            showError(error.message || 'ログインに失敗しました');
        }
    } catch (error) {
        showError('ネットワークエラーが発生しました');
    } finally {
        hideLoading();
    }
}

async function handleRegister() {
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    
    if (!email || !password) {
        showError('メールアドレスとパスワードを入力してください');
        return;
    }
    
    const name = prompt('お名前を入力してください:');
    if (!name) return;
    
    const organization = prompt('組織名を入力してください（任意）:');
    
    showLoading();
    
    try {
        const response = await fetch(`${API_BASE_URL}/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password, name, organization })
        });
        
        if (response.ok) {
            const data = await response.json();
            authToken = data.access_token;
            userEmail = email;
            
            localStorage.setItem('authToken', authToken);
            localStorage.setItem('userEmail', userEmail);
            
            showApp();
            showSuccess('登録に成功しました');
        } else {
            const error = await response.json();
            showError(error.message || '登録に失敗しました');
        }
    } catch (error) {
        showError('ネットワークエラーが発生しました');
    } finally {
        hideLoading();
    }
}

function handleLogout() {
    localStorage.removeItem('authToken');
    localStorage.removeItem('userEmail');
    authToken = null;
    userEmail = null;
    showLogin();
}

// Transform Functions
async function handleTransform() {
    const inputText = document.getElementById('inputText').value;
    const transformType = document.getElementById('transformationType').value;
    const targetTone = document.getElementById('targetTone').value;
    const intensityLevel = parseInt(document.getElementById('intensity').value);
    
    if (!inputText) {
        showError('変換するテキストを入力してください');
        return;
    }
    
    showLoading();
    
    try {
        const payload = {
            text: inputText,
            transformation_type: transformType,
            intensity_level: intensityLevel
        };
        
        if (transformType === 'tone') {
            payload.target_tone = targetTone;
        }
        
        const response = await fetch(`${API_BASE_URL}/transform`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(payload)
        });
        
        if (response.ok) {
            const result = await response.json();
            displayTransformResult(inputText, result.data);
        } else if (response.status === 401) {
            handleLogout();
            showError('セッションが期限切れです。再度ログインしてください');
        } else {
            const error = await response.json();
            showError(error.message || '変換に失敗しました');
        }
    } catch (error) {
        showError('ネットワークエラーが発生しました');
    } finally {
        hideLoading();
    }
}

async function handleAnalyze() {
    const inputText = document.getElementById('inputText').value;
    
    if (!inputText) {
        showError('分析するテキストを入力してください');
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch(`${API_BASE_URL}/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ text: inputText })
        });
        
        if (response.ok) {
            const result = await response.json();
            displayAnalysisResult(result.data);
        } else if (response.status === 401) {
            handleLogout();
            showError('セッションが期限切れです。再度ログインしてください');
        } else {
            const error = await response.json();
            showError(error.message || '分析に失敗しました');
        }
    } catch (error) {
        showError('ネットワークエラーが発生しました');
    } finally {
        hideLoading();
    }
}

// Display Functions
function displayTransformResult(original, data) {
    const resultsSection = document.getElementById('resultsSection');
    const originalText = document.getElementById('originalText');
    const transformedText = document.getElementById('transformedText');
    const suggestions = document.getElementById('suggestions');
    
    originalText.textContent = original;
    transformedText.textContent = data.transformed_text;
    
    if (data.suggestions && data.suggestions.length > 0) {
        suggestions.innerHTML = `
            <h4>💡 提案</h4>
            <ul>
                ${data.suggestions.map(s => `<li>${s}</li>`).join('')}
            </ul>
        `;
        suggestions.style.display = 'block';
    } else {
        suggestions.style.display = 'none';
    }
    
    resultsSection.style.display = 'block';
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

function displayAnalysisResult(data) {
    const analysisSection = document.getElementById('analysisSection');
    const toneResult = document.getElementById('toneResult');
    const clarityResult = document.getElementById('clarityResult');
    const priorityResult = document.getElementById('priorityResult');
    const analysisSuggestions = document.getElementById('analysisSuggestions');
    
    // Display metrics
    toneResult.textContent = translateTone(data.tone);
    clarityResult.textContent = `${(data.clarity * 100).toFixed(0)}%`;
    
    // Display priority with color
    const priorityClass = `priority-${data.priority}`;
    priorityResult.textContent = translatePriority(data.priority);
    priorityResult.className = `metric-value ${priorityClass}`;
    
    // Display suggestions
    if (data.suggestions && data.suggestions.length > 0) {
        analysisSuggestions.innerHTML = `
            <h4>📝 改善提案</h4>
            <ul>
                ${data.suggestions.map(s => `<li>${s}</li>`).join('')}
            </ul>
        `;
        analysisSuggestions.style.display = 'block';
    } else {
        analysisSuggestions.style.display = 'none';
    }
    
    analysisSection.style.display = 'block';
    
    // Scroll to results
    analysisSection.scrollIntoView({ behavior: 'smooth' });
}

async function loadHistory() {
    showLoading();
    
    try {
        const response = await fetch(`${API_BASE_URL}/history?limit=10`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            const result = await response.json();
            displayHistory(result.data);
        } else if (response.status === 401) {
            handleLogout();
            showError('セッションが期限切れです。再度ログインしてください');
        } else {
            showError('履歴の読み込みに失敗しました');
        }
    } catch (error) {
        showError('ネットワークエラーが発生しました');
    } finally {
        hideLoading();
    }
}

function displayHistory(history) {
    const historyList = document.getElementById('historyList');
    
    if (!history || history.length === 0) {
        historyList.innerHTML = '<p>履歴がありません</p>';
        return;
    }
    
    historyList.innerHTML = history.map(item => `
        <div class="history-item" onclick="loadHistoryItem('${item.id}')">
            <div class="history-item-date">${formatDate(item.created_at)}</div>
            <div class="history-item-text">${item.original_text}</div>
        </div>
    `).join('');
}

function copyTransformedText() {
    const transformedText = document.getElementById('transformedText').textContent;
    
    navigator.clipboard.writeText(transformedText).then(() => {
        showSuccess('クリップボードにコピーしました');
    }).catch(() => {
        showError('コピーに失敗しました');
    });
}

// UI Helper Functions
function showApp() {
    loginSection.style.display = 'none';
    appSection.style.display = 'block';
    document.getElementById('userEmail').textContent = userEmail;
}

function showLogin() {
    loginSection.style.display = 'block';
    appSection.style.display = 'none';
}

function showLoading() {
    loadingIndicator.style.display = 'block';
}

function hideLoading() {
    loadingIndicator.style.display = 'none';
}

function showError(message) {
    errorText.textContent = message;
    errorMessage.style.display = 'flex';
    setTimeout(() => {
        errorMessage.style.display = 'none';
    }, 5000);
}

function showSuccess(message) {
    // Create success message element
    const successMessage = document.createElement('div');
    successMessage.className = 'error-message';
    successMessage.style.background = '#5CB85C';
    successMessage.innerHTML = `
        <span>${message}</span>
        <button onclick="this.parentElement.remove()">×</button>
    `;
    document.body.appendChild(successMessage);
    
    setTimeout(() => {
        successMessage.remove();
    }, 3000);
}

function closeError() {
    errorMessage.style.display = 'none';
}

// Utility Functions
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('ja-JP', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function translateTone(tone) {
    const toneMap = {
        'technical': '技術的',
        'casual': 'カジュアル',
        'formal': 'フォーマル',
        'aggressive': '攻撃的',
        'passive': '受動的',
        'neutral': 'ニュートラル',
        'warm': '温かみのある'
    };
    return toneMap[tone] || tone;
}

function translatePriority(priority) {
    const priorityMap = {
        'critical': '緊急',
        'high': '高',
        'medium': '中',
        'low': '低'
    };
    return priorityMap[priority] || priority;
}

// Preview Mode Functions
function enterPreviewMode() {
    isPreviewMode = true;
    const loginSection = document.getElementById('loginSection');
    const previewSection = document.getElementById('previewSection');
    
    loginSection.style.display = 'none';
    previewSection.style.display = 'block';
    
    // Load preview info
    loadPreviewInfo();
}

function exitPreviewMode() {
    isPreviewMode = false;
    const loginSection = document.getElementById('loginSection');
    const previewSection = document.getElementById('previewSection');
    
    loginSection.style.display = 'block';
    previewSection.style.display = 'none';
}

async function loadPreviewInfo() {
    try {
        const response = await fetch(`${API_BASE_URL}/preview/info`);
        if (response.ok) {
            const data = await response.json();
            console.log('Preview info loaded:', data);
        }
    } catch (error) {
        console.error('Failed to load preview info:', error);
    }
}

async function handlePreviewTransform() {
    const inputText = document.getElementById('previewInputText').value;
    const targetTone = document.getElementById('previewTargetTone').value;
    const intensityLevel = parseInt(document.getElementById('previewIntensity').value);
    
    if (!inputText) {
        showError('変換するテキストを入力してください');
        return;
    }
    
    if (inputText.length > 500) {
        showError('テキストは500文字以内で入力してください');
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch(`${API_BASE_URL}/preview/transform`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: inputText,
                target_tone: targetTone,
                intensity_level: intensityLevel
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            displayPreviewResult(inputText, result.data);
            
            // Update usage display if available
            if (response.headers.get('X-RateLimit-Remaining-Daily')) {
                const remaining = response.headers.get('X-RateLimit-Remaining-Daily');
                const usageElement = document.getElementById('previewUsage');
                if (usageElement) {
                    usageElement.textContent = `本日残り: ${remaining}回`;
                }
            }
            
            showSuccess('変換が完了しました（プレビュー版）');
        } else if (response.status === 429) {
            showError(result.message || 'レート制限に達しました。しばらくお待ちください。');
        } else {
            showError(result.message || '変換に失敗しました');
        }
    } catch (error) {
        showError('ネットワークエラーが発生しました');
    } finally {
        hideLoading();
    }
}

function displayPreviewResult(original, data) {
    const previewResults = document.getElementById('previewResults');
    const previewOriginal = document.getElementById('previewOriginal');
    const previewTransformed = document.getElementById('previewTransformed');
    
    previewOriginal.textContent = original;
    previewTransformed.textContent = data.transformed_text;
    
    previewResults.style.display = 'block';
    previewResults.scrollIntoView({ behavior: 'smooth' });
}

function copyPreviewText() {
    const transformedText = document.getElementById('previewTransformed').textContent;
    
    navigator.clipboard.writeText(transformedText).then(() => {
        showSuccess('クリップボードにコピーしました');
    }).catch(() => {
        showError('コピーに失敗しました');
    });
}

function updateCharCount() {
    const inputText = document.getElementById('previewInputText').value;
    const charCount = document.getElementById('charCount');
    
    if (charCount) {
        charCount.textContent = inputText.length;
        
        // Change color if approaching limit
        if (inputText.length > 450) {
            charCount.style.color = '#ff6b6b';
        } else if (inputText.length > 400) {
            charCount.style.color = '#ffa94d';
        } else {
            charCount.style.color = '#51cf66';
        }
    }
}

window.closeError = closeError;