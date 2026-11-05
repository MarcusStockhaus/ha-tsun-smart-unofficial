"""Shared entity base."""
from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import TsunCoordinator


class TsunEntity(CoordinatorEntity[TsunCoordinator]):
    _attr_has_entity_name = True

    def __init__(
        self, coordinator: TsunCoordinator, station_id: int, description: EntityDescription
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._station_id = station_id
        self._attr_unique_id = f"{DOMAIN}_{station_id}_{description.key}"
        station = coordinator.data[station_id]
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(station_id))},
            name=f"TSUN {station['name']}",
            manufacturer="TSUN (cloud data, unofficial)",
            model="DCU2000Lite" if station["has_storage"] else "PV station",
        )

    @property
    def station(self) -> dict[str, Any]:
        return self.coordinator.data[self._station_id]

    @property
    def available(self) -> bool:
        return super().available and self._station_id in self.coordinator.data
