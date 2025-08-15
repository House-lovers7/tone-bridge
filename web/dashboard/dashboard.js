// ToneBridge KPI Dashboard JavaScript

// Configuration
const API_BASE_URL = '/api/v1';
const REFRESH_INTERVAL = 30000; // 30 seconds
const CHART_COLORS = {
    primary: '#4F46E5',
    success: '#10B981',
    warning: '#F59E0B',
    danger: '#EF4444',
    info: '#3B82F6',
    purple: '#8B5CF6',
    pink: '#EC4899'
};

// Global variables
let charts = {};
let refreshTimer = null;
let currentPeriod = 30;
let tenantData = null;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', async () => {
    console.log('Initializing ToneBridge KPI Dashboard...');
    
    // Setup event listeners
    setupEventListeners();
    
    // Load initial data
    await loadDashboardData();
    
    // Start auto-refresh
    startAutoRefresh();
    
    // Initialize real-time activity feed
    initializeActivityFeed();
});

// Setup event listeners
function setupEventListeners() {
    // Period selector
    document.getElementById('periodSelector').addEventListener('change', async (e) => {
        currentPeriod = parseInt(e.target.value);
        document.getElementById('dateRange').textContent = `Last ${currentPeriod} days`;
        await loadDashboardData();
    });
    
    // Refresh button
    document.getElementById('refreshBtn').addEventListener('click', async () => {
        await loadDashboardData();
    });
    
    // Export button
    document.getElementById('exportBtn').addEventListener('click', exportToCSV);
    
    // Error modal close
    document.querySelector('.close').addEventListener('click', () => {
        document.getElementById('errorModal').style.display = 'none';
    });
}

// Load dashboard data
async function loadDashboardData() {
    showLoading(true);
    
    try {
        // Fetch all data in parallel
        const [metricsData, trendsData, insightsData] = await Promise.all([
            fetchMetrics(),
            fetchTrends(),
            fetchInsights()
        ]);
        
        // Update UI components
        updateMetricsCards(metricsData);
        updateCharts(trendsData);
        updateInsights(insightsData);
        updateMetricsTable(metricsData.daily);
        
        // Update tenant info
        updateTenantInfo(metricsData.tenant);
        
        showLoading(false);
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        showError('Failed to load dashboard data. Please try again.');
        showLoading(false);
    }
}

// Fetch metrics from API
async function fetchMetrics() {
    // Mock data for demonstration
    // In production, this would fetch from the actual API
    return {
        tenant: {
            name: 'Acme Corporation',
            plan: 'Pro',
            id: 'tenant-123'
        },
        summary: {
            totalTransformations: 15842,
            transformationChange: 23.5,
            preventionRate: 87.3,
            preventionChange: 5.2,
            timeSaved: 342,
            timeChange: 18.7,
            activeUsers: 127,
            usersChange: 12.3
        },
        daily: generateDailyMetrics(currentPeriod)
    };
}

// Fetch trends data
async function fetchTrends() {
    // Mock data for demonstration
    return {
        usage: generateUsageTrend(currentPeriod),
        features: {
            'Tone Transform': 4521,
            'Structure': 3234,
            'Summarize': 2876,
            'Requirements': 2145,
            'Background': 1897,
            'Priority': 1169
        },
        platforms: {
            'Slack': 45,
            'Teams': 30,
            'Discord': 15,
            'Web': 10
        },
        priorities: {
            'Critical': 234,
            'High': 567,
            'Medium': 1234,
            'Low': 789
        }
    };
}

// Fetch insights data
async function fetchInsights() {
    // Mock data for demonstration
    return {
        topUsers: [
            { name: 'Sarah Chen', count: 234 },
            { name: 'Mike Johnson', count: 189 },
            { name: 'Emily Davis', count: 167 },
            { name: 'James Wilson', count: 145 },
            { name: 'Lisa Anderson', count: 123 }
        ],
        topFeatures: [
            { name: 'Soften Message', count: 1234 },
            { name: 'Clarify Structure', count: 987 },
            { name: 'Priority Score', count: 765 },
            { name: 'Requirements', count: 543 },
            { name: 'Background Check', count: 321 }
        ],
        peakHours: [
            { hour: '10:00 AM', count: 234 },
            { hour: '2:00 PM', count: 198 },
            { hour: '11:00 AM', count: 176 },
            { hour: '3:00 PM', count: 165 },
            { hour: '4:00 PM', count: 143 }
        ],
        recentFeedback: [
            'Great tool! Saved me hours of editing.',
            'The tone adjustment slider is amazing.',
            'Priority scoring helps me focus on what matters.',
            'Background completion catches things I miss.'
        ]
    };
}

