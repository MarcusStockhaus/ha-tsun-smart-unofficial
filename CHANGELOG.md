# Changelog / Änderungsprotokoll

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
