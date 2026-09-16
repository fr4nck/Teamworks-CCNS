from __future__ import annotations

import hashlib
import os
from pathlib import Path
import subprocess
import sys
import textwrap

import pytest

from infrastructure.documents import LegacyTwdImportError, import_twd_bytes, import_twd_file


ROOT = Path(__file__).resolve().parents[1]
REAL_CORPUS_DIR = ROOT / "teamworks" / "Static" / "Documents"
TECHNICAL_FIXTURE = ROOT / "tests" / "fixtures" / "twd" / "TECHNIQUE_url_pagebreak.twd"

REAL_CORPUS = {
    "Autorisation parentale mineurs - Exemple.twd": {
        "recognized": {"{PRENOM}", "{NOM}"},
        "unknown": set(),
        "contains": "Autorisation parentale",
    },
    "Certificat de travail - Exemple.twd": {
        "recognized": {"{CIVILITE}", "{PRENOM}", "{NOM}", "{CLASSIFICATION}", "{DATEDEBUT}", "{DATEFIN}"},
        "unknown": {"{NUMSECU}"},
        "contains": "Certificat de travail",
    },
    "Confirmation d'embauche - Exemple.twd": {
        "recognized": {"{CIVILITE}", "{NOM}", "{PRENOM}", "{ADRESSERESID}", "{CPRESID}", "{VILLERESID}", "{CLASSIFICATION}", "{DATEDEBUT}", "{DATEFIN}"},
        "unknown": set(),
        "contains": "Confirmation",
    },
    "Contrat d'engagement éducatif - Exemple.twd": {
        "recognized": {"{CIVILITE}", "{NOM}", "{PRENOM}", "{DATENAISS}", "{ADRESSERESID}", "{CPRESID}", "{VILLERESID}", "{CLASSIFICATION}", "{DATEDEBUT}", "{DATEFIN}"},
        "unknown": {"{CPNAISS}", "{VILLENAISS}", "{NUMSECU}", "{ESSAI}", "{NBREJOURS}", "{REPARTITION}", "{BRUTJOUR}", "{VALEURPOINT}"},
        "contains": "engagement",
    },
    "Contrat à durée déterminée - Exemple.twd": {
        "recognized": {"{CIVILITE}", "{NOM}", "{PRENOM}", "{DATENAISS}", "{ADRESSERESID}", "{CPRESID}", "{VILLERESID}", "{CLASSIFICATION}", "{DATEDEBUT}", "{DATEFIN}"},
        "unknown": {"{CPNAISS}", "{VILLENAISS}", "{NUMSECU}", "{ESSAI}", "{NBREJOURS}", "{REPARTITION}", "{BRUTJOUR}", "{VALEURPOINT}"},
        "contains": "durée déterminée",
    },
    "Lettre de refus - Exemple.twd": {
        "recognized": {"{CIVILITE}", "{NOM}", "{PRENOM}", "{ADRESSERESID}", "{CPRESID}", "{VILLERESID}"},
        "unknown": set(),
        "contains": "Candidature",
    },
}


@pytest.mark.parametrize("filename", REAL_CORPUS)
def test_real_twd_corpus_imports_non_destructively(filename: str):
    path = REAL_CORPUS_DIR / filename
    before = path.read_bytes()
    before_hash = hashlib.sha256(before).hexdigest()

    result = import_twd_file(path)

    after = path.read_bytes()
    assert after == before
    assert result.source_hash == before_hash
    assert result.document.format_version == 1
    assert result.document.metadata.attributes["legacy_format"] == "wx-richtext-xml"
    assert result.document.metadata.attributes["legacy_namespace"] == "http://www.wxwidgets.org"
    assert result.document.metadata.attributes["legacy_version"] == "1.0.0.0"
    assert REAL_CORPUS[filename]["contains"] in result.document.html

    # Direct inspection of the six repository blobs shows one embedded BMP logo
    # at the start of each document. The importer must retain it as an Asset.
    assert len(result.imported_assets) == 1
    asset = result.imported_assets[0]
    assert asset.mime_type == "image/bmp"
    assert asset.to_bytes().startswith(b"BM")
    assert asset.uri in result.document.html
    assert result.document.assets == result.imported_assets

    assert set(result.placeholders_recognized) == REAL_CORPUS[filename]["recognized"]
    assert set(result.placeholders_unknown) == REAL_CORPUS[filename]["unknown"]
    for token in result.placeholders_unknown:
        assert token in result.document.html


