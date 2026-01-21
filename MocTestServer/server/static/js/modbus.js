/**
 * Modbus Server page JavaScript
 */

let isRunning = false;

// Parse offline sensors string to array
function parseOfflineSensors(str) {
    if (!str) return [];
    return str.split(',')
        .map(s => parseInt(s.trim()))
        .filter(n => !isNaN(n));
}

// Toggle Modbus server
async function toggleModbus() {
    const action = isRunning ? 'stop' : 'start';
    
    try {
        await api(`/api/modbus/${action}`, 'POST');
        showToast(`Modbus сервер ${action === 'start' ? 'запущен' : 'остановлен'}`, 'success');
        loadStatus();
    } catch (e) {
        showToast('Ошибка: ' + e.message, 'error');
    }
}

// Load current status
async function loadStatus() {
    try {
        const data = await api('/api/modbus/status');
        isRunning = data.running;
        
        document.getElementById('toggle-text').textContent = isRunning ? '⏹ Stop' : '▶ Start';
        document.getElementById('btn-toggle').className = `btn ${isRunning ? 'btn-danger' : 'btn-success'}`;
    } catch (e) {
        console.error('Error loading status:', e);
    }
}

// Load configuration
async function loadConfig() {
    try {
        const data = await api('/api/modbus/config');
        
        // Server
        document.getElementById('cfg-port').value = data.server?.port || 5020;
        document.getElementById('cfg-unit-id').value = data.server?.unit_id || 16;
        
        // Sensors
        document.getElementById('cfg-sensors').value = data.sensors?.count || 10;
        document.getElementById('sensors-val').textContent = data.sensors?.count || 10;
        document.getElementById('cfg-value-base').value = data.sensors?.value_register_base || 30000;
        document.getElementById('cfg-status-base').value = data.sensors?.status_register_base || 40000;
        
        // Temperature values
        const temp = data.values?.temperature || {};
        document.getElementById('cfg-temp-base').value = temp.base ?? 22;
        document.getElementById('cfg-temp-var').value = temp.variation ?? 2;
        document.getElementById('cfg-temp-min').value = temp.min ?? -40;
        document.getElementById('cfg-temp-max').value = temp.max ?? 85;
        
        // Humidity values
        const hum = data.values?.humidity || {};
        document.getElementById('cfg-hum-base').value = hum.base ?? 45;
        document.getElementById('cfg-hum-var').value = hum.variation ?? 5;
        document.getElementById('cfg-hum-min').value = hum.min ?? 0;
        document.getElementById('cfg-hum-max').value = hum.max ?? 100;
        
        // Errors
        const errors = data.errors || {};
        document.getElementById('cfg-error-rate').value = (errors.error_rate || 0) * 100;
        document.getElementById('error-val').textContent = Math.round((errors.error_rate || 0) * 100) + '%';
        document.getElementById('cfg-timeout-rate').value = (errors.timeout_rate || 0) * 100;
        document.getElementById('timeout-val').textContent = Math.round((errors.timeout_rate || 0) * 100) + '%';
        document.getElementById('cfg-offline').value = (errors.offline_sensors || []).join(', ');
        
        // Scenario
        document.getElementById('cfg-scenario').value = data.generation?.scenario || 'normal';
        document.getElementById('cfg-interval').value = data.generation?.update_interval_ms || 1000;
        
        showToast('Конфигурация загружена', 'info');
    } catch (e) {
        showToast('Ошибка загрузки: ' + e.message, 'error');
    }
}

// Save configuration
async function saveConfig() {
    const config = {
        server: {
            port: parseInt(document.getElementById('cfg-port').value),
            unit_id: parseInt(document.getElementById('cfg-unit-id').value)
        },
        sensors: {
            count: parseInt(document.getElementById('cfg-sensors').value),
            value_register_base: parseInt(document.getElementById('cfg-value-base').value),
            status_register_base: parseInt(document.getElementById('cfg-status-base').value)
        },
        generation: {
            scenario: document.getElementById('cfg-scenario').value,
            update_interval_ms: parseInt(document.getElementById('cfg-interval').value)
        },
        values: {
            temperature: {
                base: parseFloat(document.getElementById('cfg-temp-base').value),
                variation: parseFloat(document.getElementById('cfg-temp-var').value),
                min: parseFloat(document.getElementById('cfg-temp-min').value),
                max: parseFloat(document.getElementById('cfg-temp-max').value)
            },
            humidity: {
                base: parseFloat(document.getElementById('cfg-hum-base').value),
                variation: parseFloat(document.getElementById('cfg-hum-var').value),
                min: parseFloat(document.getElementById('cfg-hum-min').value),
                max: parseFloat(document.getElementById('cfg-hum-max').value)
            }
        },
        errors: {
            error_rate: parseFloat(document.getElementById('cfg-error-rate').value) / 100,
            timeout_rate: parseFloat(document.getElementById('cfg-timeout-rate').value) / 100,
            offline_sensors: parseOfflineSensors(document.getElementById('cfg-offline').value)
        }
    };
    
    try {
        await api('/api/modbus/config', 'POST', config);
        showToast('Конфигурация сохранена', 'success');
    } catch (e) {
        showToast('Ошибка сохранения: ' + e.message, 'error');
    }
}

