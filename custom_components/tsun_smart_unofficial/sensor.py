"""Sensors."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import TsunConfigEntry
from .entity import TsunEntity


@dataclass(frozen=True, kw_only=True)
class TsunSensorDescription(SensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], Any]
    # Optional sensors are only created if the cloud delivers a value for them (not every system has every part).
    optional: bool = False
    exists_fn: Callable[[dict[str, Any]], bool] | None = None


def _dev(key: str) -> Callable[[dict[str, Any]], Any]:
    """Value from the real-time device screen."""
    return lambda d: d["dev"].get(key)


def _dev_sensor(key: str, name_key: str, **kwargs: Any) -> "TsunSensorDescription":
    return TsunSensorDescription(
        key=f"dev_{key.lower()}",
        translation_key=name_key,
        value_fn=_dev(key),
        optional=True,
        **kwargs,
    )


_MEAS = SensorStateClass.MEASUREMENT
_DIAG = EntityCategory.DIAGNOSTIC
_TEMP = dict(
    native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    device_class=SensorDeviceClass.TEMPERATURE,
    state_class=_MEAS,
)
_VOLT = dict(
    native_unit_of_measurement=UnitOfElectricPotential.VOLT,
    device_class=SensorDeviceClass.VOLTAGE,
    state_class=_MEAS,
    suggested_display_precision=2,
)
_AMP = dict(
    native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
    device_class=SensorDeviceClass.CURRENT,
    state_class=_MEAS,
    suggested_display_precision=2,
)
_WATT = dict(
    native_unit_of_measurement=UnitOfPower.WATT,
    device_class=SensorDeviceClass.POWER,
    state_class=_MEAS,
)
_MV = dict(
    native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT,
    device_class=SensorDeviceClass.VOLTAGE,
    state_class=_MEAS,
)

# Detail values of the storage unit, from the app's device screen (created only if present).
DEVICE_SENSORS: tuple[TsunSensorDescription, ...] = (
    _dev_sensor("BAT_V", "battery_voltage", **_VOLT),
    _dev_sensor("BAT_C", "battery_current", **_AMP),
    _dev_sensor("BAT_MAX_T", "battery_temp_max", **_TEMP),
    _dev_sensor("BAT_MIN_T", "battery_temp_min", **_TEMP),
    _dev_sensor("BAT_P1_SOH", "battery_soh", native_unit_of_measurement=PERCENTAGE, state_class=_MEAS),
    _dev_sensor("BAT_P1_MAX_CV", "cell_voltage_max", **_MV),
    _dev_sensor("BAT_P1_MIN_CV", "cell_voltage_min", **_MV),
    _dev_sensor("BAT_P1_RES_CAP", "battery_remaining_ah", native_unit_of_measurement="Ah", state_class=_MEAS),
    _dev_sensor("BAT_P1_DOD", "battery_dod", native_unit_of_measurement=PERCENTAGE),
    _dev_sensor("BAT_WM", "work_mode"),
    _dev_sensor("OUT_OS", "output_state", entity_category=_DIAG),
    _dev_sensor("PV_OUT_P", "output_power", **_WATT),
    _dev_sensor("PV_OUT_V", "output_voltage", entity_registry_enabled_default=False, **_VOLT),
    _dev_sensor("PV_OUT_C", "output_current", entity_registry_enabled_default=False, **_AMP),
    _dev_sensor("IN_P_PV1", "pv1_power", **_WATT),
    _dev_sensor("IN_P_PV2", "pv2_power", **_WATT),
    _dev_sensor("DC_V_PV1", "pv1_voltage", entity_registry_enabled_default=False, **_VOLT),
    _dev_sensor("DC_V_PV2", "pv2_voltage", entity_registry_enabled_default=False, **_VOLT),
    _dev_sensor("DC_C_PV1", "pv1_current", entity_registry_enabled_default=False, **_AMP),
    _dev_sensor("DC_C_PV2", "pv2_current", entity_registry_enabled_default=False, **_AMP),
    _dev_sensor("PV1_T", "pv1_temp", **_TEMP),
    _dev_sensor("PV2_T", "pv2_temp", **_TEMP),
    _dev_sensor("PV1_OS", "pv1_state", entity_category=_DIAG, entity_registry_enabled_default=False),
    _dev_sensor("PV2_OS", "pv2_state", entity_category=_DIAG, entity_registry_enabled_default=False),
    _dev_sensor("SWv1", "firmware", entity_category=_DIAG, entity_registry_enabled_default=False),
    _dev_sensor("BAT_P1_FW_VER", "battery_firmware", entity_category=_DIAG, entity_registry_enabled_default=False),
    # Smart meter block of the device screen (only if a meter is connected to the DCU; experimental).
    _dev_sensor("METER_TYP", "meter_type", entity_category=_DIAG, entity_registry_enabled_default=False),
    _dev_sensor("A_P_METER", "meter_power_a", entity_category=_DIAG, entity_registry_enabled_default=False, **_WATT),
    _dev_sensor("B_P_METER", "meter_power_b", entity_category=_DIAG, entity_registry_enabled_default=False, **_WATT),
    _dev_sensor("C_P_METER", "meter_power_c", entity_category=_DIAG, entity_registry_enabled_default=False, **_WATT),
)

_METER = lambda d: bool(d["has_meter"])  # noqa: E731

# Logger Wi-Fi signal level (read per storage unit; the scale is unclear, see README).
LOGGER_SIGNAL = TsunSensorDescription(
    key="logger_signal", translation_key="logger_signal", value_fn=lambda d: d["logger_signal"],
    optional=True, entity_category=_DIAG, state_class=_MEAS,
)

# House connection: only present when a smart meter reports to the TSUN cloud (experimental, seen on one system).
METER_SENSORS: tuple[TsunSensorDescription, ...] = (
    TsunSensorDescription(
        key="use_power", translation_key="use_power", value_fn=lambda d: d["use_power"], optional=True,
        exists_fn=_METER, **_WATT,
    ),
    TsunSensorDescription(
        key="grid_power", translation_key="grid_power", value_fn=lambda d: d["grid_power"], optional=True,
        exists_fn=_METER, **_WATT,
    ),
    TsunSensorDescription(
        key="grid_status", translation_key="grid_status",
        value_fn=lambda d: (d["grid_status"] or "").lower() or None, optional=True,
        exists_fn=_METER, entity_category=_DIAG,
    ),
    # The three totals are disabled by default: on the only system seen so far they were the meter's own counters
    # divided by 1000 and swapped, so they are not usable for the energy dashboard (see README).
    TsunSensorDescription(
        key="grid_import_total", translation_key="grid_import_total",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING, value_fn=lambda d: d["grid_import_total"],
        optional=True, exists_fn=_METER, entity_registry_enabled_default=False,
    ),
    TsunSensorDescription(
        key="grid_export_total", translation_key="grid_export_total",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING, value_fn=lambda d: d["grid_export_total"],
        optional=True, exists_fn=_METER, entity_registry_enabled_default=False,
    ),
    TsunSensorDescription(
        key="use_total", translation_key="use_total",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING, value_fn=lambda d: d["use_total"],
        optional=True, exists_fn=_METER, entity_registry_enabled_default=False,
    ),
    LOGGER_SIGNAL,
)


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
        key="pv_total",
        translation_key="pv_total",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda d: d["pv_total"],
    ),
    TsunSensorDescription(
        key="charge_total",
        translation_key="charge_total",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda d: d["charge_total"],
    ),
    TsunSensorDescription(
        key="discharge_total",
        translation_key="discharge_total",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda d: d["discharge_total"],
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


# What a further storage unit of the same station gets (the first unit's values sit on the station device):
# its own state of charge, remaining energy, status and energy counters, plus the detail sensors.
_UNIT_BASE_KEYS = (
    "soc",
    "battery_power",
    "pv_power",
    "remaining_energy",
    "battery_status",
    "pv_today",
    "charge_today",
    "discharge_today",
    "pv_total",
    "charge_total",
    "discharge_total",
)
# Timestamp of the values on the device screen (plant local time).
DEVICE_TIME = TsunSensorDescription(
    key="device_time",
    translation_key="device_time",
    device_class=SensorDeviceClass.TIMESTAMP,
    entity_category=EntityCategory.DIAGNOSTIC,
    value_fn=lambda d: d["device_time"],
)
UNIT_SENSORS: tuple[TsunSensorDescription, ...] = (
    *(d for d in SENSORS if d.key in _UNIT_BASE_KEYS),
    DEVICE_TIME,
    *DEVICE_SENSORS,
    LOGGER_SIGNAL,
)


async def async_setup_entry(
    hass: HomeAssistant, entry: TsunConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = entry.runtime_data

    def wanted(description: TsunSensorDescription, data: dict[str, Any]) -> bool:
        if not description.optional:
            return True
        if description.exists_fn is not None and not description.exists_fn(data):
            return False
        return description.value_fn(data) is not None

    entities: list[TsunSensor] = [
        TsunSensor(coordinator, station_id, description)
        for station_id, data in coordinator.data.items()
        for description in (*SENSORS, *DEVICE_SENSORS, *METER_SENSORS)
        if wanted(description, data)
    ]
    # Further storage units of a station (e.g. two DCU2000Lite in one plant) get their own device and entities.
    # Their keys carry the cloud device id so the unique ids of the first unit stay unchanged.
    for station_id, data in coordinator.data.items():
        for unit in data.get("units", []):
            for description in UNIT_SENSORS:
                # optional: a unit only gets a sensor if the cloud delivers a value for it
                unit_description = replace(
                    description, key=f"{description.key}_dev{unit['device_id']}", optional=True
                )
                if wanted(unit_description, unit):
                    entities.append(TsunSensor(coordinator, station_id, unit_description, unit["device_id"]))
    async_add_entities(entities)


class TsunSensor(TsunEntity, SensorEntity):
    entity_description: TsunSensorDescription

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self.station)
