// Auto-Transform Settings JavaScript

const API_BASE_URL = 'http://localhost:8080/api/v1';
const AUTO_TRANSFORM_URL = 'http://localhost:8002';

// State management
let currentConfig = null;
let currentRules = [];
let templates = [];
let editingRuleId = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
    loadConfig();
    loadRules();
    loadTemplates();
    setupEventListeners();
});

// Check authentication
function checkAuth() {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = 'login.html';
        return;
    }
}

// Setup event listeners
function setupEventListeners() {
    // Master toggle
    document.getElementById('masterToggle').addEventListener('click', toggleAutoTransform);
    
    // Save settings button
    document.getElementById('saveSettingsBtn').addEventListener('click', saveSettings);
    
    // Add rule button
    document.getElementById('addRuleBtn').addEventListener('click', () => openRuleModal());
    
    // Modal controls
    document.getElementById('modalClose').addEventListener('click', closeRuleModal);
    document.getElementById('cancelBtn').addEventListener('click', closeRuleModal);
    document.getElementById('ruleForm').addEventListener('submit', saveRule);
    
    // Trigger type change
    document.getElementById('triggerType').addEventListener('change', updateTriggerInput);
    
    // Logout
    document.getElementById('logoutBtn').addEventListener('click', logout);
}

// Load configuration
async function loadConfig() {
    try {
        const tenantId = localStorage.getItem('tenantId') || 'default';
        const response = await fetch(`${AUTO_TRANSFORM_URL}/config/${tenantId}`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
        
        if (response.ok) {
            currentConfig = await response.json();
            displayConfig();
        }
    } catch (error) {
        console.error('Failed to load config:', error);
        showNotification('Failed to load configuration', 'error');
    }
}

// Display configuration
function displayConfig() {
    if (!currentConfig) return;
    
    // Master toggle
    const toggle = document.getElementById('masterToggle');
    if (currentConfig.enabled) {
        toggle.classList.add('active');
    } else {
        toggle.classList.remove('active');
    }
    
    // Global settings
    document.getElementById('defaultType').value = currentConfig.default_transformation_type || 'soften';
    document.getElementById('defaultIntensity').value = currentConfig.default_intensity || 2;
    document.getElementById('minLength').value = currentConfig.min_message_length || 50;
    document.getElementById('processingDelay').value = currentConfig.max_processing_delay_ms || 500;
    
    // Behavior settings
    document.getElementById('requireConfirmation').checked = currentConfig.require_confirmation !== false;
    document.getElementById('showPreview').checked = currentConfig.show_preview !== false;
    document.getElementById('preserveOriginal').checked = currentConfig.preserve_original !== false;
}

// Toggle auto-transform
function toggleAutoTransform() {
    const toggle = document.getElementById('masterToggle');
    toggle.classList.toggle('active');
}

// Save settings
async function saveSettings() {
    try {
        const tenantId = localStorage.getItem('tenantId') || 'default';
        const config = {
            tenant_id: tenantId,
            enabled: document.getElementById('masterToggle').classList.contains('active'),
            default_transformation_type: document.getElementById('defaultType').value,
            default_intensity: parseInt(document.getElementById('defaultIntensity').value),
            min_message_length: parseInt(document.getElementById('minLength').value),
            max_processing_delay_ms: parseInt(document.getElementById('processingDelay').value),
            require_confirmation: document.getElementById('requireConfirmation').checked,
            show_preview: document.getElementById('showPreview').checked,
            preserve_original: document.getElementById('preserveOriginal').checked
        };
        
        const response = await fetch(`${AUTO_TRANSFORM_URL}/config/${tenantId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify(config)
        });
        
        if (response.ok) {
            showNotification('Settings saved successfully', 'success');
            currentConfig = config;
        } else {
            throw new Error('Failed to save settings');
        }
    } catch (error) {
        console.error('Failed to save settings:', error);
        showNotification('Failed to save settings', 'error');
    }
}

// Load rules
async function loadRules() {
    try {
        const tenantId = localStorage.getItem('tenantId') || 'default';
        const response = await fetch(`${AUTO_TRANSFORM_URL}/rules/${tenantId}`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
        
        if (response.ok) {
            currentRules = await response.json();
            displayRules();
        }
    } catch (error) {
        console.error('Failed to load rules:', error);
    }
}

// Display rules
function displayRules() {
    const rulesList = document.getElementById('rulesList');
    
    if (currentRules.length === 0) {
        rulesList.innerHTML = `
            <div style="text-align: center; padding: 40px; color: #718096;">
                <p>No rules configured yet</p>
                <p style="font-size: 14px; margin-top: 10px;">Add rules to automatically transform messages based on triggers</p>
            </div>
        `;
        return;
    }
    
    rulesList.innerHTML = currentRules.map(rule => `
        <div class="rule-card" data-rule-id="${rule.id}">
            <div class="rule-info">
                <div class="rule-name">${rule.rule_name}</div>
                <div class="rule-description">${rule.description || 'No description'}</div>
                <div class="rule-tags">
                    <span class="rule-tag trigger">${rule.trigger_type}</span>
                    <span class="rule-tag transform">${rule.transformation_type}</span>
                    ${rule.platforms && rule.platforms.length > 0 ? 
                        rule.platforms.map(p => `<span class="rule-tag platform">${p}</span>`).join('') : 
                        '<span class="rule-tag platform">all platforms</span>'}
                </div>
            </div>
            <div class="rule-actions">
                <div class="rule-toggle ${rule.enabled ? 'active' : ''}" 
                     onclick="toggleRule('${rule.id}')">
                    <div class="rule-toggle-slider"></div>
                </div>
                <button class="rule-edit-btn" onclick="editRule('${rule.id}')">
                    ✏️
                </button>
                <button class="rule-delete-btn" onclick="deleteRule('${rule.id}')">
                    🗑️
                </button>
            </div>
        </div>
    `).join('');
}

// Toggle rule
async function toggleRule(ruleId) {
    const rule = currentRules.find(r => r.id === ruleId);
    if (!rule) return;
    
    rule.enabled = !rule.enabled;
    
    // Update UI immediately
    const toggle = document.querySelector(`[data-rule-id="${ruleId}"] .rule-toggle`);
    if (rule.enabled) {
        toggle.classList.add('active');
    } else {
        toggle.classList.remove('active');
    }
    
    // TODO: Send update to server
}

// Edit rule
function editRule(ruleId) {
    const rule = currentRules.find(r => r.id === ruleId);
    if (!rule) return;
    
    editingRuleId = ruleId;
    
    // Populate form
    document.getElementById('ruleName').value = rule.rule_name;
    document.getElementById('ruleDescription').value = rule.description || '';
    document.getElementById('triggerType').value = rule.trigger_type;
    document.getElementById('transformationType').value = rule.transformation_type;
    document.getElementById('transformIntensity').value = rule.transformation_intensity || 2;
    document.getElementById('platforms').value = (rule.platforms || []).join(', ');
    document.getElementById('priority').value = rule.priority || 0;
    
    // Set trigger value based on type
    updateTriggerInput();
    const triggerInput = document.getElementById('triggerValue');
    if (rule.trigger_value) {
        if (rule.trigger_type === 'keyword') {
            triggerInput.value = (rule.trigger_value.keywords || []).join(', ');
        } else if (rule.trigger_type === 'sentiment') {
            triggerInput.value = rule.trigger_value.threshold || '0';
        } else if (rule.trigger_type === 'time') {
            triggerInput.value = `${rule.trigger_value.after || '09:00'} - ${rule.trigger_value.before || '17:00'}`;
        } else {
            triggerInput.value = JSON.stringify(rule.trigger_value);
        }
    }
    
    openRuleModal();
}

// Delete rule
async function deleteRule(ruleId) {
    if (!confirm('Are you sure you want to delete this rule?')) return;
    
    try {
        // Remove from UI
        currentRules = currentRules.filter(r => r.id !== ruleId);
        displayRules();
        
        showNotification('Rule deleted successfully', 'success');
        
        // TODO: Send delete request to server
    } catch (error) {
        console.error('Failed to delete rule:', error);
        showNotification('Failed to delete rule', 'error');
        loadRules(); // Reload to restore state
    }
}

// Open rule modal
function openRuleModal() {
    document.getElementById('ruleModal').classList.add('active');
}

// Close rule modal
function closeRuleModal() {
    document.getElementById('ruleModal').classList.remove('active');
    document.getElementById('ruleForm').reset();
    editingRuleId = null;
}

// Update trigger input based on type
function updateTriggerInput() {
    const triggerType = document.getElementById('triggerType').value;
    const triggerGroup = document.getElementById('triggerValueGroup');
    const triggerInput = document.getElementById('triggerValue');
    
    switch (triggerType) {
        case 'keyword':
            triggerGroup.querySelector('.form-label').textContent = 'Keywords';
            triggerInput.placeholder = 'Enter keywords separated by commas';
            triggerInput.type = 'text';
            break;
        case 'sentiment':
            triggerGroup.querySelector('.form-label').textContent = 'Sentiment Threshold';
            triggerInput.placeholder = 'Enter threshold (-1 to 1)';
            triggerInput.type = 'number';
            triggerInput.min = '-1';
            triggerInput.max = '1';
            triggerInput.step = '0.1';
            break;
        case 'recipient':
            triggerGroup.querySelector('.form-label').textContent = 'Recipient Roles/IDs';
            triggerInput.placeholder = 'e.g., executive, manager, user@example.com';
            triggerInput.type = 'text';
            break;
        case 'channel':
            triggerGroup.querySelector('.form-label').textContent = 'Channel Type/IDs';
            triggerInput.placeholder = 'e.g., support, general, #channel-name';
            triggerInput.type = 'text';
            break;
        case 'time':
            triggerGroup.querySelector('.form-label').textContent = 'Time Window';
            triggerInput.placeholder = 'e.g., 09:00 - 17:00';
            triggerInput.type = 'text';
            break;
        case 'pattern':
            triggerGroup.querySelector('.form-label').textContent = 'Regex Patterns';
            triggerInput.placeholder = 'Enter regex patterns separated by commas';
            triggerInput.type = 'text';
            break;
    }
}

// Save rule
async function saveRule(e) {
    e.preventDefault();
    
    try {
        const triggerType = document.getElementById('triggerType').value;
        const triggerInput = document.getElementById('triggerValue').value;
        
        // Parse trigger value based on type
        let triggerValue = {};
        switch (triggerType) {
            case 'keyword':
                triggerValue = { keywords: triggerInput.split(',').map(k => k.trim()) };
                break;
            case 'sentiment':
                triggerValue = { threshold: parseFloat(triggerInput), operator: 'less_than' };
                break;
            case 'recipient':
                const recipients = triggerInput.split(',').map(r => r.trim());
                triggerValue = { 
                    roles: recipients.filter(r => !r.includes('@')),
                    ids: recipients.filter(r => r.includes('@'))
                };
                break;
            case 'channel':
                triggerValue = { type: triggerInput };
                break;
            case 'time':
                const [after, before] = triggerInput.split('-').map(t => t.trim());
                triggerValue = { after, before };
                break;
            case 'pattern':
                triggerValue = { patterns: triggerInput.split(',').map(p => p.trim()) };
                break;
        }
        
        const rule = {
            rule_name: document.getElementById('ruleName').value,
            description: document.getElementById('ruleDescription').value,
            enabled: true,
            priority: parseInt(document.getElementById('priority').value) || 0,
            trigger_type: triggerType,
            trigger_value: triggerValue,
            transformation_type: document.getElementById('transformationType').value,
            transformation_intensity: parseInt(document.getElementById('transformIntensity').value),
            platforms: document.getElementById('platforms').value
                .split(',')
                .map(p => p.trim())
                .filter(p => p),
            channels: [],
            user_roles: []
        };
        
        const tenantId = localStorage.getItem('tenantId') || 'default';
        
        if (editingRuleId) {
            // Update existing rule
            const index = currentRules.findIndex(r => r.id === editingRuleId);
            if (index !== -1) {
                currentRules[index] = { ...currentRules[index], ...rule };
            }
        } else {
            // Add new rule
            const response = await fetch(`${AUTO_TRANSFORM_URL}/rules/${tenantId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify(rule)
            });
            
            if (response.ok) {
                const result = await response.json();
                rule.id = result.rule_id;
                currentRules.push(rule);
            }
        }
        
        displayRules();
        closeRuleModal();
        showNotification(editingRuleId ? 'Rule updated successfully' : 'Rule created successfully', 'success');
        
    } catch (error) {
        console.error('Failed to save rule:', error);
        showNotification('Failed to save rule', 'error');
    }
}

