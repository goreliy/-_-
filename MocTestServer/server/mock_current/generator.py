"""
Генератор current.json - эмуляция выхода Modbus Poller
"""

import json
import os
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from ..scenarios import get_scenario
from ..scenarios.base import BaseScenario

# Базовая директория проекта (KVT-C)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATA_DIR = os.path.join(BASE_DIR, 'data')


class CurrentGenerator:
    """Генератор файла current.json"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._default_config()
        self._scenario: Optional[BaseScenario] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._poll_count = 0
        self._successful_polls = 0
        self._failed_polls = 0
        self._last_error = None
        self._current_data: Dict[str, Any] = {}
        self._log_entries: List[Dict] = []
        
        self._init_scenario()
    
    def _default_config(self) -> Dict[str, Any]:
        return {
            "output": {
                "current_path": "../data/current.json",
                "log_path": "../data/modbus_log.json",
                "generate_log": True,
                "log_max_entries": 1000
            },
            "generation": {
                "enabled": True,
                "interval_ms": 1000,
                "scenario": "normal"
            },
            "sensors": {
                "count": 10,
                "name_prefix": "ХРАН. №",
                "modbus_slave_id": 16,
                "start_modbus_addr": 1,
                "value_register_base": 30000,
                "status_register_base": 40000
            },
            "values": {
                "temperature": {
                    "min": -40.0,
                    "max": 85.0,
                    "base": 22.0,
                    "variation": 2.0
                },
                "humidity": {
                    "min": 0.0,
                    "max": 100.0,
                    "base": 45.0,
                    "variation": 5.0
                }
            },
            "limits": {
                "temperature": {
                    "min": -10.0,
                    "max": 40.0,
                    "warning_delta": 3.0,
                    "alarm_delta": 5.0
                },
                "humidity": {
                    "min": 20.0,
                    "max": 80.0,
                    "warning_delta": 5.0,
                    "alarm_delta": 10.0
                }
            },
            "errors": {
                "error_rate": 0.0,
                "offline_sensors": []
            },
            "per_sensor_overrides": {}
        }
    
    def _init_scenario(self):
        """Инициализация сценария на основе конфигурации"""
        scenario_name = self.config["generation"]["scenario"]
        temp_cfg = self.config["values"]["temperature"]
        hum_cfg = self.config["values"]["humidity"]
        
        self._scenario = get_scenario(
            scenario_name,
            temp_base=temp_cfg["base"],
            temp_variation=temp_cfg["variation"],
            temp_min=temp_cfg["min"],
            temp_max=temp_cfg["max"],
            hum_base=hum_cfg["base"],
            hum_variation=hum_cfg["variation"],
            hum_min=hum_cfg["min"],
            hum_max=hum_cfg["max"],
            offline_sensors=self.config["errors"].get("offline_sensors", [])
        )
    
    def _get_limits_dict(self) -> Dict:
        """Конвертация limits в формат для сценария"""
        temp_limits = self.config["limits"]["temperature"]
        hum_limits = self.config["limits"]["humidity"]
        return {
            'temp_min': temp_limits["min"],
            'temp_max': temp_limits["max"],
            'temp_warning_delta': temp_limits["warning_delta"],
            'temp_alarm_delta': temp_limits["alarm_delta"],
            'hum_min': hum_limits["min"],
            'hum_max': hum_limits["max"],
            'hum_warning_delta': hum_limits["warning_delta"],
            'hum_alarm_delta': hum_limits["alarm_delta"],
        }
    
    def _generate_sensor_data(self, sensor_id: int) -> Dict[str, Any]:
        """Генерация данных одного датчика"""
        cfg = self.config["sensors"]
        limits = self._get_limits_dict()
        
        # Проверка на offline
        if sensor_id in self.config["errors"].get("offline_sensors", []):
            return {
                "id": sensor_id,
                "name": f"{cfg['name_prefix']} {sensor_id}",
                "modbus_slave_id": cfg["modbus_slave_id"],
                "modbus_addr_temp": cfg["start_modbus_addr"] + (sensor_id - 1) * 2,
                "modbus_addr_hum": cfg["start_modbus_addr"] + (sensor_id - 1) * 2 + 1,
                "temperature": {
                    "value": None,
                    "raw": None,
                    "status": "offline",
                    "modbus_status": 1,
                    "timestamp": datetime.now().isoformat()
                },
                "humidity": {
                    "value": None,
                    "raw": None,
                    "status": "offline",
                    "modbus_status": 1,
                    "timestamp": datetime.now().isoformat()
                },
                "combined_status": "offline"
            }
        
        # Получение значений из сценария
        value = self._scenario.get_value(sensor_id, limits)
        now = datetime.now()
        
        return {
            "id": sensor_id,
            "name": f"{cfg['name_prefix']} {sensor_id}",
            "modbus_slave_id": cfg["modbus_slave_id"],
            "modbus_addr_temp": cfg["start_modbus_addr"] + (sensor_id - 1) * 2,
            "modbus_addr_hum": cfg["start_modbus_addr"] + (sensor_id - 1) * 2 + 1,
            "temperature": {
                "value": value.temperature,
                "raw": int(value.temperature * 10),
                "status": value.temp_status,
                "modbus_status": 0,
                "timestamp": now.isoformat()
            },
            "humidity": {
                "value": value.humidity,
                "raw": int(value.humidity * 10),
                "status": value.hum_status,
                "modbus_status": 0,
                "timestamp": now.isoformat()
            },
            "combined_status": value.combined_status
        }
    
    def generate_current_json(self) -> Dict[str, Any]:
        """Генерация полного current.json"""
        sensor_count = self.config["sensors"]["count"]
        sensors = []
        
        for sensor_id in range(1, sensor_count + 1):
            sensors.append(self._generate_sensor_data(sensor_id))
        
        self._poll_count += 1
        self._successful_polls += 1
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "poll_period_ms": self.config["generation"]["interval_ms"],
            "com_port": "MOCK",
            "baudrate": 9600,
            "sensors": sensors,
            "statistics": {
                "total_polls": self._poll_count,
                "successful_polls": self._successful_polls,
                "failed_polls": self._failed_polls,
                "last_error": self._last_error
            },
            "_mock": {
                "generator": "mock_current_generator",
                "scenario": self.config["generation"]["scenario"],
                "version": "1.0"
            }
        }
        
        self._current_data = data
        return data
    
    def _generate_log_entries(self, sensor_data: Dict) -> List[Dict]:
        """
        Генерация записей лога Modbus (TX запрос + RX ответ) согласно ТЗ
        Формат: direction, raw_hex, parsed
        """
        import random
        
        entries = []
        now = datetime.now()
        slave_id = sensor_data["modbus_slave_id"]
        addr_temp = sensor_data["modbus_addr_temp"]
        value_register_base = self.config["sensors"].get("value_register_base", 30000)
        status_register_base = self.config["sensors"].get("status_register_base", 40000)
        
        # Адрес регистра значений (30000 + N)
        start_addr_value = value_register_base + (sensor_data["id"] - 1) * 2
        # Адрес регистра статусов (40000 + N)
        start_addr_status = status_register_base + (sensor_data["id"] - 1) * 2
        
        # Генерируем CRC (заглушка)
        def fake_crc():
            return f"{random.randint(0, 255):02X} {random.randint(0, 255):02X}"
        
        # Время ответа
        response_time_ms = round(random.uniform(5, 30), 2)
        
        # === Запрос значений (TX) ===
        tx_time = now
        # Формат: SlaveID FuncCode StartAddrHi StartAddrLo QuantityHi QuantityLo CRC
        tx_raw = f"{slave_id:02X} 04 {(start_addr_value >> 8):02X} {(start_addr_value & 0xFF):02X} 00 02 {fake_crc()}"
        entries.append({
            "timestamp": tx_time.isoformat(),
            "direction": "TX",
            "raw_hex": tx_raw,
            "parsed": {
                "slave_id": slave_id,
                "function": 4,
                "start_addr": start_addr_value,
                "quantity": 2,
                "description": f"Запрос значений датчика {sensor_data['id']}"
            },
            "response_time_ms": None
        })
        
        # === Ответ значений (RX) ===
        rx_time = tx_time + timedelta(milliseconds=random.randint(5, 25))
        
        if sensor_data["combined_status"] == "offline":
            # Нет ответа - таймаут
            entries.append({
                "timestamp": rx_time.isoformat(),
                "direction": "RX",
                "raw_hex": None,
                "parsed": {
                    "error": "timeout",
                    "description": f"Таймаут ответа от датчика {sensor_data['id']}"
                },
                "response_time_ms": response_time_ms
            })
        else:
            temp_raw = sensor_data["temperature"]["raw"] if sensor_data["temperature"]["raw"] else 0
            hum_raw = sensor_data["humidity"]["raw"] if sensor_data["humidity"]["raw"] else 0
            
            # Формат ответа: SlaveID FuncCode ByteCount TempHi TempLo HumHi HumLo CRC
            byte_count = 4
            rx_raw = (f"{slave_id:02X} 04 {byte_count:02X} "
                     f"{(temp_raw >> 8) & 0xFF:02X} {temp_raw & 0xFF:02X} "
                     f"{(hum_raw >> 8) & 0xFF:02X} {hum_raw & 0xFF:02X} "
                     f"{fake_crc()}")
            
            temp_val = sensor_data["temperature"]["value"]
            hum_val = sensor_data["humidity"]["value"]
            
            entries.append({
                "timestamp": rx_time.isoformat(),
                "direction": "RX",
                "raw_hex": rx_raw,
                "parsed": {
                    "slave_id": slave_id,
                    "function": 4,
                    "byte_count": byte_count,
                    "values": [temp_raw, hum_raw],
                    "description": f"Ответ: T={temp_val}°C, H={hum_val}%"
                },
                "response_time_ms": response_time_ms
            })
        
        # === Запрос статусов (TX) ===
        tx_status_time = rx_time + timedelta(milliseconds=random.randint(10, 30))
        tx_status_raw = f"{slave_id:02X} 04 {(start_addr_status >> 8):02X} {(start_addr_status & 0xFF):02X} 00 02 {fake_crc()}"
        entries.append({
            "timestamp": tx_status_time.isoformat(),
            "direction": "TX",
            "raw_hex": tx_status_raw,
            "parsed": {
                "slave_id": slave_id,
                "function": 4,
                "start_addr": start_addr_status,
                "quantity": 2,
                "description": f"Запрос статусов датчика {sensor_data['id']}"
            },
            "response_time_ms": None
        })
        
        # === Ответ статусов (RX) ===
        rx_status_time = tx_status_time + timedelta(milliseconds=random.randint(5, 25))
        response_time_ms_2 = round(random.uniform(5, 30), 2)
        
        if sensor_data["combined_status"] == "offline":
            entries.append({
                "timestamp": rx_status_time.isoformat(),
                "direction": "RX",
                "raw_hex": None,
                "parsed": {
                    "error": "timeout",
                    "description": f"Таймаут ответа статусов от датчика {sensor_data['id']}"
                },
                "response_time_ms": response_time_ms_2
            })
        else:
            temp_status = sensor_data["temperature"]["modbus_status"]
            hum_status = sensor_data["humidity"]["modbus_status"]
            
            rx_status_raw = (f"{slave_id:02X} 04 04 "
                            f"00 {temp_status:02X} 00 {hum_status:02X} "
                            f"{fake_crc()}")
            
            status_desc = "OK" if temp_status == 0 and hum_status == 0 else f"T:{temp_status}, H:{hum_status}"
            
            entries.append({
                "timestamp": rx_status_time.isoformat(),
                "direction": "RX",
                "raw_hex": rx_status_raw,
                "parsed": {
                    "slave_id": slave_id,
                    "function": 4,
                    "byte_count": 4,
                    "values": [temp_status, hum_status],
                    "description": f"Ответ: статусы {status_desc}"
                },
                "response_time_ms": response_time_ms_2
            })
        
        return entries
    
    def _write_files(self, data: Dict):
        """Запись файлов на диск"""
        output_cfg = self.config["output"]
        
        # Создаём DATA_DIR если нет
        os.makedirs(DATA_DIR, exist_ok=True)
        
        # Получаем абсолютные пути
        current_path = os.path.join(DATA_DIR, 'current.json')
        
        # Записываем current.json
        with open(current_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # Генерируем и записываем лог Modbus если включено
        if output_cfg["generate_log"]:
            log_path = os.path.join(DATA_DIR, 'modbus_log.json')
            
            # Добавляем записи в лог (TX + RX для каждого датчика)
            for sensor in data["sensors"]:
                entries = self._generate_log_entries(sensor)
                self._log_entries.extend(entries)
            
            # Ограничиваем размер лога
            max_entries = output_cfg["log_max_entries"]
            if len(self._log_entries) > max_entries:
                self._log_entries = self._log_entries[-max_entries:]
            
            # Формат согласно ТЗ
            with open(log_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "max_entries": max_entries,
                    "entries": self._log_entries
                }, f, ensure_ascii=False, indent=2)
    
    def _generation_loop(self):
        """Основной цикл генерации"""
        interval_sec = self.config["generation"]["interval_ms"] / 1000.0
        
        while self._running:
            try:
                data = self.generate_current_json()
                self._write_files(data)
            except Exception as e:
                self._failed_polls += 1
                self._last_error = str(e)
            
            time.sleep(interval_sec)
    
    def start(self):
        """Запустить генерацию"""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._generation_loop, daemon=True)
        self._thread.start()
    
    def stop(self):
        """Остановить генерацию"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
    
    def generate_once(self) -> Dict[str, Any]:
        """Сгенерировать один раз и записать файлы"""
        data = self.generate_current_json()
        self._write_files(data)
        return data
    
    def get_preview(self) -> Dict[str, Any]:
        """Получить превью следующего current.json без записи"""
        return self.generate_current_json()
    
    def get_status(self) -> Dict[str, Any]:
        """Получить статус генератора"""
        return {
            "running": self._running,
            "scenario": self.config["generation"]["scenario"],
            "interval_ms": self.config["generation"]["interval_ms"],
            "sensor_count": self.config["sensors"]["count"],
            "output_path": DATA_DIR,
            "current_file": os.path.join(DATA_DIR, 'current.json'),
            "log_file": os.path.join(DATA_DIR, 'modbus_log.json'),
            "statistics": {
                "total_polls": self._poll_count,
                "successful_polls": self._successful_polls,
                "failed_polls": self._failed_polls,
                "last_error": self._last_error
            }
        }
    
    def update_config(self, new_config: Dict[str, Any]):
        """Обновить конфигурацию"""
        was_running = self._running
        if was_running:
            self.stop()
        
        # Глубокое слияние конфигураций
        self._merge_config(self.config, new_config)
        self._init_scenario()
        
        if was_running:
            self.start()
    
    def _merge_config(self, base: Dict, update: Dict):
        """Рекурсивное слияние конфигураций"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def set_scenario(self, scenario_name: str):
        """Изменить сценарий"""
        self.config["generation"]["scenario"] = scenario_name
        self._init_scenario()
    
    def set_sensor_value(self, sensor_id: int, temperature: float = None, humidity: float = None):
        """Установить значения датчика вручную (переопределение)"""
        if sensor_id not in self.config["per_sensor_overrides"]:
            self.config["per_sensor_overrides"][sensor_id] = {}
        
        if temperature is not None:
            self.config["per_sensor_overrides"][sensor_id]["temp_base"] = temperature
            self.config["per_sensor_overrides"][sensor_id]["temp_variation"] = 0.1
        
        if humidity is not None:
            self.config["per_sensor_overrides"][sensor_id]["hum_base"] = humidity
            self.config["per_sensor_overrides"][sensor_id]["hum_variation"] = 0.1
