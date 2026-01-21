"""
Базовый класс сценария генерации данных
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class SensorValue:
    """Значение датчика"""
    temperature: float
    humidity: float
    temp_status: str = "normal"
    hum_status: str = "normal"
    combined_status: str = "normal"
    modbus_error: Optional[str] = None


class BaseScenario(ABC):
    """Базовый класс для всех сценариев"""
    
    description = "Base scenario"
    
    def __init__(
        self,
        temp_base: float = 22.0,
        temp_variation: float = 2.0,
        temp_min: float = -40.0,
        temp_max: float = 85.0,
        hum_base: float = 45.0,
        hum_variation: float = 5.0,
        hum_min: float = 0.0,
        hum_max: float = 100.0,
        offline_sensors: list = None,
        **kwargs
    ):
        self.temp_base = temp_base
        self.temp_variation = temp_variation
        self.temp_min = temp_min
        self.temp_max = temp_max
        self.hum_base = hum_base
        self.hum_variation = hum_variation
        self.hum_min = hum_min
        self.hum_max = hum_max
        self.offline_sensors = offline_sensors or []
        
        self._iteration = 0
        self._start_time = None
    
    @abstractmethod
    def get_value(self, sensor_id: int, limits: Dict[str, float]) -> SensorValue:
        """
        Получить значение для датчика
        
        Args:
            sensor_id: ID датчика
            limits: Словарь с лимитами (temp_min, temp_max, hum_min, hum_max, etc.)
        
        Returns:
            SensorValue с температурой, влажностью и статусами
        """
        pass
    
    def _clamp(self, value: float, min_val: float, max_val: float) -> float:
        """Ограничение значения в диапазоне"""
        return max(min_val, min(max_val, value))
    
    def _calculate_status(self, value: float, limit_min: float, limit_max: float, 
                          warning_delta: float, alarm_delta: float) -> str:
        """Вычисление статуса значения"""
        if value < limit_min - alarm_delta or value > limit_max + alarm_delta:
            return "alarm"
        elif value < limit_min - warning_delta or value > limit_max + warning_delta:
            return "warning"
        elif value < limit_min or value > limit_max:
            return "warning"
        return "normal"
    
    def _get_combined_status(self, temp_status: str, hum_status: str) -> str:
        """Определение комбинированного статуса"""
        if temp_status == "alarm" or hum_status == "alarm":
            return "alarm"
        elif temp_status == "warning" or hum_status == "warning":
            return "warning"
        return "normal"
    
    def tick(self):
        """Увеличить счётчик итераций"""
        self._iteration += 1
