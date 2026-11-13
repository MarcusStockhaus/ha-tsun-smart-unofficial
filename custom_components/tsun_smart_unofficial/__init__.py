"""TSUN Smart (unofficial): Home Assistant integration built for the TSUN DCU2000Lite.

Not affiliated with TSUN / TSUNESS. Uses the same cloud API as the TSUN Smart app.
"""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceEntry
from homeassistant.helpers.storage import Store

from .api import TsunSmartApi
from .const import CONF_PASSWORD_HASH, DOMAIN
from .coordinator import TsunCoordinator, store_key
from .model import expected_device_identifiers

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.BUTTON]

type TsunConfigEntry = ConfigEntry[TsunCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: TsunConfigEntry) -> bool:
    api = TsunSmartApi(
        async_get_clientsession(hass), entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD_HASH]
    )
    coordinator = TsunCoordinator(hass, entry, api)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    entry.async_on_unload(entry.add_update_listener(_async_reload))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _async_reload(hass: HomeAssistant, entry: TsunConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_remove_config_entry_device(
    hass: HomeAssistant, entry: TsunConfigEntry, device_entry: DeviceEntry
) -> bool:
    """Let the user delete a device in the UI, but only if the cloud no longer reports it."""
    coordinator = getattr(entry, "runtime_data", None)
    if coordinator is None or not coordinator.data:
        return False
    wanted = expected_device_identifiers(coordinator.data)
    return not any(domain == DOMAIN and ident in wanted for domain, ident in device_entry.identifiers)


async def async_remove_entry(hass: HomeAssistant, entry: TsunConfigEntry) -> None:
    """Forget what the coordinator remembered about this account."""
    await Store(hass, 1, store_key(entry.entry_id)).async_remove()


async def async_unload_entry(hass: HomeAssistant, entry: TsunConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
