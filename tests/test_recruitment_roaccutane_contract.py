from pathlib import Path


VISIBLE_RECRUITMENT = (
    "teamworks/Ctrl/CTRL_Recrutement.py",
    "teamworks/Ctrl/CTRL_Recrutement_navigation.py",
    "teamworks/Dlg/DLG_Saisie_candidat.py",
    "teamworks/Dlg/DLG_Saisie_candidature.py",
    "teamworks/Dlg/DLG_Saisie_emploi.py",
)


def _source(path):
    return Path(path).read_text(encoding="utf-8")


def test_recrutement_visible_ne_reintroduit_pas_de_boutons_wx_locaux():
    for path in VISIBLE_RECRUITMENT:
        source = _source(path)
        assert "wx.BitmapButton(" not in source, path
        assert "wx.Button(" not in source, path
        assert "wx.ToggleButton(" not in source, path


def test_recrutement_utilise_le_contrat_bouton_commun():
    page = _source("teamworks/Ctrl/CTRL_Recrutement.py")
    navigation = _source("teamworks/Ctrl/CTRL_Recrutement_navigation.py")
    candidat = _source("teamworks/Dlg/DLG_Saisie_candidat.py")
    candidature = _source("teamworks/Dlg/DLG_Saisie_candidature.py")
    emploi = _source("teamworks/Dlg/DLG_Saisie_emploi.py")

    assert "CTRL_Bouton_image.CTRL(" in page
    assert "CTRL_Bouton_image.Toggle" in navigation
    for source in (candidat, candidature, emploi):
        assert "CTRL_Bouton_image.CTRL(" in source


def test_actions_destructives_et_validation_restent_semantiques():
    for path in (
        "teamworks/Dlg/DLG_Saisie_candidat.py",
        "teamworks/Dlg/DLG_Saisie_candidature.py",
        "teamworks/Dlg/DLG_Saisie_emploi.py",
    ):
        source = _source(path)
        assert 'texte=_(u"Supprimer")' in source
        assert 'texte=_(u"Valider")' in source
