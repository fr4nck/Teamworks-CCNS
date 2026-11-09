# -*- coding: utf-8 -*-
"""Candidat Windows de recette : aucun push ne doit publier sa release."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"


def test_marqueur_candidate_only_declenche_un_build_sans_release():
    source = WORKFLOW.read_text(encoding="utf-8")
    package = source.split("  build-windows:", 1)[1]
    build_gate = package.split("    steps:", 1)[0]
    release_gate = package.split(
        "      - name: Publier la release GitHub", 1
    )[1].split("        shell: pwsh", 1)[0]

    # Le workflow existant doit compiler avec le marqueur explicite.
    assert "contains(github.event.head_commit.message, '[windows]')" in build_gate
    # La publication doit etre interdite au candidat de recette.
    assert "startsWith(github.ref, 'refs/tags/')" in release_gate
    assert "head_commit.message" not in release_gate
    # Un commit [windows] ne peut jamais suffire pour publier.
    assert "contains(github.event.head_commit.message" not in release_gate


def test_candidat_doit_etre_trace_par_sha_et_sha256():
    source = WORKFLOW.read_text(encoding="utf-8")
    assert 'Commit $env:GITHUB_SHA' in source
    assert 'SHA256SUMS.txt' in source
    assert 'PACKAGE-SHA256SUMS.txt' in source
    assert 'actions/upload-artifact@v6' in source
