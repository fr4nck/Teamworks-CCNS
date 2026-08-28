from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
METADATA_MODULE = ROOT / "teamworks" / "Utils" / "UTILS_Contrats_modeles_documents.py"
ORGANISATION_MODULE = ROOT / "teamworks" / "Utils" / "UTILS_Organisation.py"
ORGANISATION_DIALOG = ROOT / "teamworks" / "Dlg" / "DLG_Organisation.py"
DOCUMENT_BRIDGE = ROOT / "teamworks" / "Utils" / "UTILS_Documents_RH.py"
CONTRACT_MAILMERGE = ROOT / "teamworks" / "Dlg" / "DLG_Publiposteur_contrat.py"


def _load_metadata_module():
    spec = importlib.util.spec_from_file_location("tw_hr_document_metadata", METADATA_MODULE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_structure_profile_exposes_dedicated_hr_email_and_document_mapping() -> None:
    source = ORGANISATION_MODULE.read_text(encoding="utf-8")
    assert '"email_rh": ""' in source
    assert "def BuildProfilPublipostage(" in source
    assert '"raison_sociale": p["nom_officiel"] or p["nom_usage"]' in source
    assert '"email_rh": p["email_rh"] or p["email"]' in source
    assert '"logo": logo_path or ""' in source
    assert "def GetProfilPublipostage(" in source
    assert "UTILS_Branding.GetAssociationLogoPath()" in source


def test_structure_dialog_allows_and_validates_hr_email() -> None:
    source = ORGANISATION_DIALOG.read_text(encoding="utf-8")
    assert '"Email RH / recrutement :", "email_rh"' in source
    assert '(("email", "générale"), ("email_rh", "RH / recrutement"))' in source


def test_runtime_bridge_preserves_legacy_keywords_and_adds_canonical_namespaces() -> None:
    source = DOCUMENT_BRIDGE.read_text(encoding="utf-8")
    assert "UTILS_Publipostage_donnees.GetDonneesDocument" in source
    assert 'legacy_values.get("NOM", "")' in source
    assert 'legacy_values.get("DATEDEBUT", "")' in source
    assert "extra=legacy_values" in source
    assert "UTILS_Organisation.GetProfilPublipostage()" in source
    assert "def EnrichirDictDonneesContrat(" in source
    assert 'prepared = _prepare_from_values("contract", legacy_values)' in source


def test_contract_mailmerge_uses_hr_enrichment_and_catalog_classification() -> None:
    source = CONTRACT_MAILMERGE.read_text(encoding="utf-8")
    assert "UTILS_Documents_RH.EnrichirDictDonneesContrat(dict_donnees)" in source
    assert '_(u"Type de document RH…")' in source
    assert "def Menu_TypeDocumentRH(" in source
    assert "document_kind=document_kind" in source
    assert "scope=DocumentScope.CONTRACT" in source
    assert "generated_by_teamworks=True" in source


def test_document_kind_compatibility_keeps_legacy_models_visible() -> None:
    metadata = _load_metadata_module()
    assert metadata.IsDocumentKindCompatible(None, "contract") is True
    assert metadata.IsDocumentKindCompatible({}, "contract") is True
    assert metadata.IsDocumentKindCompatible(
        {"document_kind": "contract"}, "contract"
    ) is True
    assert metadata.IsDocumentKindCompatible(
        {"document_kind": "amendment"}, "contract"
    ) is False
    assert metadata.IsDocumentKindCompatible(
        {"document_kind": "amendment"}, None
    ) is True


def test_document_kind_can_strictly_exclude_legacy_models() -> None:
    metadata = _load_metadata_module()
    assert metadata.IsDocumentKindCompatible(
        None, "contract", include_legacy=False
    ) is False
    assert metadata.IsDocumentKindCompatible(
        {}, "contract", include_legacy=False
    ) is False


def test_metadata_schema_migrates_existing_table_additively() -> None:
    metadata = _load_metadata_module()

    class FakeDB:
        def __init__(self):
            self.added = []
            self.commits = 0

        def IsTableExists(self, table):
            assert table == metadata.TABLE
            return True

        def GetListeChamps2(self, table):
            assert table == metadata.TABLE
            return [("IDdocument_modele",), ("nom_fichier",)]

        def AjoutChamp(self, **kwargs):
            self.added.append(kwargs)

        def Commit(self):
            self.commits += 1

    db = FakeDB()
    created_table = metadata.EnsureTable(db)
    assert created_table is False
    assert db.added == [
        {
            "nomTable": metadata.TABLE,
            "nomChamp": "document_kind",
            "typeChamp": "VARCHAR(48)",
        }
    ]
    assert db.commits == 1