// Refresh registers table
async function refreshRegisters() {
    const tbody = document.querySelector('#registers-table tbody');
    
    try {
        const data = await api('/api/modbus/registers');
        
        if (!data || Object.keys(data).length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="loading">Нет данных</td></tr>';
            return;
        }
        
        tbody.innerHTML = Object.entries(data).map(([id, sensor]) => `
            <tr>
                <td>Датчик ${id}</td>
                <td>${sensor.temperature?.address}</td>
                <td>${sensor.temperature?.value?.toFixed(1)}°C</td>
                <td>${sensor.temperature?.raw}</td>
                <td>${sensor.humidity?.address}</td>
                <td>${sensor.humidity?.value?.toFixed(1)}%</td>
                <td>${sensor.humidity?.raw}</td>
            </tr>
        `).join('');
    } catch (e) {
        tbody.innerHTML = '<tr><td colspan="7" class="loading">Ошибка загрузки</td></tr>';
    }
}

// Refresh Modbus log - загружаем из файла modbus_log.json
async function refreshModbusLog() {
    const tbody = document.querySelector('#modbus-log-table tbody');
    
    try {
        // Загружаем лог из файла modbus_log.json через Current Generator API
        const data = await api('/api/current/modbus_log?limit=100');
        
        // Update statistics
        if (data.statistics) {
            const stats = data.statistics;
            document.getElementById('stat-tx').textContent = stats.tx_count || 0;
            document.getElementById('stat-rx').textContent = stats.rx_count || 0;
            document.getElementById('stat-errors').textContent = stats.error_count || 0;
            document.getElementById('stat-avg-time').textContent = (stats.avg_response_time_ms || 0).toFixed(2) + ' мс';
            document.getElementById('stat-minmax-time').textContent = 
                `${(stats.min_response_time_ms || 0).toFixed(2)}/${(stats.max_response_time_ms || 0).toFixed(2)} мс`;
        }
        
        // Update log entries
        if (!data.entries || data.entries.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="loading">Нет данных лога</td></tr>';
            return;
        }
        
        // Show newest first
        const entries = [...data.entries].reverse();
        
        tbody.innerHTML = entries.map(entry => {
            const timestamp = new Date(entry.timestamp).toLocaleTimeString('ru-RU', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                fractionalSecondDigits: 3
            });
            
            const dirClass = entry.direction === 'TX' ? 'tx' : 'rx';
            const dirIcon = entry.direction === 'TX' ? '➡️' : '⬅️';
            
            const rawHex = entry.raw_hex || '—';
            const description = entry.parsed?.description || entry.parsed?.error || '—';
            
            let responseTime = '—';
            if (entry.response_time_ms !== null && entry.response_time_ms !== undefined) {
                const timeClass = entry.response_time_ms > 50 ? 'slow' : (entry.response_time_ms > 20 ? 'medium' : 'fast');
                responseTime = `<span class="response-time ${timeClass}">${entry.response_time_ms.toFixed(2)} мс</span>`;
            }
            
            const errorClass = entry.parsed?.error ? 'error-row' : '';
            
            return `
                <tr class="${errorClass}">
                    <td>${timestamp}</td>
                    <td class="direction ${dirClass}">${dirIcon} ${entry.direction}</td>
                    <td class="raw-hex"><code>${rawHex}</code></td>
                    <td class="description">${description}</td>
                    <td>${responseTime}</td>
                </tr>
            `;
        }).join('');
    } catch (e) {
        tbody.innerHTML = `<tr><td colspan="5" class="loading">Ошибка: ${e.message}</td></tr>`;
    }
}

// Clear Modbus log
async function clearModbusLog() {
    try {
        await api('/api/modbus/log/clear', 'POST');
        showToast('Лог очищен', 'info');
        refreshModbusLog();
    } catch (e) {
        showToast('Ошибка очистки лога: ' + e.message, 'error');
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadStatus();
    loadConfig();
    refreshRegisters();
    refreshModbusLog();
    
    // Auto-refresh registers and log
    setInterval(refreshRegisters, 2000);
    setInterval(refreshModbusLog, 1000);
});
