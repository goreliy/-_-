"""
Генератор исторических данных для Mock Archive Server
"""

import random
import math
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional


class HistoryGenerator:
    """Генератор исторических данных"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._default_config()
        self._data_cache: Dict[int, List[Dict]] = {}
        self._generate_history()
    
    def _default_config(self) -> Dict[str, Any]:
        return {
            "sensor_count": 10,
            "history_days": 30,
            "data_resolution_ms": 60000,
            "scenario": "normal",
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
            "gaps": {
                "enabled": False,
                "probability": 0.05,
                "max_duration_minutes": 30
            },
            "compression_ratio": 0.3
        }
    
    def _generate_history(self):
        """Генерация исторических данных для всех датчиков"""
        sensor_count = self.config["sensor_count"]
        history_days = self.config["history_days"]
        resolution_ms = self.config["data_resolution_ms"]
        
        end_time = datetime.now()
        start_time = end_time - timedelta(days=history_days)
        
        interval = timedelta(milliseconds=resolution_ms)
        
        for sensor_id in range(1, sensor_count + 1):
            self._data_cache[sensor_id] = []
            current_time = start_time
            
            sensor_offset = (sensor_id - 1) * 0.5
            
            while current_time <= end_time:
                if self.config["gaps"]["enabled"]:
                    if random.random() < self.config["gaps"]["probability"]:
                        gap_minutes = random.randint(1, self.config["gaps"]["max_duration_minutes"])
                        current_time += timedelta(minutes=gap_minutes)
                        continue
                
                hour = current_time.hour + current_time.minute / 60.0
                daily_factor = math.sin((hour - 6) * math.pi / 12)
                
                temp_cfg = self.config["values"]["temperature"]
                hum_cfg = self.config["values"]["humidity"]
                
                temp_base = temp_cfg["base"] + sensor_offset
                temp = temp_base + temp_cfg["daily_amplitude"] * daily_factor
                temp += random.uniform(-temp_cfg["variation"], temp_cfg["variation"])
                
                hum_base = hum_cfg["base"]
                hum = hum_base - hum_cfg["daily_amplitude"] * daily_factor
                hum += random.uniform(-hum_cfg["variation"], hum_cfg["variation"])
                
                temp = max(-40, min(85, temp))
                hum = max(0, min(100, hum))
                
                self._data_cache[sensor_id].append({
                    "timestamp": current_time.isoformat(),
                    "temperature": round(temp, 1),
                    "humidity": round(hum, 1),
                    "status": "normal"
                })
                
                current_time += interval
    
    def query(
        self,
        sensor_id: int,
        from_time: datetime,
        to_time: datetime,
        resolution: str = "minute"
    ) -> Dict[str, Any]:
        """Запрос данных с агрегацией"""
        if sensor_id not in self._data_cache:
            return {"error": "Sensor not found", "data": []}
        
        filtered = []
        for point in self._data_cache[sensor_id]:
            ts = datetime.fromisoformat(point["timestamp"])
            if from_time <= ts <= to_time:
                filtered.append(point)
        
        if resolution == "minute":
            aggregated = filtered
        elif resolution == "hour":
            aggregated = self._aggregate_by_hour(filtered)
        elif resolution == "day":
            aggregated = self._aggregate_by_day(filtered)
        else:
            aggregated = filtered
        
        return {
            "sensor_id": sensor_id,
            "from": from_time.isoformat(),
            "to": to_time.isoformat(),
            "resolution": resolution,
            "data": aggregated,
            "_mock": {
                "generated": True,
                "scenario": self.config["scenario"]
            }
        }
    
    def _aggregate_by_hour(self, data: List[Dict]) -> List[Dict]:
        """Агрегация по часам"""
        if not data:
            return []
        
        hourly: Dict[str, List[Dict]] = {}
        
        for point in data:
            ts = datetime.fromisoformat(point["timestamp"])
            hour_key = ts.strftime("%Y-%m-%dT%H:00:00")
            
            if hour_key not in hourly:
                hourly[hour_key] = []
            hourly[hour_key].append(point)
        
        result = []
        for hour_key, points in sorted(hourly.items()):
            temps = [p["temperature"] for p in points]
            hums = [p["humidity"] for p in points]
            
            result.append({
                "timestamp": hour_key,
                "temperature": {
                    "avg": round(sum(temps) / len(temps), 1),
                    "min": round(min(temps), 1),
                    "max": round(max(temps), 1)
                },
                "humidity": {
                    "avg": round(sum(hums) / len(hums), 1),
                    "min": round(min(hums), 1),
                    "max": round(max(hums), 1)
                },
                "status": "normal",
                "sample_count": len(points)
            })
        
        return result
    
    def _aggregate_by_day(self, data: List[Dict]) -> List[Dict]:
        """Агрегация по дням"""
        if not data:
            return []
        
        daily: Dict[str, List[Dict]] = {}
        
        for point in data:
            ts = datetime.fromisoformat(point["timestamp"])
            day_key = ts.strftime("%Y-%m-%dT00:00:00")
            
            if day_key not in daily:
                daily[day_key] = []
            daily[day_key].append(point)
        
        result = []
        for day_key, points in sorted(daily.items()):
            temps = [p["temperature"] for p in points]
            hums = [p["humidity"] for p in points]
            
            result.append({
                "timestamp": day_key,
                "temperature": {
                    "avg": round(sum(temps) / len(temps), 1),
                    "min": round(min(temps), 1),
                    "max": round(max(temps), 1)
                },
                "humidity": {
                    "avg": round(sum(hums) / len(hums), 1),
                    "min": round(min(hums), 1),
                    "max": round(max(hums), 1)
                },
                "status": "normal",
                "sample_count": len(points)
            })
        
        return result
    
    def get_status(self) -> Dict[str, Any]:
        """Получить статус хранилища"""
        total_records = sum(len(data) for data in self._data_cache.values())
        
        return {
            "sensor_count": len(self._data_cache),
            "total_records": total_records,
            "history_days": self.config["history_days"],
            "resolution_ms": self.config["data_resolution_ms"],
            "memory_usage_mb": round(total_records * 100 / 1024 / 1024, 2)
        }
    
    def regenerate(self):
        """Перегенерировать данные"""
        self._data_cache.clear()
        self._generate_history()
    
    def update_config(self, new_config: Dict[str, Any]):
        """Обновить конфигурацию и перегенерировать данные"""
        self._merge_config(self.config, new_config)
        self.regenerate()
    
    def _merge_config(self, base: Dict, update: Dict):
        """Рекурсивное слияние конфигураций"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
