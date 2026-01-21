"""
Сценарии Drift - плавное изменение значений
"""

import random
from typing import Dict

from .base import BaseScenario, SensorValue


class DriftUpScenario(BaseScenario):
    """Плавное повышение температуры"""
    
    description = "Температура плавно растёт (имитация нагрева)"
    
    def __init__(self, drift_rate: float = 0.1, **kwargs):
        super().__init__(**kwargs)
        self.drift_rate = drift_rate
        self._current_offset = 0.0
    
    def get_value(self, sensor_id: int, limits: Dict[str, float]) -> SensorValue:
        sensor_offset = (sensor_id - 1) * 0.3
        
        # Увеличиваем смещение
        self._current_offset += self.drift_rate
        
        temp = self.temp_base + sensor_offset + self._current_offset
        temp += random.uniform(-self.temp_variation * 0.5, self.temp_variation * 0.5)
        
        hum = self.hum_base - self._current_offset * 0.5  # Влажность падает при росте температуры
        hum += random.uniform(-self.hum_variation, self.hum_variation)
        
        temp = self._clamp(temp, self.temp_min, self.temp_max)
        hum = self._clamp(hum, self.hum_min, self.hum_max)
        
        temp = round(temp, 1)
        hum = round(hum, 1)
        
        temp_status = self._calculate_status(
            temp, limits.get('temp_min', -10), limits.get('temp_max', 40),
            limits.get('temp_warning_delta', 3), limits.get('temp_alarm_delta', 5)
        )
        
        hum_status = self._calculate_status(
            hum, limits.get('hum_min', 20), limits.get('hum_max', 80),
            limits.get('hum_warning_delta', 5), limits.get('hum_alarm_delta', 10)
        )
        
        return SensorValue(
            temperature=temp,
            humidity=hum,
            temp_status=temp_status,
            hum_status=hum_status,
            combined_status=self._get_combined_status(temp_status, hum_status)
        )


class DriftDownScenario(BaseScenario):
    """Плавное понижение температуры"""
    
    description = "Температура плавно падает (имитация охлаждения)"
    
    def __init__(self, drift_rate: float = 0.1, **kwargs):
        super().__init__(**kwargs)
        self.drift_rate = drift_rate
        self._current_offset = 0.0
    
    def get_value(self, sensor_id: int, limits: Dict[str, float]) -> SensorValue:
        sensor_offset = (sensor_id - 1) * 0.3
        
        self._current_offset -= self.drift_rate
        
        temp = self.temp_base + sensor_offset + self._current_offset
        temp += random.uniform(-self.temp_variation * 0.5, self.temp_variation * 0.5)
        
        hum = self.hum_base - self._current_offset * 0.5
        hum += random.uniform(-self.hum_variation, self.hum_variation)
        
        temp = self._clamp(temp, self.temp_min, self.temp_max)
        hum = self._clamp(hum, self.hum_min, self.hum_max)
        
        temp = round(temp, 1)
        hum = round(hum, 1)
        
        temp_status = self._calculate_status(
            temp, limits.get('temp_min', -10), limits.get('temp_max', 40),
            limits.get('temp_warning_delta', 3), limits.get('temp_alarm_delta', 5)
        )
        
        hum_status = self._calculate_status(
            hum, limits.get('hum_min', 20), limits.get('hum_max', 80),
            limits.get('hum_warning_delta', 5), limits.get('hum_alarm_delta', 10)
        )
        
        return SensorValue(
            temperature=temp,
            humidity=hum,
            temp_status=temp_status,
            hum_status=hum_status,
            combined_status=self._get_combined_status(temp_status, hum_status)
        )
