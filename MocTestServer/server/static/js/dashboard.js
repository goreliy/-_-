/**
 * Dashboard page JavaScript
 */

let archiveChart = null;
let currentSensorId = 1;

// Load all status
async function loadStatus() {
    try {
        const data = await api('/api/status');
        
        // Modbus
        updateStatusCard('modbus', data.modbus);
        document.getElementById('modbus-port').textContent = data.modbus.port;
        document.getElementById('modbus-unit').textContent = data.modbus.unit_id;
        document.getElementById('modbus-scenario').textContent = data.modbus.scenario;
        
        // Current
        updateStatusCard('current', data.current);
        document.getElementById('current-sensors').textContent = data.current.sensor_count;
        document.getElementById('current-interval').textContent = data.current.interval_ms + ' мс';
        document.getElementById('current-scenario').textContent = data.current.scenario;
        
        // Archive
        updateStatusCard('archive', data.archive);
        document.getElementById('archive-records').textContent = data.archive.data?.total_records || 0;
        document.getElementById('archive-events').textContent = data.archive.events?.total_events || 0;
        document.getElementById('archive-days').textContent = (data.archive.data?.history_days || 30) + ' дней';
        
    } catch (e) {
        console.error('Error loading status:', e);
    }
}

function updateStatusCard(name, status) {
    const badge = document.getElementById(`${name}-status`);
    if (badge) {
        badge.textContent = status.running ? 'Running' : 'Stopped';
        badge.className = `status-badge ${status.running ? 'running' : 'stopped'}`;
    }
}

// Toggle server
async function toggleServer(name) {
    try {
        const data = await api('/api/status');
        const isRunning = data[name]?.running;
        const action = isRunning ? 'stop' : 'start';
        
        await api(`/api/${name}/${action}`, 'POST');
        showToast(`${name} ${action === 'start' ? 'запущен' : 'остановлен'}`, 'success');
        loadStatus();
    } catch (e) {
        showToast('Ошибка: ' + e.message, 'error');
    }
}

// Set scenario
async function setScenario(scenario) {
    try {
        await api('/api/set_scenario_all', 'POST', { scenario });
        showToast(`Сценарий "${scenario}" установлен`, 'success');
        loadStatus();
    } catch (e) {
        showToast('Ошибка: ' + e.message, 'error');
    }
}

// Refresh preview
async function refreshPreview() {
    const container = document.getElementById('sensors-preview');
    
    try {
        const data = await api('/api/current/preview');
        
        if (!data.sensors || data.sensors.length === 0) {
            container.innerHTML = '<div class="loading">Нет данных</div>';
            return;
        }
        
        container.innerHTML = data.sensors.map(sensor => `
            <div class="preview-item status-${sensor.combined_status}" 
                 onclick="showArchiveModal(${sensor.id}, '${sensor.name}')">
                <div class="name">${sensor.name}</div>
                <div class="values">
                    <span class="temp">${sensor.temperature?.value?.toFixed(1) ?? '—'}°C</span>
                    <span class="hum">${sensor.humidity?.value?.toFixed(1) ?? '—'}%</span>
                </div>
            </div>
        `).join('');
    } catch (e) {
        container.innerHTML = '<div class="loading">Ошибка загрузки</div>';
    }
}

// Show archive modal for sensor
function showArchiveModal(sensorId, sensorName) {
    currentSensorId = sensorId;
    document.getElementById('modal-title').textContent = `Архив: ${sensorName}`;
    document.getElementById('archive-modal').style.display = 'flex';
    updateChart();
}

// Close archive modal
function closeArchiveModal() {
    document.getElementById('archive-modal').style.display = 'none';
}

// Update chart
async function updateChart() {
    const hours = parseInt(document.getElementById('chart-period').value);
    const toTime = new Date().toISOString();
    const fromTime = new Date(Date.now() - hours * 60 * 60 * 1000).toISOString();
    
    try {
        const data = await api(`/api/archive/query?sensor_id=${currentSensorId}&from=${fromTime}&to=${toTime}&resolution=hour`);
        
        const ctx = document.getElementById('archive-chart').getContext('2d');
        
        if (archiveChart) {
            archiveChart.destroy();
        }
        
        const labels = data.data.map(p => {
            const d = new Date(p.timestamp);
            return d.toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
        });
        
        const tempData = data.data.map(p => p.temperature?.avg ?? p.temperature);
        const humData = data.data.map(p => p.humidity?.avg ?? p.humidity);
        
        archiveChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Температура (°C)',
                        data: tempData,
                        borderColor: '#f85149',
                        backgroundColor: 'rgba(248, 81, 73, 0.1)',
                        tension: 0.3,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Влажность (%)',
                        data: humData,
                        borderColor: '#58a6ff',
                        backgroundColor: 'rgba(88, 166, 255, 0.1)',
                        tension: 0.3,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Температура (°C)'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Влажность (%)'
                        },
                        grid: {
                            drawOnChartArea: false
                        }
                    }
                }
            }
        });
    } catch (e) {
        console.error('Error loading chart data:', e);
    }
}

// Close modal on click outside
document.addEventListener('click', (e) => {
    const modal = document.getElementById('archive-modal');
    if (e.target === modal) {
        closeArchiveModal();
    }
});

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadStatus();
    refreshPreview();
    
    // Auto-refresh
    setInterval(loadStatus, 5000);
    setInterval(refreshPreview, 2000);
});
