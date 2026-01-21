"""
Сценарий Normal - стабильные значения с небольшими колебаниями
"""

import random
from typing import Dict

from .base import BaseScenario, SensorValue


class NormalScenario(BaseScenario):
    """Нормальное поведение - стабильные значения"""
    
    description = "Стабильные значения с небольшими случайными колебаниями"
    
    def get_value(self, sensor_id: int, limits: Dict[str, float]) -> SensorValue:
        # Небольшое смещение для каждого датчика
        sensor_offset = (sensor_id - 1) * 0.3
        
        # Генерация значений
        temp = self.temp_base + sensor_offset + random.uniform(-self.temp_variation, self.temp_variation)
        hum = self.hum_base + random.uniform(-self.hum_variation, self.hum_variation)
        
        # Ограничение
        temp = self._clamp(temp, self.temp_min, self.temp_max)
        hum = self._clamp(hum, self.hum_min, self.hum_max)
        
        # Округление
        temp = round(temp, 1)
        hum = round(hum, 1)
        
        # Статусы
        temp_status = self._calculate_status(
            temp,
            limits.get('temp_min', -10),
            limits.get('temp_max', 40),
            limits.get('temp_warning_delta', 3),
            limits.get('temp_alarm_delta', 5)
        )
        
        hum_status = self._calculate_status(
            hum,
            limits.get('hum_min', 20),
            limits.get('hum_max', 80),
            limits.get('hum_warning_delta', 5),
            limits.get('hum_alarm_delta', 10)
        )
        
        return SensorValue(
            temperature=temp,
            humidity=hum,
            temp_status=temp_status,
            hum_status=hum_status,
            combined_status=self._get_combined_status(temp_status, hum_status)
        )
