"""Sensors."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfEnergy, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import TsunConfigEntry
from .entity import TsunEntity


@dataclass(frozen=True, kw_only=True)
class TsunSensorDescription(SensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], Any]


SENSORS: tuple[TsunSensorDescription, ...] = (
    TsunSensorDescription(
        key="soc",
        translation_key="soc",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d["soc"],
    ),
    TsunSensorDescription(
        key="battery_power",
        translation_key="battery_power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d["battery_power"],
    ),
    TsunSensorDescription(
        key="remaining_energy",
        translation_key="remaining_energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY_STORAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d["remaining_energy"],
    ),
    TsunSensorDescription(
        key="pv_power",
        translation_key="pv_power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d["pv_power"],
    ),
    TsunSensorDescription(
        key="pv_today",
        translation_key="pv_today",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda d: d["pv_today"],
    ),
    TsunSensorDescription(
        key="charge_today",
        translation_key="charge_today",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda d: d["charge_today"],
    ),
    TsunSensorDescription(
        key="discharge_today",
        translation_key="discharge_today",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda d: d["discharge_today"],
    ),
    TsunSensorDescription(
        key="battery_status",
        translation_key="battery_status",
        value_fn=lambda d: (d["battery_status"] or "").lower() or None,
    ),
    TsunSensorDescription(
        key="network_status",
        translation_key="network_status",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: (d["network_status"] or "").lower() or None,
    ),
    TsunSensorDescription(
        key="last_update",
        translation_key="last_update",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d["last_update"],
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: TsunConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        TsunSensor(coordinator, station_id, description)
        for station_id in coordinator.data
        for description in SENSORS
    )


class TsunSensor(TsunEntity, SensorEntity):
    entity_description: TsunSensorDescription

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self.station)
