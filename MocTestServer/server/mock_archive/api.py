"""
REST API для Mock Archive Server
"""

from flask import Blueprint, jsonify, request, Response

from .server import ArchiveServer

archive_api = Blueprint('archive_api', __name__, url_prefix='/api/archive')

_server = None


def init_server(config=None):
    """Инициализация сервера"""
    global _server
    _server = ArchiveServer(config)
    return _server


def get_server():
    """Получить экземпляр сервера"""
    global _server
    if _server is None:
        _server = ArchiveServer()
    return _server


@archive_api.route('/status', methods=['GET'])
def get_status():
    """GET /api/archive/status - Статус сервера"""
    return jsonify(get_server().get_status())


@archive_api.route('/start', methods=['POST'])
def start():
    """POST /api/archive/start - Запустить сервер"""
    get_server().start()
    return jsonify({"status": "ok", "message": "Archive server started"})


@archive_api.route('/stop', methods=['POST'])
def stop():
    """POST /api/archive/stop - Остановить сервер"""
    get_server().stop()
    return jsonify({"status": "ok", "message": "Archive server stopped"})


@archive_api.route('/query', methods=['GET'])
def query():
    """GET /api/archive/query - Запрос исторических данных"""
    sensor_id = request.args.get('sensor_id', 1, type=int)
    from_time = request.args.get('from')
    to_time = request.args.get('to')
    resolution = request.args.get('resolution', 'minute')
    
    if not from_time or not to_time:
        return jsonify({"error": "from and to parameters required"}), 400
    
    result = get_server().query(sensor_id, from_time, to_time, resolution)
    return jsonify(result)


@archive_api.route('/events', methods=['GET'])
def get_events():
    """GET /api/archive/events - Получить события"""
    return jsonify(get_server().get_events(
        from_time=request.args.get('from'),
        to_time=request.args.get('to'),
        sensor_id=request.args.get('sensor_id', type=int),
        event_type=request.args.get('event_type'),
        priority=request.args.get('priority'),
        acknowledged=request.args.get('acknowledged', type=lambda x: x.lower() == 'true') 
                     if request.args.get('acknowledged') else None,
        limit=request.args.get('limit', 100, type=int),
        offset=request.args.get('offset', 0, type=int)
    ))


@archive_api.route('/events/<int:event_id>/acknowledge', methods=['POST'])
def acknowledge_event(event_id):
    """POST /api/archive/events/{id}/acknowledge - Квитировать событие"""
    params = request.get_json() or {}
    user = params.get('user', 'operator')
    
    result = get_server().acknowledge_event(event_id, user)
    if result:
        return jsonify(result)
    return jsonify({"error": "Event not found"}), 404


@archive_api.route('/export', methods=['GET'])
def export_data():
    """GET /api/archive/export - Экспорт данных"""
    sensor_id = request.args.get('sensor_id', 1, type=int)
    from_time = request.args.get('from')
    to_time = request.args.get('to')
    format = request.args.get('format', 'json')
    
    if not from_time or not to_time:
        return jsonify({"error": "from and to parameters required"}), 400
    
    result = get_server().export_data(sensor_id, from_time, to_time, format)
    
    if format == 'csv':
        return Response(
            result,
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=sensor_{sensor_id}.csv'}
        )
    return jsonify(result)


@archive_api.route('/config', methods=['GET'])
def get_config():
    """GET /api/archive/config - Получить конфигурацию"""
    return jsonify(get_server().config)


@archive_api.route('/config', methods=['POST'])
def update_config():
    """POST /api/archive/config - Обновить конфигурацию"""
    new_config = request.get_json()
    if not new_config:
        return jsonify({"error": "No config provided"}), 400
    
    get_server().update_config(new_config)
    return jsonify({"status": "ok"})


@archive_api.route('/regenerate', methods=['POST'])
def regenerate():
    """POST /api/archive/regenerate - Перегенерировать данные"""
    get_server().regenerate()
    return jsonify({"status": "ok", "message": "Data regenerated"})


@archive_api.route('/cleanup', methods=['POST'])
def cleanup():
    """POST /api/archive/cleanup - Очистка старых данных"""
    params = request.get_json() or {}
    days = params.get('days_to_keep', 7)
    
    result = get_server().cleanup(days)
    return jsonify(result)
