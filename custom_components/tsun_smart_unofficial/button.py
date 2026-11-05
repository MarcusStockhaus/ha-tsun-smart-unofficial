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
from .model import build_report, issue_url, mailto_url

REPORT = ButtonEntityDescription(
    key="device_report",
    translation_key="device_report",
    entity_category=EntityCategory.DIAGNOSTIC,
)

INTRO = (
    "**EN:** Nothing was sent. The links below open a prefilled GitHub issue or an e-mail that contain only the "
    "structure of your cloud data (field names, device types) - no values, serial numbers or names. Review it, add "
    "what the TSUN Smart app shows that is missing here, and send it yourself.\n\n"
    "**DE:** Es wurde nichts gesendet. Die Links unten öffnen ein vorausgefülltes GitHub-Issue oder eine E-Mail, die nur "
    "die Struktur deiner Cloud-Daten enthalten (Feldnamen, Gerätetypen) - keine Werte, Seriennummern oder Namen. "
    "Prüfe den Text, ergänze, was die TSUN-Smart-App zeigt und hier fehlt, und sende ihn selbst ab.\n\n"
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
        issue = issue_url(report)
        mail = mailto_url(report, REPORT_EMAIL)
        message = (
            INTRO
            + f"[GitHub: open prefilled issue / Vorausgefülltes Issue öffnen]({issue})\n\n"
            + f"[No GitHub account? Send by e-mail / Kein GitHub-Konto? Per E-Mail senden]({mail})\n\n"
            + "**Report text (copy if needed) / Berichtstext (bei Bedarf kopieren):**\n\n"
            + "```\n"
            + report["summary"]
            + "\n```"
        )
        persistent_notification.async_create(
            self.hass,
            message,
            title="TSUN Smart (unofficial): device report",
            notification_id=f"{DOMAIN}_device_report",
        )
