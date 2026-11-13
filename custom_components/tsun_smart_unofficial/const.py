"""Constants for TSUN Smart (unofficial)."""
from __future__ import annotations

DOMAIN = "tsun_smart_unofficial"

BASE_URL = "https://pro.talent-monitoring.com"
CLIENT_ID = "sdl_client"
# The cloud API was observed with this client string; it is sent unchanged.
USER_AGENT = "ja-solar/20 CFNetwork/3860.700.2 Darwin/25.6.0"
REQUEST_TIMEOUT = 30

CONF_PASSWORD_HASH = "password_hash"
CONF_SCAN_INTERVAL = "scan_interval"

# The cloud only receives new values roughly every 5 minutes.
MIN_SCAN_INTERVAL = 5  # minutes
DEFAULT_SCAN_INTERVAL = 5  # minutes
MAX_SCAN_INTERVAL = 60  # minutes

# A plant or storage unit the cloud no longer lists is disabled first and removed after this many days.
MISSING_GRACE_DAYS = 30

# deviceType values seen in the cloud API
DEVICE_TYPE_STORAGE = 3  # DCU2000Lite (DC-coupled storage unit)
DEVICE_TYPE_LOGGER = 18  # WiFi data logger / gateway

# Optional way to send a device report without a GitHub account (opens the user's mail app).
REPORT_EMAIL = "marcus@stockha.us"
