from pathlib import Path

from application.services.document_template_catalog import (
    DocumentTemplateFormat,
    discover_document_template_files,
    discover_document_templates,
    legacy_software_choice_format,
)


def test_legacy_software_choice_mapping_matches_the_wx_publiposteur() -> None:
    assert legacy_software_choice_format(1) is DocumentTemplateFormat.WORD_LEGACY
    assert legacy_software_choice_format(2) is DocumentTemplateFormat.LIBREOFFICE
    assert legacy_software_choice_format(3) is DocumentTemplateFormat.TEAMWORD
    assert legacy_software_choice_format(4) is DocumentTemplateFormat.TEAMWORD


def test_unknown_legacy_software_choice_is_rejected() -> None:
    try:
        legacy_software_choice_format(99)
    except ValueError as exc:
        assert "99" in str(exc)
    else:
        raise AssertionError("un choix logiciel inconnu doit être refusé")


def test_discovery_filters_files_without_opening_templates(tmp_path: Path) -> None:
    (tmp_path / "b.odt").write_bytes(b"odt")
    (tmp_path / "a.odt").write_bytes(b"odt")
    (tmp_path / "c.doc").write_bytes(b"doc")
    (tmp_path / "ignore.txt").write_text("x", encoding="utf-8")
    (tmp_path / "subdir").mkdir()

    files = discover_document_template_files(
        tmp_path,
        template_format=DocumentTemplateFormat.LIBREOFFICE,
    )

    assert [item.name for item in files] == ["a.odt", "b.odt"]
    assert all(item.format is DocumentTemplateFormat.LIBREOFFICE for item in files)
    assert all(item.size_bytes == 3 for item in files)


def test_discovery_can_return_all_supported_formats(tmp_path: Path) -> None:
    for name in ("a.doc", "b.odt", "c.twd", "d.pdf"):
        (tmp_path / name).write_bytes(b"x")

    files = discover_document_template_files(tmp_path)

    assert [item.name for item in files] == ["a.doc", "b.odt", "c.twd"]


def test_domain_templates_are_enriched_with_injected_metadata(tmp_path: Path) -> None:
    (tmp_path / "contrat-g2.twd").write_bytes(b"x")
    (tmp_path / "legacy.twd").write_bytes(b"x")

    def metadata_loader(filename):
        if filename == "contrat-g2.twd":
            return {
                "convention_code": "CCNS",
                "ccns_group": "G2",
                "document_kind": "contract",
            }
        return None

    templates = discover_document_templates(
        tmp_path,
        template_format=DocumentTemplateFormat.TEAMWORD,
        metadata_loader=metadata_loader,
    )

    by_name = {item.name: item for item in templates}
    assert by_name["legacy.twd"].legacy is True
    assert by_name["contrat-g2.twd"].target is not None
    assert by_name["contrat-g2.twd"].target.convention_code == "CCNS"
    assert by_name["contrat-g2.twd"].target.ccns_group == "G2"
    assert by_name["contrat-g2.twd"].target.document_kind == "contract"


def test_missing_template_directory_returns_an_empty_catalog(tmp_path: Path) -> None:
    missing = tmp_path / "missing"

    assert discover_document_template_files(missing) == ()
    assert discover_document_templates(missing) == ()
