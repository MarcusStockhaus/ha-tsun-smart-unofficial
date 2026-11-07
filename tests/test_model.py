"""Stand-alone tests for the pure helpers (no Home Assistant required)."""
import importlib.util
from datetime import timezone
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "model", Path(__file__).parent.parent / "custom_components" / "tsun_smart_unofficial" / "model.py"
)
model = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(model)

STATION = {"id": 1, "name": "Storage"}
FLOW_DISCHARGE = {
    "batterySoc": 20.0,
    "batteryStatus": "DISCHARGE",
    "batteryPower": 15.0,
    "generationPower": 0.0,
    "generationValue": 0.6,
    "chargeValue": 0.27,
    "dischargeValue": 0.99,
    "networkStatus": "ALL_OFFLINE",
    "updateTime": 1793913517,
}
DEVICES = [
    {"deviceType": 3, "deviceSn": "X1", "batteries": [{"sn": "B1", "totalCapacity": 39.2, "soc": 20.0, "remainingCapacity": 0.4023}]},
    {"deviceType": 18, "deviceSn": "L1", "batteries": []},
]


def test_hash_matches_sha256_of_known_value():
    assert model.hash_password("abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_discharge_is_negative():
    out = model.parse_station(STATION, FLOW_DISCHARGE, DEVICES)
    assert out["battery_power"] == -15.0
    assert out["soc"] == 20.0
    assert out["battery_status"] == "DISCHARGE"


def test_charge_is_positive():
    out = model.parse_station(STATION, {**FLOW_DISCHARGE, "batteryStatus": "CHARGE"}, DEVICES)
    assert out["battery_power"] == 15.0


def test_offline_flag_and_timestamp():
    out = model.parse_station(STATION, FLOW_DISCHARGE, DEVICES)
    assert out["online"] is False
    assert out["last_update"].tzinfo == timezone.utc
    online = model.parse_station(STATION, {**FLOW_DISCHARGE, "networkStatus": "ALL_ONLINE"}, DEVICES)
    assert online["online"] is True


def test_storage_detection_and_remaining_energy():
    out = model.parse_station(STATION, FLOW_DISCHARGE, DEVICES)
    assert out["has_storage"] is True
    assert out["remaining_energy"] == 0.402
    assert out["device_types"] == [3, 18]


def test_empty_payloads_do_not_crash():
    out = model.parse_station({"id": 2}, {}, [])
    assert out["soc"] is None and out["battery_power"] is None
    assert out["online"] is None and out["last_update"] is None
    assert out["has_storage"] is False and out["name"] == "TSUN"


RAW = {
    1: {
        "station": {"id": 1, "name": "Secret Name", "powerType": "PV", "locationAddress": "Somewhere 1"},
        "flow": {**FLOW_DISCHARGE, "gridPower": None},
        "devices": DEVICES,
    }
}


def test_report_contains_structure_but_no_values_or_identifiers():
    report = model.build_report("0.2.0", "2026.10.4", RAW)
    text = report["summary"]
    assert "batterySoc" in text and "gridPower" in text
    assert report["device"] == "device types 3, 18"
    for secret in ("Secret Name", "Somewhere 1", "X1", "B1", "L1", "0.4023", "1793913517"):
        assert secret not in text


def test_issue_url_is_prefilled_and_bounded():
    url = model.issue_url(model.build_report("0.2.0", "2026.10.4", RAW))
    assert url.startswith("https://github.com/MarcusStockhaus/ha-tsun-smart-unofficial/issues/new?template=device-report.yml")
    assert len(url) <= 7000
    big = {i: RAW[1] for i in range(60)}
    assert len(model.issue_url(model.build_report("0.2.0", "x", big))) <= 7000


def test_mailto_link_bounded_and_value_free():
    report = model.build_report("0.2.0", "2026.10.4", RAW)
    url = model.mailto_url(report, "someone@example.org")
    assert url.startswith("mailto:someone@example.org?subject=")
    assert len(url) <= 1800
    assert "Secret%20Name" not in url


def test_is_auth_failure():
    assert model.is_auth_failure(412, {"code": "AUTH_INVALID_USERNAME_OR_PASSWORD"})
    assert model.is_auth_failure(401, None)
    assert not model.is_auth_failure(500, {"code": "sorry_for_server_exception"})
    assert not model.is_auth_failure(502, "bad gateway")


def test_lifetime_counters():
    flow = {"generationUploadTotal": 0.93, "chargeUploadTotal": 0.54, "dischargeUploadTotal": 1.02}
    out = model.parse_station(STATION, flow, [])
    assert (out["pv_total"], out["charge_total"], out["discharge_total"]) == (0.93, 0.54, 1.02)
    empty = model.parse_station(STATION, {}, [])
    assert empty["pv_total"] is None


def test_last_update_prefers_last_update_time():
    out = model.parse_station(STATION, {"updateTime": 1000, "lastUpdateTime": 2000}, [])
    assert int(out["last_update"].timestamp()) == 2000
    out = model.parse_station(STATION, {"updateTime": 1000, "lastUpdateTime": None}, [])
    assert int(out["last_update"].timestamp()) == 1000


def test_mail_report_is_compact_and_flags_unknown_devices():
    flow = {k: 1 for k in model.KNOWN_FLOW_FIELDS}
    dcu = {k: 1 for k in model.KNOWN_DEVICE_FIELDS[3]}
    dcu.update(deviceType=3, productId="p3")
    other = {"deviceType": 99, "productId": "p99", "newField": 1}
    raw = {1: {"station": {}, "flow": flow, "devices": [dcu, other]}}
    report = model.build_report("0.2.4", "x", raw)
    mail = report["mail_summary"]
    assert "new: none" in mail
    assert "type=3" in mail and "new fields: none" in mail
    assert "type=99" in mail and "newField" in mail
    assert len(model.mailto_url(report, "a@b.c")) < 1800
    assert "shortened" not in model.mailto_url(report, "a@b.c")


def test_report_message_contains_links_and_text():
    report = model.build_report("0.2.4", "x", RAW)
    msg = model.report_message(report, "a@b.c")
    assert "issues/new?template=device-report.yml" in msg and "mailto:a@b.c" in msg
    assert report["summary"] in msg and msg.count("```") == 2
