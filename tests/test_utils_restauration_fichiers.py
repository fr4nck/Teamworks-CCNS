import io
from pathlib import Path
import sqlite3
import zipfile

import pytest

from teamworks.Utils import UTILS_RestaurationFichiers as restauration
from teamworks.Utils.UTILS_RestaurationFichiers import ExtraireFichierAtomiquement


SOURCE_SAUVEGARDE = Path("teamworks/Utils/UTILS_Sauvegarde.py")


def _creer_base_sqlite(path, table="donnees", valeur="originale"):
    with sqlite3.connect(path) as connexion:
        connexion.execute("CREATE TABLE %s(id INTEGER PRIMARY KEY, valeur TEXT)" % table)
        connexion.execute("INSERT INTO %s(valeur) VALUES (?)" % table, (valeur,))


def _octets_sqlite(tmp_path, nom="source.sqlite", table="donnees", valeur="nouvelle"):
    path = tmp_path / nom
    _creer_base_sqlite(path, table=table, valeur=valeur)
    contenu = path.read_bytes()
    path.unlink()
    return contenu


def _archive_en_memoire(nom_fichier=None, contenu=None, entrees=None):
    flux = io.BytesIO()
    with zipfile.ZipFile(flux, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        if entrees is not None:
            for nom, valeur in entrees:
                archive.writestr(nom, valeur)
        elif nom_fichier is not None:
            archive.writestr(nom_fichier, contenu)
    flux.seek(0)
    return flux


def _assert_base_originale(cible):
    with sqlite3.connect(cible) as connexion:
        assert connexion.execute("PRAGMA quick_check;").fetchone() == ("ok",)
        assert connexion.execute("SELECT valeur FROM donnees").fetchone() == ("originale",)


def _assert_aucun_temporaire(tmp_path):
    assert list(tmp_path.glob(".teamworks-restore-*.tmp")) == []


def test_extraction_atomique_remplace_le_fichier_apres_validation_sqlite(tmp_path):
    cible = tmp_path / "teamworks_data.dat"
    _creer_base_sqlite(cible)
    contenu = _octets_sqlite(tmp_path)

    flux = _archive_en_memoire("teamworks_data.dat", contenu)
    with zipfile.ZipFile(flux, "r") as archive:
        restaure = ExtraireFichierAtomiquement(
            archive,
            "teamworks_data.dat",
            str(tmp_path),
        )

    with sqlite3.connect(cible) as connexion:
        assert connexion.execute("SELECT valeur FROM donnees").fetchone() == ("nouvelle",)
    assert restaure == str(cible)
    _assert_aucun_temporaire(tmp_path)


class _SourceEnEchec(io.BytesIO):
    def __init__(self):
        super().__init__(b"contenu-partiel")
        self._nombre_lectures = 0

    def read(self, taille=-1):
        self._nombre_lectures += 1
        if self._nombre_lectures > 1:
            raise OSError("lecture interrompue")
        if taille < 0:
            taille = 4
        return super().read(min(taille, 4))


class _Membre:
    filename = "teamworks_data.dat"


class _ArchiveEnEchec:
    def infolist(self):
        return [_Membre()]

    def open(self, membre, mode):
        assert membre.filename == "teamworks_data.dat"
        assert mode == "r"
        return _SourceEnEchec()


def test_extraction_atomique_conserve_l_ancien_fichier_si_la_lecture_echoue(tmp_path):
    cible = tmp_path / "teamworks_data.dat"
    _creer_base_sqlite(cible)

    with pytest.raises(OSError, match="lecture interrompue"):
        ExtraireFichierAtomiquement(
            _ArchiveEnEchec(),
            "teamworks_data.dat",
            str(tmp_path),
        )

    _assert_base_originale(cible)
    _assert_aucun_temporaire(tmp_path)


def test_zip_valide_octets_non_sqlite_preserve_base(tmp_path):
    cible = tmp_path / "teamworks_data.dat"
    _creer_base_sqlite(cible)
    flux = _archive_en_memoire("teamworks_data.dat", b"pas une base sqlite")

    with zipfile.ZipFile(flux, "r") as archive:
        with pytest.raises(sqlite3.DatabaseError):
            ExtraireFichierAtomiquement(
                archive,
                "teamworks_data.dat",
                str(tmp_path),
            )

    _assert_base_originale(cible)
    _assert_aucun_temporaire(tmp_path)


def test_quick_check_non_ok_refuse_le_remplacement(tmp_path, monkeypatch):
    cible = tmp_path / "teamworks_data.dat"
    _creer_base_sqlite(cible)
    original = cible.read_bytes()
    contenu = _octets_sqlite(tmp_path)

    class Curseur:
        def execute(self, _requete):
            return None

        def fetchall(self):
            return [("corruption detectee",)]

        def close(self):
            return None

    class Connexion:
        def cursor(self):
            return Curseur()

        def close(self):
            return None

    monkeypatch.setattr(restauration.sqlite3, "connect", lambda _path: Connexion())
    flux = _archive_en_memoire("teamworks_data.dat", contenu)
    with zipfile.ZipFile(flux, "r") as archive:
        with pytest.raises(sqlite3.DatabaseError, match="quick_check"):
            ExtraireFichierAtomiquement(
                archive,
                "teamworks_data.dat",
                str(tmp_path),
            )

    assert cible.read_bytes() == original
    _assert_aucun_temporaire(tmp_path)


def test_exception_validation_sqlite_preserve_base_et_nettoie(tmp_path, monkeypatch):
    cible = tmp_path / "teamworks_data.dat"
    _creer_base_sqlite(cible)
    original = cible.read_bytes()
    contenu = _octets_sqlite(tmp_path)

    def _connexion_en_echec(_path):
        raise sqlite3.OperationalError("validation impossible")

    monkeypatch.setattr(restauration.sqlite3, "connect", _connexion_en_echec)
    flux = _archive_en_memoire("teamworks_data.dat", contenu)
    with zipfile.ZipFile(flux, "r") as archive:
        with pytest.raises(sqlite3.OperationalError, match="validation impossible"):
            ExtraireFichierAtomiquement(
                archive,
                "teamworks_data.dat",
                str(tmp_path),
            )

    assert cible.read_bytes() == original
    _assert_aucun_temporaire(tmp_path)


def test_exception_fsync_preserve_base_et_nettoie(tmp_path, monkeypatch):
    cible = tmp_path / "teamworks_data.dat"
    _creer_base_sqlite(cible)
    contenu = _octets_sqlite(tmp_path)

    def _fsync_en_echec(_fd):
        raise OSError("fsync impossible")

    monkeypatch.setattr(restauration.os, "fsync", _fsync_en_echec)
    flux = _archive_en_memoire("teamworks_data.dat", contenu)
    with zipfile.ZipFile(flux, "r") as archive:
        with pytest.raises(OSError, match="fsync impossible"):
            ExtraireFichierAtomiquement(
                archive,
                "teamworks_data.dat",
                str(tmp_path),
            )

    _assert_base_originale(cible)
    _assert_aucun_temporaire(tmp_path)


def test_exception_replace_pas_de_faux_succes_et_nettoie(tmp_path, monkeypatch):
    cible = tmp_path / "teamworks_data.dat"
    _creer_base_sqlite(cible)
    contenu = _octets_sqlite(tmp_path)

    def _replace_en_echec(_source, _destination):
        raise OSError("replace impossible")

    monkeypatch.setattr(restauration.os, "replace", _replace_en_echec)
    flux = _archive_en_memoire("teamworks_data.dat", contenu)
    with zipfile.ZipFile(flux, "r") as archive:
        with pytest.raises(OSError, match="replace impossible"):
            ExtraireFichierAtomiquement(
                archive,
                "teamworks_data.dat",
                str(tmp_path),
            )

    _assert_base_originale(cible)
    _assert_aucun_temporaire(tmp_path)


def test_archive_sans_entree_echoue_explicitement(tmp_path):
    flux = _archive_en_memoire()
    with zipfile.ZipFile(flux, "r") as archive:
        with pytest.raises(ValueError, match="absent"):
            ExtraireFichierAtomiquement(
                archive,
                "teamworks_data.dat",
                str(tmp_path),
            )
    _assert_aucun_temporaire(tmp_path)


def test_archive_entrees_dupliquees_echoue_sans_choix_arbitraire(tmp_path):
    contenu = _octets_sqlite(tmp_path)
    flux = _archive_en_memoire(
        entrees=[
            ("teamworks_data.dat", contenu),
            ("teamworks_data.dat", contenu),
        ]
    )
    with zipfile.ZipFile(flux, "r") as archive:
        with pytest.raises(ValueError, match="ambigu"):
            ExtraireFichierAtomiquement(
                archive,
                "teamworks_data.dat",
                str(tmp_path),
            )
    _assert_aucun_temporaire(tmp_path)


@pytest.mark.parametrize(
    "nom_fichier",
    [
        "../foo",
        "..\\foo",
        "/foo",
        "\\foo",
        "C:\\foo",
        "C:/foo",
        "sous-dossier/base.dat",
        "sous-dossier\\base.dat",
    ],
)
def test_extraction_atomique_refuse_les_chemins_de_fichier(tmp_path, nom_fichier):
    flux = _archive_en_memoire()
    with zipfile.ZipFile(flux, "r") as archive:
        with pytest.raises(ValueError):
            ExtraireFichierAtomiquement(
                archive,
                nom_fichier,
                str(tmp_path),
            )

    assert not (tmp_path.parent / "foo").exists()
    _assert_aucun_temporaire(tmp_path)


def test_sqlite_valide_non_teamworks_est_acceptee(tmp_path):
    cible = tmp_path / "teamworks_data.dat"
    _creer_base_sqlite(cible)
    contenu = _octets_sqlite(
        tmp_path,
        table="toto",
        valeur="sqlite-valide",
    )
    flux = _archive_en_memoire("teamworks_data.dat", contenu)

    with zipfile.ZipFile(flux, "r") as archive:
        ExtraireFichierAtomiquement(
            archive,
            "teamworks_data.dat",
            str(tmp_path),
        )

    with sqlite3.connect(cible) as connexion:
        assert connexion.execute("PRAGMA quick_check;").fetchone() == ("ok",)
        assert connexion.execute("SELECT valeur FROM toto").fetchone() == ("sqlite-valide",)
    _assert_aucun_temporaire(tmp_path)


def test_restauration_legacy_utilise_l_extraction_atomique_pour_sqlite():
    source = SOURCE_SAUVEGARDE.read_text(encoding="utf-8")

    assert "UTILS_RestaurationFichiers.ExtraireFichierAtomiquement(" in source
    assert "fichierZip.extract(fichier_temp, UTILS_Fichiers.GetRepData())" not in source