// Load templates
async function loadTemplates() {
    try {
        const response = await fetch(`${AUTO_TRANSFORM_URL}/templates`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
        
        if (response.ok) {
            templates = await response.json();
            displayTemplates();
        }
    } catch (error) {
        console.error('Failed to load templates:', error);
    }
}

// Display templates
function displayTemplates() {
    const templatesGrid = document.getElementById('templatesGrid');
    
    const templateIcons = {
        'communication': '📧',
        'support': '🤝',
        'documentation': '📚',
        'priority': '🚨',
        'sentiment': '😊',
        'schedule': '⏰',
        'meetings': '📅'
    };
    
    templatesGrid.innerHTML = templates.map(template => `
        <div class="template-card" onclick="applyTemplate('${template.id}')">
            <div class="template-icon">${templateIcons[template.category] || '📋'}</div>
            <div class="template-name">${template.template_name}</div>
            <div class="template-category">${template.category}</div>
            <div class="template-description">${template.description}</div>
        </div>
    `).join('');
}

// Apply template
async function applyTemplate(templateId) {
    if (!confirm('Apply this template to create a new rule?')) return;
    
    try {
        const tenantId = localStorage.getItem('tenantId') || 'default';
        const response = await fetch(`${AUTO_TRANSFORM_URL}/apply-template/${tenantId}/${templateId}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
        
        if (response.ok) {
            showNotification('Template applied successfully', 'success');
            loadRules(); // Reload rules to show new one
        } else {
            throw new Error('Failed to apply template');
        }
    } catch (error) {
        console.error('Failed to apply template:', error);
        showNotification('Failed to apply template', 'error');
    }
}

// Show notification
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background: ${type === 'success' ? '#48bb78' : type === 'error' ? '#f56565' : '#4299e1'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 10000;
        animation: slideIn 0.3s ease;
    `;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Logout
function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('tenantId');
    window.location.href = 'login.html';
}

// Add animation styles
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);