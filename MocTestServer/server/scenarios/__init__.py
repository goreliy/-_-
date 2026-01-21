"""
Сценарии генерации данных
"""

from .base import BaseScenario
from .normal import NormalScenario
from .drift import DriftUpScenario, DriftDownScenario
from .sine import SineScenario
from .errors import OfflineScenario, IntermittentScenario, TimeoutScenario, CRCErrorScenario, PartialOfflineScenario
from .realworld import DailyCycleScenario, HVACControlScenario, DoorOpenScenario, PowerOutageScenario, SensorFailureScenario

SCENARIOS = {
    'normal': NormalScenario,
    'drift_up': DriftUpScenario,
    'drift_down': DriftDownScenario,
    'sine': SineScenario,
    'offline': OfflineScenario,
    'intermittent': IntermittentScenario,
    'timeout': TimeoutScenario,
    'crc_error': CRCErrorScenario,
    'partial_offline': PartialOfflineScenario,
    'daily_cycle': DailyCycleScenario,
    'hvac_control': HVACControlScenario,
    'door_open': DoorOpenScenario,
    'power_outage': PowerOutageScenario,
    'sensor_failure': SensorFailureScenario,
}


def get_scenario(name: str, **kwargs) -> BaseScenario:
    """Получить экземпляр сценария по имени"""
    scenario_class = SCENARIOS.get(name, NormalScenario)
    return scenario_class(**kwargs)
