# -*- coding: utf-8 -*-
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "scripts" / "audit_runtime_risks.py"


def load_audit_module():
    spec = importlib.util.spec_from_file_location("audit_runtime_risks", AUDIT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_module(root, source):
    package = root / "teamworks"
    package.mkdir()
    path = package / "sample.py"
    path.write_text(source, encoding="utf-8")
    return path


def test_reports_removed_python2_builtin(tmp_path):
    audit = load_audit_module()
    write_module(tmp_path, "def values():\n    return xrange(3)\n")

    result = audit.run(tmp_path)

    findings = [
        finding
        for finding in result["findings"]
        if finding["category"] == "python2-removed-builtin"
    ]
    assert len(findings) == 1
    assert findings[0]["detail"] == "xrange is unavailable on Python 3"
    assert findings[0]["line"] == 2


def test_ignores_explicit_compatibility_alias(tmp_path):
    audit = load_audit_module()
    write_module(
        tmp_path,
        "try:\n"
        "    basestring\n"
        "except NameError:\n"
        "    basestring = str\n"
        "\n"
        "def is_text(value):\n"
        "    return isinstance(value, basestring)\n",
    )

    result = audit.run(tmp_path)

    assert result["counts"].get("python2-removed-builtin", 0) == 0


def test_audit_declares_blocking_cli_option():
    source = AUDIT_PATH.read_text(encoding="utf-8")
    assert '"--fail-on-python2-builtins"' in source
    assert 'result["counts"].get("python2-removed-builtin", 0)' in source
