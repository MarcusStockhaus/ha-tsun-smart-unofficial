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


DEVICE_SCREEN = {
    "paramCategoryList": [
        {"fieldList": [{"storageName": "SN1", "value": "Y001A14C000D0001"}, {"storageName": "DEV_TYP", "value": "DCU2000Lite"}]},
        {
            "fieldList": [
                {"storageName": "BAT_V", "value": "41.94"},
                {"storageName": "BAT_MAX_T", "value": "8.90"},
                {"storageName": "BAT_P1_SN", "value": "1004251219DE2239"},
                {"storageName": "BAT_WM", "value": "Constant Power Mode"},
                {"storageName": "EMPTY", "value": " "},
            ]
        },
    ]
}


def test_flatten_device_data_numbers_text_and_no_serials():
    out = model.flatten_device_data(DEVICE_SCREEN)
    assert out["BAT_V"] == 41.94 and out["BAT_MAX_T"] == 8.9
    assert out["DEV_TYP"] == "DCU2000Lite" and out["BAT_WM"] == "Constant Power Mode"
    assert out["EMPTY"] is None
    assert "SN1" not in out and "BAT_P1_SN" not in out
    assert model.flatten_device_data(None) == {}


def test_logger_signal_and_storage_device_id():
    assert model.logger_signal([{"signalIntensity": 2}]) == 2
    assert model.logger_signal([]) is None and model.logger_signal(None) is None
    assert model.storage_device_id([{"deviceType": 18, "deviceId": 1}, {"deviceType": 3, "deviceId": 7}]) == 7
    assert model.storage_device_id([{"deviceType": 18, "deviceId": 1}]) is None


METER_FLOW = {
    "batterySoc": 22.0,
    "batteryStatus": "CHARGE",
    "batteryPower": -68.1,
    "usePower": 310.0,
    "wirePower": 295.0,
    "wireStatus": "PURCHASE",
    "buyUploadTotal": 0.83,
    "gridUploadTotal": 7.67,
    "useUploadTotal": 162.81,
}


def test_meter_values_only_with_a_meter():
    with_meter = model.parse_station(STATION, METER_FLOW, DEVICES)
    assert with_meter["has_meter"] is True
    assert with_meter["use_power"] == 310.0
    assert with_meter["grid_power"] == 295.0  # import is positive
    assert with_meter["grid_import_total"] == 0.83 and with_meter["grid_export_total"] == 7.67
    # a system without meter reports a lifetime "use" counter equal to generation, but no grid fields
    without = model.parse_station(STATION, {**FLOW_DISCHARGE, "useUploadTotal": 1.11}, DEVICES)
    assert without["has_meter"] is False and without["grid_power"] is None


def test_grid_power_sign_follows_status():
    assert model._grid_power({"wirePower": 120.0, "wireStatus": "PURCHASE"}) == 120.0
    assert model._grid_power({"wirePower": 120.0, "wireStatus": "SELL"}) == -120.0
    assert model._grid_power({"wirePower": -120.0, "wireStatus": "FEED_IN"}) == -120.0
    assert model._grid_power({}) is None


def test_parse_station_carries_device_screen_and_signal():
    data = model.parse_station(STATION, FLOW_DISCHARGE, DEVICES, model.flatten_device_data(DEVICE_SCREEN), 2)
    assert data["dev"]["BAT_V"] == 41.94 and data["logger_signal"] == 2
    assert model.parse_station(STATION, FLOW_DISCHARGE, DEVICES)["dev"] == {}
