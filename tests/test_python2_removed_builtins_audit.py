# -*- coding: utf-8 -*-
import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "scripts" / "audit_runtime_risks.py"


def load_audit_module():
    module_name = "audit_runtime_risks"
    spec = importlib.util.spec_from_file_location(module_name, AUDIT_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(module_name, None)
        raise
    return module


def write_module(root, source):
    package = root / "teamworks"
    package.mkdir()
    path = package / "sample.py"
    path.write_text(source, encoding="utf-8")
    return path


def python2_findings(result):
    return [
        finding
        for finding in result["findings"]
        if finding["category"] == "python2-removed-builtin"
    ]


def test_reports_removed_python2_builtin(tmp_path):
    audit = load_audit_module()
    write_module(tmp_path, "def values():\n    return xrange(3)\n")

    findings = python2_findings(audit.run(tmp_path))

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

    assert python2_findings(audit.run(tmp_path)) == []


def test_reports_module_use_before_later_binding(tmp_path):
    audit = load_audit_module()
    write_module(tmp_path, "print(xrange)\nxrange = range\n")

    findings = python2_findings(audit.run(tmp_path))

    assert len(findings) == 1
    assert findings[0]["line"] == 1
    assert findings[0]["detail"] == "xrange is unavailable on Python 3"


def test_accepts_module_use_after_binding(tmp_path):
    audit = load_audit_module()
    write_module(tmp_path, "xrange = range\nprint(xrange)\n")

    assert python2_findings(audit.run(tmp_path)) == []


def test_audit_declares_blocking_cli_option():
    source = AUDIT_PATH.read_text(encoding="utf-8")
    assert '"--fail-on-python2-builtins"' in source
    assert 'result["counts"].get("python2-removed-builtin", 0)' in source
