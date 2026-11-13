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
        self,
        coordinator: TsunCoordinator,
        station_id: int,
        description: EntityDescription,
        unit_index: int | None = None,
    ) -> None:
        """unit_index is None for the station's main device, 0 for its second storage unit, 1 for the third, ..."""
        super().__init__(coordinator)
        self.entity_description = description
        self._station_id = station_id
        self._unit_index = unit_index
        self._attr_unique_id = f"{DOMAIN}_{station_id}_{description.key}"
        station = coordinator.data[station_id]
        if unit_index is None:
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, str(station_id))},
                name=f"TSUN {station['name']}",
                manufacturer="TSUN (cloud data, unofficial)",
                model="DCU2000Lite" if station["has_storage"] else "PV station",
            )
        else:
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, f"{station_id}_unit{unit_index + 2}")},
                name=f"TSUN {station['name']} storage {unit_index + 2}",
                manufacturer="TSUN (cloud data, unofficial)",
                model="DCU2000Lite",
                via_device=(DOMAIN, str(station_id)),
            )

    @property
    def station(self) -> dict[str, Any]:
        """The data this entity reads: the station, or for an extra storage unit that unit's values."""
        data = self.coordinator.data[self._station_id]
        if self._unit_index is None:
            return data
        return data["units"][self._unit_index]

    @property
    def available(self) -> bool:
        if not super().available or self._station_id not in self.coordinator.data:
            return False
        if self._unit_index is None:
            return True
        return self._unit_index < len(self.coordinator.data[self._station_id]["units"])