@pytest.mark.parametrize("filename", REAL_CORPUS)
def test_real_twd_corpus_import_is_deterministic(filename: str):
    path = REAL_CORPUS_DIR / filename
    first = import_twd_file(path)
    second = import_twd_file(path)
    assert first.document.id == second.document.id
    assert [asset.id for asset in first.imported_assets] == [asset.id for asset in second.imported_assets]
    assert first.document.to_json() == second.document.to_json()


def test_real_corpus_exercises_observed_styles_and_symbol_line_break():
    refusal = import_twd_file(REAL_CORPUS_DIR / "Lettre de refus - Exemple.twd")
    assert "font-style: italic" in refusal.document.html
    assert "text-decoration: underline" in refusal.document.html
    assert "text-align: right" in refusal.document.html
    assert "margin-left: 100mm" in refusal.document.html

    contract = import_twd_file(REAL_CORPUS_DIR / "Contrat d'engagement éducatif - Exemple.twd")
    assert contract.document.metadata.attributes["legacy_symbol_29_line_breaks"] >= 1
    assert "<br>" in contract.document.html
    assert "font-weight: 700" in contract.document.html


def test_technical_fixture_covers_url_and_page_break_missing_from_real_corpus():
    result = import_twd_file(TECHNICAL_FIXTURE)
    assert '<a href="https://example.org/documentation">' in result.document.html
    assert "page-break-before: always" in result.document.html
    assert "margin-bottom: 1mm" in result.document.html
    assert "line-height: 1" in result.document.html
    assert result.imported_assets == ()
    assert result.placeholders_recognized == ()
    assert result.placeholders_unknown == ()


def test_unknown_placeholder_is_preserved_and_reported():
    raw = '''<?xml version="1.0" encoding="UTF-8"?>
<richtext version="1.0.0.0" xmlns="http://www.wxwidgets.org">
  <paragraphlayout><paragraph><text>{VARIABLE_INCONNUE}</text></paragraph></paragraphlayout>
</richtext>'''.encode("utf-8")
    result = import_twd_bytes(raw, source="fixture-technique-inconnue.twd")
    assert result.placeholders_unknown == ("{VARIABLE_INCONNUE}",)
    assert "{VARIABLE_INCONNUE}" in result.document.html
    assert any("non mappées" in warning for warning in result.warnings)


def test_unknown_element_keeps_visible_text_and_is_reported():
    raw = '''<?xml version="1.0" encoding="UTF-8"?>
<richtext version="1.0.0.0" xmlns="http://www.wxwidgets.org">
  <paragraphlayout><paragraph><mystery>texte conservé</mystery></paragraph></paragraphlayout>
</richtext>'''.encode("utf-8")
    result = import_twd_bytes(raw, source="fixture-technique-element.twd")
    assert "texte conservé" in result.document.html
    assert "paragraph-element:mystery" in result.unsupported_features


def test_invalid_or_non_wx_xml_is_rejected():
    with pytest.raises(LegacyTwdImportError, match="XML invalide"):
        import_twd_bytes(b"<richtext>", source="broken.twd")
    with pytest.raises(LegacyTwdImportError, match="Namespace TWD inattendu"):
        import_twd_bytes(b"<richtext><paragraphlayout /></richtext>", source="not-wx.twd")
    with pytest.raises(LegacyTwdImportError, match="DTD/entités XML interdits"):
        import_twd_bytes(
            b'<!DOCTYPE richtext [<!ENTITY x "boom">]><richtext xmlns="http://www.wxwidgets.org" />',
            source="entity.twd",
        )


def test_importer_and_document_core_do_not_require_wx_or_qt():
    source_root = str(ROOT)
    script = textwrap.dedent(
        '''
        import builtins
        from pathlib import Path

        real_import = builtins.__import__
        blocked = ("wx", "PySide6", "PyQt5", "PyQt6")
        def guarded_import(name, *args, **kwargs):
            if name.startswith(blocked):
                raise AssertionError("UI dependency imported: " + name)
            return real_import(name, *args, **kwargs)
        builtins.__import__ = guarded_import

        from infrastructure.documents import import_twd_file
        result = import_twd_file(Path("teamworks/Static/Documents/Autorisation parentale mineurs - Exemple.twd"))
        assert result.document.format_version == 1
        assert result.imported_assets
        print("TWD_PORTABLE_OK")
        '''
    )
    env = dict(os.environ)
    env["PYTHONPATH"] = source_root
    process = subprocess.run(
        [sys.executable, "-c", script],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert process.returncode == 0, process.stderr
    assert process.stdout.strip() == "TWD_PORTABLE_OK"
