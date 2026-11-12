# Notizen zur Cloud-Schnittstelle (inoffiziell, beobachtet)

[English](API.md)

Am 05.11.2026 anhand der Netzwerkanfragen der TSUN-Smart-App im eigenen Konto des Autors beobachtet.
Das ist **von TSUN nicht dokumentiert** und kann sich ändern. Host: `https://pro.talent-monitoring.com`.

## Warum nicht die Webportale?
- `pro.talent-monitoring.com` (Weboberfläche) ist für Gewerbe-/Installateurkonten: *„end users not allowed to log in“*.
- `www.talent-monitoring.com` nutzt ein älteres Backend (`/prod-api`), das Konten der TSUN-Smart-App nicht kennt.
- Die **App-Schnittstelle** auf `pro.talent-monitoring.com` akzeptiert Privatkonten.

## Login
`POST /oauth2-s/oauth/token`, `application/x-www-form-urlencoded`

```
grant_type=password&username=<E-Mail>&password=<SHA-256-Hex des Passworts>
&client_id=sdl_client&identity_type=2&system=TSUN
```
Antwort: `access_token` (JWT), `refresh_token`, `expires_in` ≈ 60 Tage, `token_type=bearer`.
Folgeaufrufe: `Authorization: bearer <access_token>`. Ein Refresh mit `grant_type=refresh_token` ist angenommen; die Integration fällt auf einen neuen Login zurück.

## Genutzte Endpunkte
| Zweck | Aufruf |
|---|---|
| Anlagen | `POST /station-s/station/query/list?page=1&size=9999`, Body `{"region":{…null…},"returnTag":true,"powerTypeList":null}` |
| Aktuelle Werte | `GET /station-s/station/statistic/current/flow/{stationId}?year=J&month=M&day=T` → `stationCurrentDto` |
| Echtzeitwerte eines Geräts | `POST /device-s/device-monitor/current-data`, Body `{"language":"en","siteId":"<stationId>","deviceId":"<deviceId des Speichers>","needRealTimeDataFlag":true,"tag":"version"}` → `paramCategoryList[].fieldList[]` mit `key`, `value`, `unit`, `storageName` (z. B. `BAT_V`, `BAT_C`, `BAT_MAX_T`, `BAT_P1_SOH`, `DC_V_PV1`); funktioniert mit einem Endkunden-Konto |
| Logger und WLAN-Signal | `GET /device-s/device-monitor/get-communication/{deviceId}` → Liste mit `signalIntensity` und den Kindgeräten |
| Geräte und Akkupacks | `GET /station-s/{stationId}/device/common?page=1&size=200` |

Weitere gesehene, noch ungenutzte Endpunkte: `…/summary/overview` (Online-Zähler), `…/electric/energy/analysis/{id}/day`, `…/chargeRatio/{id}`, `…/alert/list`.

## Felder (current/flow)
`batterySoc`, `batteryStatus` (`DISCHARGE`, …), `batteryPower`, `dischargePower`, `generationPower`, `generationValue`,
`chargeValue`, `dischargeValue`, `networkStatus` (`ALL_OFFLINE`, …), `updateTime` (Unix-Sekunden, springt nur etwa alle 30 Minuten), `lastUpdateTime` (Unix-Sekunden, 5-Minuten-Raster, Zeitstempel des neuesten Datenpunkts; die Daten hinken der Echtzeit etwa 3-10 Minuten hinterher).
`device/common`: `deviceType` 3 = Speicher (DCU), 18 = Logger/Gateway; `batteries[].soc/totalCapacity/remainingCapacity`
(`remainingCapacity` in kWh; `totalCapacity` sieht nach Ah aus).

Weitere in Geräte-Berichten gesehene Gerätetypen (nur Struktur, keine Werte geprüft):
- `deviceType` 5 = Smart Meter, der an die DCU meldet. Gesehen mit einem EcoTracker IR (Produkt `0_0084_5`, vom Besitzer emuliert) und laut Nutzerbericht einem Shelly Pro 3EM (Produkt `0_0517_5`).
- `deviceType` 15 = laut Nutzerbericht ein TSUN-Mikrowechselrichter (MS-Serie) mit eigenem Logger (Typ 18, Produkt `35_…`). Er hat `generationPower` und `generationToday`. Dieses System war vom Besitzer aus der Cloud ausgeschlossen, daher zeigten beide Geräte Status 3; die Felder wurden nie mit Werten gesehen, und die Integration legt für diesen Typ keine Sensoren an.
