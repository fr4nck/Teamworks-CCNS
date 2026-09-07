from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import sys

from .driver import WindowsRecipeDriver
from .errors import BlockedEnvironment, DestructiveDialogDetected, RecipeError
from .scenarios import SCENARIOS


def repository_root():
    return Path(__file__).resolve().parents[2]


def build_parser():
    parser = argparse.ArgumentParser(description="Recette Windows interactive Teamworks-CCNS wx")
    parser.add_argument("--scenario", choices=sorted(SCENARIOS), default="individus-smoke")
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--backend", choices=("uia", "win32"), default="uia")
    parser.add_argument("--artifacts", type=Path, default=None)
    return parser


def _read_keyboard_trace(artifacts):
    path = artifacts / "keyboard-focus.json"
    if not path.is_file():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return []


def _write_result(artifacts, result):
    (artifacts / "result.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def main(argv=None):
    args = build_parser().parse_args(argv)
    root = repository_root()
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    artifacts = args.artifacts or root / "artifacts" / "recette-windows" / (stamp + "-" + args.scenario)
    driver = WindowsRecipeDriver(root, artifacts, timeout=args.timeout, backend=args.backend)
    result = {
        "scenario": args.scenario,
        "status": "running",
        "backend": args.backend,
    }
    failure = None
    exit_status = 0
    try:
        driver.start()
        scenario_result = SCENARIOS[args.scenario](driver)
        result.update(scenario_result)
        result["status"] = "ok"
        print("OK %s: %s" % (args.scenario, result["action"]))
    except DestructiveDialogDetected as exc:
        failure = exc
        exit_status = 3
        result.update({"status": "stopped-destructive", "error": str(exc)})
        driver.capture_failure(exc)
        print("STOP DESTRUCTIF: %s" % exc, file=sys.stderr)
    except BlockedEnvironment as exc:
        failure = exc
        exit_status = 4
        result.update({"status": "BLOCKED", "error": str(exc)})
        driver.capture_failure(exc)
        print("BLOCKED: %s" % exc, file=sys.stderr)
    except (RecipeError, LookupError, RuntimeError) as exc:
        failure = exc
        exit_status = 2
        result.update({"status": "ko", "error": str(exc)})
        driver.capture_failure(exc)
        print("KO %s: %s" % (args.scenario, exc), file=sys.stderr)
    finally:
        if driver.process is not None:
            try:
                driver.dump_windows()
            except Exception as exc:
                (artifacts / "windows-dump-error.txt").write_text(repr(exc), encoding="utf-8")
            driver.shutdown(graceful=failure is None)
        result["keyboard"] = _read_keyboard_trace(artifacts)
        result["exit_status"] = exit_status
        _write_result(artifacts, result)
    return exit_status
