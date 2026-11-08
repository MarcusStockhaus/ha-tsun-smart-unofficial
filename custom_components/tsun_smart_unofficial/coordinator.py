"""Data update coordinator."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import TsunApiError, TsunAuthError, TsunSmartApi
from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN
from .model import flatten_device_data, logger_signal, parse_station, storage_device_id

_LOGGER = logging.getLogger(__name__)


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

    async def _async_update_data(self) -> dict[int, dict[str, Any]]:
        try:
            result: dict[int, dict[str, Any]] = {}
            raw: dict[int, dict[str, Any]] = {}
            for station in await self.api.stations():
                sid = station["id"]
                flow = await self.api.current_flow(sid)
                devices = await self.api.devices(sid)
                device_data: dict[str, Any] = {}
                signal = None
                device_id = storage_device_id(devices)
                if device_id is not None:
                    # Extra detail from the device screen; the main values must not fail if this is unavailable.
                    try:
                        device_data = flatten_device_data(await self.api.device_data(sid, device_id))
                    except TsunApiError as err:
                        _LOGGER.debug("Device detail unavailable: %s", err)
                    try:
                        signal = logger_signal(await self.api.logger_info(device_id))
                    except TsunApiError as err:
                        _LOGGER.debug("Logger info unavailable: %s", err)
                raw[sid] = {"station": station, "flow": flow, "devices": devices}
                result[sid] = parse_station(station, flow, devices, device_data, signal)
        except TsunAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except TsunApiError as err:
            raise UpdateFailed(str(err)) from err
        self.raw = raw
        return result
