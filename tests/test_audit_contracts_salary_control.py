from __future__ import annotations

from copy import deepcopy
from datetime import date

import pytest

from domain.repositories.ccns_data import CcnsContratRecord, CcnsGrilleRecord, CcnsLigneGrilleRecord
from teamworks.CcnsCore import audit_contracts_ccns as audit_module
from teamworks.CcnsCore.audit_contracts_ccns import audit_contracts
from teamworks.CcnsCore.home_gadgets_ccns import _build_stats
from teamworks.CcnsCore.audit_person_summary import build_person_ccns_summary


class Reader:
    def __init__(self, contracts):
        self.contracts = contracts
        self.calls = []
        self.closed = False

    def lire_contrats(self, limit=None):
        self.calls.append(("contrats", limit))
        data = list(self.contracts)
        return data[:limit] if limit else data

    def lire_contrats_personne(self, IDpersonne, limit=None):
        self.calls.append(("contrats_personne", IDpersonne, limit))
        data = [record for record in self.contracts if record.IDpersonne == IDpersonne]
        return data[:limit] if limit else data

    def lire_grilles(self, limit=None):
        self.calls.append(("grilles", limit))
        return [CcnsGrilleRecord(7, "CCNS-2026", "Grille 2026", "CCNS", "standard", date(2026, 1, 1), None, "test")]

    def lire_lignes_grille(self, IDtw_salary_grid):
        self.calls.append(("lignes", IDtw_salary_grid))
        return [
            CcnsLigneGrilleRecord(1, IDtw_salary_grid, "G1", "monthly", 1800.00, "EUR", None, None, None, None, ""),
            CcnsLigneGrilleRecord(2, IDtw_salary_grid, "G3", "monthly", 1997.87, "EUR", None, None, None, None, ""),
        ]

    def close(self):
        self.closed = True


class UppercasePeriodicityReader(Reader):
    def lire_lignes_grille(self, IDtw_salary_grid):
        self.calls.append(("lignes", IDtw_salary_grid))
        return [
            CcnsLigneGrilleRecord(1, IDtw_salary_grid, "G3", "MONTHLY", 1997.87, "EUR", None, None, None, None, ""),
            CcnsLigneGrilleRecord(2, IDtw_salary_grid, "G7", "ANNUAL", 50000.00, "EUR", None, None, None, None, ""),
            CcnsLigneGrilleRecord(3, IDtw_salary_grid, "G8", "ANNUAL", 60000.00, "EUR", None, None, None, None, ""),
        ]


class ReaderWithoutSalaryGrid(Reader):
    def lire_grilles(self, limit=None):
        self.calls.append(("grilles", limit))
        return []

    def lire_lignes_grille(self, IDtw_salary_grid):
        raise AssertionError("aucune ligne de grille ne doit être lue")


def contract(IDcontrat, salaire, classification="G3", type_contrat="CDI", date_fin=None, prenom="Ada", nom="Lovelace"):
    return CcnsContratRecord(
        IDcontrat,
        100 + IDcontrat,
        date(2026, 1, 1),
        date_fin,
        salaire,
        35.0,
        0.0,
        prenom,
        nom,
        classification,
        type_contrat,
    )


def test_audit_accepte_les_periodicites_teamworks_en_majuscules_avec_g7_et_g8():
    rows = audit_contracts(
        data_reader=UppercasePeriodicityReader([contract(1, 2100.0)]),
        reference_date=date(2026, 7, 1),
    )

    assert [row.IDcontrat for row in rows] == [1]
    assert "REMUNERATION_BELOW_APPLICABLE_MINIMUM" not in rows[0].anomalies


def test_audit_sans_grille_retourne_une_anomalie_stable_sans_planter():
    reader = ReaderWithoutSalaryGrid([contract(1, 2100.0)])

    rows = audit_contracts(data_reader=reader, reference_date=date(2026, 7, 1))

    assert [row.IDcontrat for row in rows] == [1]
    assert "CONTRAT_SANS_GRILLE" in rows[0].anomalies
    assert "Grille salariale manquante" in rows[0].messages
    assert not any(call[0] == "lignes" for call in reader.calls)


