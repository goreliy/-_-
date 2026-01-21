"""
Генератор событий для Mock Archive Server
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional


class EventGenerator:
    """Генератор событий"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._default_config()
        self._events: List[Dict] = []
        self._event_id_counter = 0
        self._generate_events()
    
    def _default_config(self) -> Dict[str, Any]:
        return {
            "sensor_count": 10,
            "history_days": 30,
            "include_events": True,
            "event_frequency": 0.01,
            "event_types": [
                "warning_high_temp",
                "warning_low_temp",
                "alarm_high_temp",
                "alarm_low_temp",
                "warning_high_hum",
                "warning_low_hum",
                "sensor_offline",
                "sensor_online"
            ]
        }
    
    def _generate_events(self):
        """Генерация исторических событий"""
        if not self.config["include_events"]:
            return
        
        end_time = datetime.now()
        start_time = end_time - timedelta(days=self.config["history_days"])
        
        current_time = start_time
        
        while current_time <= end_time:
            for sensor_id in range(1, self.config["sensor_count"] + 1):
                if random.random() < self.config["event_frequency"]:
                    self._create_event(sensor_id, current_time)
            
            current_time += timedelta(hours=1)
    
    def _create_event(self, sensor_id: int, timestamp: datetime, 
                      event_type: str = None, value: float = None) -> Dict:
        """Создание события"""
        self._event_id_counter += 1
        
        if event_type is None:
            event_type = random.choice(self.config["event_types"])
        
        # Генерация значения на основе типа
        if value is None:
            if "high_temp" in event_type:
                value = random.uniform(35, 45)
            elif "low_temp" in event_type:
                value = random.uniform(-15, -5)
            elif "high_hum" in event_type:
                value = random.uniform(75, 95)
            elif "low_hum" in event_type:
                value = random.uniform(5, 20)
            else:
                value = None
        
        # Определение приоритета
        if "alarm" in event_type:
            priority = "high"
        elif "warning" in event_type:
            priority = "medium"
        else:
            priority = "low"
        
        event = {
            "id": self._event_id_counter,
            "timestamp": timestamp.isoformat(),
            "sensor_id": sensor_id,
            "event_type": event_type,
            "priority": priority,
            "value": round(value, 1) if value else None,
            "message": self._generate_message(sensor_id, event_type, value),
            "acknowledged": random.random() < 0.7,
            "acknowledged_by": "operator" if random.random() < 0.7 else None,
            "acknowledged_at": (timestamp + timedelta(minutes=random.randint(5, 60))).isoformat() 
                              if random.random() < 0.7 else None
        }
        
        self._events.append(event)
        return event
    
    def _generate_message(self, sensor_id: int, event_type: str, value: float) -> str:
        """Генерация текста сообщения"""
        messages = {
            "warning_high_temp": f"Датчик {sensor_id}: Высокая температура {value}°C",
            "warning_low_temp": f"Датчик {sensor_id}: Низкая температура {value}°C",
            "alarm_high_temp": f"АВАРИЯ Датчик {sensor_id}: Критически высокая температура {value}°C",
            "alarm_low_temp": f"АВАРИЯ Датчик {sensor_id}: Критически низкая температура {value}°C",
            "warning_high_hum": f"Датчик {sensor_id}: Высокая влажность {value}%",
            "warning_low_hum": f"Датчик {sensor_id}: Низкая влажность {value}%",
            "sensor_offline": f"Датчик {sensor_id}: Потеря связи",
            "sensor_online": f"Датчик {sensor_id}: Связь восстановлена"
        }
        return messages.get(event_type, f"Датчик {sensor_id}: {event_type}")
    
    def get_events(
        self,
        from_time: datetime = None,
        to_time: datetime = None,
        sensor_id: int = None,
        event_type: str = None,
        priority: str = None,
        acknowledged: bool = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Получить события с фильтрацией"""
        filtered = self._events.copy()
        
        if from_time:
            filtered = [e for e in filtered 
                       if datetime.fromisoformat(e["timestamp"]) >= from_time]
        
        if to_time:
            filtered = [e for e in filtered 
                       if datetime.fromisoformat(e["timestamp"]) <= to_time]
        
        if sensor_id:
            filtered = [e for e in filtered if e["sensor_id"] == sensor_id]
        
        if event_type:
            filtered = [e for e in filtered if e["event_type"] == event_type]
        
        if priority:
            filtered = [e for e in filtered if e["priority"] == priority]
        
        if acknowledged is not None:
            filtered = [e for e in filtered if e["acknowledged"] == acknowledged]
        
        # Сортировка по времени (новые первые)
        filtered.sort(key=lambda x: x["timestamp"], reverse=True)
        
        total = len(filtered)
        paginated = filtered[offset:offset + limit]
        
        return {
            "events": paginated,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    
    def acknowledge_event(self, event_id: int, user: str = "operator") -> Optional[Dict]:
        """Квитировать событие"""
        for event in self._events:
            if event["id"] == event_id:
                event["acknowledged"] = True
                event["acknowledged_by"] = user
                event["acknowledged_at"] = datetime.now().isoformat()
                return event
        return None
    
    def add_event(self, sensor_id: int, event_type: str, value: float = None) -> Dict:
        """Добавить событие вручную"""
        return self._create_event(sensor_id, datetime.now(), event_type, value)
    
    def get_status(self) -> Dict[str, Any]:
        """Получить статус"""
        unacknowledged = sum(1 for e in self._events if not e["acknowledged"])
        
        by_priority = {
            "high": sum(1 for e in self._events if e["priority"] == "high"),
            "medium": sum(1 for e in self._events if e["priority"] == "medium"),
            "low": sum(1 for e in self._events if e["priority"] == "low")
        }
        
        return {
            "total_events": len(self._events),
            "unacknowledged": unacknowledged,
            "by_priority": by_priority
        }
    
    def regenerate(self):
        """Перегенерировать события"""
        self._events.clear()
        self._event_id_counter = 0
        self._generate_events()
