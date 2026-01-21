"""
Сценарий Sine - синусоидальные колебания
"""

import math
import random
from typing import Dict

from .base import BaseScenario, SensorValue


class SineScenario(BaseScenario):
    """Синусоидальные колебания температуры"""
    
    description = "Периодические синусоидальные колебания температуры"
    
    def __init__(self, period: int = 60, amplitude: float = 5.0, **kwargs):
        super().__init__(**kwargs)
        self.period = period  # Период в итерациях
        self.amplitude = amplitude
    
    def get_value(self, sensor_id: int, limits: Dict[str, float]) -> SensorValue:
        sensor_offset = (sensor_id - 1) * 0.3
        
        # Синусоидальное изменение со сдвигом фазы для каждого датчика
        phase_shift = (sensor_id - 1) * (2 * math.pi / 10)
        sine_value = math.sin(2 * math.pi * self._iteration / self.period + phase_shift)
        
        temp = self.temp_base + sensor_offset + self.amplitude * sine_value
        temp += random.uniform(-self.temp_variation * 0.3, self.temp_variation * 0.3)
        
        # Влажность в противофазе
        hum = self.hum_base - (self.amplitude * 2) * sine_value
        hum += random.uniform(-self.hum_variation * 0.5, self.hum_variation * 0.5)
        
        temp = self._clamp(temp, self.temp_min, self.temp_max)
        hum = self._clamp(hum, self.hum_min, self.hum_max)
        
        temp = round(temp, 1)
        hum = round(hum, 1)
        
        self._iteration += 1
        
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
