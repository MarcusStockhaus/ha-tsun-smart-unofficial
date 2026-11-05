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
| Devices & battery packs | `GET /station-s/{stationId}/device/common?page=1&size=200` |

Other endpoints seen (not used yet): `…/summary/overview` (online counts), `…/electric/energy/analysis/{id}/day`, `…/chargeRatio/{id}`, `…/alert/list`.

## Fields (current/flow)
`batterySoc`, `batteryStatus` (`DISCHARGE`, …), `batteryPower`, `dischargePower`, `generationPower`, `generationValue`,
`chargeValue`, `dischargeValue`, `networkStatus` (`ALL_OFFLINE`, …), `updateTime` (Unix seconds).
`device/common`: `deviceType` 3 = storage (DCU), 18 = logger/gateway; `batteries[].soc/totalCapacity/remainingCapacity`
(`remainingCapacity` is kWh; `totalCapacity` looks like Ah).
