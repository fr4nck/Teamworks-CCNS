import json
import os
import subprocess
import sys
import textwrap

import pytest

from domain.documents import (
    Asset,
    DEFAULT_DOCUMENT_FIELD_REGISTRY,
    DocumentFormatError,
    DocumentMetadata,
    DocumentModel,
    HtmlMergeRenderer,
    MergeContext,
    MergeField,
    MergeFieldRegistry,
    UnknownMergeFieldError,
    build_merge_context,
    sanitize_html,
    validate_required_fields,
)
from domain.documents.legacy import upgrade_legacy_placeholders


def test_document_model_round_trip_with_asset_and_version():
    asset = Asset.from_bytes(content=b"fake-image", mime_type="image/png", name="logo.png")
    document = DocumentModel.create(document_type="contract", html=f'<p>Logo <img src="{asset.uri}" alt="Logo"></p>', metadata=DocumentMetadata(title="Contrat", owner_domain="rh"), assets=(asset,), render_options={"page_size": "A4", "margins_mm": [20, 20, 20, 20]})
    raw = document.to_json(); restored = DocumentModel.from_json(raw)
    assert restored == document
    assert restored.format_version == 1
    assert restored.assets[0].to_bytes() == b"fake-image"
    assert json.loads(raw)["metadata"]["owner_domain"] == "rh"


def test_document_model_rejects_unknown_format_version():
    document = DocumentModel.create(document_type="contract", html="<p>x</p>"); payload = document.to_dict(); payload["format_version"] = 99
    with pytest.raises(DocumentFormatError, match="Unsupported document format_version"):
        DocumentModel.from_dict(payload)


def test_document_model_rejects_non_json_metadata():
    with pytest.raises(DocumentFormatError, match="unsupported non-JSON"):
        DocumentMetadata(attributes={"bad": object()})


def test_default_registry_exposes_canonical_alias_and_provenance():
    field = DEFAULT_DOCUMENT_FIELD_REGISTRY.get("NOM")
    assert field is not None and field.key == "SALARIE_NOM"
    assert field.owner_domain == "rh" and field.source_of_truth == "Teamworks-CCNS"
    assert "{NOM}" in field.all_legacy_tokens() and field.resolver_id == "rh.employee.last_name"


def test_registry_rejects_identifier_collision():
    registry = MergeFieldRegistry([MergeField(key="SALARIE_NOM", label="Nom", owner_domain="rh", source_of_truth="Teamworks-CCNS", category="salarie", aliases=("NOM",))])
    with pytest.raises(ValueError, match="Duplicate merge-field identifier"):
        registry.register(MergeField(key="CONTACT_NOM", label="Nom contact", owner_domain="rh", source_of_truth="Teamworks-CCNS", category="contact", aliases=("NOM",)))


def test_sanitizer_removes_active_content_and_event_handlers():
    raw = '<p onclick="steal()" style="color: red; background-image:url(http://evil)">OK</p><script>alert(1)</script><iframe src="https://evil">bad</iframe>'
    cleaned = sanitize_html(raw)
    assert "onclick" not in cleaned and "script" not in cleaned and "iframe" not in cleaned and "alert" not in cleaned
    assert "background-image" not in cleaned and "color: red" in cleaned and "OK" in cleaned


def test_sanitizer_allows_safe_links_and_blocks_dangerous_protocols():
    cleaned = sanitize_html('<a href="https://example.org">web</a><a href="javascript:alert(1)">bad</a><img src="https://example.org/logo.png"><img src="asset://123e4567-e89b-12d3-a456-426614174000" alt="logo">')
    assert 'href="https://example.org"' in cleaned and "javascript:" not in cleaned
    assert 'src="https://example.org/logo.png"' not in cleaned
    assert 'src="asset://123e4567-e89b-12d3-a456-426614174000"' in cleaned


def test_semantic_merge_escapes_values_and_records_used_fields():
    document = DocumentModel.create(document_type="contract", html='<p>Bonjour <span data-pmsl-field="SALARIE_PRENOM">[Prénom]</span> <span data-pmsl-field="SALARIE_NOM">[Nom]</span></p>')
    result = HtmlMergeRenderer().render(document, MergeContext({"SALARIE_PRENOM": "Marie", "SALARIE_NOM": "<DUPONT>"}))
    assert "Marie" in result.content and "&lt;DUPONT&gt;" in result.content and "data-pmsl-field" not in result.content
    assert result.used_fields == ("SALARIE_PRENOM", "SALARIE_NOM") and result.unresolved_fields == ()


