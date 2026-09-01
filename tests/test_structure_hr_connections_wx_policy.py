import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIALOG = ROOT / "teamworks" / "Dlg" / "DLG_Connexions_RH.py"
PAGE = ROOT / "teamworks" / "Ctrl" / "CTRL_Page_protection_sociale.py"
RUNTIME = ROOT / "teamworks" / "Ctrl" / "CTRL_Page_protection_sociale_runtime.py"


def _source(path):
    return path.read_text(encoding="utf-8")


def test_dialogue_structure_ne_fait_aucun_acces_direct_aux_donnees_ou_reseau():
    source = _source(DIALOG)
    tree = ast.parse(source, filename=str(DIALOG))
    imported_modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_modules.append(node.module or "")

    for forbidden in (
        "GestionDB",
        "sqlite3",
        "infrastructure.persistence",
        "requests",
        "webbrowser",
    ):
        assert all(
            module != forbidden and not module.startswith(forbidden + ".")
            for module in imported_modules
        )

    assert "StructureOrganizationProfileRequest" in source
    assert "OrganizationReference.create" in source
    assert "PortalLink.create" in source
    assert "DELETE FROM" not in source


def test_modification_verrouille_code_et_famille_stables():
    source = _source(DIALOG)

    assert "self.choice_kind.Enable(False)" in source
    assert "self.ctrl_code.Enable(False)" in source
    assert "OnSupprimer" not in source
    assert "bouton_supprimer" not in source


def test_page_salarie_separe_navigation_structure_et_trois_actions_metier():
    source = _source(PAGE)

    assert "self.bouton_organismes" in source
    assert "def OnOrganismes" in source
    assert "self.bouton_ajouter" in source
    assert "self.bouton_cloturer" in source
    assert "self.bouton_nouvelle_periode" in source


def test_dialogue_structure_est_importe_seulement_sur_action_explicite():
    source = _source(RUNTIME)
    tree = ast.parse(source, filename=str(RUNTIME))

    top_level_modules = [
        node.module or ""
        for node in tree.body
        if isinstance(node, ast.ImportFrom)
    ]
    assert "Dlg.DLG_Connexions_RH" not in top_level_modules
    assert "from Dlg import DLG_Connexions_RH" in source
    assert "def OnOrganismes" in source
    assert "self._actions_runtime = None" in source


def test_ui_ne_propose_pas_de_saisie_d_authentification():
    source = _source(DIALOG).lower()
    forbidden_controls = (
        "ctrl_password",
        "ctrl_token",
        "ctrl_secret",
        "ctrl_api_key",
        "ctrl_private_key",
    )
    for token in forbidden_controls:
        assert token not in source
