/**
 * Current Generator page JavaScript
 */

let isRunning = false;

// Toggle generator
async function toggleCurrent() {
    const action = isRunning ? 'stop' : 'start';
    
    try {
        await api(`/api/current/${action}`, 'POST');
        showToast(`Генератор ${action === 'start' ? 'запущен' : 'остановлен'}`, 'success');
        loadStatus();
    } catch (e) {
        showToast('Ошибка: ' + e.message, 'error');
    }
}

// Load status
async function loadStatus() {
    try {
        const data = await api('/api/current/status');
        isRunning = data.running;
        
        document.getElementById('toggle-text').textContent = isRunning ? '⏹ Stop' : '▶ Start';
        document.getElementById('btn-toggle').className = `btn ${isRunning ? 'btn-danger' : 'btn-success'}`;
        
        // Statistics
        document.getElementById('stat-total').textContent = data.statistics?.total_polls || 0;
        document.getElementById('stat-success').textContent = data.statistics?.successful_polls || 0;
        document.getElementById('stat-failed').textContent = data.statistics?.failed_polls || 0;
    } catch (e) {
        console.error('Error loading status:', e);
    }
}

// Load config
async function loadConfig() {
    try {
        const data = await api('/api/current/config');
        
        // Output
        document.getElementById('cfg-current-path').value = data.output?.current_path || '../data/current.json';
        document.getElementById('cfg-log-path').value = data.output?.log_path || '../data/modbus_log.json';
        document.getElementById('cfg-gen-log').checked = data.output?.generate_log !== false;
        
        // Sensors
        document.getElementById('cfg-sensors').value = data.sensors?.count || 10;
        document.getElementById('sensors-val').textContent = data.sensors?.count || 10;
        document.getElementById('cfg-name-prefix').value = data.sensors?.name_prefix || 'ХРАН. №';
        document.getElementById('cfg-slave-id').value = data.sensors?.modbus_slave_id || 16;
        
        // Generation
        document.getElementById('cfg-interval').value = data.generation?.interval_ms || 1000;
        document.getElementById('cfg-scenario').value = data.generation?.scenario || 'normal';
        
        showToast('Конфигурация загружена', 'info');
    } catch (e) {
        showToast('Ошибка загрузки: ' + e.message, 'error');
    }
}

// Save config
async function saveConfig() {
    const config = {
        output: {
            generate_log: document.getElementById('cfg-gen-log').checked
        },
        sensors: {
            count: parseInt(document.getElementById('cfg-sensors').value),
            name_prefix: document.getElementById('cfg-name-prefix').value,
            modbus_slave_id: parseInt(document.getElementById('cfg-slave-id').value)
        },
        generation: {
            interval_ms: parseInt(document.getElementById('cfg-interval').value),
            scenario: document.getElementById('cfg-scenario').value
        }
    };
    
    try {
        await api('/api/current/config', 'POST', config);
        showToast('Конфигурация сохранена', 'success');
    } catch (e) {
        showToast('Ошибка сохранения: ' + e.message, 'error');
    }
}

// Generate once
async function generateOnce() {
    try {
        await api('/api/current/generate', 'POST');
        showToast('Данные сгенерированы', 'success');
        refreshPreview();
    } catch (e) {
        showToast('Ошибка генерации: ' + e.message, 'error');
    }
}

// Refresh preview
async function refreshPreview() {
    const jsonPreview = document.getElementById('json-preview');
    const logPreview = document.getElementById('log-preview');
    
    try {
        const data = await api('/api/current/preview');
        jsonPreview.textContent = JSON.stringify(data, null, 2);
        
        // Generate sample log entries
        if (data.sensors && data.sensors.length > 0) {
            const sampleSensor = data.sensors[0];
            const sampleLog = {
                max_entries: 1000,
                entries: [
                    {
                        timestamp: new Date().toISOString(),
                        direction: "TX",
                        raw_hex: "10 04 75 30 00 02 A1 B2",
                        parsed: {
                            slave_id: sampleSensor.modbus_slave_id,
                            function: 4,
                            start_addr: 30000,
                            quantity: 2,
                            description: `Запрос значений датчика ${sampleSensor.id}`
                        },
                        response_time_ms: null
                    },
                    {
                        timestamp: new Date().toISOString(),
                        direction: "RX",
                        raw_hex: "10 04 04 00 DC 01 C2 XX XX",
                        parsed: {
                            slave_id: sampleSensor.modbus_slave_id,
                            function: 4,
                            byte_count: 4,
                            values: [sampleSensor.temperature?.raw || 220, sampleSensor.humidity?.raw || 450],
                            description: `Ответ: T=${sampleSensor.temperature?.value}°C, H=${sampleSensor.humidity?.value}%`
                        },
                        response_time_ms: 15.32
                    }
                ]
            };
            logPreview.textContent = JSON.stringify(sampleLog, null, 2);
        }
    } catch (e) {
        jsonPreview.textContent = 'Ошибка: ' + e.message;
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadStatus();
    loadConfig();
    refreshPreview();
    
    setInterval(loadStatus, 2000);
    setInterval(refreshPreview, 2000);
});
