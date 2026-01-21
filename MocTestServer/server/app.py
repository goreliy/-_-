"""
Главное Flask приложение - веб-интерфейс управления Mock Server
"""

import json
import os
from flask import Flask, render_template, jsonify, request

# Импорт API модулей
from .mock_modbus.api import modbus_api, init_server as init_modbus
from .mock_current.api import current_api, init_generator as init_current
from .mock_archive.api import archive_api, init_server as init_archive

# Создаём Flask приложение
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')

# Регистрируем blueprints
app.register_blueprint(modbus_api)
app.register_blueprint(current_api)
app.register_blueprint(archive_api)

# Глобальные компоненты
_config = None


def load_config(config_path: str = None) -> dict:
    """Загрузка конфигурации из файла"""
    global _config
    
    if config_path and os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            _config = json.load(f)
    else:
        _config = default_config()
    
    return _config


def default_config() -> dict:
    """Конфигурация по умолчанию"""
    return {
        "config_version": "1.0",
        "ui": {
            "port": 8000,
            "host": "0.0.0.0"
        },
        "servers": {
            "modbus": {
                "enabled": True,
                "config": None
            },
            "current": {
                "enabled": True,
                "config": None
            },
            "archive": {
                "enabled": True,
                "config": None
            }
        },
        "auto_start": False,
        "log_level": "INFO"
    }


def init_app(config: dict = None):
    """Инициализация приложения с конфигурацией"""
    global _config
    _config = config or default_config()
    
    # Инициализация компонентов
    servers_cfg = _config.get("servers", {})
    
    if servers_cfg.get("modbus", {}).get("enabled", True):
        init_modbus(servers_cfg.get("modbus", {}).get("config"))
    
    if servers_cfg.get("current", {}).get("enabled", True):
        init_current(servers_cfg.get("current", {}).get("config"))
    
    if servers_cfg.get("archive", {}).get("enabled", True):
        init_archive(servers_cfg.get("archive", {}).get("config"))
    
    return app


# === Маршруты веб-интерфейса ===

@app.route('/')
def dashboard():
    """Главная страница - Dashboard"""
    return render_template('dashboard.html')


@app.route('/modbus')
def modbus_page():
    """Страница настроек Mock Modbus Server"""
    return render_template('modbus.html')


@app.route('/current')
def current_page():
    """Страница настроек Mock Current Generator"""
    return render_template('current.html')


@app.route('/archive')
def archive_page():
    """Страница настроек Mock Archive Server"""
    return render_template('archive.html')


@app.route('/scenarios')
def scenarios_page():
    """Страница управления сценариями"""
    return render_template('scenarios.html')


# === API управления всеми серверами ===

@app.route('/api/status', methods=['GET'])
def get_all_status():
    """GET /api/status - Статус всех серверов"""
    from .mock_modbus.api import get_server as get_modbus
    from .mock_current.api import get_generator as get_current
    from .mock_archive.api import get_server as get_archive
    
    return jsonify({
        "modbus": get_modbus().get_status(),
        "current": get_current().get_status(),
        "archive": get_archive().get_status()
    })


@app.route('/api/start_all', methods=['POST'])
def start_all():
    """POST /api/start_all - Запустить все серверы"""
    from .mock_modbus.api import get_server as get_modbus
    from .mock_current.api import get_generator as get_current
    from .mock_archive.api import get_server as get_archive
    
    get_modbus().start()
    get_current().start()
    get_archive().start()
    
    return jsonify({"status": "ok", "message": "All servers started"})


@app.route('/api/stop_all', methods=['POST'])
def stop_all():
    """POST /api/stop_all - Остановить все серверы"""
    from .mock_modbus.api import get_server as get_modbus
    from .mock_current.api import get_generator as get_current
    from .mock_archive.api import get_server as get_archive
    
    get_modbus().stop()
    get_current().stop()
    get_archive().stop()
    
    return jsonify({"status": "ok", "message": "All servers stopped"})


@app.route('/api/config', methods=['GET'])
def get_config():
    """GET /api/config - Получить всю конфигурацию"""
    from .mock_modbus.api import get_server as get_modbus
    from .mock_current.api import get_generator as get_current
    from .mock_archive.api import get_server as get_archive
    
    return jsonify({
        "ui": _config.get("ui", {}),
        "modbus": get_modbus().config,
        "current": get_current().config,
        "archive": get_archive().config
    })


@app.route('/api/config', methods=['POST'])
def save_config():
    """POST /api/config - Сохранить всю конфигурацию"""
    new_config = request.get_json()
    if not new_config:
        return jsonify({"error": "No config provided"}), 400
    
    from .mock_modbus.api import get_server as get_modbus
    from .mock_current.api import get_generator as get_current
    from .mock_archive.api import get_server as get_archive
    
    if "modbus" in new_config:
        get_modbus().update_config(new_config["modbus"])
    
    if "current" in new_config:
        get_current().update_config(new_config["current"])
    
    if "archive" in new_config:
        get_archive().update_config(new_config["archive"])
    
    return jsonify({"status": "ok"})


@app.route('/api/scenarios', methods=['GET'])
def get_scenarios():
    """GET /api/scenarios - Список доступных сценариев"""
    from .scenarios import SCENARIOS
    
    scenarios_info = []
    for name, cls in SCENARIOS.items():
        scenarios_info.append({
            "name": name,
            "description": getattr(cls, 'description', name)
        })
    
    return jsonify({"scenarios": scenarios_info})


@app.route('/api/set_scenario_all', methods=['POST'])
def set_scenario_all():
    """POST /api/set_scenario_all - Установить сценарий для всех серверов"""
    params = request.get_json()
    if not params or 'scenario' not in params:
        return jsonify({"error": "scenario required"}), 400
    
    scenario = params['scenario']
    
    from .mock_modbus.api import get_server as get_modbus
    from .mock_current.api import get_generator as get_current
    
    get_modbus().set_scenario(scenario)
    get_current().set_scenario(scenario)
    
    return jsonify({"status": "ok", "scenario": scenario})


def run_server(host: str = "0.0.0.0", port: int = 8000, debug: bool = False):
    """Запуск веб-сервера"""
    app.run(host=host, port=port, debug=debug, threaded=True)


if __name__ == '__main__':
    init_app()
    run_server(debug=True)
