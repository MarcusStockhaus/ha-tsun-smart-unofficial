# Mitmachen

[English](CONTRIBUTING.md)

Dies ist eine **inoffizielle** Integration für den TSUN DCU2000Lite über die Cloud-Schnittstelle der TSUN-Smart-App.

## Am hilfreichsten: Geräte-Berichte
Andere TSUN-Geräte in derselben App funktionieren eventuell schon. Eröffne bitte einen *Geräte-Bericht* mit dem
**geschwärzten Diagnose-Download** (Einstellungen → Geräte & Dienste → TSUN Smart (inoffiziell) → ⋮ → Diagnose herunterladen).
Prüfe die Datei vor dem Anhängen auf persönliche Daten. Schreib dazu, was die App zeigt, Home Assistant aber nicht.

## Code
- `model.py` bleibt frei von Home-Assistant-Importen; Änderungen mit Tests in `tests/` (`pytest`) absichern.
- Entitätsnamen stehen in `translations/en.json` **und** `translations/de.json` (ein Test prüft gleiche Schlüssel).
- Keine Funktionen, die die TSUN-Cloud stärker belasten (keine Abfrage unter 5 Minuten).
- Keine Geheimnisse, Tokens oder persönlichen Daten in Commits, Issues, Tests oder Fixtures.

## Endpunkte finden
Siehe [docs/API.de.md](docs/API.de.md) für den bekannten Stand. Neue Felder oder Endpunkte bitte über den Knopf *Geräte-Bericht vorbereiten* und ein Geräte-Bericht-Issue melden, niemals mit Tokens, Passwörtern oder Seriennummern.
