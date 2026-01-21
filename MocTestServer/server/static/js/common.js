/**
 * Common JavaScript utilities
 */

// API helper
async function api(url, method = 'GET', data = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json'
        }
    };
    
    if (data) {
        options.body = JSON.stringify(data);
    }
    
    const response = await fetch(url, options);
    
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    return response.json();
}

// Toast notifications
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Global actions
async function startAll() {
    try {
        await api('/api/start_all', 'POST');
        showToast('Все серверы запущены', 'success');
        if (typeof loadStatus === 'function') loadStatus();
    } catch (e) {
        showToast('Ошибка: ' + e.message, 'error');
    }
}

async function stopAll() {
    try {
        await api('/api/stop_all', 'POST');
        showToast('Все серверы остановлены', 'info');
        if (typeof loadStatus === 'function') loadStatus();
    } catch (e) {
        showToast('Ошибка: ' + e.message, 'error');
    }
}
