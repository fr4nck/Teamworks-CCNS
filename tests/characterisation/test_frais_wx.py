"""Caractérisation Déplacements/Remboursements wxPython avant transposition Qt."""

from __future__ import annotations

import decimal

import pytest

from source_legacy import (
    column_names,
    compact_whitespace,
    db_data_schema,
    function_source,
    load_method_as_function,
    read_source,
)


DEPLACEMENT = "teamworks/Dlg/DLG_Saisie_deplacement.py"
REMBOURSEMENT = "teamworks/Dlg/DLG_Saisie_remboursement.py"
PAGE_FRAIS = "teamworks/Ctrl/CTRL_Page_frais.py"
IMPRESSION = "teamworks/Dlg/DLG_Impression_frais.py"


class _Control:
    def __init__(self, value: str | bool = "") -> None:
        self.value = value
        self.label: str | None = None

    def GetValue(self):  # noqa: N802 - API wx historique
        return self.value

    def SetValue(self, value):  # noqa: N802 - API wx historique
        self.value = value

    def SetLabel(self, label: str) -> None:  # noqa: N802 - API wx historique
        self.label = label


class _DeplacementDouble:
    def __init__(self, distance: str, tarif: str = "0", aller_retour: bool = False) -> None:
        self.ctrl_distance = _Control(distance)
        self.ctrl_tarif = _Control(tarif)
        self.ctrl_aller_retour = _Control(aller_retour)
        self.ctrl_montant = _Control()
        self.label_km = _Control()
        self.recalculs = 0

    def ValideControleFloat(self, controle=None):  # noqa: N802
        return True

    def CalcMontantRmbst(self):  # noqa: N802
        self.recalculs += 1


def test_schema_frais_duplique_le_rattachement_sans_contrainte_fk() -> None:
    assert column_names("distances") == [
        "IDdistance",
        "cp_depart",
        "ville_depart",
        "cp_arrivee",
        "ville_arrivee",
        "distance",
    ]
    assert column_names("deplacements") == [
        "IDdeplacement",
        "IDpersonne",
        "date",
        "objet",
        "cp_depart",
        "ville_depart",
        "cp_arrivee",
        "ville_arrivee",
        "distance",
        "aller_retour",
        "tarif_km",
        "IDremboursement",
    ]
    assert column_names("remboursements") == [
        "IDremboursement",
        "IDpersonne",
        "date",
        "montant",
        "listeIDdeplacement",
    ]
    assert "montant" not in column_names("deplacements")
    declarations = [
        str(column[1]).upper()
        for table in ("distances", "deplacements", "remboursements")
        for column in db_data_schema(table)
    ]
    assert not any("FOREIGN KEY" in declaration for declaration in declarations)
    assert not any("REFERENCES" in declaration for declaration in declarations)
    assert not any("CHECK" in declaration for declaration in declarations)


def test_case_aller_retour_double_ou_divise_la_distance_stockee() -> None:
    on_aller_retour = load_method_as_function(
        DEPLACEMENT,
        "SaisieDeplacement",
        "OnAllerRetour",
        globals_={"_": lambda value: value},
    )

    aller_simple = _DeplacementDouble("20", aller_retour=False)
    on_aller_retour(aller_simple, None)
    assert aller_simple.ctrl_distance.GetValue() == "10.0"
    assert aller_simple.label_km.label == "Km (aller simple)"
    assert aller_simple.recalculs == 1

    aller_retour = _DeplacementDouble("10", aller_retour=True)
    on_aller_retour(aller_retour, None)
    assert aller_retour.ctrl_distance.GetValue() == "20.0"
    assert aller_retour.label_km.label == "Km (aller / retour)"
    assert aller_retour.recalculs == 1


def test_montant_est_distance_stockee_fois_tarif_sans_multiplicateur_supplementaire() -> None:
    calcul = load_method_as_function(
        DEPLACEMENT,
        "SaisieDeplacement",
        "CalcMontantRmbst",
        globals_={"decimal": decimal},
    )
    double = _DeplacementDouble("12", tarif="0.5")
    calcul(double)
    assert double.ctrl_montant.label == "6.00 €"

    for relative_path, class_name, method_name in (
        (REMBOURSEMENT, "ListCtrl_deplacements", "Importation"),
        (PAGE_FRAIS, "ListCtrl_deplacements", "Importation"),
    ):
        source = function_source(relative_path, method_name, class_name=class_name)
        assert "float(distance) * float(tarif_km)" in source


def test_montant_kilometrique_conserve_une_precision_monetaire_normale() -> None:
    calcul = load_method_as_function(
        DEPLACEMENT,
        "SaisieDeplacement",
        "CalcMontantRmbst",
        globals_={"decimal": decimal},
    )
    double = _DeplacementDouble("123", tarif="0.55")

    # Rejoue l'environnement numérique réellement imposé par le module historique.
    precision = 2 if "decimal.getcontext().prec = 2" in read_source(DEPLACEMENT) else 28
    with decimal.localcontext() as contexte:
        contexte.prec = precision
        calcul(double)

    assert double.ctrl_montant.label == "67.65 €"


