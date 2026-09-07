from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import sys

from .driver import WindowsRecipeDriver
from .errors import DestructiveDialogDetected, RecipeError, UnsupportedRunner
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


def main(argv=None):
    args = build_parser().parse_args(argv)
    root = repository_root()
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    artifacts = args.artifacts or root / "artifacts" / "recette-windows" / (stamp + "-" + args.scenario)
    driver = WindowsRecipeDriver(root, artifacts, timeout=args.timeout, backend=args.backend)
    result = None
    failure = None
    exit_status = 0
    try:
        driver.start()
        result = SCENARIOS[args.scenario](driver)
        (artifacts / "result.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        print("OK %s: %s" % (args.scenario, result["action"]))
    except DestructiveDialogDetected as exc:
        failure = exc
        exit_status = 3
        driver.capture_failure(exc)
        print("STOP DESTRUCTIF: %s" % exc, file=sys.stderr)
    except UnsupportedRunner as exc:
        failure = exc
        exit_status = 4
        print("RUNNER NON SUPPORTE: %s" % exc, file=sys.stderr)
    except (RecipeError, LookupError, RuntimeError) as exc:
        failure = exc
        exit_status = 2
        driver.capture_failure(exc)
        print("KO %s: %s" % (args.scenario, exc), file=sys.stderr)
    finally:
        if driver.process is not None:
            driver.shutdown(graceful=failure is None)
    return exit_status
