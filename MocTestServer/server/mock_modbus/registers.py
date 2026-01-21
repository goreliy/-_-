"""
Виртуальные Modbus регистры
"""

import threading
from typing import Dict, Optional


class VirtualRegisters:
    """Управление виртуальными Modbus регистрами"""
    
    def __init__(self, value_base: int = 30000, status_base: int = 40000, sensor_count: int = 10):
        self.value_base = value_base
        self.status_base = status_base
        self.sensor_count = sensor_count
        
        self._registers: Dict[int, int] = {}
        self._lock = threading.Lock()
        
        # Инициализация регистров
        self._init_registers()
    
    def _init_registers(self):
        """Инициализация регистров значениями по умолчанию"""
        for sensor_id in range(1, self.sensor_count + 1):
            # Регистры значений (температура и влажность)
            temp_addr = self.value_base + (sensor_id - 1) * 2
            hum_addr = self.value_base + (sensor_id - 1) * 2 + 1
            
            self._registers[temp_addr] = 220  # 22.0°C
            self._registers[hum_addr] = 450   # 45.0%
            
            # Регистры статусов
            temp_status_addr = self.status_base + (sensor_id - 1) * 2
            hum_status_addr = self.status_base + (sensor_id - 1) * 2 + 1
            
            self._registers[temp_status_addr] = 0  # OK
            self._registers[hum_status_addr] = 0   # OK
    
    def get_register(self, address: int) -> int:
        """Получить значение регистра"""
        with self._lock:
            return self._registers.get(address, 0)
    
    def set_register(self, address: int, value: int):
        """Установить значение регистра"""
        with self._lock:
            # Ограничение значения 16-битным числом
            self._registers[address] = value & 0xFFFF
    
    def get_registers(self, start_address: int, count: int) -> list:
        """Получить несколько регистров"""
        return [self.get_register(start_address + i) for i in range(count)]
    
    def set_registers(self, start_address: int, values: list):
        """Установить несколько регистров"""
        for i, value in enumerate(values):
            self.set_register(start_address + i, value)
    
    def set_sensor_values(self, sensor_id: int, temperature: float, humidity: float, 
                          temp_status: int = 0, hum_status: int = 0):
        """Установить значения датчика"""
        # Преобразование в raw (умножаем на 10)
        temp_raw = int(temperature * 10) & 0xFFFF
        hum_raw = int(humidity * 10) & 0xFFFF
        
        temp_addr = self.value_base + (sensor_id - 1) * 2
        hum_addr = self.value_base + (sensor_id - 1) * 2 + 1
        temp_status_addr = self.status_base + (sensor_id - 1) * 2
        hum_status_addr = self.status_base + (sensor_id - 1) * 2 + 1
        
        with self._lock:
            self._registers[temp_addr] = temp_raw
            self._registers[hum_addr] = hum_raw
            self._registers[temp_status_addr] = temp_status
            self._registers[hum_status_addr] = hum_status
    
    def get_sensor_values(self, sensor_id: int) -> Dict:
        """Получить значения датчика"""
        temp_addr = self.value_base + (sensor_id - 1) * 2
        hum_addr = self.value_base + (sensor_id - 1) * 2 + 1
        temp_status_addr = self.status_base + (sensor_id - 1) * 2
        hum_status_addr = self.status_base + (sensor_id - 1) * 2 + 1
        
        with self._lock:
            temp_raw = self._registers.get(temp_addr, 0)
            hum_raw = self._registers.get(hum_addr, 0)
            temp_status = self._registers.get(temp_status_addr, 0)
            hum_status = self._registers.get(hum_status_addr, 0)
        
        # Преобразование из raw (делим на 10)
        # Обработка знака для температуры
        if temp_raw > 32767:
            temp_raw = temp_raw - 65536
        
        return {
            "temperature": {
                "value": temp_raw / 10.0,
                "raw": temp_raw,
                "address": temp_addr,
                "status": temp_status
            },
            "humidity": {
                "value": hum_raw / 10.0,
                "raw": hum_raw,
                "address": hum_addr,
                "status": hum_status
            }
        }
    
    def get_all_values(self) -> Dict:
        """Получить значения всех датчиков"""
        result = {}
        for sensor_id in range(1, self.sensor_count + 1):
            result[sensor_id] = self.get_sensor_values(sensor_id)
        return result
