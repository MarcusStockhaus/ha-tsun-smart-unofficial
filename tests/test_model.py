"""Stand-alone tests for the pure helpers (no Home Assistant required)."""
import importlib.util
from datetime import timedelta, timezone
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


TWO_UNITS = [
    {"deviceType": 18, "deviceId": 1, "batteries": []},
    {"deviceType": 18, "deviceId": 2, "batteries": []},
    {"deviceType": 3, "deviceId": 7, "batteries": [{"remainingCapacity": 0.4}]},
    {"deviceType": 3, "deviceId": 8, "batteries": [{"remainingCapacity": 0.6}]},
]


def test_storage_device_ids_lists_all_units_in_order():
    assert model.storage_device_ids(TWO_UNITS) == [7, 8]
    assert model.storage_device_ids([{"deviceType": 18, "deviceId": 1}]) == []
    # a storage device without an id is skipped
    assert model.storage_device_ids([{"deviceType": 3}, {"deviceType": 3, "deviceId": 9}]) == [9]
    # the first unit stays the one used for the station device
    assert model.storage_device_id(TWO_UNITS) == 7


def test_parse_station_with_two_units_sums_energy_and_keeps_units():
    units = [{"dev": {"BAT_V": 50.1}, "logger_signal": 3}]
    out = model.parse_station(STATION, FLOW_DISCHARGE, TWO_UNITS, {"BAT_V": 49.9}, 2, units)
    assert out["remaining_energy"] == 1.0
    assert out["dev"] == {"BAT_V": 49.9} and out["logger_signal"] == 2
    assert out["units"] == units


def test_storage_unit_summary_uses_device_values_then_battery_values():
    full = {"soc": 55.0, "batteryStatus": "CHARGE", "batteries": [{"soc": 50.0, "remainingCapacity": 1.2}, {"remainingCapacity": 0.8}]}
    assert model.storage_unit_summary(full) == {"soc": 55.0, "remaining_energy": 2.0, "battery_status": "CHARGE"}
    # no device-level soc: average of the battery packs that report one
    packs = {"batteries": [{"soc": 40.0}, {"soc": 50.0}]}
    assert model.storage_unit_summary(packs) == {"soc": 45.0, "remaining_energy": None, "battery_status": None}
    assert model.storage_unit_summary({}) == {"soc": None, "remaining_energy": None, "battery_status": None}


def test_expected_device_identifiers_covers_stations_and_extra_units():
    data = {
        10: {"units": [{"device_id": 7}, {"device_id": 8}]},
        20: {"units": []},
        30: {},
    }
    assert model.expected_device_identifiers(data) == {"10", "10_dev7", "10_dev8", "20", "30"}
    assert model.expected_device_identifiers({}) == set()


GRACE = 30 * 86400


def _unit(device_id):
    return {"deviceType": 3, "deviceId": device_id}


def test_assign_units_first_seen_is_main_and_others_are_numbered():
    state = {}
    primary, extras = model.assign_units(state, [_unit(7), _unit(8), _unit(9)], 1000, GRACE)
    assert primary["deviceId"] == 7
    assert [(n, d["deviceId"]) for n, d in extras] == [(2, 8), (3, 9)]
    assert state["primary"] == 7


def test_assign_units_main_stays_main_when_the_list_order_changes():
    state = {}
    model.assign_units(state, [_unit(7), _unit(8)], 1000, GRACE)
    primary, extras = model.assign_units(state, [_unit(8), _unit(7)], 2000, GRACE)
    assert primary["deviceId"] == 7
    assert [(n, d["deviceId"]) for n, d in extras] == [(2, 8)]


def test_assign_units_missing_main_is_not_replaced_before_the_grace_period():
    state = {}
    model.assign_units(state, [_unit(7), _unit(8)], 1000, GRACE)
    primary, extras = model.assign_units(state, [_unit(8)], 2000, GRACE)
    # unit 8 keeps its own number, the main device gets no values for now
    assert primary is None
    assert [(n, d["deviceId"]) for n, d in extras] == [(2, 8)]
    # still within the grace period
    primary, _ = model.assign_units(state, [_unit(8)], 1000 + GRACE, GRACE)
    assert primary is None
    # after the grace period the remaining unit takes over the main device
    primary, extras = model.assign_units(state, [_unit(8)], 3000 + GRACE, GRACE)
    assert primary["deviceId"] == 8 and extras == []
    assert state["primary"] == 8 and "primary_missing" not in state


def test_assign_units_returning_main_clears_the_missing_mark():
    state = {}
    model.assign_units(state, [_unit(7), _unit(8)], 1000, GRACE)
    model.assign_units(state, [_unit(8)], 2000, GRACE)
    primary, _ = model.assign_units(state, [_unit(7), _unit(8)], 3000, GRACE)
    assert primary["deviceId"] == 7 and "primary_missing" not in state


