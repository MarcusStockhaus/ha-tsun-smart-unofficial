# Cloud API notes (unofficial, observed)

[Deutsch](API.de.md)

Observed on 5 Nov 2026 from the network requests of the TSUN Smart app on the author's own account.
This is **not documented by TSUN** and may change. Host: `https://pro.talent-monitoring.com`.

## Why not the web portals?
- `pro.talent-monitoring.com` (web UI) is for business/installer accounts: *"end users not allowed to log in"*.
- `www.talent-monitoring.com` uses an older backend (`/prod-api`) that does not know TSUN Smart app accounts.
- The **app API** on `pro.talent-monitoring.com` accepts private accounts.

## Login
`POST /oauth2-s/oauth/token`, `application/x-www-form-urlencoded`

```
grant_type=password&username=<e-mail>&password=<sha256 hex of password>
&client_id=sdl_client&identity_type=2&system=TSUN
```
Response: `access_token` (JWT), `refresh_token`, `expires_in` ≈ 60 days, `token_type=bearer`.
Later requests: `Authorization: bearer <access_token>`. A refresh with `grant_type=refresh_token` is assumed; the integration falls back to a new login.

## Endpoints used
| Purpose | Request |
|---|---|
| Stations | `POST /station-s/station/query/list?page=1&size=9999` body `{"region":{…null…},"returnTag":true,"powerTypeList":null}` |
| Current values | `GET /station-s/station/statistic/current/flow/{stationId}?year=Y&month=M&day=D` → `stationCurrentDto` |
| Device real-time values | `POST /device-s/device-monitor/current-data`, body `{"language":"en","siteId":"<stationId>","deviceId":"<storage deviceId>","needRealTimeDataFlag":true,"tag":"version"}` → `paramCategoryList[].fieldList[]` with `key`, `value`, `unit`, `storageName` (e.g. `BAT_V`, `BAT_C`, `BAT_MAX_T`, `BAT_P1_SOH`, `DC_V_PV1`); works with an end-user account |
| Logger and Wi-Fi signal | `GET /device-s/device-monitor/get-communication/{deviceId}` → list with `signalIntensity` and the child devices |
| Devices & battery packs | `GET /station-s/{stationId}/device/common?page=1&size=200` |

Other endpoints seen (not used yet): `…/summary/overview` (online counts), `…/electric/energy/analysis/{id}/day`, `…/chargeRatio/{id}`, `…/alert/list`.

## Fields (current/flow)
`batterySoc`, `batteryStatus` (`DISCHARGE`, …), `batteryPower`, `dischargePower`, `generationPower`, `generationValue`,
`chargeValue`, `dischargeValue`, `networkStatus` (`ALL_OFFLINE`, …), `updateTime` (Unix seconds, moves only about every 30 minutes), `lastUpdateTime` (Unix seconds, 5-minute grid, timestamp of the newest data point; the data lags real time by roughly 3-10 minutes).
`device/common`: `deviceType` 3 = storage (DCU), 18 = logger/gateway; `batteries[].soc/totalCapacity/remainingCapacity`
(`remainingCapacity` is kWh; `totalCapacity` looks like Ah).

Other device types seen in device reports (structure only, no values checked):
- `deviceType` 5 = smart meter that reports to the DCU. Seen with an EcoTracker IR (product `0_0084_5`, emulated by its owner) and, per a user report, a Shelly Pro 3EM (product `0_0517_5`).
- `deviceType` 15 = per a user report a TSUN micro-inverter (MS series) with its own logger (type 18, product `35_…`). It carries `generationPower` and `generationToday`. That system was excluded from the cloud by its owner, so both devices showed status 3; the fields have never been seen with values, and the integration creates no sensors for this type.
