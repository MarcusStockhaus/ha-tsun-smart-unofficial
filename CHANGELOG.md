# Changelog / Änderungsprotokoll

## 0.3.2 – 2026-11-09
- EN: Battery health (SOH), minimum/maximum cell voltage, remaining capacity (Ah) and depth of discharge are now regular sensors instead of diagnostic ones, so they show up in dashboards and device cards. Firmware, output state, logger signal level and meter type stay diagnostic. Suggested by a tester.
- DE: Zustand (SOH), min./max. Zellspannung, Restkapazität (Ah) und Entladetiefe sind jetzt normale Sensoren statt Diagnosewerte und erscheinen damit in Dashboards und auf der Geräteseite. Firmware, Ausgangszustand, Signalstufe des Loggers und Zählertyp bleiben Diagnose. Anregung eines Testers.

## 0.3.1 – 2026-11-09
- EN: Voltages and currents are displayed with two decimals (a voltage of 50.43 V was shown as 50 V in some views; the value itself was always exact).
- DE: Spannungen und Ströme werden mit zwei Nachkommastellen angezeigt (50,43 V erschien in manchen Ansichten als 50 V; der Wert selbst war immer exakt).
- EN: The house-connection totals (grid import / export / consumption) are now disabled by default for new installations: on the only system seen so far they were the smart meter's own counters divided by 1000 with import and export swapped. Not suitable for the energy dashboard. Existing entities are not changed.
- DE: Die Zähler zum Hausanschluss (Bezug / Einspeisung / Verbrauch gesamt) sind für neue Installationen jetzt standardmäßig deaktiviert: Beim einzigen bisher gesehenen System waren es die Zählerstände des Smart Meters geteilt durch 1000 mit vertauschtem Bezug und Einspeisung. Für das Energie-Dashboard nicht geeignet. Bestehende Entitäten bleiben unverändert.
- EN: New, disabled by default: smart meter type and per-phase power from the device screen.
- DE: Neu, standardmäßig deaktiviert: Zählertyp und Leistung je Phase vom Geräte-Bildschirm.
- EN: The logger signal sensor is renamed to "Logger signal level"; its scale is unclear (the app shows a different number). README: the PV temperatures are those of the MPPT inputs inside the DCU, and values of one update can come from slightly different moments.
- DE: Der Logger-Sensor heißt jetzt "Signalstufe des Loggers"; die Skala ist unklar (die App zeigt eine andere Zahl). README: Die PV-Temperaturen sind die der MPPT-Eingänge im Inneren der DCU, und Werte eines Updates können aus leicht unterschiedlichen Zeitpunkten stammen.

## 0.3.0 – 2026-11-08
- EN: New battery detail sensors from the app's device screen (voltage, current, min/max temperature, health SOH, min/max cell voltage, remaining capacity in Ah, depth of discharge, work mode), PV1/PV2 and output values, firmware versions and the logger's Wi-Fi signal. They are created only if the cloud delivers a value. This works with a normal (end-user) account.
- DE: Neue Akku-Detailsensoren vom Geräte-Bildschirm der App (Spannung, Strom, Min-/Max-Temperatur, Zustand SOH, min./max. Zellspannung, Restkapazität in Ah, Entladetiefe, Arbeitsmodus), PV1/PV2- und Ausgangswerte, Firmware-Versionen und das WLAN-Signal des Loggers. Sie werden nur angelegt, wenn die Cloud einen Wert liefert. Funktioniert mit einem normalen Endkunden-Konto.
- EN: Experimental house-connection sensors (consumption, grid power, grid import/export/consumption totals), only if a smart meter reports to the cloud. Grid power: positive = import; the sign for feed-in is still to be verified.
- DE: Experimentelle Sensoren zum Hausanschluss (Verbrauch, Netzleistung, Zähler für Bezug/Einspeisung/Verbrauch), nur wenn ein Smart Meter an die Cloud meldet. Netzleistung: positiv = Bezug; das Vorzeichen bei Einspeisung ist noch zu prüfen.

## 0.2.5 – 2026-11-08
- EN: Diagnostics now also redact station, device and gateway IDs, set-up dates, time zone and country code, and the station ID is no longer used as a key. README: delete the `home_assistant` / `custom_components` block (added by Home Assistant, lists all your integrations) before sharing a diagnostics file.
- DE: Die Diagnose schwärzt jetzt auch Stations-, Geräte- und Gateway-IDs, Einrichtungsdaten, Zeitzone und Ländercode; die Stations-ID dient nicht mehr als Schlüssel. README: Den Block `home_assistant` / `custom_components` (von Home Assistant ergänzt, listet alle Integrationen) vor dem Teilen der Diagnosedatei löschen.

