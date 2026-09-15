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


def _convertir_version(texte):
    if isinstance(texte, tuple):
        return texte
    if isinstance(texte, list):
        return tuple(texte)
    prefixe = str(texte).split("-", 1)[0]
    return tuple(int(element) for element in prefixe.split("."))


class FakeDB:
    def __init__(self, tables=None, champs=None, parametres=None):
        self.tables = set(tables or ())
        self.champs = {nom: set(valeurs) for nom, valeurs in (champs or {}).items()}
        self.parametres = dict(parametres or {})
        self.creations = []
        self.ajouts = []
        self.commits = 0
        self._resultat = []

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

    def Commit(self):
        self.commits += 1

    def ExecuterReq(self, requete):
        if "SELECT nom, parametre" in requete:
            self._resultat = [
                (nom, valeur)
                for nom, valeur in self.parametres.items()
                if nom in ("version", "schema_version")
            ]
        elif "SELECT IDparametre" in requete and "schema_version" in requete:
            self._resultat = [(2,)] if "schema_version" in self.parametres else []
        else:
            self._resultat = []
        return 1

    def ResultatReq(self):
        return list(self._resultat)

    def ReqMAJ(self, nom_table, donnees, nom_id, valeur_id):
        assert nom_table == "parametres"
        self.parametres["schema_version"] = dict(donnees)["parametre"]
        self.Commit()

    def ReqInsert(self, nom_table, donnees):
        assert nom_table == "parametres"
        valeurs = dict(donnees)
        self.parametres[valeurs["nom"]] = valeurs["parametre"]
        self.Commit()
        return 2


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
    assert db.commits >= 1
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
    assert db.commits == 0
    assert rapport == {"tables_creees": (), "champs_ajoutes": ()}


def test_version_produit_ccns_ne_declenche_pas_les_migrations_historiques():
    module = _charger_module()
    db = FakeDB(parametres={"version": "0.9.2-rc2"})

    version, source = module.DeterminerVersionSchema(db, _convertir_version)

    assert version is None
    assert source == "produit_ccns"


def test_version_historique_reste_utilisable_pour_les_anciennes_bases():
    module = _charger_module()
    db = FakeDB(parametres={"version": "2.0.0.1"})

    version, source = module.DeterminerVersionSchema(db, _convertir_version)

    assert version == (2, 0, 0, 1)
    assert source == "version_historique"


def test_schema_version_dedie_est_prioritaire_et_memorise_separement():
    module = _charger_module()
    db = FakeDB(
        parametres={
            "version": "0.9.2-rc3",
            "schema_version": "2.1.1.0",
        }
    )

    version, source = module.DeterminerVersionSchema(db, _convertir_version)
    assert version == (2, 1, 1, 0)
    assert source == "schema_version"

    module.MemoriserVersionSchema(db)
    assert db.parametres["schema_version"] == "2.1.2.0"
    assert db.parametres["version"] == "0.9.2-rc3"


def test_absence_de_version_conserve_le_fallback_historique():
    module = _charger_module()
    db = FakeDB()

    version, source = module.DeterminerVersionSchema(db, _convertir_version)

    assert version == (1, 0, 5, 2)
    assert source == "fallback_historique"


def test_coque_rc3_ne_delegue_plus_la_version_produit_au_validateur_historique():
    source = TEAMWORKS.read_text(encoding="utf-8")
    bloc = source.split("def ValidationVersionFichier", 1)[1].split("def AnnonceFinancement", 1)[0]
    assert "UTILS_Schema_compat.DeterminerVersionSchema" in bloc
    assert "db_schema.Upgrade(version_schema)" in bloc
    assert "UTILS_Schema_compat.Assurer" in bloc
    assert "UTILS_Schema_compat.MemoriserVersionSchema" in bloc
    assert "super(MyFrame, self).ValidationVersionFichier" not in bloc
    assert "return True" in bloc