def test_audit_traduit_conforme_non_conforme_et_non_evaluable_sans_recalcul_ancien(monkeypatch):
    assert not hasattr(audit_module, "check_contract_minimum_from_grid")
    reader = Reader([
        contract(1, 2100.0, "G3", prenom="Ada"),
        contract(2, 1500.0, "G3", prenom="Grace"),
        contract(3, None, "G3", prenom="Linus"),
    ])
    calls = []
    original = audit_module.ContractSalaryControlControllerFactory.create_from_provider

    def spy(self, **kwargs):
        calls.append(kwargs["contract_provider"].__class__.__name__)
        return original(self, **kwargs)

    monkeypatch.setattr(audit_module.ContractSalaryControlControllerFactory, "create_from_provider", spy)

    rows = audit_contracts(data_reader=reader, reference_date=date(2026, 7, 1))

    assert calls == ["TeamworksContractSalaryControlProvider"]
    assert reader.calls.count(("contrats", None)) == 1
    assert [row.IDcontrat for row in rows] == [1, 2, 3]
    assert rows[0].nom_complet == "Ada Lovelace"
    assert "REMUNERATION_BELOW_APPLICABLE_MINIMUM" not in rows[0].anomalies
    assert "REMUNERATION_BELOW_APPLICABLE_MINIMUM" in rows[1].anomalies
    assert "La rémunération brute mensuelle est inférieure au minimum salarial applicable." in rows[1].messages
    assert "CONTROLE_SALARIAL_NON_EVALUABLE_MISSING_REMUNERATION" in rows[2].anomalies
    assert "Le contrat ne possède pas de rémunération exploitable." in rows[2].messages


def test_audit_signale_minimum_smic_et_classification_absente():
    rows = audit_contracts(
        data_reader=Reader([
            contract(1, 1700.0, "G1"),
            contract(2, 2100.0, None),
        ]),
        reference_date=date(2026, 7, 1),
    )

    assert "REMUNERATION_BELOW_APPLICABLE_MINIMUM" in rows[0].anomalies
    assert "CONTROLE_SALARIAL_NON_EVALUABLE_MISSING_CLASSIFICATION" in rows[1].anomalies
    assert "Le contrat ne possède pas de classification CCNS exploitable." in rows[1].messages


def test_audit_conserve_identite_type_ordre_limit_et_ne_mute_pas():
    records = [contract(3, 2100.0, prenom="C"), contract(1, 2100.0, type_contrat="CDD", date_fin=date(2026, 12, 31), prenom="A")]
    before = deepcopy(records)
    reader = Reader(records)

    rows = audit_contracts(limit=1, data_reader=reader, reference_date=date(2026, 7, 1))

    assert reader.calls[0] == ("contrats", 1)
    assert [row.IDcontrat for row in rows] == [3]
    assert rows[0].type_contrat == "CDI"
    assert records == before


def test_cdd_cee_historique_sans_date_fin_reste_visible():
    rows = audit_contracts(
        data_reader=Reader([contract(1, 2100.0, "G3", "CEE", None)]),
        reference_date=date(2026, 7, 1),
    )

    assert "CONTROLE_SALARIAL_NON_EVALUABLE_HISTORICAL_FIXED_TERM_MISSING_END_DATE" in rows[0].anomalies
    assert "CONTRAT_A_DUREE_DETERMINEE_SANS_DATE_FIN" in rows[0].anomalies


def test_compatibilite_gadgets_et_synthese_individuelle():
    reader = Reader([contract(1, 2100.0), contract(2, 1500.0)])
    rows = audit_contracts(data_reader=reader, reference_date=date(2026, 7, 1))
    stats = _build_stats(rows)
    summary = build_person_ccns_summary(101, data_reader=Reader([contract(1, 2100.0)]), reference_date=date(2026, 7, 1))

    assert stats[0]["value"] == 2
    assert summary["IDpersonne"] == 101
    assert summary["nb_contracts"] == 1
    assert summary["rows"][0]["IDcontrat"] == 1


def test_erreurs_lecteur_propagees_et_pas_import_circulaire():
    class Broken(Reader):
        def lire_grilles(self, limit=None):
            raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        audit_contracts(data_reader=Broken([contract(1, 2100.0)]), reference_date=date(2026, 7, 1))

    __import__("infrastructure.persistence.teamworks_contract_salary_control_provider")
    __import__("teamworks.CcnsCore.audit_contracts_ccns")
