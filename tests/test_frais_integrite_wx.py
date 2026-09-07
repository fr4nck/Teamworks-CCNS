from pathlib import Path
import ast


ROOT = Path(__file__).resolve().parents[1]
IMPRESSION = ROOT / "teamworks" / "Dlg" / "DLG_Impression_frais.py"
DEPLACEMENT = ROOT / "teamworks" / "Dlg" / "DLG_Saisie_deplacement.py"


def _method_source(path: Path, class_name: str, method_name: str) -> str:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and child.name == method_name:
                    lines = source.splitlines()
                    return "\n".join(lines[child.lineno - 1 : child.end_lineno])
    raise AssertionError(f"{class_name}.{method_name} introuvable dans {path}")


def test_selection_impression_frais_ne_modifie_pas_la_base():
    method = _method_source(IMPRESSION, "ListCtrl", "OnCheckItem")
    assert "GestionDB" not in method
    assert "ReqMAJ" not in method
    assert "gadgets" not in method


def test_cache_distance_preserve_les_codes_postaux_en_chaine():
    method = _method_source(DEPLACEMENT, "SaisieDeplacement", "SauvegardeDistance")
    assert "int(self.ctrl_cp_depart.GetValue())" not in method
    assert "int(self.ctrl_cp_arrivee.GetValue())" not in method
    assert "cp_depart = self.ctrl_cp_depart.GetValue()" in method
    assert "cp_arrivee = self.ctrl_cp_arrivee.GetValue()" in method
