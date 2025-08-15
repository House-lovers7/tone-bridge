// ToneBridge for Outlook - Taskpane JavaScript

// API Configuration
const API_BASE_URL = 'https://api.tonebridge.io/api/v1';
const LOCAL_API_URL = 'http://localhost:8080/api/v1'; // For development

// Global variables
let currentMode = 'compose';
let currentEmailContent = '';
let transformedContent = '';
let authToken = '';

// Initialize Office.js
Office.onReady((info) => {
    if (info.host === Office.HostType.Outlook) {
        document.getElementById('refreshEmailBtn').onclick = loadEmailContent;
        document.getElementById('transformBtn').onclick = performTransformation;
        document.getElementById('analyzeBtn').onclick = analyzeEmail;
        document.getElementById('applyBtn').onclick = applyTransformation;
        document.getElementById('copyBtn').onclick = copyToClipboard;
        document.getElementById('retryBtn').onclick = retryTransformation;
        
        // Mode switching
        setupModeSwitching();
        
        // Advanced options
        setupAdvancedOptions();
        
        // Intensity slider
        setupIntensitySlider();
        
        // Quick actions
        setupQuickActions();
        
        // Load initial email content
        loadEmailContent();
        
        // Initialize auth
        initializeAuth();
    }
});

// Initialize authentication
async function initializeAuth() {
    try {
        // In production, this would get the auth token from Office SSO or your auth service
        // For now, using a placeholder
        authToken = await getAuthToken();
    } catch (error) {
        console.error('Auth initialization failed:', error);
        showError('Authentication failed. Please try again.');
    }
}

// Get auth token (placeholder - implement actual auth)
async function getAuthToken() {
    // In production:
    // return await Office.auth.getAccessToken({ forceConsent: false });
    return 'demo-token';
}

// Setup mode switching
function setupModeSwitching() {
    const modeTabs = document.querySelectorAll('.tab-button');
    modeTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const mode = tab.dataset.mode;
            switchMode(mode);
        });
    });
}

// Switch between compose and analyze modes
function switchMode(mode) {
    currentMode = mode;
    
    // Update tabs
    document.querySelectorAll('.tab-button').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.mode === mode);
    });
    
    // Update panels
    document.querySelectorAll('.mode-panel').forEach(panel => {
        panel.classList.remove('active');
    });
    
    if (mode === 'compose') {
        document.getElementById('composeMode').classList.add('active');
    } else {
        document.getElementById('analyzeMode').classList.add('active');
    }
    
    // Load content if switching to analyze mode
    if (mode === 'analyze') {
        loadEmailForAnalysis();
    }
}

// Setup advanced options
function setupAdvancedOptions() {
    const collapseBtn = document.querySelector('.collapse-button');
    const advancedOptions = document.getElementById('advancedOptions');
    
    collapseBtn.addEventListener('click', () => {
        const isCollapsed = advancedOptions.classList.contains('collapsed');
        advancedOptions.classList.toggle('collapsed');
        collapseBtn.setAttribute('aria-expanded', !isCollapsed);
        
        // Update icon
        const icon = collapseBtn.querySelector('.collapse-icon');
        icon.textContent = isCollapsed ? '▼' : '▶';
    });
}

// Setup intensity slider
function setupIntensitySlider() {
    const slider = document.getElementById('intensitySlider');
    const description = document.getElementById('intensityDescription');
    
    const descriptions = [
        'Minimal changes',
        'Light transformation',
        'Balanced transformation',
        'Maximum transformation'
    ];
    
    slider.addEventListener('input', (e) => {
        const value = parseInt(e.target.value);
        description.textContent = descriptions[value];
    });
}

// Setup quick actions
function setupQuickActions() {
    const actionButtons = document.querySelectorAll('.action-button[data-action]');
    actionButtons.forEach(button => {
        button.addEventListener('click', () => {
            const action = button.dataset.action;
            performQuickAction(action);
        });
    });
}

// Load email content
function loadEmailContent() {
    showLoading('Loading email content...');
    
    Office.context.mailbox.item.body.getAsync(
        Office.CoercionType.Text,
        { asyncContext: 'GetBodyContext' },
        (result) => {
            hideLoading();
            
            if (result.status === Office.AsyncResultStatus.Succeeded) {
                currentEmailContent = result.value;
                displayEmailContent(currentEmailContent);
                updateStatus('Email content loaded');
            } else {
                showError('Failed to load email content');
            }
        }
    );
}

