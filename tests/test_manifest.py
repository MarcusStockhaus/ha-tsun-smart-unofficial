import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
INT = ROOT / "custom_components" / "tsun_smart_unofficial"


def test_manifest_domain_matches_folder():
    manifest = json.loads((INT / "manifest.json").read_text())
    assert manifest["domain"] == INT.name


def test_translations_have_same_keys():
    def keys(d, prefix=""):
        for k, v in d.items():
            if isinstance(v, dict):
                yield from keys(v, f"{prefix}{k}.")
            else:
                yield f"{prefix}{k}"

    en = set(keys(json.loads((INT / "translations" / "en.json").read_text())))
    de = set(keys(json.loads((INT / "translations" / "de.json").read_text())))
    assert en == de
