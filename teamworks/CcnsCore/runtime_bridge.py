from __future__ import annotations

import sys
from pathlib import Path


def add_repo_root_to_path() -> Path:
    current_file = Path(__file__).resolve()
    repo_root = current_file.parents[2]
    repo_root_str = str(repo_root)
    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)
    return repo_root


def build_runtime():
    add_repo_root_to_path()
    from application.bootstrap.bootstrap_runtime import build_runtime_container
    return build_runtime_container()


def summary() -> dict[str, int]:
    runtime = build_runtime()
    return {
        "classifications": len(runtime.classifications.list_all()),
        "salary_grids": len(runtime.salary_grids.list_all()),
        "salary_grid_lines": len(runtime.salary_grid_lines.list_all()),
        "calculation_rules": len(runtime.calculation_rules.list_all()),
    }