def test_assign_units_without_storage():
    assert model.assign_units({}, [], 1000, GRACE) == (None, [])


def _entry(rid, ident, disabled=False):
    return {"id": rid, "ident": ident, "disabled": disabled}


def test_plan_disables_missing_devices_first_and_removes_them_after_the_grace_period():
    entries = [_entry("a", "10"), _entry("b", "10_dev8")]
    enable, disable, remove, missing = model.plan_device_changes({"10"}, entries, {}, 1000, GRACE)
    assert (enable, disable, remove) == ([], ["b"], [])
    assert missing == {"10_dev8": 1000}
    # already disabled, still inside the grace period: nothing to do
    entries = [_entry("a", "10"), _entry("b", "10_dev8", disabled=True)]
    assert model.plan_device_changes({"10"}, entries, missing, 2000, GRACE)[:3] == ([], [], [])
    # after the grace period it is removed
    enable, disable, remove, missing2 = model.plan_device_changes({"10"}, entries, missing, 1001 + GRACE, GRACE)
    assert remove == ["b"] and disable == []


def test_plan_enables_a_device_that_comes_back_and_forgets_the_missing_mark():
    entries = [_entry("b", "10_dev8", disabled=True)]
    enable, disable, remove, missing = model.plan_device_changes(
        {"10", "10_dev8"}, entries, {"10_dev8": 1000}, 2000, GRACE
    )
    assert enable == ["b"] and disable == [] and remove == [] and missing == {}


def test_plan_removes_identifiers_of_version_0_3_3_at_once():
    entries = [_entry("old", "10_unit2"), _entry("main", "10")]
    enable, disable, remove, missing = model.plan_device_changes({"10"}, entries, {}, 1000, GRACE)
    assert remove == ["old"] and disable == [] and missing == {}


def test_plan_does_not_enable_devices_the_user_disabled():
    # a wanted device that is not disabled by the integration is left alone
    entries = [_entry("a", "10", disabled=False)]
    assert model.plan_device_changes({"10"}, entries, {}, 1000, GRACE)[:3] == ([], [], [])


def test_parse_device_time_is_local_time_of_the_plant():
    berlin = timezone(timedelta(hours=1))
    out = model.parse_device_time("2026-11-8 16:25:24", berlin)
    assert out.isoformat() == "2026-11-08T16:25:24+01:00"
    assert model.parse_device_time("2026-11-08 16:25:24", berlin).day == 8
    assert model.parse_device_time("not a date", berlin) is None
    assert model.parse_device_time(None, berlin) is None
    assert model.parse_device_time("2026-11-8 16:25:24", None) is None


def test_unit_values_prefer_the_device_screen():
    device = {"soc": 60.0, "batteryStatus": "DISCHARGE", "batteries": [{"remainingCapacity": 1.4}]}
    dev = {
        "BT_SOC": 68.0, "DAY_GEN": 0.56, "TOT_GEN": 169.94, "BAT_DAY_CE": 0.36, "BAT_TOT_CE": 78.8,
        "BAT_DAY_DCE": 0.3, "BAT_TOT_DCE": 73.29, "BAT_TIME": "2026-11-8 16:25:24",
    }
    out = model.unit_values(device, dev, timezone.utc)
    assert out["soc"] == 68.0
    assert out["remaining_energy"] == 1.4 and out["battery_status"] == "DISCHARGE"
    assert (out["pv_today"], out["pv_total"]) == (0.56, 169.94)
    assert (out["charge_today"], out["charge_total"]) == (0.36, 78.8)
    assert (out["discharge_today"], out["discharge_total"]) == (0.3, 73.29)
    assert out["device_time"].hour == 16


def test_unit_battery_power_sign_follows_the_unit_status_and_pv_power_is_the_input_total():
    dev = {"BAT_P": 15.0, "TOT_PV_IN_P": 230.0}
    discharging = model.unit_values({"batteryStatus": "DISCHARGE"}, dev, timezone.utc)
    assert discharging["battery_power"] == -15.0 and discharging["pv_power"] == 230.0
    charging = model.unit_values({"batteryStatus": "CHARGE"}, {"BAT_P": -15.0}, timezone.utc)
    assert charging["battery_power"] == 15.0


def test_unit_values_without_device_screen_fall_back_to_the_device_list():
    out = model.unit_values({"soc": 60.0}, {"BT_SOC": "n/a"}, timezone.utc)
    assert out["soc"] == 60.0
    assert out["charge_total"] is None and out["device_time"] is None
    assert out["battery_power"] is None and out["pv_power"] is None


def test_parse_station_without_extra_units_has_empty_list():
    assert model.parse_station(STATION, FLOW_DISCHARGE, DEVICES)["units"] == []


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
