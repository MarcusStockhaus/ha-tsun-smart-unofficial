"""Shared entity base."""
from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import TsunCoordinator

# Values of a storage unit the cloud no longer lists (the entity is then unavailable anyway).
_EMPTY_UNIT: dict[str, Any] = {
    "dev": {},
    "logger_signal": None,
    "soc": None,
    "remaining_energy": None,
    "battery_status": None,
}


class TsunEntity(CoordinatorEntity[TsunCoordinator]):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: TsunCoordinator,
        station_id: int,
        description: EntityDescription,
        unit_id: int | None = None,
    ) -> None:
        """unit_id is None for the station's main device, else the cloud device id of a further storage unit."""
        super().__init__(coordinator)
        self.entity_description = description
        self._station_id = station_id
        self._unit_id = unit_id
        self._attr_unique_id = f"{DOMAIN}_{station_id}_{description.key}"
        station = coordinator.data[station_id]
        if unit_id is None:
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, str(station_id))},
                name=f"TSUN {station['name']}",
                manufacturer="TSUN (cloud data, unofficial)",
                model="DCU2000Lite" if station["has_storage"] else "PV station",
            )
        else:
            unit = self._find_unit(station) or {}
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, f"{station_id}_dev{unit_id}")},
                name=f"TSUN {station['name']} storage {unit.get('ordinal', '?')}",
                manufacturer="TSUN (cloud data, unofficial)",
                model="DCU2000Lite",
                via_device=(DOMAIN, str(station_id)),
            )

    def _find_unit(self, station: dict[str, Any]) -> dict[str, Any] | None:
        for unit in station.get("units") or []:
            if unit["device_id"] == self._unit_id:
                return unit
        return None

    @property
    def station(self) -> dict[str, Any]:
        """The data this entity reads: the station, or for a further storage unit that unit's values."""
        data = self.coordinator.data[self._station_id]
        if self._unit_id is None:
            return data
        return self._find_unit(data) or _EMPTY_UNIT

    @property
    def available(self) -> bool:
        if not super().available or self._station_id not in self.coordinator.data:
            return False
        if self._unit_id is None:
            return True
        return self._find_unit(self.coordinator.data[self._station_id]) is not None
