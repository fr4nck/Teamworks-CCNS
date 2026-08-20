from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GADGET = ROOT / "teamworks" / "Ctrl" / "CTRL_Gadget_pb_personnes.py"


def test_contract_due_group_is_presented_as_documents_to_process() -> None:
    source = GADGET.read_text(encoding="utf-8")

    assert '_(u"1 document à traiter")' in source
    assert '_(u" documents à traiter")' in source
    assert 'nomCategorie == _(u"1 contrat à voir")' in source
    assert 'nomCategorie.endswith(_(u" contrats à voir"))' in source


def test_specific_document_labels_are_not_replaced() -> None:
    source = GADGET.read_text(encoding="utf-8")

    # Le renommage ne concerne que le niveau agrégé de l'arborescence.
    assert 'return nomCategorie' in source
