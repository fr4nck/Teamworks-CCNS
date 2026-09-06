import io
from pathlib import Path
import zipfile

import pytest

from teamworks.Utils.UTILS_RestaurationFichiers import ExtraireFichierAtomiquement


SOURCE_SAUVEGARDE = Path("teamworks/Utils/UTILS_Sauvegarde.py")


def _archive_en_memoire(nom_fichier, contenu):
    flux = io.BytesIO()
    with zipfile.ZipFile(flux, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(nom_fichier, contenu)
    flux.seek(0)
    return flux


def test_extraction_atomique_remplace_le_fichier_apres_lecture_complete(tmp_path):
    cible = tmp_path / "teamworks_data.dat"
    cible.write_bytes(b"ancienne-base")

    flux = _archive_en_memoire("teamworks_data.dat", b"nouvelle-base-complete")
    with zipfile.ZipFile(flux, "r") as archive:
        restaure = ExtraireFichierAtomiquement(
            archive,
            "teamworks_data.dat",
            str(tmp_path),
        )

    assert cible.read_bytes() == b"nouvelle-base-complete"
    assert restaure == str(cible)
    assert list(tmp_path.glob(".teamworks-restore-*.tmp")) == []


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


class _ArchiveEnEchec:
    def open(self, nom_fichier, mode):
        assert nom_fichier == "teamworks_data.dat"
        assert mode == "r"
        return _SourceEnEchec()


def test_extraction_atomique_conserve_l_ancien_fichier_si_la_lecture_echoue(tmp_path):
    cible = tmp_path / "teamworks_data.dat"
    cible.write_bytes(b"base-originale-intacte")

    with pytest.raises(OSError, match="lecture interrompue"):
        ExtraireFichierAtomiquement(
            _ArchiveEnEchec(),
            "teamworks_data.dat",
            str(tmp_path),
        )

    assert cible.read_bytes() == b"base-originale-intacte"
    assert list(tmp_path.glob(".teamworks-restore-*.tmp")) == []


def test_restauration_legacy_utilise_l_extraction_atomique_pour_sqlite():
    source = SOURCE_SAUVEGARDE.read_text(encoding="utf-8")

    assert "UTILS_RestaurationFichiers.ExtraireFichierAtomiquement(" in source
    assert "fichierZip.extract(fichier_temp, UTILS_Fichiers.GetRepData())" not in source
