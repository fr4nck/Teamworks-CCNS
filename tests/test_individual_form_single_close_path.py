"""La fermeture de la fiche individuelle n'a qu'un seul chemin réel.

Les variantes installées par Dlg.__getattr__ (lazy, problèmes, rafraîchissement
ciblé) spécialisent la sauvegarde des pages ou le rafraîchissement de la liste,
mais ne redéfinissent plus Fermer() : la garde de réentrance, l'arrêt des
callbacks et l'annulation atomique d'une fiche neuve restent effectifs.
"""
from pathlib import Path

DLG = Path("teamworks/Dlg")
CORE = (DLG / "DLG_Fiche_individuelle_core.py").read_text(encoding="utf-8")
WRAPPER = (DLG / "DLG_Fiche_individuelle.py").read_text(encoding="utf-8")
LAZY = (DLG / "DLG_Fiche_individuelle_lazy.py").read_text(encoding="utf-8")
REFRESH = (DLG / "DLG_Fiche_individuelle_refresh.py").read_text(encoding="utf-8")
PROBLEMS = (DLG / "DLG_Fiche_individuelle_problems.py").read_text(encoding="utf-8")


def test_les_variantes_installees_ne_redefinissent_pas_fermer():
    for source in (LAZY, REFRESH, PROBLEMS):
        assert "def Fermer(" not in source


def test_les_variantes_passent_par_les_points_d_extension_du_coeur():
    assert "def _sauvegarder_pages(self):" in CORE
    assert "def _rafraichir_personnes(self, frame, save):" in CORE
    assert "def _sauvegarder_pages(self):" in LAZY
    assert "def _rafraichir_personnes(self, frame, save):" in REFRESH


def test_le_coeur_ne_rafraichit_que_une_page_personnes_construite():
    helper = CORE.split("def _rafraichir_frame_personnes(self, save=True):", 1)[1].split(
        "def _rafraichir_personnes", 1
    )[0]
    assert 'getattr(frm, "listCtrl_personnes", None) is None' in helper
    fermer = CORE.split("def Fermer(self, save=True):", 1)[1].split(
        "def _sauvegarder_pages", 1
    )[0]
    assert "self._sauvegarder_pages()" in fermer
    assert "self._rafraichir_frame_personnes(save=save)" in fermer
    assert "frm.listCtrl_personnes" not in fermer


def test_l_annulation_atomique_utilise_le_meme_rafraichissement_protege():
    assert "self._rafraichir_frame_personnes(save=False)" in WRAPPER
    assert "frm.listCtrl_personnes" not in WRAPPER


def test_les_smokes_windows_activent_faulthandler_pour_les_crashs_natifs():
    import sys
    sys.path.insert(0, "tools")
    try:
        import smoke_runtime
    finally:
        sys.path.pop(0)
    env = smoke_runtime.build_environment(Path("."), Path("teamworks"))
    assert env["PYTHONFAULTHANDLER"] == "1"
