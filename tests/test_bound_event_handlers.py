# -*- coding: utf-8 -*-
"""Guarde-fou statique pour les gestionnaires wxPython liés par ``self.Bind``.

Le contrôle partage le même moteur que l'audit runtime afin de suivre aussi les
handlers hérités des coques modernes ``CORE.*`` sans masquer les vrais oublis.
"""

from pathlib import Path

from scripts.audit_runtime_risks import audit_ast, source_lines


ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS = ROOT / "teamworks"


def test_all_bound_self_handlers_exist():
    missing: list[str] = []
    for path in sorted(TEAMWORKS.rglob("*.py")):
        try:
            findings = audit_ast(ROOT, path, source_lines(path))
        except (SyntaxError, UnicodeDecodeError):
            # Les inventaires de compilation dédiés couvrent déjà ces fichiers.
            continue
        missing.extend(
            f"{finding.path}:{finding.line} {finding.detail}"
            for finding in findings
            if finding.category == "missing-bound-handler"
        )

    assert not missing, "Gestionnaires wxPython absents :\n" + "\n".join(missing)
