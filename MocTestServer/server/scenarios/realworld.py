"""
Реальные сценарии - имитация реальных ситуаций
"""

import math
import random
from datetime import datetime
from typing import Dict

from .base import BaseScenario, SensorValue


class DailyCycleScenario(BaseScenario):
    """Суточный цикл температуры"""
    
    description = "Имитация суточного цикла температуры (день/ночь)"
    
    def __init__(self, day_temp: float = 25.0, night_temp: float = 18.0, **kwargs):
        super().__init__(**kwargs)
        self.day_temp = day_temp
        self.night_temp = night_temp
    
    def get_value(self, sensor_id: int, limits: Dict[str, float]) -> SensorValue:
        now = datetime.now()
        hour = now.hour + now.minute / 60.0
        
        # Синусоида с пиком в 14:00
        daily_factor = math.sin((hour - 8) * math.pi / 12)
        
        temp_amplitude = (self.day_temp - self.night_temp) / 2
        temp_center = (self.day_temp + self.night_temp) / 2
        
        sensor_offset = (sensor_id - 1) * 0.2
        temp = temp_center + temp_amplitude * daily_factor + sensor_offset
        temp += random.uniform(-1, 1)
        
        # Влажность обратно пропорциональна
        hum = self.hum_base - 10 * daily_factor
        hum += random.uniform(-self.hum_variation, self.hum_variation)
        
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


class HVACControlScenario(BaseScenario):
    """Имитация работы HVAC системы"""
    
    description = "Имитация работы системы кондиционирования (вкл/выкл)"
    
    def __init__(self, setpoint: float = 22.0, hysteresis: float = 1.0, **kwargs):
        super().__init__(**kwargs)
        self.setpoint = setpoint
        self.hysteresis = hysteresis
        self._hvac_on = False
        self._current_temp = setpoint
    
    def get_value(self, sensor_id: int, limits: Dict[str, float]) -> SensorValue:
        # Логика HVAC
        if self._current_temp > self.setpoint + self.hysteresis:
            self._hvac_on = True
        elif self._current_temp < self.setpoint - self.hysteresis:
            self._hvac_on = False
        
        # Изменение температуры
        if self._hvac_on:
            self._current_temp -= random.uniform(0.1, 0.3)
        else:
            self._current_temp += random.uniform(0.05, 0.15)
        
        sensor_offset = (sensor_id - 1) * 0.1
        temp = self._current_temp + sensor_offset + random.uniform(-0.3, 0.3)
        
        hum = self.hum_base + (5 if self._hvac_on else -2)
        hum += random.uniform(-self.hum_variation * 0.5, self.hum_variation * 0.5)
        
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


class DoorOpenScenario(BaseScenario):
    """Имитация открытия двери"""
    
    description = "Периодическое открытие двери (резкие изменения)"
    
    def __init__(self, open_probability: float = 0.1, outside_temp: float = 35.0, **kwargs):
        super().__init__(**kwargs)
        self.open_probability = open_probability
        self.outside_temp = outside_temp
        self._door_open = False
        self._door_timer = 0
    
    def get_value(self, sensor_id: int, limits: Dict[str, float]) -> SensorValue:
        # Случайное открытие двери
        if not self._door_open and random.random() < self.open_probability:
            self._door_open = True
            self._door_timer = random.randint(5, 15)
        
        if self._door_open:
            self._door_timer -= 1
            if self._door_timer <= 0:
                self._door_open = False
        
        sensor_offset = (sensor_id - 1) * 0.3
        
        if self._door_open:
            # Температура стремится к наружной
            temp = self.temp_base + (self.outside_temp - self.temp_base) * 0.3
            temp += random.uniform(-2, 2)
            hum = self.hum_base + random.uniform(-10, 10)
        else:
            temp = self.temp_base + sensor_offset
            temp += random.uniform(-self.temp_variation, self.temp_variation)
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


class PowerOutageScenario(BaseScenario):
    """Имитация отключения питания"""
    
    description = "Отключение питания с последующим восстановлением"
    
    def __init__(self, outage_probability: float = 0.05, **kwargs):
        super().__init__(**kwargs)
        self.outage_probability = outage_probability
        self._power_off = False
        self._outage_timer = 0
    
    def get_value(self, sensor_id: int, limits: Dict[str, float]) -> SensorValue:
        # Случайное отключение
        if not self._power_off and random.random() < self.outage_probability:
            self._power_off = True
            self._outage_timer = random.randint(10, 30)
        
        if self._power_off:
            self._outage_timer -= 1
            if self._outage_timer <= 0:
                self._power_off = False
            
            return SensorValue(
                temperature=0.0,
                humidity=0.0,
                temp_status="offline",
                hum_status="offline",
                combined_status="offline",
                modbus_error="no_power"
            )
        
        # Нормальная работа
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


class SensorFailureScenario(BaseScenario):
    """Имитация выхода датчика из строя"""
    
    description = "Постепенный выход датчиков из строя"
    
    def __init__(self, failure_rate: float = 0.01, **kwargs):
        super().__init__(**kwargs)
        self.failure_rate = failure_rate
        self._failed_sensors = set()
    
    def get_value(self, sensor_id: int, limits: Dict[str, float]) -> SensorValue:
        # Случайный выход из строя
        if sensor_id not in self._failed_sensors:
            if random.random() < self.failure_rate:
                self._failed_sensors.add(sensor_id)
        
        if sensor_id in self._failed_sensors:
            # Датчик сломан - показывает случайный мусор или не отвечает
            if random.random() < 0.5:
                return SensorValue(
                    temperature=0.0,
                    humidity=0.0,
                    temp_status="offline",
                    hum_status="offline",
                    combined_status="offline",
                    modbus_error="sensor_failure"
                )
            else:
                # "Мусорные" данные
                return SensorValue(
                    temperature=round(random.uniform(-40, 85), 1),
                    humidity=round(random.uniform(0, 100), 1),
                    temp_status="alarm",
                    hum_status="alarm",
                    combined_status="alarm",
                    modbus_error="invalid_data"
                )
        
        # Нормальная работа
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
