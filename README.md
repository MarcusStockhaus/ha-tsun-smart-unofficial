<p align="center">
  <a href="README.md">English</a> · <a href="README.de.md">Deutsch</a>
</p>

<p align="center">
  <img src="custom_components/tsun_smart_unofficial/brand/icon@2x.png" width="140" alt="TSUN Smart (unofficial) icon">
</p>

<h1 align="center">TSUN Smart (unofficial)</h1>
<p align="center"><strong>Home Assistant integration for the TSUN SolarCan DCU2000Lite — via the cloud of the TSUN Smart app.</strong></p>

<p align="center">
  <a href="https://github.com/hacs/integration"><img alt="HACS Custom" src="https://img.shields.io/badge/HACS-Custom-41BDF5"></a>
  <img alt="Status" src="https://img.shields.io/badge/status-early%20%E2%80%A2%20tested%20on%20DCU2000Lite-orange">
  <a href="LICENSE"><img alt="GPL-3.0" src="https://img.shields.io/badge/license-GPL--3.0-blue"></a>
</p>

> [!IMPORTANT]
> **Unofficial community project. Not affiliated with, endorsed by or supported by TSUN / TSUNESS.**
> "TSUN", "TSUN Smart" and "SolarCan" are names of their respective owners and are used here only to
> describe what the integration works with. It talks to the same cloud API as the TSUN Smart app, which is
> **not a documented public API** and can change or stop working at any time. Use it at your own risk.

## Why this exists

