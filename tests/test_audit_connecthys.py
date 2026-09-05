from pathlib import Path
import importlib.util
import sys


MODULE_PATH = Path(__file__).parents[1] / "tools" / "audit_connecthys.py"
SPEC = importlib.util.spec_from_file_location("audit_connecthys", MODULE_PATH)
assert SPEC and SPEC.loader
AUDIT = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = AUDIT
SPEC.loader.exec_module(AUDIT)


def _brand_bloquante(hit):
    """Une marque en commentaire reste une preuve historique, pas du code actif."""
    return (
        hit.category == "brand"
        and hit.scope == "active"
        and not hit.snippet.lstrip().startswith("#")
    )


def test_connecthys_dans_code_actif_est_bloquant():
    hits = AUDIT.scan_text("teamworks/module.py", "client = ConnecthysClient()\n")
    assert [hit for hit in hits if _brand_bloquante(hit)]


def test_connecthys_dans_commentaire_actif_reste_historique():
    hits = AUDIT.scan_text(
        "teamworks/module.py",
        "# Ancienne intégration Connecthys supprimée\n",
    )
    assert any(hit.category == "brand" for hit in hits)
    assert not any(_brand_bloquante(hit) for hit in hits)


def test_connecthys_dans_documentation_n_est_pas_actif():
    hits = AUDIT.scan_text("docs/historique.md", "Ancien service : Connecthys\n")
    assert [(hit.category, hit.scope) for hit in hits if hit.category == "brand"] == [
        ("brand", "documentation")
    ]


def test_archive_bak_est_classee_historique():
    assert AUDIT.classify_scope("teamworks/Dlg/exemple.py.bak-2026") == "historical_archive"


def test_url_et_domaine_sont_inventories():
    hits = AUDIT.scan_text(
        "teamworks/Utils/example.py",
        'endpoint = "https://portal.example.test/api/v1"\n',
    )
    report = AUDIT.build_report(Path("."), hits, [], 1)
    assert report["domains"] == {"portal.example.test": 1}
    assert any(hit.category == "url" and hit.scope == "active" for hit in hits)


def test_primitive_reseau_est_candidate_pas_connecthys():
    hits = AUDIT.scan_text("teamworks/example.py", "import smtplib\n")
    assert any(hit.category == "network_api" for hit in hits)
    assert not any(hit.category == "brand" for hit in hits)


def test_depot_reel_n_a_pas_de_reference_connecthys_executable():
    import warnings

    root = Path(__file__).parents[1]
    hits, skipped, scanned_count = AUDIT.scan_repository(root)
    report = AUDIT.build_report(root, hits, skipped, scanned_count)
    brand_hits = [hit for hit in hits if hit.category == "brand"]
    blocking_brand_hits = [hit for hit in brand_hits if _brand_bloquante(hit)]
    active_candidates = [
        hit
        for hit in hits
        if hit.scope == "active"
        and hit.category in {"url", "network_api", "sync_portal", "automation"}
    ]
    lines = [
        "INVENTAIRE CONNECTHYS",
        f"scanned_text_files={scanned_count}",
        f"skipped_files={len(skipped)}",
        f"counts={report['counts']}",
        f"domains={report['domains']}",
        f"brand_hits={len(brand_hits)}",
        f"blocking_brand_hits={len(blocking_brand_hits)}",
        f"active_high_signal_candidates={len(active_candidates)}",
        "REFERENCES CONNECTHYS:",
    ]
    lines.extend(
        f"{hit.scope} {hit.path}:{hit.line} {hit.snippet}"
        for hit in brand_hits
    )
    warnings.warn("\n".join(lines), UserWarning, stacklevel=1)
    assert not blocking_brand_hits, "\n".join(lines)
