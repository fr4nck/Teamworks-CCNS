"""Précontrôle de compatibilité d'une base Teamworks avec le runtime Qt.

Lecture seule : ce module ne crée, ne modifie et ne migre rien. Il compare le
schéma réel aux tables et colonnes que le SQL Qt utilise effectivement
(inventaire des readers/adapters de ``infrastructure/persistence`` et de
``poc/qt-theme/contract_document_adapter.py``) et classe chaque écart :

* ``BLOQUANT`` : une lecture ou écriture Qt échouerait en SQL ; Qt refuse
  d'ouvrir la base et explique quelle mise à niveau wx manque ;
* ``EVOLUTION`` : colonnes CCNS additives des contrats, absentes tant que la
  page Contrats wx n'a jamais été ouverte ; consultation possible, création
  et modification de contrat soumises à une évolution autorisée ;
* ``INFO`` : tables propres à wx (profils, e-mails, moteur ``tw_*``…), sans
  effet sur Qt.

``UpgradeDB`` n'est jamais exécuté par Qt : ses paliers TW1→TW2 créent des
fichiers PHOTOS/DOCUMENTS et relèvent de Teamworks wx.
"""

from __future__ import annotations

from dataclasses import dataclass, field

BLOQUANT = "bloquant"
EVOLUTION = "evolution"
INFO = "info"

# Dernier palier UpgradeDB connu (teamworks/UpgradeDB.py).
LAST_KNOWN_FILE_VERSION = (2, 1, 2, 0)
FIRST_TW2_FILE_VERSION = (2, 0, 0, 0)

# Colonnes indispensables au SQL Qt, par table (fichier DATA).
QT_REQUIRED_SCHEMA: dict[str, tuple[str, ...]] = {
    "personnes": (
        "IDpersonne", "nom", "prenom", "civilite", "nom_jfille", "date_naiss",
        "cp_naiss", "ville_naiss", "pays_naiss", "nationalite", "adresse_resid",
        "cp_resid", "ville_resid", "memo", "IDsituation",
    ),
    "pays": ("IDpays", "nom", "nationalite"),
    "situations": ("IDsituation", "situation"),
    "coordonnees": ("IDcoord", "categorie", "texte", "intitule", "IDpersonne"),
    "contrats": (
        "IDcontrat", "IDpersonne", "IDtype", "IDclassification", "valeur_point",
        "date_debut", "date_fin", "date_rupture", "essai", "signature", "due",
    ),
    "contrats_types": ("IDtype", "nom", "nom_abrege"),
    "contrats_class": ("IDclassification", "nom"),
    "valeurs_point": ("IDvaleur_point", "valeur", "date_debut"),
    "contrats_valchamps": ("IDcontrat",),
    "scenarios": ("IDscenario", "IDpersonne", "nom", "description", "date_debut", "date_fin"),
    "deplacements": (
        "IDdeplacement", "IDpersonne", "date", "objet", "cp_depart", "ville_depart",
        "cp_arrivee", "ville_arrivee", "distance", "aller_retour", "tarif_km",
        "IDremboursement",
    ),
    "remboursements": ("IDremboursement", "IDpersonne", "date", "montant", "listeIDdeplacement"),
    "presences": (
        "IDpresence", "IDpersonne", "date", "heure_debut", "heure_fin", "IDcategorie", "intitule",
    ),
    "cat_presences": ("IDcategorie", "nom_categorie", "couleur"),
    "periodes_vacances": ("IDperiode", "nom", "annee", "date_debut", "date_fin"),
    "questionnaire_categories": ("IDcategorie", "ordre", "visible", "couleur", "label", "type"),
    "questionnaire_questions": (
        "IDquestion", "IDcategorie", "ordre", "visible", "label", "controle", "defaut", "options",
    ),
    "questionnaire_reponses": ("IDreponse", "reponse", "IDquestion", "IDindividu"),
    "questionnaire_choix": ("IDchoix", "IDquestion", "ordre", "visible", "label"),
}

# Colonnes additives des contrats (UTILS_Contrats_schema.ADDITIVE_COLUMNS) :
# requises par la création et la modification Qt, facultatives en lecture.
CONTRACT_ENGINE_COLUMNS: tuple[tuple[str, str], ...] = (
    ("cee_qualification", "VARCHAR(32)"),
    ("convention_code", "VARCHAR(32)"),
    ("ccns_group", "VARCHAR(8)"),
    ("weekly_hours", "REAL"),
    ("gross_monthly_salary", "REAL"),
    ("gross_annual_salary", "REAL"),
    ("operation_type", "VARCHAR(24)"),
    ("previous_contract_id", "INTEGER"),
    ("trial_period_value", "INTEGER"),
    ("trial_period_unit", "VARCHAR(8)"),
)

