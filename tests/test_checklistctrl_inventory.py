from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS = ROOT / "teamworks"
MIXIN = re.compile(r"(?m)^[ \t]*CheckListCtrlMixin\.__init__\(self\)[ \t]*$")
FORBIDDEN = (
    "InsertItem(six.MAXSIZE,",
    "InsertItem(sys.maxsize,",
    "InsertStringItem(six.MAXSIZE,",
    "InsertStringItem(sys.maxsize,",
)


def test_all_checklist_mixins_enable_native_phoenix_checkboxes() -> None:
    initialisations = 0
    files = []
    for path in sorted(TEAMWORKS.rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        count = len(MIXIN.findall(source))
        if not count:
            continue
        initialisations += count
        files.append(path)
        assert source.count("self.EnableCheckBoxes(True)") >= count, path
        for token in FORBIDDEN:
            assert token not in source, (path, token)
        compile(source, str(path), "exec")

    assert initialisations >= 10
    assert len(files) >= 9


def test_secondary_checklist_smoke_covers_high_risk_controls() -> None:
    source = (ROOT / "tools" / "smoke_checklist_controls.py").read_text(encoding="utf-8")
    for stage in (
        "gadgets",
        "config-personnes",
        "selection",
        "publipostage",
        "frais",
        "remboursement",
        "statistiques",
        "modeles",
        "modele-contrat",
    ):
        assert f"TEAMWORKS_SMOKE_CHECKLIST_STAGE:{stage}" in source
    assert "TEAMWORKS_SMOKE_CHECKLIST_CONTROLS_READY" in source
    assert "TEAMWORKS_SMOKE_CHECKLIST_CONTROLS_FAILED" in source
