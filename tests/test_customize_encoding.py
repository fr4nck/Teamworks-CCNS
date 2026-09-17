import importlib
import sys
import types
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS = ROOT / "teamworks"


def _load_customize(monkeypatch, tmp_path):
    monkeypatch.syspath_prepend(str(TEAMWORKS))

    wx_stub = types.ModuleType("wx")
    wx_stub.GetApp = lambda: None
    monkeypatch.setitem(sys.modules, "wx", wx_stub)
    monkeypatch.setitem(sys.modules, "Chemins", types.ModuleType("Chemins"))

    fichiers_stub = types.SimpleNamespace(
        GetRepUtilisateur=lambda nom: str(tmp_path / nom)
    )

    # UTILS_Customize charge ses dépendances via UTILS_Adaptations.Import().
    # On ne simule que la localisation du fichier utilisateur : le décodage
    # doit rester celui de la vraie frontière UTILS_Encodage pour que ces
    # tests vérifient réellement UTF-8 et les anciens fichiers CP1252.
    sys.modules.pop("Utils.UTILS_Encodage", None)
    encodage = importlib.import_module("Utils.UTILS_Encodage")

    adaptations_stub = types.ModuleType("Utils.UTILS_Adaptations")

    def importer(nom):
        if nom == "Utils.UTILS_Fichiers":
            return fichiers_stub
        if nom == "Utils.UTILS_Encodage":
            return encodage
        raise AssertionError(f"Import inattendu dans le test : {nom}")

    adaptations_stub.Import = importer

    theme_stub = types.ModuleType("Utils.UTILS_Theme")
    theme_stub.enable_native_dark_mode = lambda: None
    theme_stub.install_auto_theming = lambda: None

    monkeypatch.setitem(sys.modules, "Utils.UTILS_Adaptations", adaptations_stub)
    monkeypatch.setitem(sys.modules, "Utils.UTILS_Theme", theme_stub)
    sys.modules.pop("Utils.UTILS_Customize", None)
    return importlib.import_module("Utils.UTILS_Customize")


def test_customize_reads_utf8_accents_and_writes_utf8(monkeypatch, tmp_path):
    module = _load_customize(monkeypatch, tmp_path)
    path = tmp_path / "Customize.ini"
    path.write_text(
        "[interface]\n"
        "theme = Systeme\n"
        "libelle = Équipe été – salarié\n",
        encoding="utf-8",
    )

    customize = module.Customize()

    assert customize.GetValeur("interface", "libelle") == "Équipe été – salarié"
    customize.Enregistrement()
    assert "Équipe été – salarié" in path.read_text(encoding="utf-8")


def test_customize_reads_legacy_cp1252_and_rewrites_utf8(monkeypatch, tmp_path):
    module = _load_customize(monkeypatch, tmp_path)
    path = tmp_path / "Customize.ini"
    path.write_bytes(
        "[interface]\ntheme = Système\nlibelle = équipe été\n".encode("cp1252")
    )

    brut_avant = path.read_bytes()
    assert b"Syst\xe8me" in brut_avant
    assert b"\xe9quipe \xe9t\xe9" in brut_avant

    customize = module.Customize()

    assert customize.GetValeur("interface", "theme") == "Système"
    assert customize.GetValeur("interface", "libelle") == "équipe été"

    brut_apres = path.read_bytes()

    assert "Système".encode("utf-8") in brut_apres
    assert "équipe été".encode("utf-8") in brut_apres
    assert b"Syst\xe8me" not in brut_apres
    assert b"\xe9quipe \xe9t\xe9" not in brut_apres

    texte_apres = brut_apres.decode("utf-8")
    assert "Système" in texte_apres
    assert "équipe été" in texte_apres