# Tables créées par UpgradeDB mais lues uniquement par wx (ou facultatives en Qt).
WX_ONLY_TABLES: tuple[str, ...] = (
    "profils", "profils_parametres", "sauvegardes_auto", "modeles_emails",
    "contrats_documents_modeles", "tw_people", "tw_legal_profiles", "tw_contract_types",
    "tw_employment_regimes", "tw_time_organizations", "tw_contracts",
    "tw_ccns_classifications", "tw_salary_grids", "tw_salary_grid_lines",
    "tw_calculation_rules", "tw_calculation_results", "tw_anomalies",
    "tw_individual_counters",
)

_UPGRADE_HINT = (
    "Ouvrez une fois ce fichier avec Teamworks (wx) à jour : sa mise à niveau "
    "automatique (UpgradeDB) crée les éléments manquants. Qt ne lance jamais "
    "cette mise à niveau."
)


@dataclass(frozen=True)
class SchemaIssue:
    level: str
    table: str
    columns: tuple[str, ...] = ()
    message: str = ""


@dataclass(frozen=True)
class SchemaReport:
    file_version: tuple[int, ...] | None
    issues: tuple[SchemaIssue, ...] = field(default_factory=tuple)

    @property
    def compatible(self) -> bool:
        """Qt peut ouvrir la base : aucune lecture/écriture SQL ne manquera de table."""
        return not any(issue.level == BLOQUANT for issue in self.issues)

    @property
    def missing_contract_columns(self) -> tuple[str, ...]:
        for issue in self.issues:
            if issue.level == EVOLUTION and issue.table == "contrats":
                return issue.columns
        return ()

    @property
    def contract_writes_ready(self) -> bool:
        return self.compatible and not self.missing_contract_columns

    def blocking_text(self) -> str:
        lines = [issue.message for issue in self.issues if issue.level == BLOQUANT]
        return "\n".join(lines + ["", _UPGRADE_HINT]) if lines else ""

    def summary(self) -> str:
        if not self.compatible:
            return "Base incompatible avec Teamworks Qt"
        if self.missing_contract_columns:
            return (
                "Base compatible · consultation complète · création/modification de contrat "
                "après ajout des %d colonnes CCNS" % len(self.missing_contract_columns)
            )
        return "Base compatible avec Teamworks Qt"


def parse_file_version(text) -> tuple[int, ...] | None:
    try:
        parts = tuple(int(part) for part in str(text).strip().split("."))
    except (TypeError, ValueError):
        return None
    return parts or None


def _table_names(db) -> set[str]:
    return {str(row[0]) for row in (db.GetListeTables() or ()) if row}


def _column_names(db, table: str) -> set[str]:
    return {str(item[0]) for item in (db.GetListeChamps2(table) or ()) if item}


def _file_version(db, tables: set[str]) -> tuple[int, ...] | None:
    if "parametres" not in tables:
        return None
    db.ExecuterReq(
        "SELECT parametre FROM parametres WHERE categorie='fichier' AND nom='version';"
    )
    rows = db.ResultatReq() or ()
    return parse_file_version(rows[0][0]) if rows else None


def check_schema(db) -> SchemaReport:
    """Inspecte le schéma via GestionDB (SQLite ou MySQL), sans aucune écriture."""
    tables = _table_names(db)
    version = _file_version(db, tables)
    issues: list[SchemaIssue] = []

    if version is not None and version < FIRST_TW2_FILE_VERSION:
        issues.append(SchemaIssue(
            BLOQUANT, "parametres", (),
            "Fichier Teamworks 1 (version %s) : conversion TW1 → TW2 nécessaire."
            % ".".join(map(str, version)),
        ))

    for table, required in QT_REQUIRED_SCHEMA.items():
        if table not in tables:
            issues.append(SchemaIssue(BLOQUANT, table, (), "Table « %s » absente." % table))
            continue
        present = _column_names(db, table)
        missing = tuple(name for name in required if name not in present)
        if missing:
            issues.append(SchemaIssue(
                BLOQUANT, table, missing,
                "Table « %s » : colonne(s) absente(s) %s." % (table, ", ".join(missing)),
            ))

    if "contrats" in tables:
        present = _column_names(db, "contrats")
        missing = tuple(name for name, _type in CONTRACT_ENGINE_COLUMNS if name not in present)
        if missing:
            issues.append(SchemaIssue(
                EVOLUTION, "contrats", missing,
                "Contrats : %d colonne(s) CCNS additive(s) absente(s) (%s)."
                % (len(missing), ", ".join(missing)),
            ))

    absent_wx = tuple(name for name in WX_ONLY_TABLES if name not in tables)
    if absent_wx:
        issues.append(SchemaIssue(
            INFO, "*", absent_wx,
            "Tables propres à wx absentes, sans effet sur Qt : %s." % ", ".join(absent_wx),
        ))

    if version is not None and version > LAST_KNOWN_FILE_VERSION:
        issues.append(SchemaIssue(
            INFO, "parametres", (),
            "Fichier enregistré par une version plus récente (%s)." % ".".join(map(str, version)),
        ))
    return SchemaReport(file_version=version, issues=tuple(issues))