// Update metrics cards
function updateMetricsCards(data) {
    const summary = data.summary;
    
    // Total Transformations
    document.getElementById('totalTransformations').textContent = formatNumber(summary.totalTransformations);
    updateChangeIndicator('transformationChange', summary.transformationChange);
    
    // Prevention Rate
    document.getElementById('preventionRate').textContent = `${summary.preventionRate}%`;
    updateChangeIndicator('preventionChange', summary.preventionChange);
    
    // Time Saved
    document.getElementById('timeSaved').textContent = `${summary.timeSaved}h`;
    updateChangeIndicator('timeChange', summary.timeChange);
    
    // Active Users
    document.getElementById('activeUsers').textContent = formatNumber(summary.activeUsers);
    updateChangeIndicator('usersChange', summary.usersChange);
}

// Update change indicator
function updateChangeIndicator(elementId, value) {
    const element = document.getElementById(elementId);
    const isPositive = value >= 0;
    element.textContent = `${isPositive ? '+' : ''}${value}%`;
    element.className = `metric-change ${isPositive ? 'positive' : 'negative'}`;
}

// Update charts
function updateCharts(data) {
    // Usage Trend Chart
    if (charts.usageTrend) {
        charts.usageTrend.destroy();
    }
    
    const usageCtx = document.getElementById('usageTrendChart').getContext('2d');
    charts.usageTrend = new Chart(usageCtx, {
        type: 'line',
        data: {
            labels: data.usage.labels,
            datasets: [{
                label: 'Transformations',
                data: data.usage.transformations,
                borderColor: CHART_COLORS.primary,
                backgroundColor: `${CHART_COLORS.primary}20`,
                tension: 0.4
            }, {
                label: 'Active Users',
                data: data.usage.users,
                borderColor: CHART_COLORS.success,
                backgroundColor: `${CHART_COLORS.success}20`,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    labels: { color: '#9CA3AF' }
                }
            },
            scales: {
                x: {
                    grid: { color: '#374151' },
                    ticks: { color: '#9CA3AF' }
                },
                y: {
                    grid: { color: '#374151' },
                    ticks: { color: '#9CA3AF' }
                }
            }
        }
    });
    
    // Feature Usage Chart
    if (charts.features) {
        charts.features.destroy();
    }
    
    const featureCtx = document.getElementById('featureChart').getContext('2d');
    charts.features = new Chart(featureCtx, {
        type: 'bar',
        data: {
            labels: Object.keys(data.features),
            datasets: [{
                label: 'Usage Count',
                data: Object.values(data.features),
                backgroundColor: [
                    CHART_COLORS.primary,
                    CHART_COLORS.success,
                    CHART_COLORS.warning,
                    CHART_COLORS.info,
                    CHART_COLORS.purple,
                    CHART_COLORS.pink
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    grid: { color: '#374151' },
                    ticks: { color: '#9CA3AF' }
                },
                y: {
                    grid: { color: '#374151' },
                    ticks: { color: '#9CA3AF' }
                }
            }
        }
    });
    
    // Platform Distribution Chart
    if (charts.platforms) {
        charts.platforms.destroy();
    }
    
    const platformCtx = document.getElementById('platformChart').getContext('2d');
    charts.platforms = new Chart(platformCtx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(data.platforms),
            datasets: [{
                data: Object.values(data.platforms),
                backgroundColor: [
                    CHART_COLORS.primary,
                    CHART_COLORS.success,
                    CHART_COLORS.warning,
                    CHART_COLORS.info
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#9CA3AF' }
                }
            }
        }
    });
    
    // Priority Distribution Chart
    if (charts.priorities) {
        charts.priorities.destroy();
    }
    
    const priorityCtx = document.getElementById('priorityChart').getContext('2d');
    charts.priorities = new Chart(priorityCtx, {
        type: 'polarArea',
        data: {
            labels: Object.keys(data.priorities),
            datasets: [{
                data: Object.values(data.priorities),
                backgroundColor: [
                    `${CHART_COLORS.danger}80`,
                    `${CHART_COLORS.warning}80`,
                    `${CHART_COLORS.info}80`,
                    `${CHART_COLORS.success}80`
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#9CA3AF' }
                }
            },
            scales: {
                r: {
                    grid: { color: '#374151' },
                    ticks: { color: '#9CA3AF' }
                }
            }
        }
    });
}

// Update insights
function updateInsights(data) {
    // Top Users
    const topUsersList = document.getElementById('topUsersList');
    topUsersList.innerHTML = data.topUsers.map(user => 
        `<li><span>${user.name}</span><strong>${user.count}</strong></li>`
    ).join('');
    
    // Top Features
    const topFeaturesList = document.getElementById('topFeaturesList');
    topFeaturesList.innerHTML = data.topFeatures.map(feature => 
        `<li><span>${feature.name}</span><strong>${feature.count}</strong></li>`
    ).join('');
    
    // Peak Hours
    const peakHoursList = document.getElementById('peakHoursList');
    peakHoursList.innerHTML = data.peakHours.map(hour => 
        `<li><span>${hour.hour}</span><strong>${hour.count}</strong></li>`
    ).join('');
    
    // Recent Feedback
    const recentFeedback = document.getElementById('recentFeedback');
    recentFeedback.innerHTML = data.recentFeedback.map(feedback => 
        `<li>${feedback}</li>`
    ).join('');
}

// Update metrics table
function updateMetricsTable(dailyData) {
    const tbody = document.getElementById('metricsTableBody');
    tbody.innerHTML = dailyData.map(day => `
        <tr>
            <td>${day.date}</td>
            <td>${formatNumber(day.transformations)}</td>
            <td>${day.clarityScore}%</td>
            <td>${day.avgResponseTime}ms</td>
            <td>${day.topFeature}</td>
            <td>${day.cacheHitRate}%</td>
        </tr>
    `).join('');
}

// Update tenant info
function updateTenantInfo(tenant) {
    document.getElementById('tenantName').textContent = tenant.name;
    document.getElementById('planBadge').textContent = tenant.plan;
    
    // Update plan badge color
    const planBadge = document.getElementById('planBadge');
    planBadge.className = 'plan-badge';
    if (tenant.plan === 'Enterprise') {
        planBadge.style.background = CHART_COLORS.purple;
    } else if (tenant.plan === 'Pro') {
        planBadge.style.background = CHART_COLORS.primary;
    }
}

// Initialize activity feed
function initializeActivityFeed() {
    // Simulate real-time activity
    setInterval(() => {
        addActivityItem(generateRandomActivity());
    }, 5000);
    
    // Add initial activities
    for (let i = 0; i < 5; i++) {
        addActivityItem(generateRandomActivity());
    }
}

// Add activity item
function addActivityItem(activity) {
    const activityList = document.getElementById('activityList');
    
    const activityItem = document.createElement('div');
    activityItem.className = 'activity-item';
    activityItem.innerHTML = `
        <span class="activity-icon">${activity.icon}</span>
        <div class="activity-content">
            <div>${activity.message}</div>
            <div class="activity-time">${activity.time}</div>
        </div>
    `;
    
    // Add to top of list
    activityList.insertBefore(activityItem, activityList.firstChild);
    
    // Keep only last 10 items
    while (activityList.children.length > 10) {
        activityList.removeChild(activityList.lastChild);
    }
}

// Generate random activity
function generateRandomActivity() {
    const activities = [
        { icon: '✨', message: 'Sarah transformed a message using Soften' },
        { icon: '📊', message: 'Mike analyzed priority for 3 messages' },
        { icon: '📝', message: 'Emily structured requirements from email' },
        { icon: '🎯', message: 'James used background completion' },
        { icon: '⚡', message: 'Lisa batch processed 10 messages' }
    ];
    
    const activity = activities[Math.floor(Math.random() * activities.length)];
    return {
        ...activity,
        time: new Date().toLocaleTimeString()
    };
}

// Export to CSV
function exportToCSV() {
    // Implementation for CSV export
    console.log('Exporting to CSV...');
    // In production, this would generate and download a CSV file
    alert('CSV export feature coming soon!');
}

// Show/hide loading overlay
function showLoading(show) {
    const overlay = document.getElementById('loadingOverlay');
    overlay.classList.toggle('hidden', !show);
}

// Show error message
function showError(message) {
    document.getElementById('errorMessage').textContent = message;
    document.getElementById('errorModal').style.display = 'block';
}

// Start auto-refresh
function startAutoRefresh() {
    refreshTimer = setInterval(() => {
        loadDashboardData();
    }, REFRESH_INTERVAL);
}

// Stop auto-refresh
function stopAutoRefresh() {
    if (refreshTimer) {
        clearInterval(refreshTimer);
        refreshTimer = null;
    }
}

// Utility functions
function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

function generateDailyMetrics(days) {
    const metrics = [];
    const today = new Date();
    
    for (let i = days - 1; i >= 0; i--) {
        const date = new Date(today);
        date.setDate(date.getDate() - i);
        
        metrics.push({
            date: date.toLocaleDateString(),
            transformations: Math.floor(Math.random() * 1000) + 200,
            clarityScore: Math.floor(Math.random() * 20) + 70,
            avgResponseTime: Math.floor(Math.random() * 500) + 100,
            topFeature: ['Soften', 'Clarify', 'Structure'][Math.floor(Math.random() * 3)],
            cacheHitRate: Math.floor(Math.random() * 30) + 60
        });
    }
    
    return metrics;
}

function generateUsageTrend(days) {
    const labels = [];
    const transformations = [];
    const users = [];
    const today = new Date();
    
    for (let i = days - 1; i >= 0; i--) {
        const date = new Date(today);
        date.setDate(date.getDate() - i);
        labels.push(date.toLocaleDateString());
        transformations.push(Math.floor(Math.random() * 500) + 300);
        users.push(Math.floor(Math.random() * 50) + 20);
    }
    
    return { labels, transformations, users };
}