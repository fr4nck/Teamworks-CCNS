from __future__ import annotations

import ast
from pathlib import Path

import pytest

from domain.documents import DEFAULT_DOCUMENT_FIELD_REGISTRY
from infrastructure.documents import (
    TwdInspectionError,
    compare_twd_bytes,
    import_twd_file,
    inspect_twd_bytes,
)


ROOT = Path(__file__).resolve().parents[1]
CURRENT_DIR = ROOT / "teamworks" / "Static" / "Documents"
REAL_2019_DIR = ROOT / "tests" / "fixtures" / "twd" / "real" / "2019"

MODELS = (
    "Autorisation parentale mineurs - Exemple.twd",
    "Certificat de travail - Exemple.twd",
    "Confirmation d'embauche - Exemple.twd",
    "Contrat d'engagement éducatif - Exemple.twd",
    "Contrat à durée déterminée - Exemple.twd",
    "Lettre de refus - Exemple.twd",
)

VERIFIED_ALIASES = {
    "{NUMSECU}": "SALARIE_NUMERO_SECURITE_SOCIALE",
    "{CPNAISS}": "SALARIE_CODE_POSTAL_NAISSANCE",
    "{VILLENAISS}": "SALARIE_VILLE_NAISSANCE",
    "{ESSAI}": "CONTRAT_DUREE_ESSAI_JOURS",
    "{VALEURPOINT}": "CONTRAT_VALEUR_POINT",
}

UNRESOLVED_ALIASES = ("{NBREJOURS}", "{REPARTITION}", "{BRUTJOUR}")


@pytest.mark.parametrize("filename", MODELS)
def test_2019_real_fixture_matches_2026_repository_bytes(filename: str):
    old = (REAL_2019_DIR / filename).read_bytes()
    current = (CURRENT_DIR / filename).read_bytes()
    assert old == current

    diff = compare_twd_bytes(old, current, name_a=f"2019/{filename}", name_b=f"2026/{filename}")
    assert diff.same_format
    assert diff.is_identical
    assert not diff.warnings


@pytest.mark.parametrize("generation,base", (("2019", REAL_2019_DIR), ("2026", CURRENT_DIR)))
@pytest.mark.parametrize("filename", MODELS)
def test_every_available_real_generation_imports_non_destructively_and_deterministically(
    generation: str,
    base: Path,
    filename: str,
):
    path = base / filename
    before = path.read_bytes()
    first = import_twd_file(path)
    second = import_twd_file(path)
    assert path.read_bytes() == before, generation
    assert first.document.to_json() == second.document.to_json()
    assert first.source_hash == second.source_hash
    assert len(first.imported_assets) == 1
    assert first.imported_assets[0].to_bytes().startswith(b"BM")
    assert first.unsupported_features == second.unsupported_features


@pytest.mark.parametrize("filename", MODELS)
def test_multi_version_inventory_has_expected_wxrichtext_contract(filename: str):
    inv = inspect_twd_bytes((REAL_2019_DIR / filename).read_bytes(), source=f"2019/{filename}")
    assert inv.namespace == "http://www.wxwidgets.org"
    assert inv.richtext_version == "1.0.0.0"
    assert inv.xml_declaration == '<?xml version="1.0" encoding="UTF-8"?>'
    assert inv.paragraph_count > 0
    assert inv.text_run_count > 0
    assert inv.image_count == 1
    assert inv.image_types == ("image/bmp",)
    assert not inv.unknown_structures


def test_structural_diff_separates_cosmetic_business_style_asset_placeholder_and_structure_changes():
    base = b'''<?xml version="1.0" encoding="UTF-8"?>\n<richtext version="1.0.0.0" xmlns="http://www.wxwidgets.org"><paragraphlayout fontface="Tahoma" fontsize="8"><paragraph><text>{NOM} Bonjour</text></paragraph></paragraphlayout></richtext>'''
    cosmetic = base.replace(b"><paragraph", b">\n  <paragraph")
    cosmetic_diff = compare_twd_bytes(base, cosmetic, name_a="a", name_b="b")
    assert cosmetic_diff.same_format and cosmetic_diff.is_identical
    assert cosmetic_diff.warnings

    content = base.replace(b"Bonjour", b"Bonsoir")
    assert compare_twd_bytes(base, content, name_a="a", name_b="b").content_changes

    style = base.replace(b'fontface="Tahoma"', b'fontface="Arial"')
    assert compare_twd_bytes(base, style, name_a="a", name_b="b").style_changes

    placeholder = base.replace(b"{NOM}", b"{PRENOM}")
    assert compare_twd_bytes(base, placeholder, name_a="a", name_b="b").placeholder_changes

    structure = base.replace(b"</text>", b"</text><symbol>29</symbol>")
    assert compare_twd_bytes(base, structure, name_a="a", name_b="b").structural_changes

    version = base.replace(b'version="1.0.0.0"', b'version="9.9"')
    incompatible = compare_twd_bytes(base, version, name_a="a", name_b="b")
    assert not incompatible.same_format
    assert incompatible.potentially_incompatible


def test_inventory_reports_unknown_element_and_attribute_without_gui_dependency():
    raw = b'''<?xml version="1.0" encoding="UTF-8"?>\n<richtext version="1.0.0.0" xmlns="http://www.wxwidgets.org"><paragraphlayout futureattr="x"><paragraph><future>value</future></paragraph></paragraphlayout></richtext>'''
    inv = inspect_twd_bytes(raw, source="future.twd")
    assert "element:future" in inv.unknown_structures
    assert "paragraphlayout.futureattr" in inv.attributes


def test_invalid_xml_is_rejected_by_structural_inspector():
    with pytest.raises(TwdInspectionError, match="XML invalide"):
        inspect_twd_bytes(b"<richtext>", source="broken.twd")


def test_verified_legacy_aliases_are_canonical_and_unresolved_tokens_stay_unmapped():
    for token, canonical in VERIFIED_ALIASES.items():
        field = DEFAULT_DOCUMENT_FIELD_REGISTRY.get_by_legacy_token(token)
        assert field is not None
        assert field.key == canonical
        assert field.owner_domain == "rh"
        assert field.source_of_truth == "Teamworks-CCNS"
        assert field.resolver_id
    for token in UNRESOLVED_ALIASES:
        assert DEFAULT_DOCUMENT_FIELD_REGISTRY.get_by_legacy_token(token) is None


def test_domain_documents_architecture_guard_has_no_ui_database_or_teamworks_imports():
    forbidden_roots = {"wx", "PySide6", "PyQt5", "PyQt6", "GestionDB", "teamworks"}
    domain_dir = ROOT / "domain" / "documents"
    violations: list[str] = []
    for path in sorted(domain_dir.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            for name in names:
                root = name.split(".", 1)[0]
                if root in forbidden_roots:
                    violations.append(f"{path.relative_to(ROOT)} -> {name}")
    assert not violations, "Forbidden imports in domain.documents: " + ", ".join(violations)
