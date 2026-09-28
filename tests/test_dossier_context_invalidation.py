from pathlib import Path


CORE = Path("teamworks/Teamworks_core.py")
HOME = Path("teamworks/Ctrl/CTRL_Accueil.py")


def test_frame_has_one_central_dossier_context_invalidator():
    source = CORE.read_text(encoding="utf-8")
    assert "def InvaliderContexteDossier" in source
    assert '("dictNomsPersonnes", "dictProblemesPersonnes")' in source
    assert "clear_ccns_home_cache()" in source
    assert "self.toolBook.OnChangementDossier" in source


def test_open_close_and_new_file_notify_context_change():
    source = CORE.read_text(encoding="utf-8")
    assert 'self.InvaliderContexteDossier(ancienFichier, "")' in source
    assert source.count("self.InvaliderContexteDossier(ancienFichier, nomFichier)") >= 2


def test_home_delegates_context_invalidation_to_dashboard():
    source = HOME.read_text(encoding="utf-8")
    assert "def OnChangementDossier" in source
    assert "self.html.OnChangementDossier(ancienFichier, nouveauFichier)" in source


def test_individus_discards_selection_and_filter_from_previous_dossier():
    source = Path("teamworks/Ctrl/CTRL_Personnes.py").read_text(encoding="utf-8")
    bloc = source.split("def OnChangementDossier", 1)[1].split("def MAJpanel", 1)[0]

    assert "self.listCtrl_personnes.criteres = \"\"" in bloc
    assert "self.barreRecherche.OnCancel(None)" in bloc
    assert "self.AffichePanelResume(False)" in bloc
    assert "self.AfficheLabelSelection(False)" in bloc
    assert "self.bouton_modifier.Enable(False)" in bloc
    assert "self.bouton_supprimer.Enable(False)" in bloc
