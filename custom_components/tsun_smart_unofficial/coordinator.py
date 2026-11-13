"""Data update coordinator."""
from __future__ import annotations

from datetime import timedelta
import logging
import time
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import TsunApiError, TsunAuthError, TsunSmartApi
from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN, MISSING_GRACE_DAYS
from .model import (
    assign_units,
    expected_device_identifiers,
    flatten_device_data,
    logger_signal,
    parse_station,
    plan_device_changes,
    storage_devices,
    storage_unit_summary,
)

_LOGGER = logging.getLogger(__name__)

_GRACE_SECONDS = MISSING_GRACE_DAYS * 86400
_STORE_VERSION = 1


def store_key(entry_id: str) -> str:
    return f"{DOMAIN}.{entry_id}"


class TsunCoordinator(DataUpdateCoordinator[dict[int, dict[str, Any]]]):
    """Polls all stations of the account."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, api: TsunSmartApi) -> None:
        minutes = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(minutes=minutes),
        )
        self.api = api
        # Raw payloads of the last poll, used only by diagnostics.
        self.raw: dict[int, dict[str, Any]] = {}
        # What is remembered between polls and restarts: which storage unit is the main one of a plant,
        # the numbers of the other units, and since when a device has been missing from the cloud.
        self._store: Store[dict[str, Any]] = Store(hass, _STORE_VERSION, store_key(entry.entry_id))
        self._stations: dict[str, dict[str, Any]] = {}
        self._missing: dict[str, float] = {}
        self._loaded = False
        # Device identifiers that existed when the platforms were set up; a new one triggers a reload.
        self._known: set[str] | None = None

    async def _async_load_state(self) -> None:
        if self._loaded:
            return
        stored = await self._store.async_load() or {}
        self._stations = stored.get("stations") or {}
        self._missing = stored.get("missing") or {}
        self._loaded = True

    def _state_to_save(self) -> dict[str, Any]:
        return {"stations": self._stations, "missing": self._missing}

    async def _unit_details(self, station_id: int, unit: dict[str, Any]) -> dict[str, Any]:
        """Real-time detail values and logger signal of one storage unit."""
        device_id = unit["deviceId"]
        device_data: dict[str, Any] = {}
        signal = None
        # Extra detail from the device screen; the main values must not fail if this is unavailable.
        try:
            device_data = flatten_device_data(await self.api.device_data(station_id, device_id))
        except TsunApiError as err:
            _LOGGER.debug("Device detail unavailable: %s", err)
        try:
            signal = logger_signal(await self.api.logger_info(device_id))
        except TsunApiError as err:
            _LOGGER.debug("Logger info unavailable: %s", err)
        return {"dev": device_data, "logger_signal": signal}

    async def _async_update_data(self) -> dict[int, dict[str, Any]]:
        await self._async_load_state()
        now = time.time()
        try:
            result: dict[int, dict[str, Any]] = {}
            raw: dict[int, dict[str, Any]] = {}
            for station in await self.api.stations():
                sid = station["id"]
                flow = await self.api.current_flow(sid)
                devices = await self.api.devices(sid)
                state = self._stations.setdefault(str(sid), {})
                # The main storage unit feeds the station device; every other one gets its own device.
                primary, extras = assign_units(state, storage_devices(devices), now, _GRACE_SECONDS)
                first = {"dev": {}, "logger_signal": None}
                if primary is not None:
                    first = await self._unit_details(sid, primary)
                units: list[dict[str, Any]] = []
                for ordinal, unit in extras:
                    detail = await self._unit_details(sid, unit)
                    units.append(
                        {
                            "device_id": unit["deviceId"],
                            "ordinal": ordinal,
                            **detail,
                            **storage_unit_summary(unit),
                        }
                    )
                raw[sid] = {"station": station, "flow": flow, "devices": devices}
                result[sid] = parse_station(station, flow, devices, first["dev"], first["logger_signal"], units)
        except TsunAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except TsunApiError as err:
            raise UpdateFailed(str(err)) from err
        self.raw = raw
        self._sync_registry(result, now)
        self._store.async_delay_save(self._state_to_save, 10)
        return result

    def _sync_registry(self, data: dict[int, dict[str, Any]], now: float) -> None:
        """Disable, re-enable or finally remove devices of plants or storage units that appear or vanish.

        Only runs after a successful poll that returned at least one plant, so a cloud hiccup that
        returns nothing never touches the registry.
        """
        if not data:
            return
        entry_id = self.config_entry.entry_id
        wanted = expected_device_identifiers(data)
        registry = dr.async_get(self.hass)
        devices = {}
        entries = []
        for device in dr.async_entries_for_config_entry(registry, entry_id):
            ours = [ident for domain, ident in device.identifiers if domain == DOMAIN]
            if not ours:
                continue
            devices[device.id] = device
            entries.append(
                {
                    "id": device.id,
                    "ident": ours[0],
                    "disabled": device.disabled_by == dr.DeviceEntryDisabler.INTEGRATION,
                }
            )
        enable, disable, remove, self._missing = plan_device_changes(
            wanted, entries, self._missing, now, _GRACE_SECONDS
        )
        for device_id in remove:
            _LOGGER.info("Removing device %s: missing from the TSUN cloud for too long", devices[device_id].name)
            registry.async_update_device(device_id, remove_config_entry_id=entry_id)
        for device_id in disable:
            if devices[device_id].disabled_by is None:
                _LOGGER.info("Disabling device %s: no longer listed by the TSUN cloud", devices[device_id].name)
                registry.async_update_device(device_id, disabled_by=dr.DeviceEntryDisabler.INTEGRATION)
        for device_id in enable:
            _LOGGER.info("Enabling device %s again: the TSUN cloud lists it again", devices[device_id].name)
            registry.async_update_device(device_id, disabled_by=None)
        # New or re-enabled devices have no entities yet: reload once so the platforms create them.
        if self._known is None:
            self._known = wanted
        elif enable or wanted - self._known:
            self._known = wanted
            self.hass.config_entries.async_schedule_reload(entry_id)
