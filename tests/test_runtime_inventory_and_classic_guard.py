from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS = ROOT / "teamworks"
INVENTORY_PATH = ROOT / "tools" / "inventory_python3_runtime_risks.py"


def load_inventory_module():
    spec = importlib.util.spec_from_file_location("inventory_python3_runtime_risks", INVENTORY_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_runtime_inventory_ignores_strings_and_comments(tmp_path: Path):
    module = load_inventory_module()
    source = tmp_path / "sample.py"
    source.write_text(
        '"""unicode long xrange()"""\n'
        '# raw_input() and file()\n'
        'value = unicode(payload)\n',
        encoding="utf-8",
    )

    report = module.inventory(tmp_path)

    assert report["total_occurrences"] == 1
    assert report["findings"][0]["risk"] == "unicode"
    assert report["findings"][0]["line"] == 3


def test_no_wx_classic_negative_platform_branches_remain():
    forbidden = (
        "'phoenix' not in wx.PlatformInfo",
        '"phoenix" not in wx.PlatformInfo',
    )
    findings = []

    for path in sorted(TEAMWORKS.rglob("*.py")):
        source = path.read_text(encoding="utf-8", errors="ignore")
        for marker in forbidden:
            if marker in source:
                findings.append(f"{path.relative_to(ROOT)}: {marker}")

    assert findings == []
