"""
Modbus RTU Server - эмуляция Modbus RTU устройств через TCP
"""

import logging
import threading
import random
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from collections import deque

from pymodbus.server import StartTcpServer, ServerStop
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.datastore.store import ModbusSequentialDataBlock

from .registers import VirtualRegisters
from .generator import RegisterGenerator

logger = logging.getLogger(__name__)


class ModbusRequestLog:
    """Лог Modbus запросов и ответов"""
    
    def __init__(self, max_entries: int = 1000):
        self.max_entries = max_entries
        self._entries: deque = deque(maxlen=max_entries)
        self._lock = threading.Lock()
        self._pending_requests: Dict[str, Dict] = {}
    
    def log_request(self, slave_id: int, function: int, address: int, count: int) -> str:
        """Логирование запроса (TX) и возврат ID для отслеживания"""
        request_id = f"{time.time_ns()}"
        timestamp = datetime.now()
        
        # Формируем raw_hex для запроса
        raw_hex = (f"{slave_id:02X} {function:02X} "
                   f"{(address >> 8) & 0xFF:02X} {address & 0xFF:02X} "
                   f"{(count >> 8) & 0xFF:02X} {count & 0xFF:02X} "
                   f"{random.randint(0,255):02X} {random.randint(0,255):02X}")
        
        # Определяем тип регистров
        if address >= 40000:
            reg_type = "статусов"
            sensor_num = ((address - 40000) // 2) + 1
        elif address >= 30000:
            reg_type = "значений"
            sensor_num = ((address - 30000) // 2) + 1
        else:
            reg_type = "регистров"
            sensor_num = (address // 2) + 1
        
        entry = {
            "request_id": request_id,
            "timestamp": timestamp.isoformat(),
            "direction": "TX",
            "raw_hex": raw_hex,
            "parsed": {
                "slave_id": slave_id,
                "function": function,
                "start_addr": address,
                "quantity": count,
                "description": f"Запрос {reg_type} датчика {sensor_num}"
            },
            "response_time_ms": None
        }
        
        with self._lock:
            self._entries.append(entry)
            self._pending_requests[request_id] = {
                "start_time": time.perf_counter(),
                "entry_index": len(self._entries) - 1
            }
        
        return request_id
    
    def log_response(self, request_id: str, slave_id: int, function: int, 
                     values: List[int], address: int):
        """Логирование ответа (RX) с временем ответа"""
        timestamp = datetime.now()
        response_time_ms = None
        
        with self._lock:
            if request_id in self._pending_requests:
                start_time = self._pending_requests[request_id]["start_time"]
                response_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
                del self._pending_requests[request_id]
        
        # Формируем raw_hex для ответа
        byte_count = len(values) * 2
        values_hex = " ".join(f"{(v >> 8) & 0xFF:02X} {v & 0xFF:02X}" for v in values)
        raw_hex = (f"{slave_id:02X} {function:02X} {byte_count:02X} "
                   f"{values_hex} "
                   f"{random.randint(0,255):02X} {random.randint(0,255):02X}")
        
        # Интерпретация значений
        if address >= 40000:
            status_desc = []
            for i, v in enumerate(values):
                status_desc.append("OK" if v == 0 else f"ERR:{v}")
            description = f"Ответ: статусы [{', '.join(status_desc)}]"
        elif address >= 30000:
            desc_parts = []
            for i in range(0, len(values), 2):
                if i < len(values):
                    temp_raw = values[i] if values[i] < 32768 else values[i] - 65536
                    temp = temp_raw / 10.0
                    desc_parts.append(f"T={temp}°C")
                if i + 1 < len(values):
                    hum = values[i + 1] / 10.0
                    desc_parts.append(f"H={hum}%")
            description = f"Ответ: {', '.join(desc_parts)}"
        else:
            description = f"Ответ: {values}"
        
        entry = {
            "timestamp": timestamp.isoformat(),
            "direction": "RX",
            "raw_hex": raw_hex,
            "parsed": {
                "slave_id": slave_id,
                "function": function,
                "byte_count": byte_count,
                "values": values,
                "description": description
            },
            "response_time_ms": response_time_ms
        }
        
        with self._lock:
            self._entries.append(entry)
    
    def log_error(self, request_id: str, slave_id: int, error_type: str, description: str):
        """Логирование ошибки"""
        timestamp = datetime.now()
        response_time_ms = None
        
        with self._lock:
            if request_id in self._pending_requests:
                start_time = self._pending_requests[request_id]["start_time"]
                response_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
                del self._pending_requests[request_id]
        
        entry = {
            "timestamp": timestamp.isoformat(),
            "direction": "RX",
            "raw_hex": None,
            "parsed": {
                "slave_id": slave_id,
                "error": error_type,
                "description": description
            },
            "response_time_ms": response_time_ms
        }
        
        with self._lock:
            self._entries.append(entry)
    
    def get_entries(self, limit: int = 100) -> List[Dict]:
        """Получить последние записи лога"""
        with self._lock:
            entries = list(self._entries)
        return entries[-limit:] if len(entries) > limit else entries
    
    def get_statistics(self) -> Dict:
        """Получить статистику"""
        with self._lock:
            entries = list(self._entries)
        
        tx_count = sum(1 for e in entries if e["direction"] == "TX")
        rx_count = sum(1 for e in entries if e["direction"] == "RX")
        errors = sum(1 for e in entries if e["direction"] == "RX" and e.get("parsed", {}).get("error"))
        
        response_times = [e["response_time_ms"] for e in entries 
                         if e["response_time_ms"] is not None]
        
        return {
            "total_entries": len(entries),
            "tx_count": tx_count,
            "rx_count": rx_count,
            "error_count": errors,
            "avg_response_time_ms": round(sum(response_times) / len(response_times), 2) if response_times else 0,
            "min_response_time_ms": min(response_times) if response_times else 0,
            "max_response_time_ms": max(response_times) if response_times else 0
        }
    
    def clear(self):
        """Очистить лог"""
        with self._lock:
            self._entries.clear()
            self._pending_requests.clear()


class LoggingDataBlock(ModbusSequentialDataBlock):
    """Кастомный блок данных с логированием запросов"""
    
    def __init__(self, registers: VirtualRegisters, base_address: int, 
                 request_log: ModbusRequestLog, unit_id: int, is_status: bool = False):
        self.virtual_registers = registers
        self.base_address = base_address
        self.request_log = request_log
        self.unit_id = unit_id
        self.is_status = is_status
        super().__init__(0, [0] * 65536)
    
    def getValues(self, address, count=1):
        """Получение значений из виртуальных регистров с логированием"""
        actual_address = self.base_address + address
        
        # Логируем запрос
        request_id = self.request_log.log_request(
            slave_id=self.unit_id,
            function=4 if not self.is_status else 3,
            address=actual_address,
            count=count
        )
        
        # Имитация задержки ответа (5-30 мс)
        delay_ms = random.uniform(5, 30)
        time.sleep(delay_ms / 1000.0)
        
        # Получаем значения
        result = []
        for i in range(count):
            addr = actual_address + i
            val = self.virtual_registers.get_register(addr)
            result.append(val)
        
        # Логируем ответ
        self.request_log.log_response(
            request_id=request_id,
            slave_id=self.unit_id,
            function=4 if not self.is_status else 3,
            values=result,
            address=actual_address
        )
        
        return result
    
    def setValues(self, address, values):
        """Установка значений в виртуальные регистры"""
        for i, val in enumerate(values):
            addr = self.base_address + address + i
            self.virtual_registers.set_register(addr, val)


class ModbusServer:
    """Modbus RTU Server (эмулирует через TCP)"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._default_config()
        
        self._registers: Optional[VirtualRegisters] = None
        self._generator: Optional[RegisterGenerator] = None
        self._request_log: Optional[ModbusRequestLog] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._server_context = None
        
        self._init_components()
    
    def _default_config(self) -> Dict[str, Any]:
        return {
            "server": {
                "port": 5020,
                "unit_id": 16,
                "enabled": True
            },
            "sensors": {
                "count": 10,
                "value_register_base": 30000,
                "status_register_base": 40000
            },
            "generation": {
                "update_interval_ms": 1000,
                "scenario": "normal"
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
            "errors": {
                "error_rate": 0.0,
                "timeout_rate": 0.0,
                "crc_error_rate": 0.0,
                "offline_sensors": []
            },
            "log": {
                "max_entries": 1000
            },
            "per_sensor_overrides": {}
        }
    
    def _init_components(self):
        """Инициализация компонентов сервера"""
        sensors_cfg = self.config["sensors"]
        log_cfg = self.config.get("log", {"max_entries": 1000})
        
        # Создаём лог запросов
        self._request_log = ModbusRequestLog(max_entries=log_cfg.get("max_entries", 1000))
        
        # Создаём виртуальные регистры
        self._registers = VirtualRegisters(
            value_base=sensors_cfg["value_register_base"],
            status_base=sensors_cfg["status_register_base"],
            sensor_count=sensors_cfg["count"]
        )
        
        # Создаём генератор значений
        gen_config = {
            "update_interval_ms": self.config["generation"]["update_interval_ms"],
            "scenario": self.config["generation"]["scenario"],
            "values": self.config["values"],
            "errors": self.config["errors"],
            "per_sensor_overrides": self.config.get("per_sensor_overrides", {})
        }
        self._generator = RegisterGenerator(self._registers, gen_config)
    
    def _create_server_context(self):
        """Создание контекста Modbus сервера"""
        sensors_cfg = self.config["sensors"]
        unit_id = self.config["server"]["unit_id"]
        
        # Создаём блоки данных с логированием
        ir_block = LoggingDataBlock(
            self._registers, 
            sensors_cfg["value_register_base"],
            self._request_log,
            unit_id,
            is_status=False
        )
        
        hr_block = LoggingDataBlock(
            self._registers,
            sensors_cfg["status_register_base"],
            self._request_log,
            unit_id,
            is_status=True
        )
        
        slave_context = ModbusSlaveContext(
            di=ModbusSequentialDataBlock(0, [0] * 100),
            co=ModbusSequentialDataBlock(0, [0] * 100),
            hr=hr_block,
            ir=ir_block
        )
        
        self._server_context = ModbusServerContext(
            slaves={unit_id: slave_context},
            single=False
        )
        
        return self._server_context
    
    def _run_server(self):
        """Запуск Modbus TCP сервера в отдельном потоке"""
        port = self.config["server"]["port"]
        
        logger.info(f"Starting Modbus TCP server on port {port}")
        
        try:
            context = self._create_server_context()
            StartTcpServer(
                context=context,
                address=("0.0.0.0", port)
            )
        except Exception as e:
            logger.error(f"Modbus server error: {e}")
            self._running = False
    
    def start(self):
        """Запустить сервер"""
        if self._running:
            return
        
        self._running = True
        
        # Запускаем генератор значений
        self._generator.start()
        
        # Запускаем Modbus сервер в отдельном потоке
        self._thread = threading.Thread(target=self._run_server, daemon=True)
        self._thread.start()
        
        logger.info("Modbus server started")
    
    def stop(self):
        """Остановить сервер"""
        self._running = False
        
        # Останавливаем генератор
        self._generator.stop()
        
        # Останавливаем сервер
        try:
            ServerStop()
        except:
            pass
        
        logger.info("Modbus server stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Получить статус сервера"""
        log_stats = self._request_log.get_statistics() if self._request_log else {}
        
        return {
            "running": self._running,
            "port": self.config["server"]["port"],
            "unit_id": self.config["server"]["unit_id"],
            "sensor_count": self.config["sensors"]["count"],
            "scenario": self.config["generation"]["scenario"],
            "update_interval_ms": self.config["generation"]["update_interval_ms"],
            "log_statistics": log_stats
        }
    
    def get_registers(self) -> Dict:
        """Получить текущие значения регистров"""
        return self._registers.get_all_values()
    
    def get_request_log(self, limit: int = 100) -> Dict:
        """Получить лог Modbus запросов"""
        if not self._request_log:
            return {"max_entries": 0, "entries": [], "statistics": {}}
        
        return {
            "max_entries": self._request_log.max_entries,
            "entries": self._request_log.get_entries(limit),
            "statistics": self._request_log.get_statistics()
        }
    
    def clear_request_log(self):
        """Очистить лог запросов"""
        if self._request_log:
            self._request_log.clear()
    
    def update_config(self, new_config: Dict[str, Any]):
        """Обновить конфигурацию"""
        was_running = self._running
        if was_running:
            self.stop()
        
        self._merge_config(self.config, new_config)
        self._init_components()
        
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
        self._generator.set_scenario(scenario_name)
    
    def set_value(self, address: int, value: int):
        """Установить значение регистра вручную"""
        self._registers.set_register(address, value)
