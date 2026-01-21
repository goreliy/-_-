"""
Сценарии ошибок - имитация различных сбоев
"""

import random
from typing import Dict

from .base import BaseScenario, SensorValue


class OfflineScenario(BaseScenario):
    """Все датчики недоступны"""
    
    description = "Все датчики недоступны (имитация потери связи)"
    
    def get_value(self, sensor_id: int, limits: Dict[str, float]) -> SensorValue:
        return SensorValue(
            temperature=0.0,
            humidity=0.0,
            temp_status="offline",
            hum_status="offline",
            combined_status="offline",
            modbus_error="timeout"
        )


class IntermittentScenario(BaseScenario):
    """Периодические сбои связи"""
    
    description = "Периодические сбои связи с датчиками"
    
    def __init__(self, failure_rate: float = 0.2, **kwargs):
        super().__init__(**kwargs)
        self.failure_rate = failure_rate
    
    def get_value(self, sensor_id: int, limits: Dict[str, float]) -> SensorValue:
        # Случайный сбой
        if random.random() < self.failure_rate:
            return SensorValue(
                temperature=0.0,
                humidity=0.0,
                temp_status="offline",
                hum_status="offline",
                combined_status="offline",
                modbus_error="timeout"
            )
        
        # Нормальные значения
        sensor_offset = (sensor_id - 1) * 0.3
        temp = self.temp_base + sensor_offset + random.uniform(-self.temp_variation, self.temp_variation)
        hum = self.hum_base + random.uniform(-self.hum_variation, self.hum_variation)
        
        temp = round(self._clamp(temp, self.temp_min, self.temp_max), 1)
        hum = round(self._clamp(hum, self.hum_min, self.hum_max), 1)
        
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


class TimeoutScenario(BaseScenario):
    """Медленные ответы с таймаутами"""
    
    description = "Медленные ответы от датчиков с частыми таймаутами"
    
    def __init__(self, timeout_rate: float = 0.3, **kwargs):
        super().__init__(**kwargs)
        self.timeout_rate = timeout_rate
    
    def get_value(self, sensor_id: int, limits: Dict[str, float]) -> SensorValue:
        if random.random() < self.timeout_rate:
            return SensorValue(
                temperature=0.0,
                humidity=0.0,
                temp_status="offline",
                hum_status="offline",
                combined_status="offline",
                modbus_error="timeout"
            )
        
        sensor_offset = (sensor_id - 1) * 0.3
        temp = self.temp_base + sensor_offset + random.uniform(-self.temp_variation, self.temp_variation)
        hum = self.hum_base + random.uniform(-self.hum_variation, self.hum_variation)
        
        temp = round(self._clamp(temp, self.temp_min, self.temp_max), 1)
        hum = round(self._clamp(hum, self.hum_min, self.hum_max), 1)
        
        return SensorValue(
            temperature=temp,
            humidity=hum,
            temp_status="normal",
            hum_status="normal",
            combined_status="normal"
        )


class CRCErrorScenario(BaseScenario):
    """Ошибки CRC"""
    
    description = "Частые ошибки контрольной суммы CRC"
    
    def __init__(self, crc_error_rate: float = 0.15, **kwargs):
        super().__init__(**kwargs)
        self.crc_error_rate = crc_error_rate
    
    def get_value(self, sensor_id: int, limits: Dict[str, float]) -> SensorValue:
        if random.random() < self.crc_error_rate:
            return SensorValue(
                temperature=0.0,
                humidity=0.0,
                temp_status="offline",
                hum_status="offline",
                combined_status="offline",
                modbus_error="crc_error"
            )
        
        sensor_offset = (sensor_id - 1) * 0.3
        temp = self.temp_base + sensor_offset + random.uniform(-self.temp_variation, self.temp_variation)
        hum = self.hum_base + random.uniform(-self.hum_variation, self.hum_variation)
        
        temp = round(self._clamp(temp, self.temp_min, self.temp_max), 1)
        hum = round(self._clamp(hum, self.hum_min, self.hum_max), 1)
        
        return SensorValue(
            temperature=temp,
            humidity=hum,
            temp_status="normal",
            hum_status="normal",
            combined_status="normal"
        )


class PartialOfflineScenario(BaseScenario):
    """Часть датчиков недоступна"""
    
    description = "Некоторые датчики недоступны (частичная потеря связи)"
    
    def __init__(self, offline_probability: float = 0.3, **kwargs):
        super().__init__(**kwargs)
        self.offline_probability = offline_probability
        self._offline_sensors = set()
        
        # Случайно выбираем недоступные датчики при инициализации
        for i in range(1, 11):
            if random.random() < offline_probability:
                self._offline_sensors.add(i)
    
    def get_value(self, sensor_id: int, limits: Dict[str, float]) -> SensorValue:
        if sensor_id in self._offline_sensors or sensor_id in self.offline_sensors:
            return SensorValue(
                temperature=0.0,
                humidity=0.0,
                temp_status="offline",
                hum_status="offline",
                combined_status="offline",
                modbus_error="timeout"
            )
        
        sensor_offset = (sensor_id - 1) * 0.3
        temp = self.temp_base + sensor_offset + random.uniform(-self.temp_variation, self.temp_variation)
        hum = self.hum_base + random.uniform(-self.hum_variation, self.hum_variation)
        
        temp = round(self._clamp(temp, self.temp_min, self.temp_max), 1)
        hum = round(self._clamp(hum, self.hum_min, self.hum_max), 1)
        
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