// Display email content
function displayEmailContent(content) {
    const emailContentDiv = document.getElementById('emailContent');
    if (content && content.trim()) {
        emailContentDiv.textContent = content;
    } else {
        emailContentDiv.innerHTML = '<div class="loading-message">No content to display</div>';
    }
}

// Perform transformation
async function performTransformation() {
    if (!currentEmailContent) {
        showError('Please load email content first');
        return;
    }
    
    showLoading('Transforming email...');
    
    const intensity = document.getElementById('intensitySlider').value;
    const preserveFormatting = document.getElementById('preserveFormatting').checked;
    const includeSignature = document.getElementById('includeSignature').checked;
    const targetAudience = document.getElementById('targetAudience').value;
    
    try {
        const response = await callTransformAPI({
            text: currentEmailContent,
            transformation_type: 'soften',
            intensity: parseInt(intensity),
            options: {
                preserve_formatting: preserveFormatting,
                include_signature: includeSignature,
                target_audience: targetAudience
            }
        });
        
        hideLoading();
        
        if (response.success) {
            transformedContent = response.data.transformed_text;
            displayResults(response.data);
            updateStatus('Transformation complete');
        } else {
            showError('Transformation failed');
        }
    } catch (error) {
        hideLoading();
        showError('An error occurred during transformation');
        console.error('Transformation error:', error);
    }
}

// Perform quick action
async function performQuickAction(action) {
    if (!currentEmailContent) {
        showError('Please load email content first');
        return;
    }
    
    showLoading(`Applying ${action}...`);
    
    try {
        const response = await callTransformAPI({
            text: currentEmailContent,
            transformation_type: action,
            intensity: 2 // Default balanced intensity
        });
        
        hideLoading();
        
        if (response.success) {
            transformedContent = response.data.transformed_text;
            displayResults(response.data);
            updateStatus(`${action} transformation complete`);
        } else {
            showError(`${action} transformation failed`);
        }
    } catch (error) {
        hideLoading();
        showError(`An error occurred during ${action}`);
        console.error(`${action} error:`, error);
    }
}

// Call transformation API
async function callTransformAPI(data) {
    const apiUrl = window.location.hostname === 'localhost' ? LOCAL_API_URL : API_BASE_URL;
    
    const response = await fetch(`${apiUrl}/transform`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify(data)
    });
    
    return await response.json();
}

// Display transformation results
function displayResults(data) {
    const resultsSection = document.getElementById('resultsSection');
    const transformedContentDiv = document.getElementById('transformedContent');
    const suggestionsList = document.getElementById('suggestionsList');
    
    // Show results section
    resultsSection.classList.remove('hidden');
    
    // Display transformed content
    transformedContentDiv.textContent = data.transformed_text;
    
    // Display suggestions
    suggestionsList.innerHTML = '';
    if (data.suggestions && data.suggestions.length > 0) {
        data.suggestions.forEach(suggestion => {
            const li = document.createElement('li');
            li.textContent = suggestion;
            suggestionsList.appendChild(li);
        });
    } else {
        const li = document.createElement('li');
        li.textContent = 'No additional suggestions';
        suggestionsList.appendChild(li);
    }
}

// Apply transformation to email
function applyTransformation() {
    if (!transformedContent) {
        showError('No transformed content to apply');
        return;
    }
    
    showLoading('Applying changes...');
    
    Office.context.mailbox.item.body.setAsync(
        transformedContent,
        { coercionType: Office.CoercionType.Text },
        (result) => {
            hideLoading();
            
            if (result.status === Office.AsyncResultStatus.Succeeded) {
                showSuccess('Email content updated successfully');
                updateStatus('Changes applied');
                
                // Hide results section after applying
                setTimeout(() => {
                    document.getElementById('resultsSection').classList.add('hidden');
                }, 2000);
            } else {
                showError('Failed to apply changes');
            }
        }
    );
}

// Copy to clipboard
function copyToClipboard() {
    if (!transformedContent) {
        showError('No content to copy');
        return;
    }
    
    navigator.clipboard.writeText(transformedContent).then(() => {
        showSuccess('Content copied to clipboard');
        updateStatus('Copied to clipboard');
    }).catch(err => {
        showError('Failed to copy to clipboard');
        console.error('Copy error:', err);
    });
}

// Retry transformation
function retryTransformation() {
    // Reset and retry
    document.getElementById('resultsSection').classList.add('hidden');
    performTransformation();
}

