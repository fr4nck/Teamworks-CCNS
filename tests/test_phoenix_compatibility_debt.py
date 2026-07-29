import importlib.util
from pathlib import Path


INVENTORY_PATH = Path("tools/inventory_legacy_compatibility_branches.py")
TEAMWORKS_PATH = Path("teamworks")
PHOENIX_DEBT_CEILING = 195
PHOENIX_FILE_CEILING = 76


def load_inventory_module():
    spec = importlib.util.spec_from_file_location(
        "inventory_legacy_compatibility_branches", INVENTORY_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def inventory_by_kind(report):
    return {item["kind"]: item for item in report["by_kind"]}


def test_phoenix_compatibility_debt_does_not_increase():
    module = load_inventory_module()
    report = module.inventory(TEAMWORKS_PATH)
    by_kind = inventory_by_kind(report)

    phoenix = by_kind.get(
        "phoenix PlatformInfo branch",
        {"occurrences": 0, "files": 0},
    )

    assert phoenix["occurrences"] <= PHOENIX_DEBT_CEILING, (
        "wxPython Phoenix compatibility branches increased from "
        f"{PHOENIX_DEBT_CEILING} to {phoenix['occurrences']}"
    )
    assert phoenix["files"] <= PHOENIX_FILE_CEILING, (
        "Files containing wxPython Phoenix compatibility branches increased from "
        f"{PHOENIX_FILE_CEILING} to {phoenix['files']}"
    )


def test_removed_legacy_runtime_branches_stay_absent():
    module = load_inventory_module()
    report = module.inventory(TEAMWORKS_PATH)
    by_kind = inventory_by_kind(report)

    forbidden = {
        "six.PY2",
        "sys.version_info[0] == 2",
        "sys.version_info < (3",
        "classic PlatformInfo branch",
    }
    remaining = {
        kind: by_kind[kind]["occurrences"]
        for kind in forbidden
        if by_kind.get(kind, {}).get("occurrences", 0)
    }

    assert remaining == {}, f"Legacy runtime branches returned: {remaining}"
