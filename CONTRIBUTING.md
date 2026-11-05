# Contributing

[Deutsch](CONTRIBUTING.de.md)

This is an **unofficial** integration for the TSUN DCU2000Lite using the cloud API of the TSUN Smart app.

## Most useful: device reports
Other TSUN devices in the same app may already work. Please open a *Device report* issue with the
**redacted diagnostics download** (Settings → Devices & services → TSUN Smart (unofficial) → ⋮ → Download diagnostics).
Check the file for personal data before attaching it. Mention what the app shows that Home Assistant does not.

## Code
- Keep `model.py` free of Home Assistant imports and cover changes with tests in `tests/` (`pytest`).
- Entity names go through `translations/en.json` **and** `translations/de.json` (a test checks both have the same keys).
- Do not add features that increase load on the TSUN cloud (no polling below 5 minutes).
- No secrets, tokens or personal data in commits, issues, tests or fixtures.

## Finding endpoints
See [docs/API.md](docs/API.md) for what is known. Please report new fields or endpoints through the *Prepare device report* button and a device report issue, never with tokens, passwords or serial numbers.