## 0.2.4 – 2026-11-07
- EN: The device report is now available in the integration's *Configure* dialog (menu: *Create device report*), with the links and copyable text shown right in the dialog. The button remains and creates a notification.
- DE: Der Geräte-Bericht ist jetzt im *Konfigurieren*-Dialog der Integration verfügbar (Menü: *Geräte-Bericht erstellen*), mit Links und kopierbarem Text direkt im Dialog. Der Knopf bleibt und erzeugt eine Benachrichtigung.
- EN: Device report e-mail is now compact but complete: it lists device types, product IDs and only the fields that are new compared to a known DCU2000Lite, instead of being cut off. The GitHub issue and the copyable text in Home Assistant still contain the full structure.
- DE: Die E-Mail des Geräte-Berichts ist jetzt kompakt, aber vollständig: Sie nennt Gerätetypen, Produkt-IDs und nur die Felder, die gegenüber einem bekannten DCU2000Lite neu sind, statt abgeschnitten zu werden. Das GitHub-Issue und der kopierbare Text in Home Assistant enthalten weiterhin die volle Struktur.
- EN: The report dialog now explains that the e-mail holds only a short summary and that the full report text should be pasted into it if the device differs from a DCU2000Lite.
- DE: Der Berichts-Dialog erklärt jetzt, dass die E-Mail nur eine Kurzfassung enthält und bei Abweichung von einer DCU2000Lite der volle Berichtstext eingefügt werden sollte.

## 0.2.3 – 2026-11-07
- EN: Setup dialog: the password field is now masked, and the e-mail address is kept after a failed login (the password is never kept).
- DE: Einrichtungsdialog: Das Passwortfeld ist jetzt maskiert, und die E-Mail-Adresse bleibt nach einer fehlgeschlagenen Anmeldung stehen (das Passwort nie).

## 0.2.2 – 2026-11-07
- EN: *Last cloud update* now uses `lastUpdateTime` (moves every 5 minutes with the data) instead of `updateTime` (only about every 30 minutes). Measured over one hour; the data lags real time by roughly 3-10 minutes.
- DE: *Letzte Cloud-Aktualisierung* nutzt jetzt `lastUpdateTime` (läuft alle 5 Minuten mit den Daten) statt `updateTime` (nur etwa alle 30 Minuten). Über eine Stunde gemessen; die Daten hinken der Echtzeit etwa 3-10 Minuten hinterher.

## 0.2.1 – 2026-11-06
- EN: New sensors *PV energy total*, *Charged total*, *Discharged total* (lifetime counters from the cloud, `total_increasing`; suited for the Energy dashboard).
- DE: Neue Sensoren *PV-Energie gesamt*, *Geladen gesamt*, *Entladen gesamt* (Lebenszeitzähler aus der Cloud, `total_increasing`; geeignet für das Energie-Dashboard).
- EN: Fix: a wrong password is answered by the cloud with HTTP 412 (`AUTH_INVALID_USERNAME_OR_PASSWORD`); this now correctly triggers the re-authentication dialog instead of endless "unavailable". Verified: refresh tokens work.
- DE: Korrektur: Bei falschem Passwort antwortet die Cloud mit HTTP 412 (`AUTH_INVALID_USERNAME_OR_PASSWORD`); das löst jetzt korrekt den Neuanmelde-Dialog aus statt dauerhaft „nicht verfügbar“. Geprüft: Refresh-Tokens funktionieren.

## 0.2.0 – unreleased / unveröffentlicht
- EN: First public structure. Domain `tsun_smart_unofficial`, config flow with re-auth and options (update interval 5–60 min), sensors for SoC, battery power (signed), remaining energy, PV power, daily energy, status; *Online* binary sensor; redacted diagnostics; English and German translations. Tested on a DCU2000Lite only. Button *Prepare device report* creates a prefilled GitHub issue link (structure only, nothing sent automatically).
- DE: Erste öffentliche Struktur. Domain `tsun_smart_unofficial`, Config-Flow mit Neuanmeldung und Optionen (Intervall 5–60 min), Sensoren für SoC, Akkuleistung (mit Vorzeichen), verbleibende Energie, PV-Leistung, Tagesenergie, Status; Binärsensor *Online*; geschwärzte Diagnose; englische und deutsche Übersetzungen. Nur am DCU2000Lite getestet. Knopf *Geräte-Bericht vorbereiten* erzeugt einen vorausgefüllten GitHub-Issue-Link (nur Struktur, nichts wird automatisch gesendet).

## 0.1.0 – internal / intern
- EN/DE: Private prototype (`tsun_smart`) / Privater Prototyp (`tsun_smart`).
