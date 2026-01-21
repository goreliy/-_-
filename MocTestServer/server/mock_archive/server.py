"""
Mock Archive Server - эмуляция REST API Archive Manager
"""

import csv
import io
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from .data_generator import HistoryGenerator
from .event_generator import EventGenerator


class ArchiveServer:
    """Mock Archive Server"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._default_config()
        
        self._history_gen: Optional[HistoryGenerator] = None
        self._event_gen: Optional[EventGenerator] = None
        self._running = False
        
        self._init_components()
    
    def _default_config(self) -> Dict[str, Any]:
        return {
            "server": {
                "port": 6002,
                "enabled": True
            },
            "data": {
                "sensor_count": 10,
                "history_days": 30,
                "data_resolution_ms": 60000
            },
            "generation": {
                "scenario": "normal",
                "compression_ratio": 0.3
            },
            "values": {
                "temperature": {
                    "base": 22.0,
                    "variation": 3.0,
                    "daily_amplitude": 2.0
                },
                "humidity": {
                    "base": 45.0,
                    "variation": 5.0,
                    "daily_amplitude": 10.0
                }
            },
            "events": {
                "include_events": True,
                "event_frequency": 0.01,
                "event_types": ["warning_high_temp", "warning_low_temp", "alarm_high_temp"]
            },
            "gaps": {
                "enabled": False,
                "probability": 0.05,
                "max_duration_minutes": 30
            },
            "per_sensor_overrides": {}
        }
    
    def _init_components(self):
        """Инициализация компонентов"""
        data_cfg = self.config["data"]
        
        history_config = {
            "sensor_count": data_cfg["sensor_count"],
            "history_days": data_cfg["history_days"],
            "data_resolution_ms": data_cfg["data_resolution_ms"],
            "scenario": self.config["generation"]["scenario"],
            "values": self.config["values"],
            "gaps": self.config["gaps"],
            "compression_ratio": self.config["generation"]["compression_ratio"]
        }
        self._history_gen = HistoryGenerator(history_config)
        
        event_config = {
            "sensor_count": data_cfg["sensor_count"],
            "history_days": data_cfg["history_days"],
            **self.config["events"]
        }
        self._event_gen = EventGenerator(event_config)
    
    def start(self):
        """Запустить сервер"""
        self._running = True
    
    def stop(self):
        """Остановить сервер"""
        self._running = False
    
    def get_status(self) -> Dict[str, Any]:
        """Получить статус архива"""
        history_status = self._history_gen.get_status()
        event_status = self._event_gen.get_status()
        
        return {
            "running": self._running,
            "port": self.config["server"]["port"],
            "data": history_status,
            "events": event_status,
            "scenario": self.config["generation"]["scenario"]
        }
    
    def query(
        self,
        sensor_id: int,
        from_time: str,
        to_time: str,
        resolution: str = "minute"
    ) -> Dict[str, Any]:
        """Запрос исторических данных"""
        try:
            from_dt = datetime.fromisoformat(from_time.replace('Z', '+00:00').replace('+00:00', ''))
        except:
            from_dt = datetime.now() - timedelta(days=1)
        
        try:
            to_dt = datetime.fromisoformat(to_time.replace('Z', '+00:00').replace('+00:00', ''))
        except:
            to_dt = datetime.now()
        
        return self._history_gen.query(sensor_id, from_dt, to_dt, resolution)
    
    def get_events(
        self,
        from_time: str = None,
        to_time: str = None,
        sensor_id: int = None,
        event_type: str = None,
        priority: str = None,
        acknowledged: bool = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Получить события"""
        from_dt = None
        to_dt = None
        
        if from_time:
            try:
                from_dt = datetime.fromisoformat(from_time.replace('Z', '+00:00').replace('+00:00', ''))
            except:
                pass
        
        if to_time:
            try:
                to_dt = datetime.fromisoformat(to_time.replace('Z', '+00:00').replace('+00:00', ''))
            except:
                pass
        
        return self._event_gen.get_events(
            from_time=from_dt,
            to_time=to_dt,
            sensor_id=sensor_id,
            event_type=event_type,
            priority=priority,
            acknowledged=acknowledged,
            limit=limit,
            offset=offset
        )
    
    def acknowledge_event(self, event_id: int, user: str = "operator") -> Optional[Dict]:
        """Квитировать событие"""
        return self._event_gen.acknowledge_event(event_id, user)
    
    def cleanup(self, days_to_keep: int = 7) -> Dict[str, Any]:
        """Имитация очистки архива"""
        return {
            "status": "ok",
            "message": f"Simulated cleanup: keeping last {days_to_keep} days",
            "deleted_records": 0
        }
    
    def export_data(
        self,
        sensor_id: int,
        from_time: str,
        to_time: str,
        format: str = "json"
    ) -> Any:
        """Экспорт данных"""
        data = self.query(sensor_id, from_time, to_time, "minute")
        
        if format == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            
            writer.writerow(["timestamp", "temperature", "humidity", "status"])
            
            for point in data.get("data", []):
                writer.writerow([
                    point.get("timestamp"),
                    point.get("temperature"),
                    point.get("humidity"),
                    point.get("status")
                ])
            
            return output.getvalue()
        else:
            return data
    
    def regenerate(self):
        """Перегенерировать все данные"""
        self._history_gen.regenerate()
        self._event_gen.regenerate()
    
    def add_event(self, sensor_id: int, event_type: str, value: float = None) -> Dict:
        """Добавить событие вручную"""
        return self._event_gen.add_event(sensor_id, event_type, value)
    
    def set_sensor_history(self, sensor_id: int, data: list):
        """Установить историю датчика"""
        if sensor_id not in self._history_gen._data_cache:
            self._history_gen._data_cache[sensor_id] = []
        self._history_gen._data_cache[sensor_id].extend(data)
    
    def update_config(self, new_config: Dict[str, Any]):
        """Обновить конфигурацию"""
        self._merge_config(self.config, new_config)
        self._init_components()
    
    def _merge_config(self, base: Dict, update: Dict):
        """Рекурсивное слияние конфигураций"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
