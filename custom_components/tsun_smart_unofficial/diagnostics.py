"""Diagnostics: a redacted dump you can attach to a device report."""
from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from . import TsunConfigEntry

TO_REDACT = {
    "username",
    "password_hash",
    "access_token",
    "refresh_token",
    "deviceSn",
    "parentSn",
    "sn",
    "serials",
    "deviceIp",
    "locationAddress",
    "locationLat",
    "locationLng",
    "contactPhone",
    "ownerName",
    "createdBy",
    "stationImage",
    "name",
    "stationName",
    "systemName",
    "title",
    # identifiers of your installation at the manufacturer, and set-up timestamps
    "id",
    "stationId",
    "systemId",
    "deviceId",
    "gatewayId",
    "createdDate",
    "gridTime",
    "lastInspectDate",
    "startOperatingTime",
    "regionNationId",
    "regionTimezone",
    "timeZone",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: TsunConfigEntry
) -> dict[str, Any]:
    coordinator = entry.runtime_data
    # the station id is a key in the data; replace it with a neutral label
    labels = {str(k): f"station_{i}" for i, k in enumerate(coordinator.data, 1)}
    return {
        "entry": async_redact_data(dict(entry.data), TO_REDACT),
        "options": dict(entry.options),
        "parsed": async_redact_data(
            {labels[str(k)]: {**v, "last_update": str(v["last_update"])} for k, v in coordinator.data.items()},
            TO_REDACT,
        ),
        "raw": async_redact_data({labels.get(str(k), str(k)): v for k, v in coordinator.raw.items()}, TO_REDACT),
    }
