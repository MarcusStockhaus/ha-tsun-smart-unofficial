"""Binary sensors."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import TsunConfigEntry
from .entity import TsunEntity

ONLINE = BinarySensorEntityDescription(
    key="online",
    translation_key="online",
    device_class=BinarySensorDeviceClass.CONNECTIVITY,
    entity_category=EntityCategory.DIAGNOSTIC,
)


async def async_setup_entry(
    hass: HomeAssistant, entry: TsunConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(TsunOnline(coordinator, sid, ONLINE) for sid in coordinator.data)


class TsunOnline(TsunEntity, BinarySensorEntity):
    """True while the logger reports to the cloud (False at night / low battery)."""

    @property
    def is_on(self) -> bool | None:
        return self.station["online"]