def test_cache_distances_est_symetrique_et_conserve_un_aller_simple() -> None:
    maj = compact_whitespace(
        function_source(DEPLACEMENT, "MajDistance", class_name="SaisieDeplacement")
    )
    sauvegarde = compact_whitespace(
        function_source(DEPLACEMENT, "SauvegardeDistance", class_name="SaisieDeplacement")
    )
    assert "depart == arrivee_temp and arrivee == depart_temp" in maj
    assert "distance * 2.0" in maj
    assert "depart == arrivee_temp and arrivee == depart_temp" in sauvegarde
    assert "if self.ctrl_aller_retour.GetValue() is True: distance = distance / 2" in sauvegarde
    assert "cp_depart = int(self.ctrl_cp_depart.GetValue())" in sauvegarde
    assert "cp_arrivee = int(self.ctrl_cp_arrivee.GetValue())" in sauvegarde


@pytest.mark.xfail(
    strict=True,
    reason="défaut historique : modifier un déplacement remboursé force IDremboursement à 0",
)
def test_modification_deplacement_ne_force_pas_le_rattachement_a_zero() -> None:
    source = function_source(
        DEPLACEMENT, "SauvegardeDeplacement", class_name="SaisieDeplacement"
    )
    avant_distinction_creation_modification = source.split(
        "if self.IDdeplacement is None:", 1
    )[0]
    assert '("IDremboursement", 0)' not in avant_distinction_creation_modification


def test_remboursement_ecrit_liste_et_cles_etrangeres_en_deux_transactions() -> None:
    source = function_source(REMBOURSEMENT, "Sauvegarde", class_name="SaisieRemboursement")
    assert 'texteID = "-".join(str(ID) for ID in listeIDcoches)' in source
    assert '("listeIDdeplacement", texteID)' in source
    assert source.count("GestionDB.DB()") == 2
    assert source.count("DB.Commit()") == 2
    assert '("IDremboursement", ID)' in source
    assert '("IDremboursement", 0)' in source


def test_liste_denormalisee_et_fk_pilotent_des_ecrans_differents() -> None:
    import_dialogue = function_source(
        REMBOURSEMENT, "Importation", class_name="SaisieRemboursement"
    )
    liste_dialogue = function_source(
        REMBOURSEMENT, "Importation", class_name="ListCtrl_deplacements"
    )
    liste_principale = function_source(
        PAGE_FRAIS, "Importation", class_name="ListCtrl_remboursements"
    )

    assert "listeIDdeplacement" in import_dialogue
    assert ".split(" not in import_dialogue
    assert "IDremboursement=0 OR IDremboursement=%d" in liste_dialogue
    assert "if IDremboursement != 0" in liste_dialogue
    assert 'listeIDdeplacement.split("-")' in liste_principale


def test_un_remboursement_ne_propose_que_ses_deplacements_et_les_non_affectes() -> None:
    source = compact_whitespace(
        function_source(REMBOURSEMENT, "Importation", class_name="ListCtrl_deplacements")
    )
    assert "WHERE IDpersonne=%d AND IDremboursement=0 ORDER BY date" in source
    assert (
        "WHERE IDpersonne=%d AND (IDremboursement=0 OR IDremboursement=%d) ORDER BY date"
        in source
    )


def test_ecart_montant_deplacements_est_un_avertissement_non_bloquant() -> None:
    label = function_source(
        REMBOURSEMENT, "MajLabelRattachement", class_name="ListCtrl_deplacements"
    )
    validation = function_source(
        REMBOURSEMENT, "OnBoutonOk", class_name="SaisieRemboursement"
    )
    assert "montantNonRattache == 0" in label
    assert "montantNonRattache > 0" in label
    assert "de déplacements en trop" in label
    assert "montantNonRattache" not in validation
    assert "self.Sauvegarde()" in validation


def test_remboursement_sans_deplacement_reste_validable_apres_confirmation() -> None:
    source = function_source(
        REMBOURSEMENT, "OnBoutonOk", class_name="SaisieRemboursement"
    )
    assert "if len(listeIDcoches) == 0" in source
    assert "Souhaitez-vous quand même valider" in source
    assert source.index("if len(listeIDcoches) == 0") < source.index("self.Sauvegarde()")


def test_deplacement_rattache_est_interdit_de_suppression() -> None:
    source = function_source(PAGE_FRAIS, "SupprimerDeplacement", class_name="Panel")
    assert "if IDremboursement != 0" in source
    assert "Vous ne pouvez donc pas le supprimer" in source
    assert 'DB.ReqDEL("deplacements", "IDdeplacement", IDdeplacement)' in source
    assert source.index("Vous ne pouvez donc pas le supprimer") < source.index(
        'DB.ReqDEL("deplacements", "IDdeplacement", IDdeplacement)'
    )


def test_suppression_remboursement_libere_les_deplacements_apres_avertissement() -> None:
    source = function_source(PAGE_FRAIS, "SupprimerRemboursement", class_name="Panel")
    assert "SELECT IDdeplacement FROM deplacements WHERE IDremboursement=%d" in source
    assert "nbreRattaches" in source
    assert 'DB.ReqDEL("remboursements", "IDremboursement", IDremboursement)' in source
    assert '("IDremboursement", 0)' in source
    assert 'DB.ReqMAJ(\n                "deplacements"' in source


def test_impression_recalcule_aussi_les_montants_depuis_les_deplacements() -> None:
    source = function_source(IMPRESSION, "Importation", class_name="ListCtrl")
    assert "float(distance) * float(tarif_km)" in source
    assert "IDremboursement" in source
    assert "listeIDdeplacement" not in source