The **DCU2000Lite** (DC-coupled storage unit) has **no local interface**: its WiFi logger only exposes a web
page on port 80, port 8899 is closed, and the cloud connection is TLS-encrypted. Local projects such as
[tsun-local](https://github.com/jptstar/tsun-local) and [tsun-gen3-proxy](https://github.com/s-allius/tsun-gen3-proxy)
therefore cannot read it (see [tsun-gen3-proxy discussion #525](https://github.com/s-allius/tsun-gen3-proxy/discussions/525)).

What *does* work is the **cloud of the TSUN Smart app** — the same values you see in the app. This integration
reads them and gives you the storage state in Home Assistant.

**Built for and tested on:** TSUN SolarCan **DCU2000Lite**. Everything else is untested — see
[help wanted](#help-wanted-other-devices).

## What you get

| Entity | Description |
|---|---|
| Battery SoC | State of charge in % |
| Battery power | W, **positive = charging, negative = discharging** |
| Remaining energy | kWh left in the pack(s) |
| PV power / PV energy today | from the station summary |
| Charged / discharged today | kWh |
| PV / charged / discharged total | lifetime kWh counters (never reset at midnight; best choice for the Energy dashboard) |
| Battery details | voltage, current, min/max temperature, health (SOH), cell voltages (min/max), remaining capacity (Ah), depth of discharge, work mode (e.g. *Constant Power Mode*) |
| PV inputs and output | PV1/PV2 power and temperature (voltage and current are disabled by default; the PV temperatures are those of the MPPT inputs inside the DCU, not of the panels), output power and state |
| Logger signal level | diagnostics, disabled by default; the scale is unclear (the app shows a different number on the logger page) |
| House connection *(only if a smart meter reports to the cloud; experimental)* | consumption power, grid power (**+ import / − export**), grid status; disabled by default: grid import / export / consumption totals, smart meter type and per-phase power |
| Battery status | e.g. `discharge` |
| Cloud status, Last cloud update | diagnostics |
| Online (binary sensor) | `off` while the logger is offline |
| Device report (Configure dialog or button) | shows a prefilled GitHub issue link and an e-mail link, see [help wanted](#help-wanted-other-devices) |

The battery and PV details come from the same screen the app shows under *Devices → Battery → Real-time*; they are only created if your system delivers them. The house-connection sensors were seen on one system with a smart meter (an EcoTracker-compatible meter feeding the DCU, with its values modified by the owner), so treat them as **experimental**: with import the grid power matches the meter, the sign for feed-in is not verified yet, and the three totals were the meter's own counters divided by 1000 and with import/export swapped, so they are disabled by default and not suitable for the energy dashboard. These values are also snapshots that the logger uploads every 5 minutes, not continuous measurements.

The values of one update can come from slightly different moments: the cloud does not give every value its own timestamp, so related values (for example remaining energy and remaining capacity) may briefly not match.

Systems with several storage units and devices that disappear are described under [Several storage units](#several-storage-units-in-one-plant) below.

Values arrive about **every 5 minutes** (that is how often the logger reports to the cloud).
Polling more often does not give newer data — the interval is configurable between 5 and 60 minutes.

### Offline behaviour
The DCU's logger is **offline at night / when the battery is low** (seen at 20 % SoC). The cloud then keeps the
last known values and reports `ALL_OFFLINE`. The integration shows those last values; use the **Online** sensor
and **Last cloud update** to see how fresh they are.

### Several storage units in one plant
*Added in 0.3.3 and 0.3.4, not yet verified on a system with two units — please report how it works for you.*

For example two DCU2000Lite in one plant of the TSUN Smart app:
- **Plant values** (state of charge, power, charged/discharged, PV totals) come from the cloud's plant total and cover all units together. The remaining energy adds up the packs of all units.
- **The first unit seen** is the main device of the plant ("TSUN *plant name*") and keeps its entities exactly as before. It stays the main device even if the cloud lists the units in a different order.
- **Every further unit** gets its own device ("TSUN *plant name* storage 2", "storage 3", …) with its own state of charge, remaining energy and battery status, the same detail sensors (voltage, current, temperatures, cell voltages, SOH, …) and the logger signal level. The units are told apart by their cloud device id, and each keeps its number.
- If you used 0.3.3 with two units in one plant, the entities of "storage 2" are replaced by new ones in 0.3.4.

### When a unit or plant disappears from the cloud
If the TSUN cloud no longer lists a storage unit or a whole plant (for example a unit taken out of the plant for a repair, moved to another plant, or a deleted plant), the integration does not delete anything at once:
1. The device and its entities are **disabled** in Home Assistant. Their history stays.
2. If the cloud lists the device again, it is **enabled again** automatically and the integration reloads itself; the history continues.
3. A device that stays missing for **30 days** is **removed** with its entities. (The recorded history of removed entities stays in the database until the recorder purges it.)
4. This only happens after a successful update that returned at least one plant, so a cloud hiccup does not touch your devices. You can also delete a stale device by hand on its device page.

If the main unit is missing for more than 30 days and another unit is still present, the other unit becomes the main device of the plant (its values then appear on the plant device).

Tips: For a repair, the simplest way is to leave the unit in the plant in the app and only disconnect it. A user reported that removing a device in the app also deletes the statistics the app has collected for it. Also note that the plant totals of the cloud may change when a unit is missing; how the cloud calculates them in that case is unknown, so check your energy dashboard if you use them there.

### Energy dashboard (DC-coupled setups)
The DCU2000Lite is DC-coupled: the panels charge the battery directly, and the battery feeds your micro-inverter (e.g. Hoymiles). If you add the battery to the Energy dashboard **and** use the micro-inverter's AC yield as the solar source, the battery discharge is counted twice (it is already inside the inverter yield).

Suggested setup (author's own system, still being verified):
- **Solar:** *PV energy total* of this integration (instead of the inverter's yield).
- **Battery:** energy going *out of* the battery = *Discharged total*, energy going *into* the battery = *Charged total*. The battery power sensor is optional; the cloud reports charging as negative, this integration shows charging as positive, so choose "inverted" if you add it.
- The cloud data lags real time by roughly 3-10 minutes, and the DCU itself seems to draw about 15 W. Small deviations are normal.
- Please report your experience in an issue.

## Requirements

- Home Assistant **2025.1** or newer
- A **TSUN Smart** app account (private user, e-mail login) that contains your DCU2000Lite.
  The installer/business portal (`pro.talent-monitoring.com` web UI) rejects private accounts — that is expected;
  the app API behind it accepts them.

## Installation

### HACS (custom repository)
1. HACS → ⋮ → **Custom repositories** → add `https://github.com/MarcusStockhaus/ha-tsun-smart-unofficial`, category **Integration**.
2. Install **TSUN Smart (unofficial)**, restart Home Assistant.
3. Settings → Devices & services → **Add integration** → *TSUN Smart (unofficial)*.
4. Enter the e-mail and password of your TSUN Smart app account.

### Manual
Copy `custom_components/tsun_smart_unofficial` into your Home Assistant `config/custom_components/`, restart, then continue with step 3.

## Privacy & security

- Only a **SHA-256 hash of your password** is stored in Home Assistant (the cloud login expects exactly that hash). It is
  still a credential — protect your Home Assistant backups.
- Credentials and data go **only to `pro.talent-monitoring.com`** (TSUN's cloud), nothing else.
- The client sends the same `User-Agent` as the app, because that is what the API was observed with.
- Diagnostics downloads are redacted (serial numbers, address, coordinates, names, tokens, station and device IDs, set-up dates) — still skim them before posting. The file starts with a block `home_assistant` / `custom_components` that Home Assistant itself adds (it lists *all* your integrations): delete that block before you share the file.

## Terms of use of the TSUN cloud

The published [Terms of Service](https://pro.talent-monitoring.com/agreement_docs/service_en.html) (version of 30 Sep 2023)
contain no explicit prohibition or permission for third-party/automated access. They ask users not to interfere with the proper
functioning of the system. This integration polls only your own account every 5 minutes or slower, like the app. This is
not legal advice; the terms may change.

## Help wanted: other devices

The cloud API is organised per **station** with generic fields (PV, grid, load, battery), so other TSUN products
in the same app *may* work or can be added easily — but only the DCU2000Lite has been verified.

You can help without writing code:

1. Install the integration and open Settings → Devices & services → TSUN Smart (unofficial) → **Configure** → **Create device report** (the diagnostic button *Prepare device report* does the same, but only shows a notification).
2. A Home Assistant notification appears with a link. It opens a **prefilled GitHub issue** that contains only the
   *structure* of your cloud data (device types, product IDs, which fields have data) — **no values, serial numbers,
   names or addresses**. Nothing is sent automatically; you review and submit it yourself.
3. **No GitHub account?** The notification also contains an e-mail link to the maintainer and the report text to copy.
4. Add what the app shows that is missing here. For more detail you can also attach the redacted
   *Download diagnostics* file (check it for personal data first and delete the `home_assistant` / `custom_components` block at the top).

Pull requests are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).

## Related projects

| Project | Approach | DCU2000Lite |
|---|---|---|
| [tsun-local](https://github.com/jptstar/tsun-local) | local TCP 8899, read-only | not supported (port closed) |
| [tsun-gen3-proxy](https://github.com/s-allius/tsun-gen3-proxy) | local proxy → MQTT | not supported |
| [ha-talent-monitor](https://github.com/StephanU/ha-talent-monitor) | older cloud portal, PV sensors | not verified |
| **this project** | TSUN Smart app cloud API | **yes** |

## Limitations

- Read-only. No control of the DCU (mode, output power).
- Cloud dependent; no data when the DCU is offline; update interval ≥ 5 minutes.
- Unofficial API: can break without notice.

## Documentation

[API notes](docs/API.md) · [Contributing](CONTRIBUTING.md) · [Changelog](CHANGELOG.md) · [Security](SECURITY.md)

## License

[GNU GPL v3.0](LICENSE). Copyright (C) 2026 Marcus Stockhaus. This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License version 3. It is distributed without any warranty. Derived works must stay under the same license. All product names belong to their owners.
