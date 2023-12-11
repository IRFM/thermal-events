from thermal_events.thermal_event_instance import ThermalEventInstance
from thermal_events.crud.base import CRUDBase


class CRUDThermalEventInstance(CRUDBase[ThermalEventInstance]):
    """CRUD operations for ThermalEventInstance objects."""

    pass


thermal_event_instance = CRUDThermalEventInstance(ThermalEventInstance)
