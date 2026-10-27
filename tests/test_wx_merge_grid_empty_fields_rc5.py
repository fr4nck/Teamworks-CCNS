# -*- coding: utf-8 -*-
"""Ne pas perdre les données en filtrant les mots-clés du publiposteur."""
import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "teamworks/Dlg/DLG_Publiposteur_contrat.py"
LAZY = ROOT / "teamworks/Dlg/DLG_Fiche_individuelle_lazy.py"


def _function(name):
    tree = ast.parse(ADAPTER.read_text(encoding="utf-8"))
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    scope = {"_ESSENTIAL_CONTRACT_FIELDS": frozenset((
        "CLASSIFICATION", "QUALIFICATIONCEE", "BRUTJOUR", "BAREMECEE",
        "DATEDEBUT", "DATEFIN", "NOM", "PRENOM",
        "CONTRAT_TYPE", "CONTRAT_CLASSIFICATION",
        "CONTRAT_DATE_DEBUT", "CONTRAT_DATE_FIN",
    ))}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[])),
                 str(ADAPTER), "exec"), scope)
    return scope[name]


def test_only_hide_optional_empty_fields_without_changing_catalog():
    select = _function("_visible_contract_rows")
    data = {
        "NBREDOCUMENTS": 1,
        "MOTSCLES": [
            ("STRUCTURE_SIREN", "base"),
            ("SALARIE_NOM", "base"),
            ("CONTRAT_CLASSIFICATION", "base"),
            ("CONTRAT_SALAIRE_BRUT_MENSUEL", "base"),
            ("CUSTOM", 17),
        ],
        1: {
            "STRUCTURE_SIREN": "",
            "SALARIE_NOM": "EXEMPLE",
            "CONTRAT_CLASSIFICATION": "Animateur",
            "CONTRAT_SALAIRE_BRUT_MENSUEL": "",
            "CUSTOM": "",
        },
    }
    snapshot = (tuple(data["MOTSCLES"]), dict(data[1]))
    assert select(data) == (1, 2, 4)
    assert select(data, show_all=True) == (0, 1, 2, 3, 4)
    assert (tuple(data["MOTSCLES"]), dict(data[1])) == snapshot


def test_nonempty_field_in_second_document_remains_visible():
    select = _function("_visible_contract_rows")
    data = {
        "NBREDOCUMENTS": 2,
        "MOTSCLES": [("STRUCTURE_ADRESSE", "base"), ("AUTRE", "base")],
        1: {"STRUCTURE_ADRESSE": "", "AUTRE": ""},
        2: {"STRUCTURE_ADRESSE": "Adresse de test", "AUTRE": ""},
    }
    assert select(data) == (0,)


def test_page_switch_preserves_original_row_indexes_for_edits():
    text = ADAPTER.read_text(encoding="utf-8")
    assert "self.ShowRow(index)" in text
    assert "self.HideRow(index)" in text
    assert "_base.Page2 = original_page2" in text
    assert "self.grid.SetAfficherTous(" in text
    assert "self.BeginBatch()" in text and "self.EndBatch()" in text


def test_lazy_notebook_clips_children_only_on_windows():
    text = LAZY.read_text(encoding="utf-8")
    assert 'if wx.Platform == "__WXMSW__":' in text
    assert "style |= wx.CLIP_CHILDREN" in text
    assert "wx.Notebook.__init__(self, parent, id, style=style)" in text
    assert "self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChanged)" in text
