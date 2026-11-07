"""Config flow: e-mail + password of the TSUN Smart app.

Only the SHA-256 hash of the password is stored (the cloud login expects exactly that).
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.const import __version__ as HA_VERSION
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.loader import async_get_integration
from homeassistant.helpers.selector import TextSelector, TextSelectorConfig, TextSelectorType

from .api import TsunApiError, TsunAuthError, TsunSmartApi
from .const import (
    CONF_PASSWORD_HASH,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    REPORT_EMAIL,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)
from .model import build_report, hash_password, report_message


EMAIL = TextSelector(TextSelectorConfig(type=TextSelectorType.EMAIL, autocomplete="username"))
PASSWORD = TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD, autocomplete="current-password"))


class TsunSmartConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return TsunOptionsFlow()

    async def _validate(self, username: str, password: str) -> tuple[str | None, str]:
        pw_hash = hash_password(password)
        api = TsunSmartApi(async_get_clientsession(self.hass), username, pw_hash)
        try:
            await api.login()
        except TsunAuthError:
            return "invalid_auth", pw_hash
        except TsunApiError:
            return "cannot_connect", pw_hash
        return None, pw_hash

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            username = user_input[CONF_USERNAME].strip()
            error, pw_hash = await self._validate(username, user_input[CONF_PASSWORD])
            if error:
                errors["base"] = error
            else:
                await self.async_set_unique_id(username.lower())
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=username, data={CONF_USERNAME: username, CONF_PASSWORD_HASH: pw_hash}
                )
        schema = vol.Schema({vol.Required(CONF_USERNAME): EMAIL, vol.Required(CONF_PASSWORD): PASSWORD})
        # keep the e-mail after a failed attempt, never the password
        suggested = {CONF_USERNAME: user_input[CONF_USERNAME]} if user_input else None
        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(schema, suggested),
            errors=errors,
        )

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        entry = self._get_reauth_entry()
        if user_input is not None:
            error, pw_hash = await self._validate(entry.data[CONF_USERNAME], user_input[CONF_PASSWORD])
            if error:
                errors["base"] = error
            else:
                return self.async_update_reload_and_abort(
                    entry, data_updates={CONF_PASSWORD_HASH: pw_hash}
                )
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_PASSWORD): PASSWORD}),
            description_placeholders={"username": entry.data[CONF_USERNAME]},
            errors=errors,
        )


class TsunOptionsFlow(OptionsFlow):
    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return self.async_show_menu(step_id="init", menu_options=["settings", "report"])

    async def async_step_settings(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        current = self.config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        return self.async_show_form(
            step_id="settings",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SCAN_INTERVAL, default=current): vol.All(
                        vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL)
                    )
                }
            ),
        )

    async def async_step_report(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Show the device report (links + copyable text). Nothing is sent."""
        if user_input is not None:
            return self.async_create_entry(data=dict(self.config_entry.options))
        integration = await async_get_integration(self.hass, DOMAIN)
        raw = getattr(self.config_entry.runtime_data, "raw", {})
        report = build_report(str(integration.version), HA_VERSION, raw)
        return self.async_show_form(
            step_id="report",
            data_schema=vol.Schema({}),
            description_placeholders={"report": report_message(report, REPORT_EMAIL)},
        )
