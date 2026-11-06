"""Pure helpers: password hashing and normalising cloud payloads.

This module has no Home Assistant imports so it can be unit-tested stand-alone.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

DEVICE_TYPE_STORAGE = 3


def hash_password(password: str) -> str:
    """Return the SHA-256 hex digest the cloud login expects."""
    return hashlib.sha256(password.encode()).hexdigest()


def _signed_battery_power(flow: dict[str, Any]) -> float | None:
    """Positive = charging, negative = discharging."""
    power = flow.get("batteryPower")
    if power is None:
        return None
    status = str(flow.get("batteryStatus") or "").upper()
    return -abs(power) if status == "DISCHARGE" else abs(power)


def _timestamp(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    except (TypeError, ValueError, OverflowError, OSError):
        return None


def parse_station(
    station: dict[str, Any], flow: dict[str, Any], devices: list[dict[str, Any]]
) -> dict[str, Any]:
    """Condense one station into the values the entities show."""
    storage = [d for d in devices if d.get("deviceType") == DEVICE_TYPE_STORAGE]
    packs = [b for d in storage for b in (d.get("batteries") or [])]
    remaining = [p.get("remainingCapacity") for p in packs if p.get("remainingCapacity") is not None]
    network = flow.get("networkStatus")

    return {
        "name": station.get("name") or "TSUN",
        "has_storage": bool(storage),
        "soc": flow.get("batterySoc"),
        "battery_power": _signed_battery_power(flow),
        "battery_status": flow.get("batteryStatus"),
        "pv_power": flow.get("generationPower"),
        "pv_today": flow.get("generationValue"),
        "charge_today": flow.get("chargeValue"),
        "discharge_today": flow.get("dischargeValue"),
        # lifetime counters (kWh, never reset)
        "pv_total": flow.get("generationUploadTotal"),
        "charge_total": flow.get("chargeUploadTotal"),
        "discharge_total": flow.get("dischargeUploadTotal"),
        # remainingCapacity is reported in kWh (verified against SoC and pack size)
        "remaining_energy": round(sum(remaining), 3) if remaining else None,
        "network_status": network,
        "online": None if network is None else network != "ALL_OFFLINE",
        "last_update": _timestamp(flow.get("updateTime")),
        "serials": [d.get("deviceSn") for d in devices if d.get("deviceSn")],
        "device_types": sorted({d.get("deviceType") for d in devices if d.get("deviceType") is not None}),
    }


# --------------------------------------------------------------------------
# Device report: a value-free structural summary + prefilled GitHub issue link
# --------------------------------------------------------------------------
REPO = "MarcusStockhaus/ha-tsun-smart-unofficial"
_MAX_URL = 7000


def _field_names(obj: dict[str, Any]) -> tuple[list[str], list[str]]:
    filled = sorted(k for k, v in obj.items() if v is not None)
    empty = sorted(k for k, v in obj.items() if v is None)
    return filled, empty


def build_report(
    integration_version: str, ha_version: str, raw: dict[Any, dict[str, Any]], detail: int = 2
) -> dict[str, str]:
    """Summarise the *structure* of the cloud answers. No values, no serials, no names."""
    lines = [f"integration: {integration_version}", f"home assistant: {ha_version}", f"stations: {len(raw)}"]
    for i, payload in enumerate(raw.values(), 1):
        station = payload.get("station") or {}
        flow = payload.get("flow") or {}
        devices = payload.get("devices") or []
        lines.append(f"\n## station {i}")
        for key in ("powerType", "powerSystemType", "geographyType"):
            if station.get(key) is not None:
                lines.append(f"- {key}: {station[key]}")
        filled, empty = _field_names(flow)
        lines.append(f"- flow fields with data ({len(filled)}): {', '.join(filled)}")
        if detail >= 2:
            lines.append(f"- flow fields empty ({len(empty)}): {', '.join(empty)}")
        for j, dev in enumerate(devices, 1):
            f2, e2 = _field_names({k: v for k, v in dev.items() if k != "batteries"})
            lines.append(
                f"- device {j}: type={dev.get('deviceType')} productId={dev.get('productId')} "
                f"batteries={len(dev.get('batteries') or [])} status={dev.get('deviceStatus')}"
            )
            if detail >= 2:
                lines.append(f"  - fields with data: {', '.join(f2)}")
    types = sorted(
        {d.get("deviceType") for p in raw.values() for d in (p.get("devices") or []) if d.get("deviceType") is not None}
    )
    device = "device types " + ", ".join(str(t) for t in types) if types else "unknown"
    return {"title": f"[device report] {device}", "device": device, "summary": "\n".join(lines)}


def issue_url(report: dict[str, str], repo: str = REPO, max_len: int = _MAX_URL) -> str:
    """Prefilled 'new issue' link; shortens the summary until it fits a URL."""
    from urllib.parse import quote

    summary = report["summary"]
    while True:
        url = (
            f"https://github.com/{repo}/issues/new?template=device-report.yml"
            f"&title={quote(report['title'])}&device={quote(report['device'])}"
            f"&diagnostics={quote(summary)}"
        )
        if len(url) <= max_len or len(summary) < 200:
            return url
        summary = summary[: int(len(summary) * 0.8)].rsplit("\n", 1)[0] + "\n…(shortened)"


def mailto_url(report: dict[str, str], email: str, max_len: int = 1800) -> str:
    """mailto: link with the same value-free summary (for people without a GitHub account)."""
    from urllib.parse import quote

    summary = report["summary"]
    while True:
        url = f"mailto:{email}?subject={quote(report['title'])}&body={quote(summary)}"
        if len(url) <= max_len or len(summary) < 200:
            return url
        summary = summary[: int(len(summary) * 0.8)].rsplit("\n", 1)[0] + "\n...(shortened)"


def is_auth_failure(status: int, body: object) -> bool:
    """True if a token response means 'wrong credentials' (the cloud answers HTTP 412 for that)."""
    if isinstance(body, dict) and str(body.get("code", "")).startswith("AUTH_"):
        return True
    return status in (400, 401, 403, 412)
