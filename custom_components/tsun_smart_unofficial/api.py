"""Minimal client for the cloud API behind the TSUN Smart app (unofficial)."""
from __future__ import annotations

import asyncio
import time
from datetime import datetime
from typing import Any

import aiohttp

from .const import BASE_URL, CLIENT_ID, REQUEST_TIMEOUT, USER_AGENT
from .model import hash_password, is_auth_failure  # noqa: F401  (hash_password re-exported)


class TsunAuthError(Exception):
    """Login or token refresh was rejected."""


class TsunApiError(Exception):
    """Any other API or network error."""


class TsunSmartApi:
    """Talks to pro.talent-monitoring.com the way the mobile app does."""

    def __init__(self, session: aiohttp.ClientSession, username: str, password_hash: str) -> None:
        self._session = session
        self._username = username
        self._password_hash = password_hash
        self._access: str | None = None
        self._refresh: str | None = None
        self._expires = 0.0

    async def _token_request(self, data: dict[str, Any]) -> None:
        try:
            async with self._session.post(
                f"{BASE_URL}/oauth2-s/oauth/token",
                data=data,
                headers={"User-Agent": USER_AGENT},
                timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
            ) as resp:
                status = resp.status
                body = await resp.json(content_type=None)
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise TsunApiError(f"Cannot reach the TSUN cloud: {err}") from err

        if not isinstance(body, dict) or "access_token" not in body:
            if is_auth_failure(status, body):
                raise TsunAuthError(str(body))
            raise TsunApiError(f"Unexpected login response (HTTP {status})")
        self._access = body["access_token"]
        self._refresh = body.get("refresh_token")
        self._expires = time.time() + int(body.get("expires_in", 3600)) - 300

    async def login(self) -> None:
        await self._token_request(
            {
                "grant_type": "password",
                "username": self._username,
                "password": self._password_hash,
                "client_id": CLIENT_ID,
                "identity_type": 2,
                "system": "TSUN",
            }
        )

    async def _ensure_token(self) -> None:
        if self._access and time.time() < self._expires:
            return
        if self._refresh:
            try:
                await self._token_request(
                    {"grant_type": "refresh_token", "refresh_token": self._refresh, "client_id": CLIENT_ID}
                )
                return
            except (TsunAuthError, TsunApiError):
                self._refresh = None
        await self.login()

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        for attempt in (1, 2):
            await self._ensure_token()
            headers = {"Authorization": f"bearer {self._access}", "User-Agent": USER_AGENT}
            try:
                async with self._session.request(
                    method,
                    f"{BASE_URL}{path}",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
                    **kwargs,
                ) as resp:
                    if resp.status == 401 and attempt == 1:
                        self._access = None
                        continue
                    if resp.status == 401:
                        raise TsunAuthError("Token rejected")
                    if resp.status != 200:
                        raise TsunApiError(f"{path}: HTTP {resp.status}")
                    return await resp.json(content_type=None)
            except (aiohttp.ClientError, asyncio.TimeoutError) as err:
                raise TsunApiError(f"{path}: {err}") from err
        raise TsunApiError(f"{path}: giving up")

    async def stations(self) -> list[dict[str, Any]]:
        body = {
            "region": {"nationId": None, "level1": None, "level2": None, "level3": None, "level4": None, "level5": None},
            "returnTag": True,
            "powerTypeList": None,
        }
        result = await self._request(
            "POST",
            "/station-s/station/query/list?order.direction=ASC&order.property=name&page=1&size=9999",
            json=body,
        )
        return [item["station"] for item in (result or {}).get("data", []) if "station" in item]

    async def current_flow(self, station_id: int) -> dict[str, Any]:
        now = datetime.now()
        result = await self._request(
            "GET",
            f"/station-s/station/statistic/current/flow/{station_id}"
            f"?year={now.year}&month={now.month}&day={now.day}",
        )
        return (result or {}).get("stationCurrentDto") or {}

    async def device_data(self, station_id: int, device_id: int) -> dict[str, Any]:
        """Real-time values of one device (battery voltage, temperatures, ...), as the app's device screen shows them."""
        return (
            await self._request(
                "POST",
                "/device-s/device-monitor/current-data",
                json={
                    "language": "en",
                    "siteId": str(station_id),
                    "deviceId": str(device_id),
                    "needRealTimeDataFlag": True,
                    "tag": "version",
                },
            )
            or {}
        )

    async def logger_info(self, device_id: int) -> list[dict[str, Any]]:
        """Data logger (gateway) of a device, including its Wi-Fi signal strength."""
        result = await self._request("GET", f"/device-s/device-monitor/get-communication/{device_id}")
        return result if isinstance(result, list) else []

    async def devices(self, station_id: int) -> list[dict[str, Any]]:
        result = await self._request("GET", f"/station-s/{station_id}/device/common?page=1&size=200")
        return (result or {}).get("data", [])