// Load email for analysis
function loadEmailForAnalysis() {
    Office.context.mailbox.item.body.getAsync(
        Office.CoercionType.Text,
        { asyncContext: 'GetBodyContext' },
        (result) => {
            if (result.status === Office.AsyncResultStatus.Succeeded) {
                currentEmailContent = result.value;
                updateStatus('Ready to analyze');
            }
        }
    );
}

// Analyze email
async function analyzeEmail() {
    if (!currentEmailContent) {
        showError('Please load email content first');
        return;
    }
    
    showLoading('Analyzing email...');
    
    try {
        const response = await callAnalyzeAPI({
            text: currentEmailContent
        });
        
        hideLoading();
        
        if (response.success) {
            displayAnalysisResults(response.data);
            updateStatus('Analysis complete');
        } else {
            showError('Analysis failed');
        }
    } catch (error) {
        hideLoading();
        showError('An error occurred during analysis');
        console.error('Analysis error:', error);
    }
}

// Call analyze API
async function callAnalyzeAPI(data) {
    const apiUrl = window.location.hostname === 'localhost' ? LOCAL_API_URL : API_BASE_URL;
    
    const response = await fetch(`${apiUrl}/analyze`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify(data)
    });
    
    return await response.json();
}

// Display analysis results
function displayAnalysisResults(data) {
    // Update metrics
    document.getElementById('toneValue').textContent = data.tone || 'Neutral';
    document.getElementById('clarityValue').textContent = `${data.clarity_score || 0}%`;
    document.getElementById('priorityValue').textContent = data.priority || 'Medium';
    document.getElementById('responseTimeValue').textContent = data.suggested_response_time || '24h';
    
    // Update priority matrix
    updatePriorityMatrix(data.priority_quadrant);
    
    // Display improvements
    if (data.improvements && data.improvements.length > 0) {
        displayImprovements(data.improvements);
    }
}

// Update priority matrix
function updatePriorityMatrix(quadrant) {
    // Remove active class from all cells
    document.querySelectorAll('.matrix-cell').forEach(cell => {
        cell.classList.remove('active');
    });
    
    // Add active class to the appropriate quadrant
    if (quadrant) {
        const cell = document.querySelector(`.matrix-cell[data-quadrant="${quadrant}"]`);
        if (cell) {
            cell.classList.add('active');
        }
    }
}

// Display improvements
function displayImprovements(improvements) {
    const improvementSection = document.getElementById('improvementSection');
    const improvementList = document.getElementById('improvementList');
    
    improvementSection.classList.remove('hidden');
    improvementList.innerHTML = '';
    
    improvements.forEach(improvement => {
        const li = document.createElement('li');
        li.textContent = improvement;
        improvementList.appendChild(li);
    });
}

// UI Helper Functions

// Show loading overlay
function showLoading(message = 'Processing...') {
    const overlay = document.getElementById('loadingOverlay');
    const loadingText = overlay.querySelector('.loading-text');
    loadingText.textContent = message;
    overlay.classList.remove('hidden');
}

// Hide loading overlay
function hideLoading() {
    document.getElementById('loadingOverlay').classList.add('hidden');
}

// Show error modal
function showError(message) {
    const modal = document.getElementById('errorModal');
    const messageElement = document.getElementById('errorMessage');
    messageElement.textContent = message;
    modal.classList.remove('hidden');
    
    // Setup close handlers
    document.getElementById('closeErrorBtn').onclick = () => {
        modal.classList.add('hidden');
    };
    document.getElementById('errorOkBtn').onclick = () => {
        modal.classList.add('hidden');
    };
}

// Show success modal
function showSuccess(message) {
    const modal = document.getElementById('successModal');
    const messageElement = document.getElementById('successMessage');
    messageElement.textContent = message;
    modal.classList.remove('hidden');
    
    // Setup close handlers
    document.getElementById('closeSuccessBtn').onclick = () => {
        modal.classList.add('hidden');
    };
    document.getElementById('successOkBtn').onclick = () => {
        modal.classList.add('hidden');
    };
    
    // Auto-hide after 3 seconds
    setTimeout(() => {
        modal.classList.add('hidden');
    }, 3000);
}

// Update status message
function updateStatus(message) {
    document.getElementById('statusMessage').textContent = message;
}

// Help link handler
document.getElementById('helpLink').addEventListener('click', (e) => {
    e.preventDefault();
    window.open('https://tonebridge.io/help/outlook', '_blank');
});