def test_merge_accepts_historical_alias_in_context_for_canonical_field():
    document = DocumentModel.create(document_type="contract", html='<p><span data-pmsl-field="SALARIE_NOM">[Nom]</span></p>')
    result = HtmlMergeRenderer().render(document, MergeContext({"NOM": "DUPONT"}))
    assert "DUPONT" in result.content and result.unresolved_fields == ()


def test_missing_field_is_visible_and_strict_mode_fails():
    document = DocumentModel.create(document_type="contract", html='<p><span data-pmsl-field="SALARIE_NOM">[Nom]</span></p>')
    result = HtmlMergeRenderer().render(document, MergeContext({}))
    assert "{SALARIE_NOM}" in result.content and result.unresolved_fields == ("SALARIE_NOM",)
    with pytest.raises(UnknownMergeFieldError):
        HtmlMergeRenderer().render(document, MergeContext({}), strict=True)


def test_unknown_registered_field_is_not_silently_resolved():
    document = DocumentModel.create(document_type="contract", html='<span data-pmsl-field="INCONNU">x</span>')
    result = HtmlMergeRenderer().render(document, MergeContext({"INCONNU": "secret"}))
    assert "{INCONNU}" in result.content and "secret" not in result.content and result.unresolved_fields == ("INCONNU",)


@pytest.mark.parametrize(("case", "raw", "expected"), [
    ("A", "<p>Texte simple</p>", "Texte simple"),
    ("B", '<p style="text-align:center;color:#123456"><strong>Gras</strong> <em>italique</em></p>', "Gras"),
    ("C", '<p><img src="asset://123e4567-e89b-12d3-a456-426614174000" alt="image"></p>', "asset://"),
    ("D", '<p><a href="https://example.org">Lien</a></p>', "Lien"),
    ("E", "<p>{PRENOM} {NOM}</p>", 'data-pmsl-field="SALARIE_PRENOM"'),
    ("F", '<p>Page 1</p><div style="page-break-before: always">Page 2</div>', "Page 2"),
    ("G", '<table><tr><td>{NOM}</td><td><strong>Complexe</strong></td></tr></table>', "Complexe"),
])
def test_migration_corpus_a_to_g(case, raw, expected):
    upgraded = upgrade_legacy_placeholders(raw, DEFAULT_DOCUMENT_FIELD_REGISTRY)
    assert expected in upgraded, case


def test_legacy_importer_leaves_unknown_token_untouched():
    assert "{VARIABLE_NON_RECENSEE}" in upgrade_legacy_placeholders("<p>{VARIABLE_NON_RECENSEE}</p>")


def test_legacy_importer_does_not_double_wrap_semantic_fields():
    upgraded = upgrade_legacy_placeholders('<span data-pmsl-field="SALARIE_NOM">{NOM}</span>')
    assert upgraded.count("data-pmsl-field") == 1


def test_neutral_mapping_context_normalizes_keys():
    context = MergeContext.from_mapping({" nom ": " DUPONT ", "prenom": " Marie "})
    assert context.as_dict() == {"NOM": "DUPONT", "PRENOM": "Marie"}


def test_existing_namespaced_context_builder_remains_compatible():
    context = build_merge_context(employee={"nom": "DUPONT", "prenom": "Marie"}, contract={"date_debut": "2026-10-01"}, extra={"NOM": "legacy"})
    assert context.get("SALARIE_NOM") == "DUPONT" and context.get("CONTRAT_DATE_DEBUT") == "2026-10-01" and context.get("NOM") == "legacy"
    assert not validate_required_fields(context, ["SALARIE_NOM", "CONTRAT_DATE_DEBUT"])


def test_document_core_runs_without_wx_or_qt_imports():
    source_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    script = textwrap.dedent('''
        import builtins, json
        real_import = builtins.__import__
        blocked = ("wx", "PySide6", "PyQt5", "PyQt6")
        def guarded_import(name, *args, **kwargs):
            if name.startswith(blocked):
                raise AssertionError("UI dependency imported by document core: " + name)
            return real_import(name, *args, **kwargs)
        builtins.__import__ = guarded_import
        from domain.documents import DocumentModel, HtmlMergeRenderer, MergeContext
        document = DocumentModel.create(document_type="contract", html='<p><span data-pmsl-field="SALARIE_NOM">[Nom]</span></p>')
        restored = DocumentModel.from_dict(json.loads(document.to_json()))
        result = HtmlMergeRenderer().render(restored, MergeContext({"SALARIE_NOM": "DUPONT"}))
        assert "DUPONT" in result.content
        print("PORTABLE_OK")
    ''')
    env = dict(os.environ); env["PYTHONPATH"] = source_root
    process = subprocess.run([sys.executable, "-c", script], env=env, capture_output=True, text=True, check=False)
    assert process.returncode == 0, process.stderr
    assert process.stdout.strip() == "PORTABLE_OK"
