import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_UTIL = ROOT / "teamworks" / "Utils" / "UTILS_Schema_compat.py"
TEAMWORKS = ROOT / "teamworks" / "Teamworks.py"


def _charger_module():
    spec = importlib.util.spec_from_file_location("schema_compat_rc3_test", SCHEMA_UTIL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeDB:
    def __init__(self, tables=None, champs=None):
        self.tables = set(tables or ())
        self.champs = {nom: set(valeurs) for nom, valeurs in (champs or {}).items()}
        self.creations = []
        self.ajouts = []

    def IsTableExists(self, nom_table):
        return nom_table in self.tables

    def CreationTable(self, nom_table, dico_tables):
        self.tables.add(nom_table)
        self.champs[nom_table] = {description[0] for description in dico_tables[nom_table]}
        self.creations.append(nom_table)

    def GetListeChamps2(self, nom_table):
        return [(nom, "") for nom in sorted(self.champs.get(nom_table, set()))]

    def AjoutChamp(self, nom_table, nom_champ, type_champ):
        self.champs.setdefault(nom_table, set()).add(nom_champ)
        self.ajouts.append((nom_table, nom_champ, type_champ))


def test_reparation_cree_uniquement_les_structures_manquantes():
    module = _charger_module()
    schema = {
        "sauvegardes_auto": [("IDsauvegarde", "INTEGER")],
        "adresses_mail": [
            ("IDadresse", "INTEGER"),
            ("adresse", "VARCHAR(200)"),
            ("moteur", "VARCHAR(200)"),
        ],
    }
    db = FakeDB(
        tables={"adresses_mail"},
        champs={"adresses_mail": {"IDadresse", "adresse"}},
    )

    rapport = module.Assurer(
        db,
        schema,
        tables_requises=("sauvegardes_auto", "adresses_mail"),
        champs_requis={"adresses_mail": (("moteur", "VARCHAR(200)"),)},
    )

    assert db.creations == ["sauvegardes_auto"]
    assert db.ajouts == [("adresses_mail", "moteur", "VARCHAR(200)")]
    assert rapport == {
        "tables_creees": ("sauvegardes_auto",),
        "champs_ajoutes": ("adresses_mail.moteur",),
    }


def test_reparation_est_idempotente():
    module = _charger_module()
    schema = {
        "sauvegardes_auto": [("IDsauvegarde", "INTEGER")],
        "adresses_mail": [("IDadresse", "INTEGER"), ("moteur", "VARCHAR(200)")],
    }
    db = FakeDB(
        tables={"sauvegardes_auto", "adresses_mail"},
        champs={
            "sauvegardes_auto": {"IDsauvegarde"},
            "adresses_mail": {"IDadresse", "moteur"},
        },
    )

    rapport = module.Assurer(
        db,
        schema,
        tables_requises=("sauvegardes_auto", "adresses_mail"),
        champs_requis={"adresses_mail": (("moteur", "VARCHAR(200)"),)},
    )

    assert db.creations == []
    assert db.ajouts == []
    assert rapport == {"tables_creees": (), "champs_ajoutes": ()}


def test_coque_rc3_repare_le_schema_avant_validation_historique():
    source = TEAMWORKS.read_text(encoding="utf-8")
    bloc = source.split("def ValidationVersionFichier", 1)[1].split("def AnnonceFinancement", 1)[0]
    assert "UTILS_Schema_compat.Assurer" in bloc
    assert "CORE.UpgradeDB.Tables.DB_DATA" in bloc
    assert "super(MyFrame, self).ValidationVersionFichier" in bloc
