from __future__ import annotations

import subprocess
import sys
from pathlib import Path


TOOLS = Path(__file__).resolve().parents[1] / "tools"


def run_tool(name: str, *args: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(TOOLS / name), *(str(arg) for arg in args)],
        capture_output=True,
        text=True,
        check=False,
    )


def test_ast_inventory_tools_fail_closed_on_unparsed_python(tmp_path: Path) -> None:
    source_root = tmp_path / "teamworks"
    source_root.mkdir()
    (source_root / "broken.py").write_text("def broken(:\n", encoding="utf-8")

    results = {
        "imports externes": run_tool(
            "inventory_external_imports.py", "--path", source_root
        ),
        "branches Phoenix": run_tool(
            "find_redundant_phoenix_branches.py", source_root, "--check"
        ),
        "defaults mutables": run_tool("find_mutable_defaults.py", source_root),
        "compilation": run_tool(
            "inventory_python_compile_errors.py", "--path", source_root
        ),
    }

    assert all(result.returncode != 0 for result in results.values()), {
        label: (result.returncode, result.stdout, result.stderr)
        for label, result in results.items()
    }


def test_inventory_tools_stay_successful_for_parseable_python(tmp_path: Path) -> None:
    source_root = tmp_path / "teamworks"
    source_root.mkdir()
    (source_root / "ok.py").write_text("VALUE = 1\n", encoding="utf-8")

    results = {
        "imports externes": run_tool(
            "inventory_external_imports.py", "--path", source_root
        ),
        "branches Phoenix": run_tool(
            "find_redundant_phoenix_branches.py", source_root, "--check"
        ),
        "defaults mutables": run_tool("find_mutable_defaults.py", source_root),
        "compilation": run_tool(
            "inventory_python_compile_errors.py", "--path", source_root
        ),
    }

    assert all(result.returncode == 0 for result in results.values()), {
        label: (result.returncode, result.stdout, result.stderr)
        for label, result in results.items()
    }
