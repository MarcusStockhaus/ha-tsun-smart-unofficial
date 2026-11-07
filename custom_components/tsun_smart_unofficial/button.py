"""Button that prepares a device report (prefilled GitHub issue / e-mail link)."""
from __future__ import annotations

from homeassistant.components import persistent_notification
from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.const import __version__ as HA_VERSION
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.loader import async_get_integration

from . import TsunConfigEntry
from .const import DOMAIN, REPORT_EMAIL
from .entity import TsunEntity
from .model import build_report, report_message

REPORT = ButtonEntityDescription(
    key="device_report",
    translation_key="device_report",
    entity_category=EntityCategory.DIAGNOSTIC,
)

async def async_setup_entry(
    hass: HomeAssistant, entry: TsunConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    first = next(iter(coordinator.data), None)
    if first is not None:
        async_add_entities([TsunReportButton(coordinator, first, REPORT)])


class TsunReportButton(TsunEntity, ButtonEntity):
    """Creates a notification with report links (nothing is sent automatically)."""

    async def async_press(self) -> None:
        integration = await async_get_integration(self.hass, DOMAIN)
        report = build_report(str(integration.version), HA_VERSION, self.coordinator.raw)
        message = report_message(report, REPORT_EMAIL)
        persistent_notification.async_create(
            self.hass,
            message,
            title="TSUN Smart (unofficial): device report",
            notification_id=f"{DOMAIN}_device_report",
        )
